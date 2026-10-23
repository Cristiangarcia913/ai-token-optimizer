"""
Folder Watcher & Auto-Optimizer for Claude Web (claude.ai).
Monitors an 'inbox' folder: whenever a file is dropped, it automatically
generates the .optimized.md version in under a second for easy upload to Claude.
"""
import os
import sys
import time
import argparse
from optimizer import TokenOptimizer

if hasattr(sys.stdout, 'reconfigure'):
    try:
        sys.stdout.reconfigure(encoding='utf-8')
    except Exception:
        pass

def watch_folder(watch_dir: str, output_dir: str = None, poll_interval: float = 1.0, **kwargs):
    os.makedirs(watch_dir, exist_ok=True)
    if not output_dir:
        output_dir = os.path.join(watch_dir, "optimized_for_claude")
    os.makedirs(output_dir, exist_ok=True)

    optimizer = TokenOptimizer(encoding_name="o200k_base")
    processed_mtimes = {}

    print("=" * 72)
    print("👀 CLAUDE AUTO-OPTIMIZER (FOLDER WATCHER)")
    print("=" * 72)
    print(f"📂 Carpeta vigilada : {os.path.abspath(watch_dir)}")
    print(f"✨ Carpeta de salida: {os.path.abspath(output_dir)}")
    print("Arrastra cualquier archivo aquí y se optimizará al instante para Claude.")
    print("Pulsa Ctrl+C para detener.")
    print("-" * 72)

    try:
        while True:
            for fname in os.listdir(watch_dir):
                fpath = os.path.join(watch_dir, fname)
                if not os.path.isfile(fpath):
                    continue
                if fname.endswith('.optimized.md') or fname.startswith('.'):
                    continue

                mtime = os.path.getmtime(fpath)
                if fpath not in processed_mtimes or processed_mtimes[fpath] < mtime:
                    # File added or modified
                    time.sleep(0.3) # ensure file write has concluded
                    base_name, _ = os.path.splitext(fname)
                    out_path = os.path.join(output_dir, f"{base_name}.optimized.md")

                    try:
                        print(f"\n⚡ Detectado: {fname} -> Optimizando para Claude...")
                        res = optimizer.optimize_file(fpath, output_path=out_path, **kwargs)
                        processed_mtimes[fpath] = mtime

                        print(f"   Tokens : {res['raw_tokens']:,} -> {res['optimized_tokens']:,} (-{res['reduction_percentage']}%)")
                        print(f"   Ahorro : {res['tokens_saved']:,} tokens ahorrados")
                        print(f"   Listo  : {out_path} (¡Listo para arrastrar a Claude!)")
                    except Exception as e:
                        print(f"   ❌ Error al procesar {fname}: {e}")

            time.sleep(poll_interval)
    except KeyboardInterrupt:
        print("\nWatcher detenido.")

def main():
    parser = argparse.ArgumentParser(description="Vigila una carpeta y optimiza automáticamente archivos para Claude.")
    parser.add_argument("--watch", default="./claude_inbox", help="Carpeta a vigilar")
    parser.add_argument("--out", default=None, help="Carpeta donde guardar los archivos optimizados")
    parser.add_argument("--strip-links", action="store_true", help="Eliminar URLs de enlaces")
    parser.add_argument("--table-format", default="auto", choices=["auto", "markdown", "tsv"])
    args = parser.parse_args()

    watch_folder(
        args.watch,
        output_dir=args.out,
        strip_links=args.strip_links,
        table_format=args.table_format
    )

if __name__ == "__main__":
    main()
