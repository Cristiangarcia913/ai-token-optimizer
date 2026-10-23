"""
Unit tests for Claude Prompt Engineering & Context Assembly module.
"""
import unittest
import os
import sys

# Add parent directory
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from prompt_engineer import ClaudePromptEngineer
from optimizer import TokenOptimizer

class TestClaudePromptEngineer(unittest.TestCase):

    def test_detect_task_type(self):
        self.assertEqual(ClaudePromptEngineer.detect_task_type("revisa este código python"), "code")
        self.assertEqual(ClaudePromptEngineer.detect_task_type("analiza las métricas y tendencias de ventas"), "analysis")
        self.assertEqual(ClaudePromptEngineer.detect_task_type("haz un resumen de este pdf"), "summary")
        self.assertEqual(ClaudePromptEngineer.detect_task_type("extrae una tabla de clientes"), "extraction")

    def test_assemble_payload_structure(self):
        docs = [
            {"name": "sales.csv", "content": "col1,col2\nval1,val2"}
        ]
        prompt = "analiza las ventas"
        payload = ClaudePromptEngineer.assemble_payload(
            user_prompt=prompt,
            documents=docs,
            prevent_stalls=True,
            ban_filler=True
        )

        # 1. Check XML tags presence
        self.assertIn("<documents>", payload)
        self.assertIn('<document index="1" source="sales.csv">', payload)
        self.assertIn("</documents>", payload)
        self.assertIn("<instructions>", payload)
        self.assertIn("</instructions>", payload)
        self.assertIn("<constraints>", payload)
        self.assertIn("</constraints>", payload)

        # 2. Check position: <documents> must appear before <instructions>
        doc_pos = payload.find("<documents>")
        inst_pos = payload.find("<instructions>")
        self.assertLess(doc_pos, inst_pos, "Documents must be placed before instructions per Anthropic best practices")

        # 3. Check anti-stall and anti-filler guardrails
        self.assertIn("RESOLUCIÓN DIRECTA (CERO PREGUNTAS)", payload)
        self.assertIn("CERO RELLENO CONVERSACIONAL", payload)

    def test_create_claude_prompt_integration(self):
        optimizer = TokenOptimizer()
        sample_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "samples", "strategic_plan.docx"))
        
        res = optimizer.create_claude_prompt(
            user_prompt="evalúa el plan estratégico",
            filepaths=[sample_path],
            prevent_stalls=True
        )

        self.assertIn("payload", res)
        self.assertIn("<documents>", res["payload"])
        self.assertIn("strategic_plan.docx", res["payload"])
        self.assertGreater(res["final_payload_tokens"], 0)

if __name__ == "__main__":
    unittest.main()
