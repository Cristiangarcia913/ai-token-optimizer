"""
Source code minifier and optimizer for LLMs.
"""
import os
import re
from typing import Tuple
from .base import BaseConverter

LANG_MAP = {
    '.py': 'python',
    '.js': 'javascript',
    '.jsx': 'javascript',
    '.ts': 'typescript',
    '.tsx': 'typescript',
    '.java': 'java',
    '.c': 'c',
    '.cpp': 'cpp',
    '.h': 'c',
    '.hpp': 'cpp',
    '.cs': 'csharp',
    '.go': 'go',
    '.rs': 'rust',
    '.php': 'php',
    '.rb': 'ruby',
    '.sh': 'bash',
    '.ps1': 'powershell',
    '.sql': 'sql',
    '.css': 'css',
    '.scss': 'scss',
}

class CodeConverter(BaseConverter):
    """
    Strips redundant boilerplate license headers, collapses redundant spaces/newlines,
    and formats inside token-efficient markdown code blocks.
    """

    EXTENSIONS = set(LANG_MAP.keys())

    def can_handle(self, filepath: str) -> bool:
        ext = os.path.splitext(filepath)[1].lower()
        return ext in self.EXTENSIONS

    def convert(self, filepath: str, **kwargs) -> Tuple[str, str]:
        ext = os.path.splitext(filepath)[1].lower()
        lang = LANG_MAP.get(ext, '')

        with open(filepath, 'r', encoding='utf-8', errors='ignore') as f:
            raw_code = f.read()

        strip_licenses = kwargs.get('strip_license', True)
        strip_all_comments = kwargs.get('strip_comments', False)
        strip_docstrings = kwargs.get('strip_docstrings', False)
        compact_indent = kwargs.get('compact_indent', False)

        code = raw_code

        if strip_licenses:
            code = self._strip_license_headers(code)

        if strip_docstrings and ext == '.py':
            code = self._strip_python_docstrings(code)

        if strip_all_comments:
            code = self._strip_comments(code, ext)

        if compact_indent:
            code = self._compact_indentation(code)

        cleaned_code = self.clean_text_spacing(code)
        optimized = f"```{lang}\n{cleaned_code}\n```"

        return raw_code, optimized

    def _strip_python_docstrings(self, text: str) -> str:
        """Removes multi-line Python docstrings while preserving regular strings."""
        # Strips triple double-quoted or single-quoted docstrings following def, class, or start of module
        pattern = r'(?m)^\s*([ruRU]?)(?:"""[\s\S]*?"""|\'\'\'[\s\S]*?\'\'\')\s*$'
        return re.sub(pattern, '', text)

    def _compact_indentation(self, text: str) -> str:
        """Normalizes 4-space indentation to 2-space indentation to save BPE tokens."""
        lines = text.splitlines()
        compacted = []
        for line in lines:
            match = re.match(r'^( +)', line)
            if match:
                spaces = len(match.group(1))
                new_spaces = (spaces // 4) * 2 + (spaces % 4)
                compacted.append(' ' * new_spaces + line[spaces:])
            else:
                compacted.append(line)
        return "\n".join(compacted)

    def _strip_license_headers(self, text: str) -> str:
        """Removes top-of-file copyright/license blocks."""
        # Multi-line block comment license
        text = re.sub(
            r'^\s*/\*[\s\S]*?(Copyright|License|Licensed|Apache|MIT|GNU|Mozilla)[\s\S]*?\*/\s*',
            '',
            text,
            flags=re.IGNORECASE
        )
        # Line-by-line comment license (# or //)
        lines = text.splitlines()
        first_code_idx = 0
        in_license_block = False

        for i, line in enumerate(lines[:40]): # Check top 40 lines
            stripped = line.strip()
            if not stripped:
                continue
            if stripped.startswith(('#', '//', '--', ';')):
                if any(k in stripped.lower() for k in ['copyright', 'license', 'licensed', 'apache', 'mit', 'all rights reserved', 'http://www.apache.org']):
                    in_license_block = True
                    first_code_idx = i + 1
                elif in_license_block:
                    first_code_idx = i + 1
            else:
                break

        if in_license_block and first_code_idx > 0:
            return "\n".join(lines[first_code_idx:]).lstrip()

        return text

    def _strip_comments(self, text: str, ext: str) -> str:
        """Optional aggressive stripping of comments for extreme token budget."""
        if ext in ('.py', '.sh', '.rb'):
            return re.sub(r'#[^\n]*', '', text)
        elif ext in ('.js', '.ts', '.java', '.c', '.cpp', '.cs', '.go', '.rs'):
            text = re.sub(r'/\*[\s\S]*?\*/', '', text)
            text = re.sub(r'//[^\n]*', '', text)
            return text
        elif ext == '.sql':
            return re.sub(r'--[^\n]*', '', text)
        return text
