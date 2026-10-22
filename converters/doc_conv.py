"""
Word document (.docx) to clean Markdown converter.
"""
import os
import docx
from typing import Tuple, List
from .base import BaseConverter

class DocxConverter(BaseConverter):
    """Converts DOCX documents into clean, structured Markdown."""

    EXTENSIONS = {'.docx'}

    def can_handle(self, filepath: str) -> bool:
        ext = os.path.splitext(filepath)[1].lower()
        return ext in self.EXTENSIONS

    def convert(self, filepath: str, **kwargs) -> Tuple[str, str]:
        doc = docx.Document(filepath)
        raw_elements = []
        md_elements = []

        table_format = kwargs.get('table_format', 'markdown')

        # Process document body
        for element in doc.element.body:
            tag = element.tag.split('}')[-1]

            if tag == 'p': # Paragraph
                p = docx.text.paragraph.Paragraph(element, doc)
                text = p.text.strip()
                if not text:
                    continue

                raw_elements.append(text)
                style_name = p.style.name.lower() if p.style else ""

                if 'heading 1' in style_name or 'title' in style_name:
                    md_elements.append(f"# {text}")
                elif 'heading 2' in style_name:
                    md_elements.append(f"## {text}")
                elif 'heading 3' in style_name:
                    md_elements.append(f"### {text}")
                elif 'heading 4' in style_name:
                    md_elements.append(f"#### {text}")
                elif 'bullet' in style_name or 'list' in style_name:
                    md_elements.append(f"- {text}")
                else:
                    # Check runs for bold / italic emphasis
                    formatted_p = self._format_paragraph_runs(p)
                    md_elements.append(formatted_p)

            elif tag == 'tbl': # Table
                tbl = docx.table.Table(element, doc)
                table_matrix = []
                for row in tbl.rows:
                    row_cells = [cell.text.strip().replace("\n", " ") for cell in row.cells]
                    table_matrix.append(row_cells)
                    raw_elements.append(" | ".join(row_cells))

                if table_matrix:
                    md_elements.append(self._format_table(table_matrix, table_format))

        raw_repr = "\n\n".join(raw_elements)
        optimized = "\n\n".join(md_elements)
        return raw_repr, self.clean_text_spacing(optimized)

    def _format_paragraph_runs(self, p: docx.text.paragraph.Paragraph) -> str:
        parts = []
        for run in p.runs:
            t = run.text
            if not t:
                continue
            # Preserve bold and italic if text is meaningful
            if run.bold and run.italic:
                t = f"***{t.strip()}*** "
            elif run.bold:
                t = f"**{t.strip()}** "
            elif run.italic:
                t = f"*{t.strip()}* "
            parts.append(t)
        return "".join(parts).strip()

    def _format_table(self, matrix: List[List[str]], table_format: str) -> str:
        if not matrix:
            return ""

        # Remove duplicate cells created by merged cells
        cleaned_matrix = []
        for row in matrix:
            # de-duplicate consecutive identical cells if merged
            new_row = []
            for c in row:
                if not new_row or c != new_row[-1]:
                    new_row.append(c)
                else:
                    new_row.append("")
            cleaned_matrix.append(new_row)

        max_cols = max(len(r) for r in cleaned_matrix)
        for r in cleaned_matrix:
            while len(r) < max_cols:
                r.append("")

        if table_format == 'tsv':
            return "\n".join(["\t".join(r) for r in cleaned_matrix])

        header = cleaned_matrix[0]
        data = cleaned_matrix[1:] if len(cleaned_matrix) > 1 else []

        lines = [
            "| " + " | ".join(c.replace("|", "\\|") for c in header) + " |",
            "| " + " | ".join(["---"] * max_cols) + " |"
        ]
        for r in data:
            lines.append("| " + " | ".join(c.replace("|", "\\|") for c in r) + " |")

        return "\n".join(lines)
