"""
Runs benchmarks across all sample files and displays a detailed breakdown.
"""
import os
import glob
import sys
from optimizer import TokenOptimizer

if hasattr(sys.stdout, 'reconfigure'):
    try:
        sys.stdout.reconfigure(encoding='utf-8')
    except Exception:
        pass

def run():
    base_dir = os.path.dirname(os.path.abspath(__file__))
    samples_dir = os.path.join(base_dir, "samples")
    optimizer = TokenOptimizer()

    print(f"\n{'ARCHIVO':<28} | {'FORMATO':<12} | {'ORIGINAL':<9} | {'OPTIMIZADO':<10} | {'AHORRO (%)':<10}")
    print("-" * 80)

    files = sorted([f for f in glob.glob(os.path.join(samples_dir, "*.*")) if not f.endswith('.optimized.md')])
    for filepath in files:
        filename = os.path.basename(filepath)
        
        # Test Auto (Optimal token reduction)
        res_auto = optimizer.optimize_file(filepath, add_metadata_header=False, table_format='auto')
        print(f"{filename:<28} | {'Auto (Opt)':<12} | {res_auto['raw_tokens']:>8} | {res_auto['optimized_tokens']:>10} | -{res_auto['reduction_percentage']:>8.1f}%")
        
        # Also show Markdown if different
        if any(filepath.endswith(x) for x in ['.csv', '.tsv', '.xlsx', '.json']):
            res_md = optimizer.optimize_file(filepath, add_metadata_header=False, table_format='markdown')
            print(f"{filename:<28} | {'Markdown':<12} | {res_md['raw_tokens']:>8} | {res_md['optimized_tokens']:>10} | -{res_md['reduction_percentage']:>8.1f}%")

    print("-" * 80 + "\n")

if __name__ == "__main__":
    run()
