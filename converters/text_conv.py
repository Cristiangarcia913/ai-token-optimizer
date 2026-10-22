"""
Plain text, Markdown, and Log file optimizer.
"""
import os
import re
from typing import Tuple
from .base import BaseConverter

class TextConverter(BaseConverter):
    """
    Optimizes plain text, logs, and markdown files by stripping
    redundant whitespace, collapsing separator lines, and deduplicating log bursts.
    """

    EXTENSIONS = {'.txt', '.log', '.md', '.rst', '.env', '.ini', '.conf'}

    def can_handle(self, filepath: str) -> bool:
        ext = os.path.splitext(filepath)[1].lower()
        return ext in self.EXTENSIONS or ext == ''

    def convert(self, filepath: str, **kwargs) -> Tuple[str, str]:
        ext = os.path.splitext(filepath)[1].lower()
        with open(filepath, 'r', encoding='utf-8', errors='ignore') as f:
            raw_text = f.read()

        text = raw_text

        # Deduplicate long separator dashes/equals (e.g. 80 dashes -> 3 dashes '---')
        # BPE tokenizers waste 5-10 tokens tokenizing repetitive symbols!
        text = re.sub(r'[-=~*_]{5,}', '---', text)

        # Log file optimization: deduplicate identical repeated lines
        if ext == '.log':
            text = self._compress_log_lines(text)

        cleaned = self.clean_text_spacing(text)
        return raw_text, cleaned

    def _compress_log_lines(self, log_text: str) -> str:
        lines = log_text.splitlines()
        compressed = []
        last_line = None
        repeat_count = 0

        for line in lines:
            # Check similarity with previous line (e.g. repeated heartbeat or polling)
            # Strip timestamp prefix heuristic
            line_no_time = re.sub(r'^\d{4}-\d{2}-\d{2}[ T]\d{2}:\d{2}:\d{2}(\.\d+)?', '', line).strip()
            prev_no_time = re.sub(r'^\d{4}-\d{2}-\d{2}[ T]\d{2}:\d{2}:\d{2}(\.\d+)?', '', last_line).strip() if last_line else None

            if line_no_time and line_no_time == prev_no_time:
                repeat_count += 1
            else:
                if repeat_count > 0:
                    compressed.append(f"  [... repeated {repeat_count} more times ...]")
                    repeat_count = 0
                compressed.append(line)
                last_line = line

        if repeat_count > 0:
            compressed.append(f"  [... repeated {repeat_count} more times ...]")

        return "\n".join(compressed)
