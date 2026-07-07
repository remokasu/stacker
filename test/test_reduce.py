"""Tests for reduce and fold higher-order functions."""

import unittest
from stacker.stacker import Stacker


class TestReduce(unittest.TestCase):
    """Test reduce/fold functionality."""

    def setUp(self):
        """Set up test fixtures."""
        self.stacker = Stacker()

    def test_reduce_sum(self):
        """Test reduce to sum a list."""
        # [1 2 3 4 5] 0 acc x {acc x +} reduce
        self.stacker.process_expression("[1 2 3 4 5] 0 acc x {acc x +} reduce")
        result = self.stacker.pop()
        self.assertEqual(result, 15)

    def test_reduce_product(self):
        """Test reduce to multiply all elements."""
        # [1 2 3 4 5] 1 acc x {acc x *} reduce
        self.stacker.process_expression("[1 2 3 4 5] 1 acc x {acc x *} reduce")
        result = self.stacker.pop()
        self.assertEqual(result, 120)

    def test_fold_sum(self):
        """Test fold (alias for reduce) to sum a list."""
        self.stacker.process_expression("[1 2 3 4 5] 0 acc x {acc x +} fold")
        result = self.stacker.pop()
        self.assertEqual(result, 15)

    def test_reduce_with_strings(self):
        """Test reduce with string concatenation."""
        self.stacker.process_expression('["a" "b" "c"] "" acc x {acc x concat} reduce')
        result = self.stacker.pop()
        self.assertEqual(result, "abc")

    def test_reduce_empty_list(self):
        """Test reduce with empty list returns initial value."""
        self.stacker.process_expression("[] 42 acc x {acc x +} reduce")
        result = self.stacker.pop()
        self.assertEqual(result, 42)

    def test_reduce_single_element(self):
        """Test reduce with single element."""
        self.stacker.process_expression("[5] 0 acc x {acc x +} reduce")
        result = self.stacker.pop()
        self.assertEqual(result, 5)

    def test_reduce_max(self):
        """Test reduce to find maximum."""
        # [3 7 2 9 1] -999999 acc x {acc x < {x} {acc} ifelse} reduce
        self.stacker.process_expression("[3 7 2 9 1] -999999 acc x {acc x < {x} {acc} ifelse} reduce")
        result = self.stacker.pop()
        self.assertEqual(result, 9)

    def test_reduce_count(self):
        """Test reduce to count elements."""
        # [1 2 3 4 5] 0 acc x {acc 1 +} reduce
        self.stacker.process_expression("[1 2 3 4 5] 0 acc x {acc 1 +} reduce")
        result = self.stacker.pop()
        self.assertEqual(result, 5)

    def test_reduce_with_nested_operations(self):
        """Test reduce with complex nested operations."""
        # Square each element and sum: [1 2 3 4] 0 acc x {acc x x * +} reduce
        self.stacker.process_expression("[1 2 3 4] 0 acc x {acc x x * +} reduce")
        result = self.stacker.pop()
        self.assertEqual(result, 30)  # 1^2 + 2^2 + 3^2 + 4^2 = 1 + 4 + 9 + 16 = 30


class TestFoldExceptionSafety(unittest.TestCase):
    """An exception inside a fold/reduce body must not permanently corrupt
    the interpreter state (regression: variables/stack were swapped
    without try/finally)."""

    def setUp(self):
        self.stacker = Stacker()

    def test_exception_in_fold_body_restores_state(self):
        from stacker.engine.data_type import stack_data
        from stacker.error import UndefinedSymbolError

        with self.assertRaises(UndefinedSymbolError):
            self.stacker.process_expression(
                "[1 2 3] 0 acc x {acc x + undefinedop123 +} fold"
            )
        # The engine stack must still be a stack_data, not a plain list
        self.assertIsInstance(self.stacker.stack, stack_data)
        # fold loop variables must not leak into the surviving scope
        self.assertNotIn("acc", self.stacker.variables)
        self.assertNotIn("x", self.stacker.variables)

    def test_fold_still_works_after_exception(self):
        from stacker.error import UndefinedSymbolError

        with self.assertRaises(UndefinedSymbolError):
            self.stacker.process_expression(
                "[1 2 3] 0 acc x {acc x + undefinedop123 +} fold"
            )
        self.stacker.process_expression("[1 2 3 4 5] 0 acc x {acc x +} fold")
        self.assertEqual(self.stacker.pop(), 15)


if __name__ == "__main__":
    unittest.main()
