"""
Command Line Interface (CLI) for AI Token Optimizer.
"""
import sys
import os
import argparse

if hasattr(sys.stdout, 'reconfigure'):
    try:
        sys.stdout.reconfigure(encoding='utf-8')
    except Exception:
        pass
from optimizer import TokenOptimizer

def format_number(n: int) -> str:
    return f"{n:,}".replace(",", ".")

def print_banner():
    banner = r"""
╔══════════════════════════════════════════════════════════════════════════╗
║               🚀 AI TOKEN OPTIMIZER & CONVERTER                         ║
║     Minimiza el consumo de tokens y maximiza la legibilidad para LLMs    ║
╚══════════════════════════════════════════════════════════════════════════╝
"""
    print(banner)

def print_file_result(res: dict):
    print("=" * 72)
    print(f"📄 Archivo origen   : {res['source_path']}")
    print(f"✨ Archivo optimizado: {res['output_path']}")
    print(f"⚙️  Conversor        : {res['converter']}")
    print("-" * 72)
    print(f"🔹 Tokens Originales: {format_number(res['raw_tokens'])}")
    print(f"🟢 Tokens Optimizados: {format_number(res['optimized_tokens'])}")
    print(f"📉 Reducción        : -{res['reduction_percentage']}% ({format_number(res['tokens_saved'])} tokens ahorrados)")
    print("-" * 72)
    print("💰 Ahorro Estimado de Costes:")
    for model, costs in res['cost_savings'].items():
        if costs['per_100k_calls'] > 0.001:
            print(f"   • {model:<18}: ${costs['per_100k_calls']:.2f} / 100k peticiones  |  ${costs['per_1m_calls']:.2f} / 1M peticiones")
    print("=" * 72 + "\n")

def main():
    print_banner()
    parser = argparse.ArgumentParser(
        description="Convierte y optimiza cualquier archivo a formato de bajo consumo de tokens para IA."
    )
    parser.add_argument("path", help="Ruta al archivo o carpeta a optimizar.")
    parser.add_argument("-o", "--output", help="Ruta de destino para el archivo o carpeta optimizada.")
    parser.add_argument("-p", "--prompt",
                        help="Prompt para Claude: optimiza la consulta con las mejores prácticas de Anthropic para evitar preguntas de retorno.")
    parser.add_argument("--table-format", choices=["auto", "markdown", "tsv"], default="auto",
                        help="Formato de tablas: 'auto' (selecciona el menor consumo de tokens), 'markdown' o 'tsv'")
    parser.add_argument("--strip-comments", action="store_true",
                        help="Eliminar todos los comentarios de código fuente (ahorro extra)")
    parser.add_argument("--strip-docstrings", action="store_true",
                        help="Eliminar docstrings de Python (ahorro significativo de tokens)")
    parser.add_argument("--strip-links", action="store_true",
                        help="Eliminar URLs de enlaces en Markdown/HTML, manteniendo el texto")
    parser.add_argument("--compact-indent", action="store_true",
                        help="Comprimir sangría de 4 a 2 espacios en código")
    parser.add_argument("--no-factor-constants", action="store_true",
                        help="Desactivar la extracción de columnas constantes en JSON/tablas")
    parser.add_argument("--threads", type=int, default=4,
                        help="Número de hilos concurrentes para procesamiento en lote (default: 4)")
    parser.add_argument("--no-header", action="store_true",
                        help="No incluir la cabecera YAML de metadatos en el markdown generado")
    parser.add_argument("--tokenizer", default="o200k_base",
                        choices=["o200k_base", "cl100k_base"],
                        help="Codificador BPE a usar para el cálculo de tokens")

    args = parser.parse_args()

    optimizer = TokenOptimizer(encoding_name=args.tokenizer)
    kwargs = {
        "table_format": args.table_format,
        "strip_comments": args.strip_comments,
        "strip_docstrings": args.strip_docstrings,
        "strip_links": args.strip_links,
        "compact_indent": args.compact_indent,
        "factor_constants": not args.no_factor_constants,
        "add_metadata_header": not args.no_header,
        "workers": args.threads,
    }

    target_path = os.path.abspath(args.path)

    if not os.path.exists(target_path):
        print(f"❌ Error: La ruta especificada no existe: {target_path}")
        sys.exit(1)

    if args.prompt:
        files = [target_path] if os.path.isfile(target_path) else [
            os.path.join(target_path, f) for f in os.listdir(target_path) if os.path.isfile(os.path.join(target_path, f))
        ]
        claude_res = optimizer.create_claude_prompt(args.prompt, files, **kwargs)
        print("=" * 72)
        print("🤖 PROMPT ESTRUCTURADO PARA CLAUDE (ANTHROPIC STANDARD):")
        print("=" * 72)
        print(claude_res["payload"])
        print("=" * 72)
        print(f"📊 Métricas: Docs originales: {format_number(claude_res['raw_doc_tokens'])} tokens -> Docs optimizados: {format_number(claude_res['optimized_doc_tokens'])} tokens (-{claude_res['doc_reduction_pct']}%)")
        print(f"🔹 Payload final total para Claude: {format_number(claude_res['final_payload_tokens'])} tokens")
        print("✨ ¡Listo para copiar y pegar en Claude o enviar vía API sin preguntas de retorno!\n")
        return

    if os.path.isfile(target_path):
        print(f"🔍 Procesando archivo único: {target_path} ...\n")
        res = optimizer.optimize_file(target_path, output_path=args.output, **kwargs)
        print_file_result(res)
    else:
        print(f"📁 Procesando directorio en lote: {target_path} ...\n")
        batch_res = optimizer.optimize_directory(target_path, output_dir=args.output, **kwargs)

        print(f"✅ Procesados con éxito: {batch_res['processed_count']} archivos")
        if batch_res['failed_count'] > 0:
            print(f"⚠️  Fallidos: {batch_res['failed_count']} archivos")

        print("=" * 72)
        print(f"📊 RESUMEN GLOBAL DEL LOTE:")
        print(f"🔹 Tokens Totales Antes    : {format_number(batch_res['total_raw_tokens'])}")
        print(f"🟢 Tokens Totales Después   : {format_number(batch_res['total_opt_tokens'])}")
        print(f"📉 Ahorro Total de Tokens  : -{batch_res['overall_reduction_percentage']}% ({format_number(batch_res['overall_tokens_saved'])} tokens)")
        print("=" * 72)
        print("💰 Ahorro Financiero Global:")
        for model, costs in batch_res['cost_savings'].items():
            if costs['per_100k_calls'] > 0.001:
                print(f"   • {model:<18}: ${costs['per_100k_calls']:.2f} / 100k peticiones  |  ${costs['per_1m_calls']:.2f} / 1M peticiones")
        print("=" * 72 + "\n")

if __name__ == "__main__":
    main()
