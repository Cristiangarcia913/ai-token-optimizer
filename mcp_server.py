"""
Model Context Protocol (MCP) Server for AI Token Optimizer.
Enables Claude Desktop, Claude Code, and any MCP-compatible AI client
to automatically read local files in token-optimized format.
"""
import os
import sys
import tempfile
from typing import Optional

# Ensure project modules can be imported
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from mcp.server.mcpserver import MCPServer
from optimizer import TokenOptimizer
from tokenizer_utils import count_tokens, calculate_savings

# Initialize MCP Server
mcp = MCPServer("ai-token-optimizer")
optimizer = TokenOptimizer(encoding_name="o200k_base")

@mcp.tool()
def read_and_optimize_file(
    filepath: str,
    table_format: str = "auto",
    strip_links: bool = False,
    strip_comments: bool = False,
    strip_docstrings: bool = False,
    compact_indent: bool = False
) -> str:
    """
    Reads any local file (PDF, DOCX, XLSX, CSV, JSON, XML, HTML, Code, Logs)
    and converts it into an ultra token-efficient Markdown representation.
    Saves between 15% and 70% of context tokens before Claude processes it.
    
    Args:
        filepath: Absolute or relative path to the local file.
        table_format: Tabular data format ('auto', 'markdown', or 'tsv'). 'auto' chooses the lowest token count.
        strip_links: If True, strips URL destinations from links to save tokens.
        strip_comments: If True, strips code comments.
        strip_docstrings: If True, strips Python docstrings.
        compact_indent: If True, compresses 4-space indentation to 2-space.
    """
    abs_path = os.path.abspath(filepath)
    if not os.path.exists(abs_path):
        return f"Error: File not found at {abs_path}"

    with tempfile.NamedTemporaryFile(suffix=".out.md", delete=False) as tf:
        out_temp = tf.name

    try:
        res = optimizer.optimize_file(
            abs_path,
            output_path=out_temp,
            table_format=table_format,
            strip_links=strip_links,
            strip_comments=strip_comments,
            strip_docstrings=strip_docstrings,
            compact_indent=compact_indent,
            add_metadata_header=True
        )

        with open(out_temp, 'r', encoding='utf-8') as f:
            optimized_text = f.read()

        summary_header = (
            f"<!-- TOKEN OPTIMIZATION METRICS:\n"
            f"     Original Tokens: {res['raw_tokens']:,}\n"
            f"     Optimized Tokens: {res['optimized_tokens']:,}\n"
            f"     Tokens Saved: {res['tokens_saved']:,} (-{res['reduction_percentage']}%)\n"
            f"-->\n\n"
        )
        return summary_header + optimized_text

    except Exception as e:
        return f"Error optimizing file {abs_path}: {str(e)}"
    finally:
        if os.path.exists(out_temp):
            try: os.remove(out_temp)
            except: pass

@mcp.tool()
def compress_raw_text(
    content: str,
    extension: str = ".json",
    table_format: str = "auto",
    strip_links: bool = False
) -> str:
    """
    Compresses raw text, JSON, HTML, or code snippets into high-density Markdown.
    
    Args:
        content: The raw text content to optimize.
        extension: File extension hint (e.g. '.json', '.html', '.py', '.csv', '.xml').
        table_format: Tabular format ('auto', 'markdown', or 'tsv').
        strip_links: If True, removes URLs from hyperlinks.
    """
    if not extension.startswith('.'):
        extension = '.' + extension

    with tempfile.NamedTemporaryFile(suffix=extension, delete=False, mode='w', encoding='utf-8') as tf_in:
        tf_in.write(content)
        temp_in = tf_in.name

    out_temp = temp_in + ".out.md"
    try:
        res = optimizer.optimize_file(
            temp_in,
            output_path=out_temp,
            table_format=table_format,
            strip_links=strip_links,
            add_metadata_header=False
        )
        with open(out_temp, 'r', encoding='utf-8') as f:
            optimized_text = f.read()

        return (
            f"Tokens: {res['raw_tokens']:,} -> {res['optimized_tokens']:,} (-{res['reduction_percentage']}%)\n\n"
            + optimized_text
        )
    except Exception as e:
        return f"Error compressing text: {str(e)}"
    finally:
        if os.path.exists(temp_in):
            try: os.remove(temp_in)
            except: pass
        if os.path.exists(out_temp):
            try: os.remove(out_temp)
            except: pass

@mcp.tool()
def assemble_claude_prompt(
    user_prompt: str,
    filepaths: list[str],
    prevent_clarifying_questions: bool = True
) -> str:
    """
    Combines local files with a user prompt and wraps them in an Anthropic-engineered prompt.
    Applies XML tags (<documents>, <instructions>, <constraints>) and injects strict directives
    to prevent Claude from asking follow-up questions and avoid conversational filler.
    
    Args:
        user_prompt: The task instruction you want to give Claude.
        filepaths: List of file paths to include as context.
        prevent_clarifying_questions: Forces Claude to resolve ambiguity directly without stalling for questions.
    """
    res = optimizer.create_claude_prompt(
        user_prompt=user_prompt,
        filepaths=filepaths,
        prevent_stalls=prevent_clarifying_questions
    )
    return res["payload"]

if __name__ == "__main__":
    # Start stdio MCP transport for Claude Desktop / Claude Code
    mcp.run(transport="stdio")
