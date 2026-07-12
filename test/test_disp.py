"""Regression tests for stack display.

disp_colored used to strip the trailing character of the opening
bracket's ANSI reset code when the stack was empty, emitting a broken
escape sequence on every REPL prompt with an empty stack.
"""

import unittest

from stacker.util.disp import disp_colored


class TestDispColored(unittest.TestCase):
    def test_empty_stack_keeps_ansi_sequences_intact(self):
        out = disp_colored([])
        # Every escape sequence must be terminated; the truncation bug
        # left a dangling "\x1b[0" (reset code missing its final "m")
        self.assertNotIn("\x1b[0\x1b", out)
        self.assertTrue(out.endswith("\x1b[0m"))

    def test_single_item(self):
        out = disp_colored([42])
        self.assertIn("42", out)
        self.assertTrue(out.endswith("\x1b[0m"))

    def test_two_items_separated_by_space(self):
        out = disp_colored([1, 2])
        self.assertIn("1", out)
        self.assertIn("2", out)


if __name__ == "__main__":
    unittest.main()
