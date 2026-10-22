"""
Base converter module for AI token optimization.
"""
import re
from abc import ABC, abstractmethod
from typing import Tuple, Optional

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
        Cleans redundant whitespace, collapses multiple newlines,
        and unifies line endings for maximum token efficiency.
        """
        if not text:
            return ""

        # Normalize line endings
        text = text.replace("\r\n", "\n").replace("\r", "\n")

        # Strip ANSI escape sequences (terminal formatting)
        ansi_escape = re.compile(r'\x1B(?:[@-Z\\-_]|\[[0-?]*[ -/]*[@-~])')
        text = ansi_escape.sub('', text)

        # Remove zero-width spaces and rare unicode whitespace bloat
        text = re.sub(r'[\u200B-\u200D\uFEFF]', '', text)

        # Replace non-breaking spaces with standard space
        text = text.replace('\u00A0', ' ')

        # Collapse trailing whitespace on lines
        lines = [re.sub(r'[ \t]+$', '', line) for line in text.split("\n")]

        # Collapse more than 2 consecutive blank lines into one blank line
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
