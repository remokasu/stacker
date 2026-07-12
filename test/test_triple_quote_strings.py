"""Tests for triple quotes as multi-line string literals (1.11.0).

Triple-quoted text is one token (delimiters preserved by the lexer,
stripped by token_rules), in every execution path: eval, script, arrays.
"""

import os
import tempfile
import unittest

from stacker.stacker import Stacker
from stacker.runtime.exec_modes.script_mode import ScriptMode
from stacker.syntax.lexer import UnifiedLexer
from stacker.syntax.token_rules import strip_string_delimiters


class TestTripleQuoteTokenization(unittest.TestCase):
    def test_triple_is_single_token(self):
        self.assertEqual(
            UnifiedLexer('""" abc """').tokenize(), ['""" abc """']
        )

    def test_triple_with_inner_quote_is_single_token(self):
        self.assertEqual(
            UnifiedLexer('""" a"b """').tokenize(), ['""" a"b """']
        )

    def test_single_quoted_strings_unchanged(self):
        self.assertEqual(
            UnifiedLexer('"a" \'b\' 1 +').tokenize(), ['"a"', "'b'", "1", "+"]
        )

    def test_strip_delimiters_handles_triples(self):
        self.assertEqual(strip_string_delimiters('""" abc """'), " abc ")
        self.assertEqual(strip_string_delimiters("'''x'''"), "x")
        self.assertEqual(strip_string_delimiters('""""""'), "")
        self.assertEqual(strip_string_delimiters('"a"'), "a")


class TestTripleQuoteEvaluation(unittest.TestCase):
    def setUp(self):
        self.stacker = Stacker()

    def test_triple_pushes_one_string(self):
        ans = self.stacker.eval('""" abc """')
        self.assertEqual(list(ans), [" abc "])

    def test_triple_preserves_newlines(self):
        ans = self.stacker.eval('"""a\nb"""')
        self.assertEqual(ans[-1], "a\nb")

    def test_triple_with_inner_quote(self):
        ans = self.stacker.eval('""" a"b """')
        self.assertEqual(ans[-1], ' a"b ')

    def test_empty_triple(self):
        ans = self.stacker.eval('""""""')
        self.assertEqual(ans[-1], "")

    def test_triple_single_quotes(self):
        ans = self.stacker.eval("''' hi '''")
        self.assertEqual(ans[-1], " hi ")

    def test_triple_in_array(self):
        ans = self.stacker.eval('["""a"""]')
        self.assertEqual(ans[-1], ["a"])


class TestTripleQuoteInScripts(unittest.TestCase):
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

    def test_multiline_string_keeps_newline(self):
        self._run_script('5 """ part1\npart2 """\n')
        self.assertEqual(list(self.stacker.stack), [5, " part1\npart2 "])

    def test_line_initial_triple_is_a_string_not_a_comment(self):
        # Breaking change in 1.11.0: the old docstring-comment behavior
        # of readtxt is gone; a line-initial triple quote is a string
        self._run_script('"""\ndoc\n"""\n')
        self.assertEqual(list(self.stacker.stack), ["\ndoc\n"])


if __name__ == "__main__":
    unittest.main()
