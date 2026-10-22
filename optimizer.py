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
            header = (
                f"---\n"
                f"source_file: {filename}\n"
                f"converter: {converter.__class__.__name__}\n"
                f"raw_tokens: {raw_tokens}\n"
                f"optimized_tokens: {opt_tokens}\n"
                f"reduction: {savings['reduction_percentage']}%\n"
                f"---\n\n"
            )
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
