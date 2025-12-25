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
        # Undefined symbols in lists are now treated as UndefinedSymbol objects
        # They only raise errors when used in operations
        result = stacker.eval("[x]")
        # The list should contain an UndefinedSymbol
        from stacker.engine.data_type import UndefinedSymbol

        self.assertIsInstance(result[-1][0], UndefinedSymbol)

    def test_invalid_list_2(self):
        stacker = Stacker()
        # Undefined symbols in lists are now treated as UndefinedSymbol objects
        result = stacker.eval("[x y]")
        from stacker.engine.data_type import UndefinedSymbol

        self.assertIsInstance(result[-1][0], UndefinedSymbol)
        self.assertIsInstance(result[-1][1], UndefinedSymbol)

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
        # Undefined symbols are now treated as UndefinedSymbol objects
        from stacker.engine.data_type import UndefinedSymbol

        result = stacker.eval("x")
        self.assertIsInstance(result[-1], UndefinedSymbol)
        # But using them in operations should raise an error
        with self.assertRaises(error.UndefinedSymbolError):
            stacker.eval("x 5 +")
