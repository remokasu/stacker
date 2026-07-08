"""Tests for SPEC-0001: nestable block comments ``#| ... |#``.

Block comments are consumed at the lexical layer (no token produced),
work in every execution path, and may span lines and nest.
"""

import os
import tempfile
import unittest

from stacker.stacker import Stacker
from stacker.runtime.exec_modes.script_mode import ScriptMode
from stacker.syntax.lexer import UnifiedLexer


class TestBlockCommentTokenization(unittest.TestCase):
    def test_block_comment_produces_no_token(self):
        self.assertEqual(UnifiedLexer("1 #| c |# 2").tokenize(), ["1", "2"])

    def test_nested_block_comment(self):
        self.assertEqual(
            UnifiedLexer("1 #| a #| b |# c |# 2").tokenize(), ["1", "2"]
        )

    def test_delimiters_inside_block_comment_are_inert(self):
        self.assertEqual(
            UnifiedLexer('#| " { [ ( |# 42').tokenize(), ["42"]
        )

    def test_block_comment_marker_inside_string_is_literal(self):
        self.assertEqual(
            UnifiedLexer('"a #| b"').tokenize(), ['"a #| b"']
        )


class TestBlockCommentEvaluation(unittest.TestCase):
    def setUp(self):
        self.stacker = Stacker()

    def test_inline_block_comment(self):
        ans = self.stacker.eval("1 #| comment |# 2 +")
        self.assertEqual(ans[-1], 3)

    def test_string_containing_marker_survives(self):
        ans = self.stacker.eval('"a #| b"')
        self.assertEqual(ans[-1], "a #| b")


class TestBlockCommentInScripts(unittest.TestCase):
    def setUp(self):
        self.stacker = Stacker()
        self.script_mode = ScriptMode(self.stacker)

    def _run_script(self, content):
        with tempfile.NamedTemporaryFile(mode="w", suffix=".stk", delete=False) as f:
            f.write(content)
            temp_file = f.name
        try:
            self.script_mode.execute_stacker_dotfile(temp_file)
        finally:
            os.unlink(temp_file)

    def test_multiline_block_comment(self):
        self._run_script("1\n#| line1\nline2 |#\n2 +\n")
        self.assertEqual(self.stacker.stack[-1], 2 + 1)

    def test_docstring_style_header(self):
        # The intended replacement for the removed docstring-comment
        # behavior (see slib/sfunction.stk)
        self._run_script(
            "#|\n  factorial: computes n!\n  usage: 5 fact\n|#\n3 4 +\n"
        )
        self.assertEqual(list(self.stacker.stack), [7])


if __name__ == "__main__":
    unittest.main()
