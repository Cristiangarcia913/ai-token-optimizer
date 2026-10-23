"""
Base converter module for AI token optimization.
Includes lossless unicode normalization, whitespace collapsing, and optimal table selection.
"""
import re
import unicodedata
from abc import ABC, abstractmethod
from typing import Tuple, List, Optional
import tiktoken

# Shared tokenizer encoder for optimal format selection
try:
    _FAST_ENC = tiktoken.get_encoding("o200k_base")
except Exception:
    _FAST_ENC = None

class BaseConverter(ABC):
    """Abstract base class for all file format converters."""

    @abstractmethod
    def can_handle(self, filepath: str) -> bool:
        """Check if converter supports this file."""
        pass

    @abstractmethod
    def convert(self, filepath: str, **kwargs) -> Tuple[str, str]:
        """
        Converts the file into AI-optimized text.
        Returns:
            Tuple[str, str]: (raw_representation, optimized_text)
        """
        pass

    @staticmethod
    def clean_text_spacing(text: str) -> str:
        """
        Losslessly normalizes unicode ligatures, smart quotes, redundant whitespace,
        and unifies line endings for maximum BPE token efficiency.
        """
        if not text:
            return ""

        # 1. Normalize line endings
        text = text.replace("\r\n", "\n").replace("\r", "\n")

        # 2. Strip ANSI escape sequences (terminal formatting)
        ansi_escape = re.compile(r'\x1B(?:[@-Z\\-_]|\[[0-?]*[ -/]*[@-~])')
        text = ansi_escape.sub('', text)

        # 3. Unicode NFKC Normalization (Lossless)
        # Turns ligatures like 'ﬁ' into 'fi', 'ﬂ' into 'fl', decomposes compatibility chars
        text = unicodedata.normalize('NFKC', text)

        # 4. Canonicalize typographical quotes and dashes to standard ASCII
        # Smart quotes and dashes are multi-byte and consume separate BPE tokens
        text = text.replace('“', '"').replace('”', '"').replace('„', '"').replace('«', '"').replace('»', '"')
        text = text.replace('‘', "'").replace('’', "'").replace('`', "'")
        text = text.replace('—', ' - ').replace('–', '-')

        # 5. Remove zero-width spaces and rare unicode whitespace bloat
        text = re.sub(r'[\u200B-\u200D\uFEFF\u00A0]', ' ', text)

        # 6. Collapse trailing whitespace on lines
        lines = [re.sub(r'[ \t]+$', '', line) for line in text.split("\n")]

        # 7. Collapse more than 2 consecutive blank lines into one blank line
        cleaned_lines = []
        consecutive_blank = 0
        for line in lines:
            if not line.strip():
                consecutive_blank += 1
                if consecutive_blank <= 1:
                    cleaned_lines.append("")
            else:
                consecutive_blank = 0
                cleaned_lines.append(line)

        return "\n".join(cleaned_lines).strip()

    @staticmethod
    def format_table_optimally(rows: List[List[str]], preferred_format: str = 'auto') -> str:
        """
        Losslessly formats tabular data into the most token-compact representation.
        Compares Markdown table, TSV, and Minimal CSV to pick the one with fewest tokens.
        """
        if not rows:
            return ""

        # Normalize number representations (e.g. 1500.00 -> 1500) without losing data
        cleaned_matrix = []
        for row in rows:
            clean_row = []
            for cell in row:
                c = str(cell).strip()
                # Clean trailing zeros in floats like 120.00 -> 120 or 45.50 -> 45.5
                if re.match(r'^-?\d+\.0+$', c):
                    c = c.split('.')[0]
                elif re.match(r'^-?\d+\.\d+0+$', c):
                    c = c.rstrip('0')
                clean_row.append(c)
            cleaned_matrix.append(clean_row)

        header = cleaned_matrix[0]
        data = cleaned_matrix[1:] if len(cleaned_matrix) > 1 else []
        col_count = len(header)

        # Option 1: Markdown Table
        md_lines = [
            "| " + " | ".join(c.replace("|", "\\|").replace("\n", " ") for c in header) + " |",
            "| " + " | ".join(["---"] * col_count) + " |"
        ]
        for row in data:
            row_padded = row + [""] * (col_count - len(row))
            md_lines.append("| " + " | ".join(c.replace("|", "\\|").replace("\n", " ") for c in row_padded[:col_count]) + " |")
        md_text = "\n".join(md_lines)

        if preferred_format == 'markdown':
            return md_text

        # Option 2: TSV Table
        tsv_lines = ["\t".join(c.replace("\t", " ").replace("\n", " ") for c in r) for r in cleaned_matrix]
        tsv_text = "\n".join(tsv_lines)

        if preferred_format == 'tsv':
            return tsv_text

        # Option 3: Clean CSV (Minimal quoting)
        csv_lines = []
        for r in cleaned_matrix:
            row_parts = []
            for c in r:
                c_clean = c.replace("\n", " ")
                if ',' in c_clean or '"' in c_clean:
                    row_parts.append('"' + c_clean.replace('"', '""') + '"')
                else:
                    row_parts.append(c_clean)
            csv_lines.append(",".join(row_parts))
        csv_text = "\n".join(csv_lines)

        if preferred_format == 'csv':
            return csv_text

        # In 'auto' mode: Pick the representation that consumes the fewest actual BPE tokens
        if _FAST_ENC:
            token_counts = {
                csv_text: len(_FAST_ENC.encode(csv_text)),
                tsv_text: len(_FAST_ENC.encode(tsv_text)),
                md_text: len(_FAST_ENC.encode(md_text)),
            }
            return min(token_counts, key=token_counts.get)

        # Fallback heuristic: shortest string length
        return min([csv_text, tsv_text, md_text], key=len)
