"""
Core Optimization Engine.
Dispatches files to appropriate converters and computes token reduction metrics.
"""
import os
import glob
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import Dict, Any, List, Optional
from converters import get_converter_for_file
from tokenizer_utils import count_tokens, calculate_savings

class TokenOptimizer:
    """Main engine for converting files into AI-friendly, token-reduced representations."""

    def __init__(self, encoding_name: str = "o200k_base"):
        self.encoding_name = encoding_name

    def optimize_file(
        self,
        filepath: str,
        output_path: Optional[str] = None,
        add_metadata_header: bool = True,
        **kwargs
    ) -> Dict[str, Any]:
        """
        Optimizes a single file for LLM consumption.
        """
        if not os.path.exists(filepath):
            raise FileNotFoundError(f"File not found: {filepath}")

        converter = get_converter_for_file(filepath)
        raw_repr, optimized_text = converter.convert(filepath, **kwargs)

        raw_tokens = count_tokens(raw_repr, self.encoding_name)
        opt_tokens = count_tokens(optimized_text, self.encoding_name)
        savings = calculate_savings(raw_tokens, opt_tokens)

        # Build final markdown content
        final_content = []
        if add_metadata_header:
            filename = os.path.basename(filepath)
            header = f"<!-- [{filename} | tokens: {raw_tokens} -> {opt_tokens} (-{savings['reduction_percentage']}%) | {converter.__class__.__name__}] -->\n\n"
            final_content.append(header)

        final_content.append(optimized_text)
        result_text = "".join(final_content)

        # Recalculate tokens including the small metadata header if added
        final_tokens = count_tokens(result_text, self.encoding_name)
        final_savings = calculate_savings(raw_tokens, final_tokens)

        # Determine output file path
        if not output_path:
            base_name, _ = os.path.splitext(filepath)
            output_path = f"{base_name}.optimized.md"

        os.makedirs(os.path.dirname(os.path.abspath(output_path)), exist_ok=True)
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(result_text)

        return {
            "source_path": filepath,
            "output_path": output_path,
            "converter": converter.__class__.__name__,
            "raw_chars": len(raw_repr),
            "opt_chars": len(result_text),
            "raw_tokens": raw_tokens,
            "optimized_tokens": final_tokens,
            "tokens_saved": final_savings["tokens_saved"],
            "reduction_percentage": final_savings["reduction_percentage"],
            "cost_savings": final_savings["cost_savings"],
        }

    def optimize_directory(
        self,
        input_dir: str,
        output_dir: Optional[str] = None,
        recursive: bool = True,
        workers: int = 4,
        **kwargs
    ) -> Dict[str, Any]:
        """
        Batch optimizes all files in a directory using multi-threading.
        """
        if not os.path.isdir(input_dir):
            raise NotADirectoryError(f"Directory not found: {input_dir}")

        if not output_dir:
            output_dir = os.path.join(input_dir, "optimized_ai")

        results: List[Dict[str, Any]] = []
        total_raw_tokens = 0
        total_opt_tokens = 0

        pattern = os.path.join(input_dir, "**", "*") if recursive else os.path.join(input_dir, "*")
        candidates = []
        for filepath in glob.glob(pattern, recursive=recursive):
            if not os.path.isfile(filepath):
                continue
            if filepath.endswith('.optimized.md') or os.path.basename(filepath).startswith('.'):
                continue
            candidates.append(filepath)

        def _worker(filepath: str):
            rel_path = os.path.relpath(filepath, input_dir)
            rel_base, _ = os.path.splitext(rel_path)
            dest_path = os.path.join(output_dir, f"{rel_base}.md")
            try:
                return self.optimize_file(filepath, output_path=dest_path, **kwargs)
            except Exception as e:
                return {
                    "source_path": filepath,
                    "error": str(e),
                    "status": "failed"
                }

        max_workers = min(workers, max(1, len(candidates)))
        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            future_to_file = {executor.submit(_worker, f): f for f in candidates}
            for future in as_completed(future_to_file):
                res = future.result()
                results.append(res)
                if "error" not in res:
                    total_raw_tokens += res["raw_tokens"]
                    total_opt_tokens += res["optimized_tokens"]

        # Sort results deterministically by source path
        results.sort(key=lambda x: x.get("source_path", ""))
        overall_savings = calculate_savings(total_raw_tokens, total_opt_tokens)

        return {
            "input_dir": input_dir,
            "output_dir": output_dir,
            "processed_count": len([r for r in results if "error" not in r]),
            "failed_count": len([r for r in results if "error" in r]),
            "total_raw_tokens": total_raw_tokens,
            "total_opt_tokens": total_opt_tokens,
            "overall_tokens_saved": overall_savings["tokens_saved"],
            "overall_reduction_percentage": overall_savings["reduction_percentage"],
            "cost_savings": overall_savings["cost_savings"],
            "files": results,
        }

    def create_claude_prompt(
        self,
        user_prompt: str,
        filepaths: List[str],
        task_type: str = "auto",
        prevent_stalls: bool = True,
        ban_filler: bool = True,
        **kwargs
    ) -> Dict[str, Any]:
        """
        Optimizes files and wraps them with an Anthropic-engineered prompt
        that eliminates conversational stalling, bans filler, and minimizes tokens.
        """
        from prompt_engineer import ClaudePromptEngineer

        docs = []
        total_raw = 0
        total_opt = 0

        kwargs_clean = dict(kwargs)
        kwargs_clean['add_metadata_header'] = False

        for path in filepaths:
            if not os.path.exists(path):
                continue
            res = self.optimize_file(path, **kwargs_clean)
            with open(res["output_path"], 'r', encoding='utf-8') as f:
                content = f.read()
            docs.append({
                "name": os.path.basename(path),
                "content": content
            })
            total_raw += res["raw_tokens"]
            total_opt += res["optimized_tokens"]

        payload = ClaudePromptEngineer.assemble_payload(
            user_prompt=user_prompt,
            documents=docs,
            task_type=task_type,
            prevent_stalls=prevent_stalls,
            ban_filler=ban_filler
        )

        payload_tokens = count_tokens(payload, self.encoding_name)

        return {
            "payload": payload,
            "raw_doc_tokens": total_raw,
            "optimized_doc_tokens": total_opt,
            "final_payload_tokens": payload_tokens,
            "doc_reduction_pct": round((total_raw - total_opt) / total_raw * 100, 2) if total_raw > 0 else 0.0,
            "documents_count": len(docs)
        }
