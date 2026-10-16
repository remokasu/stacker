"""Regression tests for stack display.

disp_colored used to strip the trailing character of the opening
bracket's ANSI reset code when the stack was empty, emitting a broken
escape sequence on every REPL prompt with an empty stack.
"""

import re
import unittest

from stacker.engine.data_type import String
from stacker.stacker import Stacker
from stacker.util.disp import disp_colored, disp_default

ANSI = re.compile(r"\x1b\[[0-9;]*m")


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




class TestDispDefault(unittest.TestCase):
    def test_items_are_space_separated(self):
        self.assertEqual(disp_default([3, 4]), "[3 4]")

    def test_commas_inside_strings_are_kept(self):
        self.assertEqual(disp_default([String("Hello, World!")]), "['Hello, World!']")

    def test_nested_lists_and_bools_match_the_colored_display(self):
        self.assertEqual(disp_default([[1, 2], True, 1.5]), "[[1 2] true 1.5]")

    def test_empty_stack(self):
        self.assertEqual(disp_default([]), "[]")

    def test_colored_list_keeps_commas_inside_strings(self):
        shown = ANSI.sub("", disp_colored([[1, String("b, c"), True]]))
        self.assertEqual(shown, "[[1 'b, c' true]]")

    def test_plain_and_colored_agree_on_every_item_kind(self):
        block = Stacker().eval("{1 2 +}", stack=None).pop()
        items = [1, 1.5, 1 + 2j, True, String("a, b"), "sym", [1, [2, String("c, d")]], block, len]
        self.assertEqual(ANSI.sub("", disp_colored(items)), disp_default(items))


class TestValuesSplicedIntoBlocks(unittest.TestCase):
    """A value put into a block by sub / subn / enumerate is shown like the stack shows it."""

    def shown(self, expression: str) -> str:
        return str(list(Stacker().eval(expression))[-1])

    def test_a_list_in_a_block_has_no_commas(self):
        self.assertEqual(self.shown("[1 2] sub"), "{[1 2]}")
        self.assertEqual(self.shown("[[1 2] 3] sub"), "{[[1 2] 3]}")
        self.assertEqual(self.shown("{1 2} enumerate"), "{[0 1] [1 2]}")

    def test_a_bool_in_a_block_is_lowercase(self):
        self.assertEqual(self.shown("true sub"), "{true}")

    def test_a_string_value_in_a_block_is_quoted(self):
        self.assertEqual(self.shown('"a b" sub'), '{"a b"}')

    def test_a_block_written_in_source_is_unchanged(self):
        self.assertEqual(self.shown('{[1 2] "a" 1.5 x}'), '{[1 2] "a" 1.5 x}')


if __name__ == "__main__":
    unittest.main()


class TestNullDisplay(unittest.TestCase):
    """`null` is shown as written, like `true` and `false`, not as Python's None."""

    def test_null_on_the_stack(self):
        self.assertEqual(disp_default(list(Stacker().eval("true false null"))), "[true false null]")

    def test_null_inside_a_list(self):
        self.assertEqual(disp_default(list(Stacker().eval("[null 1]"))), "[[null 1]]")

    def test_colored_display_agrees(self):
        items = list(Stacker().eval("null"))
        self.assertEqual(ANSI.sub("", disp_colored(items)), disp_default(items))
