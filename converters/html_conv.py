"""
HTML to clean LLM-optimized Markdown converter.
"""
import os
import re
from bs4 import BeautifulSoup, NavigableString, Tag
from typing import Tuple
from .base import BaseConverter

class HTMLConverter(BaseConverter):
    """Converts HTML files to concise, token-efficient Markdown."""

    EXTENSIONS = {'.html', '.htm', '.xhtml'}

    def can_handle(self, filepath: str) -> bool:
        ext = os.path.splitext(filepath)[1].lower()
        return ext in self.EXTENSIONS

    def convert(self, filepath: str, **kwargs) -> Tuple[str, str]:
        with open(filepath, 'r', encoding='utf-8', errors='ignore') as f:
            raw_html = f.read()

        strip_links = kwargs.get('strip_links', False)
        keep_links = False if strip_links else kwargs.get('keep_links', True)
        table_format = kwargs.get('table_format', 'auto')

        soup = BeautifulSoup(raw_html, 'html.parser')

        # 1. Remove non-content and layout tags
        tags_to_drop = [
            'script', 'style', 'noscript', 'svg', 'canvas', 'iframe',
            'head', 'meta', 'link', 'form', 'button', 'input', 'select',
            'nav', 'footer', 'aside'
        ]
        for tag in soup(tags_to_drop):
            tag.decompose()

        # Remove elements by common ad / cookie / tracking classes/ids
        for el in soup.find_all(attrs={"class": re.compile(r'(cookie|banner|advertisement|ads|popup|modal|tracker)', re.I)}):
            el.decompose()

        # Target main content if standard semantic tags exist
        content_root = soup.find('main') or soup.find('article') or soup.find('body') or soup

        # 2. Convert recursively to markdown
        md_text = self._element_to_markdown(content_root, keep_links=keep_links, table_format=table_format)
        cleaned_md = self.clean_text_spacing(md_text)

        return raw_html, cleaned_md

    def _element_to_markdown(self, element, keep_links: bool = True, table_format: str = 'markdown') -> str:
        if isinstance(element, NavigableString):
            text = str(element).strip()
            return f" {text} " if text else ""

        if not isinstance(element, Tag):
            return ""

        tag_name = element.name.lower()

        # Headings
        if tag_name in ['h1', 'h2', 'h3', 'h4', 'h5', 'h6']:
            level = int(tag_name[1])
            inner = self._get_children_text(element, keep_links)
            return f"\n\n{'#' * level} {inner.strip()}\n\n"

        # Paragraphs & Divs
        if tag_name == 'p':
            inner = self._get_children_text(element, keep_links)
            return f"\n\n{inner.strip()}\n\n"

        if tag_name in ['div', 'section', 'article']:
            inner = "".join(self._element_to_markdown(c, keep_links, table_format) for c in element.children)
            return f"\n{inner}\n"

        # Lists
        if tag_name == 'ul':
            items = []
            for li in element.find_all('li', recursive=False):
                li_text = self._get_children_text(li, keep_links).strip()
                if li_text:
                    items.append(f"- {li_text}")
            return "\n" + "\n".join(items) + "\n"

        if tag_name == 'ol':
            items = []
            for idx, li in enumerate(element.find_all('li', recursive=False), 1):
                li_text = self._get_children_text(li, keep_links).strip()
                if li_text:
                    items.append(f"{idx}. {li_text}")
            return "\n" + "\n".join(items) + "\n"

        # Blockquote
        if tag_name == 'blockquote':
            inner = self._get_children_text(element, keep_links).strip()
            return f"\n> {inner}\n\n"

        # Code block
        if tag_name == 'pre':
            code_text = element.get_text()
            return f"\n```\n{code_text.strip()}\n```\n"

        if tag_name == 'code':
            return f"`{element.get_text().strip()}`"

        # Links
        if tag_name == 'a':
            text = element.get_text().strip()
            href = element.get('href', '').strip()
            if not text:
                return ""
            if keep_links and href and not href.startswith('javascript:'):
                return f"[{text}]({href})"
            return text

        # Inline formatting
        if tag_name in ['strong', 'b']:
            text = self._get_children_text(element, keep_links).strip()
            return f"**{text}**" if text else ""

        if tag_name in ['em', 'i']:
            text = self._get_children_text(element, keep_links).strip()
            return f"*{text}*" if text else ""

        # Tables
        if tag_name == 'table':
            return self._convert_table(element, table_format)

        # Line break
        if tag_name == 'br':
            return "\n"

        if tag_name == 'hr':
            return "\n---\n"

        # Default fallback: concatenate children
        return "".join(self._element_to_markdown(c, keep_links, table_format) for c in element.children)

    def _get_children_text(self, tag: Tag, keep_links: bool) -> str:
        return "".join(self._element_to_markdown(c, keep_links) for c in tag.children)

    def _convert_table(self, table_tag: Tag, table_format: str) -> str:
        rows = []
        for tr in table_tag.find_all('tr'):
            cells = [cell.get_text().strip().replace("\n", " ").replace("|", "\\|") 
                     for cell in tr.find_all(['th', 'td'])]
            if any(cells):
                rows.append(cells)

        if not rows:
            return ""

        # Normalize column counts
        max_cols = max(len(r) for r in rows)
        for r in rows:
            while len(r) < max_cols:
                r.append("")

        if table_format == 'tsv':
            # TSV has minimal token overhead
            lines = ["\t".join(r) for r in rows]
            return "\n\n" + "\n".join(lines) + "\n\n"

        # Markdown table
        header = rows[0]
        data_rows = rows[1:] if len(rows) > 1 else []
        md_lines = [
            "| " + " | ".join(header) + " |",
            "| " + " | ".join(["---"] * max_cols) + " |"
        ]
        for row in data_rows:
            md_lines.append("| " + " | ".join(row) + " |")
        md_text = "\n\n" + "\n".join(md_lines) + "\n\n"

        if table_format == 'auto':
            tsv_lines = ["\t".join(r) for r in rows]
            tsv_text = "\n\n" + "\n".join(tsv_lines) + "\n\n"
            return tsv_text if len(tsv_text) <= len(md_text) else md_text

        return md_text
