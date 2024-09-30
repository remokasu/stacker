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
        with self.assertRaises(UndefinedSymbolError):
            stacker.process_expression("[x]")

    def test_invalid_list_2(self):
        stacker = Stacker()
        with self.assertRaises(UndefinedSymbolError):
            stacker.process_expression("[x y]")

    ############################
    # valid tuple
    ############################

    def test_valid_tuple(self):
        stacker = Stacker()
        ans = stacker.eval("(1 2 3)")
        self.assertEqual(ans[-1], (1, 2, 3))

    def test_valid_tuple_2(self):
        stacker = Stacker()
        ans = stacker.eval("(1 2 3; 4 5 6)")
        self.assertEqual(ans[-1], ((1, 2, 3), (4, 5, 6)))

    def test_valid_tuple_3(self):
        stacker = Stacker()
        ans = stacker.eval("(1 2 3; 4 5 6; 7 8 9)")
        self.assertEqual(ans[-1], ((1, 2, 3), (4, 5, 6), (7, 8, 9)))

    def test_valid_tuple_4(self):
        stacker = Stacker()
        ans = stacker.eval("((1 2 3; 4 5 6); (7 8 9; 10 11 12))")
        self.assertEqual(ans[-1], (((1, 2, 3), (4, 5, 6)), ((7, 8, 9), (10, 11, 12))))

    ############################
    # Invalid tuple
    ############################

    def test_invalid_tuple(self):
        stacker = Stacker()
        with self.assertRaises(UndefinedSymbolError):
            stacker.process_expression("(x)")

    def test_invalid_tuple_2(self):
        stacker = Stacker()
        with self.assertRaises(UndefinedSymbolError):
            stacker.process_expression("(x y)")

    ############################
    # Invalid string
    ############################
    def test_invalid_string(self):
        stacker = Stacker()
        with self.assertRaises(error.UndefinedSymbolError):
            stacker.eval("x")
