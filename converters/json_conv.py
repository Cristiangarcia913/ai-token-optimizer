"""
JSON, XML, and YAML optimizer for LLMs.
Features:
- Uniform array-of-dicts to high-density Markdown/TSV tables.
- Global constant column hoisting (eliminates repeated column values across rows).
- Recursive null/empty field pruning.
- Compact YAML representation for nested structures.
"""
import os
import json
import xml.etree.ElementTree as ET
import yaml
from typing import Tuple, Any, List, Dict
from .base import BaseConverter

class StructuredDataConverter(BaseConverter):
    """
    Converts verbose JSON and XML into high-density Markdown tables
    or compact YAML to eliminate repetitive keys and syntax overhead.
    """

    EXTENSIONS = {'.json', '.xml', '.yaml', '.yml'}

    def can_handle(self, filepath: str) -> bool:
        ext = os.path.splitext(filepath)[1].lower()
        return ext in self.EXTENSIONS

    def convert(self, filepath: str, **kwargs) -> Tuple[str, str]:
        ext = os.path.splitext(filepath)[1].lower()
        with open(filepath, 'r', encoding='utf-8', errors='ignore') as f:
            raw_content = f.read()

        table_format = kwargs.get('table_format', 'auto')
        prefer_table = kwargs.get('prefer_table', True)
        prune_nulls = kwargs.get('prune_nulls', True)
        factor_constants = kwargs.get('factor_constants', True)

        if ext == '.json':
            data = json.loads(raw_content)
        elif ext == '.xml':
            root = ET.fromstring(raw_content)
            data = self._xml_to_dict(root)
        else: # yaml
            data = yaml.safe_load(raw_content)

        if prune_nulls:
            data = self._prune_empty_fields(data)

        optimized = self._optimize_data(
            data,
            prefer_table=prefer_table,
            table_format=table_format,
            factor_constants=factor_constants
        )

        return raw_content, self.clean_text_spacing(optimized)

    def _prune_empty_fields(self, data: Any) -> Any:
        """Recursively removes null, empty strings, and empty collections to save tokens."""
        if isinstance(data, dict):
            cleaned = {}
            for k, v in data.items():
                if v is None or v == "":
                    continue
                v_clean = self._prune_empty_fields(v)
                if v_clean is not None and v_clean != "" and v_clean != {} and v_clean != []:
                    cleaned[k] = v_clean
            return cleaned
        elif isinstance(data, list):
            cleaned = []
            for item in data:
                if item is None or item == "":
                    continue
                item_clean = self._prune_empty_fields(item)
                if item_clean is not None and item_clean != "" and item_clean != {} and item_clean != []:
                    cleaned.append(item_clean)
            return cleaned
        return data

    def _optimize_data(
        self,
        data: Any,
        prefer_table: bool = True,
        table_format: str = 'auto',
        factor_constants: bool = True
    ) -> str:
        # Check if root is a list of flat dictionaries
        if prefer_table and isinstance(data, list) and len(data) > 0 and all(isinstance(x, dict) for x in data):
            all_keys = []
            for item in data[:50]:
                for k in item.keys():
                    if k not in all_keys:
                        all_keys.append(k)

            if 0 < len(all_keys) <= 35 and all(not isinstance(val, (dict, list)) for item in data[:5] for val in item.values()):
                return self._list_of_dicts_to_table(data, all_keys, table_format=table_format, factor_constants=factor_constants)

        # Check if dict contains prominent array fields
        if prefer_table and isinstance(data, dict):
            sections = []
            scalar_meta = {}
            for k, v in data.items():
                if isinstance(v, list) and len(v) > 0 and all(isinstance(x, dict) for x in v):
                    all_keys = []
                    for item in v[:50]:
                        for key in item.keys():
                            if key not in all_keys:
                                all_keys.append(key)
                    if 0 < len(all_keys) <= 35 and all(not isinstance(val, (dict, list)) for item in v[:5] for val in item.values()):
                        table_str = self._list_of_dicts_to_table(v, all_keys, table_format=table_format, factor_constants=factor_constants)
                        sections.append(f"### {k} ({len(v)} registros)\n\n{table_str}")
                        continue
                scalar_meta[k] = v

            if sections:
                header_yaml = yaml.dump(scalar_meta, sort_keys=False, allow_unicode=True, default_flow_style=False) if scalar_meta else ""
                combined = []
                if header_yaml.strip():
                    combined.append(f"```yaml\n{header_yaml.strip()}\n```\n")
                combined.extend(sections)
                return "\n\n".join(combined)

        # Fallback to ultra-compact YAML
        dumped_yaml = yaml.dump(data, sort_keys=False, allow_unicode=True, default_flow_style=False, indent=2)
        return f"```yaml\n{dumped_yaml.strip()}\n```"

    def _list_of_dicts_to_table(
        self,
        items: List[Dict[str, Any]],
        headers: List[str],
        table_format: str = 'auto',
        factor_constants: bool = True
    ) -> str:
        if not items or not headers:
            return ""

        active_headers = list(headers)
        constant_notes = []

        # Detect constant columns across all rows (if row count > 3)
        if factor_constants and len(items) > 3:
            for h in list(headers):
                first_val = items[0].get(h)
                if first_val is not None and all(item.get(h) == first_val for item in items):
                    # Hoist constant
                    val_str = str(first_val).strip()
                    constant_notes.append(f"`{h}={val_str}`")
                    active_headers.remove(h)

        prefix_header = f"> **Valores constantes globales:** {', '.join(constant_notes)}\n\n" if constant_notes else ""

        if not active_headers:
            return prefix_header.strip()

        # Format as TSV
        tsv_lines = ["\t".join(active_headers)]
        for item in items:
            row = [str(item.get(h, '')).replace('\n', ' ').replace('\t', ' ') for h in active_headers]
            tsv_lines.append("\t".join(row))
        tsv_text = "\n".join(tsv_lines)

        # Format as Markdown Table
        header_row = "| " + " | ".join(active_headers) + " |"
        sep_row = "| " + " | ".join(["---"] * len(active_headers)) + " |"
        md_rows = [header_row, sep_row]
        for item in items:
            row_cells = [str(item.get(h, '')).replace('\n', ' ').replace('|', '\\|') for h in active_headers]
            md_rows.append("| " + " | ".join(row_cells) + " |")
        md_text = "\n".join(md_rows)

        # In auto mode, choose between TSV and Markdown
        chosen = tsv_text if (table_format == 'tsv' or (table_format == 'auto' and len(tsv_text) <= len(md_text))) else md_text
        return prefix_header + chosen

    def _xml_to_dict(self, element: ET.Element) -> Any:
        children = list(element)
        if not children:
            return element.text or ""

        result = {}
        for child in children:
            child_res = self._xml_to_dict(child)
            tag = child.tag
            if tag in result:
                if isinstance(result[tag], list):
                    result[tag].append(child_res)
                else:
                    result[tag] = [result[tag], child_res]
            else:
                result[tag] = child_res
        return {element.tag: result}
