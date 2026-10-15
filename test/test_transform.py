import unittest

import pytest

from stacker.stacker import Stacker
from stacker.util.disp import disp_default


class TestUnit(unittest.TestCase):
    ############################
    # enumerate
    ############################
    def test_enumerate_block(self):
        stacker = Stacker()
        ans = stacker.eval("{1 2 3} enumerate list")
        self.assertEqual(ans[-1], [[0, 1], [1, 2], [2, 3]])

    def test_enumerate_list(self):
        stacker = Stacker()
        ans = stacker.eval("[1 2 3] enumerate")
        self.assertEqual(ans[-1], [[0, 1], [1, 2], [2, 3]])

    # REMOVED: test_enumerate_tuple - () now creates code blocks, not tuples

    ############################
    # sorted
    ############################
    def test_sorted_block(self):
        stacker = Stacker()
        ans = stacker.eval("{3 1 2} sorted list")
        self.assertEqual(ans[-1], [1, 2, 3])

    def test_sorted_list(self):
        stacker = Stacker()
        ans = stacker.eval("[3 1 2] sorted")
        self.assertEqual(ans[-1], [1, 2, 3])

    # REMOVED: test_sorted_tuple - () now creates code blocks, not tuples

    ############################
    # reversed
    ############################
    def test_reversed_block(self):
        stacker = Stacker()
        ans = stacker.eval("{1 2 3} reversed list")
        self.assertEqual(ans[-1], [3, 2, 1])

    def test_reversed_list(self):
        stacker = Stacker()
        ans = stacker.eval("[1 2 3] reversed")
        self.assertEqual(ans[-1], [3, 2, 1])

    # REMOVED: test_reversed_tuple - () now creates code blocks, not tuples

    ############################
    # list
    ############################
    def test_list_block(self):
        stacker = Stacker()
        ans = stacker.eval("{1 2 3} list")
        self.assertEqual(ans[-1], [1, 2, 3])

    def test_list_list(self):
        stacker = Stacker()
        ans = stacker.eval("[1 2 3] list")
        self.assertEqual(ans[-1], [1, 2, 3])

    # REMOVED: test_list_tuple - () now creates code blocks, not tuples

    # REMOVED: All tuple operator tests - tuple operator deprecated


class TestUndefinedNameArgument(unittest.TestCase):
    """An undefined name given to a transform (or to `zip`, which shares the
    argument handling) used to be treated as a one-character string."""

    def test_undefined_name_raises(self):
        from stacker.error import UndefinedSymbolError

        for expression in ("q list", "q sorted", "q reversed", "q enumerate", "q [1] zip"):
            with self.subTest(expression=expression):
                with self.assertRaises(UndefinedSymbolError):
                    Stacker().eval(expression)


class TestStringArgumentIsData(unittest.TestCase):
    """A string literal given to a transform used to be looked up as a
    variable name when one existed (`5 ab set "ab" list` tried to list 5)."""

    def test_string_with_a_variable_of_the_same_name(self):
        for expression, expected in (
            ('5 :ab set "ab" list', ["a", "b"]),
            ('5 :ab set "ab" enumerate', [[0, "a"], [1, "b"]]),
        ):
            with self.subTest(expression=expression):
                self.assertEqual(Stacker().eval(expression).pop(), expected)



@pytest.mark.parametrize(
    "expression, shown",
    [
        ("[1 2 3] [4 5 6] zip", "[[[1 4] [2 5] [3 6]]]"),
        ("[10 20] enumerate", "[[[0 10] [1 20]]]"),
    ],
)
def test_pairs_are_lists_not_python_tuples(expression, shown):
    # Tuples are not a Stacker type; a pair used to display as `(1, 4)`.
    assert disp_default(list(Stacker().eval(expression))) == shown
