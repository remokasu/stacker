import unittest

from stacker.stacker import Stacker
from stacker import error
from stacker.error import (
    # StackUnderflowError,
    # StackerSyntaxError,
    UndefinedSymbolError,
    # UnexpectedTokenError,
)


class TestUnit(unittest.TestCase):
    ############################
    # valid list
    ############################
    def test_valid_list(self):
        stacker = Stacker()
        ans = stacker.eval("[1 2 3]")
        self.assertEqual(ans[-1], [1, 2, 3])

    def test_valid_list_2(self):
        stacker = Stacker()
        ans = stacker.eval("[1 2 3; 4 5 6]")
        self.assertEqual(ans[-1], [[1, 2, 3], [4, 5, 6]])

    def test_valid_list_3(self):
        stacker = Stacker()
        ans = stacker.eval("[1 2 3; 4 5 6; 7 8 9]")
        self.assertEqual(ans[-1], [[1, 2, 3], [4, 5, 6], [7, 8, 9]])

    def test_valid_list_4(self):
        stacker = Stacker()
        ans = stacker.eval("[[1 2 3; 4 5 6]; [7 8 9; 10 11 12]]")
        self.assertEqual(ans[-1], [[[1, 2, 3], [4, 5, 6]], [[7, 8, 9], [10, 11, 12]]])

    ############################
    # Invalid list
    ############################
    def test_invalid_list(self):
        stacker = Stacker()
        # A bare name inside a list literal is a reference (1.16.0): an
        # undefined one is an error, a defined one is the variable's value.
        with self.assertRaises(error.UndefinedSymbolError):
            stacker.eval("[x]")
        self.assertEqual(stacker.eval("5 x set [x]")[-1], [5])

    def test_invalid_list_2(self):
        stacker = Stacker()
        with self.assertRaises(error.UndefinedSymbolError):
            stacker.eval("[x y]")

    def test_symbol_elements(self):
        from stacker.engine.data_type import Symbol

        stacker = Stacker()
        self.assertEqual(stacker.eval("[$x $y]")[-1], [Symbol("x"), Symbol("y")])
        with self.assertRaises(error.StackerSyntaxError):
            stacker.eval("[$1]")

    ############################
    # valid tuple
    ############################

    # REMOVED: All tuple tests - () now creates code blocks, not tuples
    # test_valid_tuple, test_valid_tuple_2, test_valid_tuple_3, test_valid_tuple_4
    # test_invalid_tuple, test_invalid_tuple_2

    ############################
    # Undefined symbol
    ############################
    def test_undefined_symbol(self):
        stacker = Stacker()
        # A reference to an undefined name is an error (1.16.0); the name
        # itself is written `$x`.
        with self.assertRaises(error.UndefinedSymbolError):
            stacker.eval("x")
        with self.assertRaises(error.UndefinedSymbolError):
            stacker.eval("x 5 +")
        from stacker.engine.data_type import Symbol

        self.assertEqual(stacker.eval("$x")[-1], Symbol("x"))
