"""
Automated unit tests for AI Token Optimizer.
"""
import unittest
import os
import tempfile
import sys

# Add parent dir to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from optimizer import TokenOptimizer
from tokenizer_utils import count_tokens, calculate_savings
from converters.html_conv import HTMLConverter
from converters.json_conv import StructuredDataConverter
from converters.code_conv import CodeConverter
from converters.text_conv import TextConverter

class TestTokenOptimizer(unittest.TestCase):

    def setUp(self):
        self.optimizer = TokenOptimizer(encoding_name="o200k_base")

    def test_count_tokens(self):
        text = "Hello world! This is a test for token counting."
        tokens = count_tokens(text)
        self.assertGreater(tokens, 0)
        self.assertLess(tokens, len(text))

    def test_calculate_savings(self):
        res = calculate_savings(1000, 400)
        self.assertEqual(res["tokens_saved"], 600)
        self.assertEqual(res["reduction_percentage"], 60.0)
        self.assertIn("GPT-4o (o200k)", res["cost_savings"])

    def test_html_converter(self):
        raw_html = """
        <html>
            <head><script>alert('noise');</script><style>.ad{color:red}</style></head>
            <body>
                <header><nav><a href="/home">Home</a></nav></header>
                <main>
                    <h1>Important Title</h1>
                    <p>Clean semantic content paragraph.</p>
                </main>
                <footer>Cookie policy notice</footer>
            </body>
        </html>
        """
        with tempfile.NamedTemporaryFile('w', suffix='.html', delete=False, encoding='utf-8') as tf:
            tf.write(raw_html)
            temp_path = tf.name

        try:
            conv = HTMLConverter()
            self.assertTrue(conv.can_handle(temp_path))
            raw, opt = conv.convert(temp_path)
            self.assertIn("# Important Title", opt)
            self.assertIn("Clean semantic content paragraph.", opt)
            self.assertNotIn("alert('noise')", opt)
            self.assertNotIn("Cookie policy notice", opt)
        finally:
            os.remove(temp_path)

    def test_json_converter_table_and_constants(self):
        data = [
            {"id": 1, "status": "active", "name": "Alpha", "empty_val": None},
            {"id": 2, "status": "active", "name": "Beta", "empty_val": None},
            {"id": 3, "status": "active", "name": "Gamma", "empty_val": None},
            {"id": 4, "status": "active", "name": "Delta", "empty_val": None},
        ]
        import json
        with tempfile.NamedTemporaryFile('w', suffix='.json', delete=False, encoding='utf-8') as tf:
            json.dump(data, tf)
            temp_path = tf.name

        try:
            conv = StructuredDataConverter()
            self.assertTrue(conv.can_handle(temp_path))
            raw, opt = conv.convert(temp_path, factor_constants=True, prune_nulls=True)
            self.assertIn("status=active", opt) # Constant hoisted
            self.assertNotIn("empty_val", opt)  # Null pruned
            self.assertIn("Alpha", opt)
        finally:
            os.remove(temp_path)

    def test_code_converter_license_stripping(self):
        raw_code = '''# Copyright (c) 2024 Acme Corp.
# Licensed under Apache License 2.0.
# All rights reserved.

def add(a: int, b: int) -> int:
    return a + b
'''
        with tempfile.NamedTemporaryFile('w', suffix='.py', delete=False, encoding='utf-8') as tf:
            tf.write(raw_code)
            temp_path = tf.name

        try:
            conv = CodeConverter()
            self.assertTrue(conv.can_handle(temp_path))
            raw, opt = conv.convert(temp_path, strip_license=True)
            self.assertNotIn("Copyright", opt)
            self.assertIn("def add", opt)
        finally:
            os.remove(temp_path)

    def test_text_converter_deduplication(self):
        raw_text = "Title\n" + ("=" * 80) + "\nBody text with huge line dashes."
        with tempfile.NamedTemporaryFile('w', suffix='.txt', delete=False, encoding='utf-8') as tf:
            tf.write(raw_text)
            temp_path = tf.name

        try:
            conv = TextConverter()
            raw, opt = conv.convert(temp_path)
            self.assertNotIn("=" * 80, opt)
            self.assertIn("---", opt)
        finally:
            os.remove(temp_path)

    def test_lossless_unicode_normalization(self):
        from converters.base import BaseConverter
        # Test ligatures and smart quotes
        raw = 'El “informe ﬁnanciero” tiene 12.00 € y guiones – largos.'
        cleaned = BaseConverter.clean_text_spacing(raw)
        self.assertIn('financiero', cleaned) # ligature 'fi' normalized losslessly
        self.assertIn('"informe financiero"', cleaned) # smart quotes normalized to ascii
        self.assertNotIn('“', cleaned)

    def test_format_table_optimally_lossless(self):
        from converters.base import BaseConverter
        rows = [
            ["ID", "Name", "Score"],
            ["1", "Alice", "95.00"],
            ["2", "Bob", "88.50"]
        ]
        res = BaseConverter.format_table_optimally(rows, preferred_format='auto')
        self.assertIn("Alice", res)
        self.assertIn("Bob", res)
        self.assertIn("95", res) # 95.00 normalized to 95 without information loss
        self.assertIn("88.5", res)

if __name__ == '__main__':
    unittest.main()
