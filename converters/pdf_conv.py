"""
PDF to clean Markdown converter with deduplication of recurring headers/footers.
"""
import os
import re
from typing import Tuple, List, Dict
from pypdf import PdfReader
from .base import BaseConverter

class PDFConverter(BaseConverter):
    """
    Extracts text from PDF, removes recurring page headers/footers,
    joins hyphenated words, and unifies broken lines.
    """

    EXTENSIONS = {'.pdf'}

    def can_handle(self, filepath: str) -> bool:
        ext = os.path.splitext(filepath)[1].lower()
        return ext in self.EXTENSIONS

    def convert(self, filepath: str, **kwargs) -> Tuple[str, str]:
        reader = PdfReader(filepath)
        page_texts = []
        raw_full = []

        for page in reader.pages:
            t = page.extract_text() or ""
            raw_full.append(t)
            page_texts.append(t.splitlines())

        raw_repr = "\n\n--- PAGE BREAK ---\n\n".join(raw_full)

        # 1. Detect recurring headers and footers
        cleaned_pages = self._remove_recurring_headers_footers(page_texts)

        # 2. Join lines, fix hyphenation, and structure markdown
        optimized_pages = []
        for idx, page_lines in enumerate(cleaned_pages, 1):
            page_content = self._process_page_lines(page_lines)
            if page_content:
                optimized_pages.append(f"<!-- Page {idx} -->\n\n{page_content}")

        optimized = "\n\n---\n\n".join(optimized_pages)
        return raw_repr, self.clean_text_spacing(optimized)

    def _remove_recurring_headers_footers(self, page_texts: List[List[str]]) -> List[List[str]]:
        if len(page_texts) <= 1:
            return page_texts

        # Count frequencies of first 2 lines and last 2 lines across pages
        header_candidates: Dict[str, int] = {}
        footer_candidates: Dict[str, int] = {}

        for lines in page_texts:
            clean_lines = [l.strip() for l in lines if l.strip()]
            if len(clean_lines) >= 1:
                header_candidates[clean_lines[0]] = header_candidates.get(clean_lines[0], 0) + 1
            if len(clean_lines) >= 2:
                header_candidates[clean_lines[1]] = header_candidates.get(clean_lines[1], 0) + 1
            if len(clean_lines) >= 1:
                footer_candidates[clean_lines[-1]] = footer_candidates.get(clean_lines[-1], 0) + 1
            if len(clean_lines) >= 2:
                footer_candidates[clean_lines[-2]] = footer_candidates.get(clean_lines[-2], 0) + 1

        total_pages = len(page_texts)
        # Recurring threshold: occurs on >= 40% of pages (or page number patterns)
        threshold = max(2, int(total_pages * 0.4))

        recurring_headers = {k for k, v in header_candidates.items() if v >= threshold}
        recurring_footers = {k for k, v in footer_candidates.items() if v >= threshold}

        page_num_regex = re.compile(r'^(page\s+\d+(\s+of\s+\d+)?|\d+\s*/\s*\d+|\d+)$', re.I)

        cleaned_pages = []
        for lines in page_texts:
            clean_lines = [l.strip() for l in lines if l.strip()]
            filtered = []
            for idx, line in enumerate(clean_lines):
                # Check recurring headers / footers
                if (idx < 2 and line in recurring_headers) or (idx >= len(clean_lines) - 2 and line in recurring_footers):
                    continue
                # Check pure page numbers
                if page_num_regex.match(line):
                    continue
                filtered.append(line)
            cleaned_pages.append(filtered)

        return cleaned_pages

    def _process_page_lines(self, lines: List[str]) -> str:
        if not lines:
            return ""

        # Join hyphenated line breaks: "exam-\nple" -> "example"
        joined_lines = []
        skip_next = False

        for i in range(len(lines)):
            if skip_next:
                skip_next = False
                continue

            current = lines[i]
            if i + 1 < len(lines):
                next_line = lines[i + 1]
                # Hyphenation check
                if current.endswith('-') and len(current) > 2 and current[-2].isalpha() and next_line and next_line[0].isalpha():
                    joined = current[:-1] + next_line
                    joined_lines.append(joined)
                    skip_next = True
                    continue

                # Soft wrap check: current line does not end with sentence-ending punctuation (. ? !)
                # and next line is not a bullet point, heading or numbered item
                is_bullet = bool(re.match(r'^[•–\-*]|\d+\.\s', next_line.strip()))
                is_header = len(next_line.strip()) < 60 and (next_line.strip().isupper() or next_line.strip().endswith(':'))
                if current and current[-1] not in '.!?:' and not is_bullet and not is_header:
                    joined_lines.append(current + " " + next_line.strip())
                    skip_next = True
                    continue

            joined_lines.append(current)

        # Detect headers by heuristics (ALL CAPS, short lines, or numbered titles)
        formatted = []
        for line in joined_lines:
            stripped = line.strip()
            if not stripped:
                continue
            # Header heuristic: short, starts with number or title case
            if len(stripped) < 70 and (stripped.isupper() or re.match(r'^((\d+\.)+\d*|[A-Z][a-z]+(\s+[A-Z][a-z]+)*):?$', stripped)):
                formatted.append(f"\n### {stripped}\n")
            elif stripped.startswith(('•', '–', '-', '*')):
                clean_bullet = re.sub(r'^[•–\-*]\s*', '', stripped)
                formatted.append(f"- {clean_bullet}")
            else:
                formatted.append(stripped)

        return "\n".join(formatted)
