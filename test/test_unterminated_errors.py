"""Tests for unterminated-construct syntax errors (1.11.0).

Finalized input (eval / script / -e) with an unterminated string, array,
block, or block comment raises UnterminatedTokenError instead of the old
silent token fusion. ``analyze_terminals`` reports the open construct
without raising, for interactive continuation input.
"""

import os
import tempfile
import unittest

from stacker.error import StackerSyntaxError, UnterminatedTokenError
from stacker.stacker import Stacker
from stacker.runtime.exec_modes.script_mode import ScriptMode
from stacker.syntax.lexer import analyze_terminals


class TestUnterminatedRaises(unittest.TestCase):
    def setUp(self):
        self.stacker = Stacker()

    def _assert_unterminated(self, expression):
        with self.assertRaises(UnterminatedTokenError):
            self.stacker.eval(expression)

    def test_unterminated_double_quote(self):
        self._assert_unterminated('"broken')

    def test_unterminated_single_quote(self):
        self._assert_unterminated("'broken")

    def test_unterminated_triple_quote(self):
        self._assert_unterminated('"""broken')

    def test_unterminated_array(self):
        self._assert_unterminated("[1 2")

    def test_unterminated_block(self):
        self._assert_unterminated("{1 2 +")

    def test_unterminated_block_comment(self):
        self._assert_unterminated("#| broken")

    def test_is_a_syntax_error(self):
        # Existing StackerSyntaxError handlers must keep catching it
        with self.assertRaises(StackerSyntaxError):
            self.stacker.eval('"broken')

    def test_terminated_input_still_works(self):
        ans = self.stacker.eval('"ok" 1 2 +')
        self.assertEqual(list(ans), ["ok", 3])


class TestAnalyzeTerminals(unittest.TestCase):
    def test_complete_expression(self):
        state = analyze_terminals("1 2 +")
        self.assertTrue(state.complete)
        self.assertIsNone(state.open_construct)

    def test_open_string(self):
        state = analyze_terminals('"abc')
        self.assertFalse(state.complete)
        self.assertEqual(state.open_construct, "string")

    def test_open_triple_string(self):
        state = analyze_terminals('"""abc\ndef')
        self.assertFalse(state.complete)
        self.assertEqual(state.open_construct, "string")
        self.assertEqual(state.start_line, 1)

    def test_open_array(self):
        state = analyze_terminals("[1 2")
        self.assertFalse(state.complete)
        self.assertEqual(state.open_construct, "array")

    def test_open_block(self):
        state = analyze_terminals("{1 2 +")
        self.assertFalse(state.complete)
        self.assertEqual(state.open_construct, "block")

    def test_open_block_comment(self):
        state = analyze_terminals("#| note")
        self.assertFalse(state.complete)
        self.assertEqual(state.open_construct, "block comment")

    def test_start_line_counts_newlines(self):
        state = analyze_terminals('1 2\n"abc')
        self.assertFalse(state.complete)
        self.assertEqual(state.start_line, 2)

    def test_line_comment_at_end_is_complete(self):
        state = analyze_terminals("1 2 + # trailing comment")
        self.assertTrue(state.complete)


class TestUnterminatedInScripts(unittest.TestCase):
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

    def test_unterminated_string_reports_file_line(self):
        with self.assertRaises(UnterminatedTokenError) as ctx:
            self._run_script('1 2 +\n"broken\n')
        self.assertEqual(ctx.exception.start_line, 2)
        self.assertIn("line 2", str(ctx.exception))

    def test_unterminated_block_comment_reports_file_line(self):
        with self.assertRaises(UnterminatedTokenError) as ctx:
            self._run_script("1 2 +\n\n#| never closed\n")
        self.assertEqual(ctx.exception.start_line, 3)


if __name__ == "__main__":
    unittest.main()
