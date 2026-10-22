"""
Spreadsheet and Tabular data optimizer (CSV, TSV, XLSX).
"""
import os
import csv
import io
import openpyxl
from typing import Tuple, List
from .base import BaseConverter

class SheetConverter(BaseConverter):
    """
    Extracts tabular data from CSV, TSV, and Excel files into
    clean, dense Markdown or TSV format.
    """

    EXTENSIONS = {'.csv', '.tsv', '.xlsx', '.xls'}

    def can_handle(self, filepath: str) -> bool:
        ext = os.path.splitext(filepath)[1].lower()
        return ext in self.EXTENSIONS

    def convert(self, filepath: str, **kwargs) -> Tuple[str, str]:
        ext = os.path.splitext(filepath)[1].lower()
        table_format = kwargs.get('table_format', 'markdown')
        max_rows = kwargs.get('max_rows', 5000)

        if ext in ('.xlsx', '.xls'):
            raw_repr, optimized = self._convert_excel(filepath, table_format, max_rows)
        else:
            raw_repr, optimized = self._convert_delimited(filepath, ext, table_format, max_rows)

        return raw_repr, self.clean_text_spacing(optimized)

    def _convert_delimited(self, filepath: str, ext: str, table_format: str, max_rows: int) -> Tuple[str, str]:
        with open(filepath, 'r', encoding='utf-8', errors='ignore') as f:
            raw_content = f.read()

        delimiter = '\t' if ext == '.tsv' else ','
        reader = csv.reader(io.StringIO(raw_content), delimiter=delimiter)
        raw_rows = [row for row in reader]

        pruned = self._prune_table(raw_rows)[:max_rows]
        optimized = self._format_table(pruned, table_format)
        return raw_content, optimized

    def _convert_excel(self, filepath: str, table_format: str, max_rows: int) -> Tuple[str, str]:
        wb = openpyxl.load_workbook(filepath, data_only=True, read_only=True)
        sheets_out = []
        raw_rows_total = []

        for sheetname in wb.sheetnames:
            ws = wb[sheetname]
            rows = []
            for row in ws.iter_rows(values_only=True):
                str_row = [str(cell) if cell is not None else "" for cell in row]
                rows.append(str_row)
                if len(rows) >= max_rows:
                    break

            pruned = self._prune_table(rows)
            if pruned:
                raw_rows_total.extend(pruned)
                table_text = self._format_table(pruned, table_format)
                sheets_out.append(f"## Sheet: {sheetname}\n\n{table_text}")

        wb.close()
        # Raw representation is standard CSV representation of extracted sheets
        raw_repr = "\n".join([",".join(f'"{c}"' for c in r) for r in raw_rows_total])
        optimized = "\n\n".join(sheets_out)
        return raw_repr, optimized

    def _prune_table(self, rows: List[List[str]]) -> List[List[str]]:
        """Removes trailing empty rows and trailing empty columns."""
        if not rows:
            return []

        # Find last non-empty column index
        max_valid_col = -1
        for row in rows:
            for i, val in enumerate(row):
                if str(val).strip():
                    if i > max_valid_col:
                        max_valid_col = i

        if max_valid_col == -1:
            return []

        # Trim columns and filter out completely empty rows
        cleaned = []
        for row in rows:
            trimmed_row = [str(c).strip() for c in row[:max_valid_col + 1]]
            if any(trimmed_row):
                cleaned.append(trimmed_row)

        return cleaned

    def _format_table(self, rows: List[List[str]], table_format: str) -> str:
        if not rows:
            return ""

        if table_format == 'tsv':
            lines = ["\t".join(r) for r in rows]
            return "\n".join(lines)

        if table_format == 'auto':
            # Compare TSV vs Markdown and pick the more token-efficient one
            tsv_lines = ["\t".join(r) for r in rows]
            tsv_text = "\n".join(tsv_lines)
            
            # Markdown table
            header = rows[0]
            data = rows[1:] if len(rows) > 1 else []
            col_count = len(header)
            md_lines = [
                "| " + " | ".join(c.replace("|", "\\|").replace("\n", " ") for c in header) + " |",
                "| " + " | ".join(["---"] * col_count) + " |"
            ]
            for row in data:
                row_padded = row + [""] * (col_count - len(row))
                md_lines.append("| " + " | ".join(c.replace("|", "\\|").replace("\n", " ") for c in row_padded[:col_count]) + " |")
            md_text = "\n".join(md_lines)

            # TSV is virtually always fewer tokens than markdown pipes
            return tsv_text if len(tsv_text) <= len(md_text) else md_text

        # Markdown Table
        header = rows[0]
        data = rows[1:] if len(rows) > 1 else []
        col_count = len(header)

        lines = [
            "| " + " | ".join(c.replace("|", "\\|").replace("\n", " ") for c in header) + " |",
            "| " + " | ".join(["---"] * col_count) + " |"
        ]
        for row in data:
            # Pad row if necessary
            row_padded = row + [""] * (col_count - len(row))
            lines.append("| " + " | ".join(c.replace("|", "\\|").replace("\n", " ") for c in row_padded[:col_count]) + " |")

        return "\n".join(lines)
