"""Tests for using operator names as variables without $ prefix."""

import unittest
from stacker import Stacker


class TestOperatorNamesAsVariables(unittest.TestCase):
    """Test that operator names can be used as variable names without $."""

    def test_sum_as_variable(self):
        """Test using 'sum' (a built-in operator) as a variable name."""
        stacker = Stacker()
        result = stacker.eval("10 sum set sum")
        self.assertEqual(result[-1], 10)

    def test_sum_in_block_reassignment(self):
        """Test reassigning 'sum' variable inside a block."""
        stacker = Stacker()
        result = stacker.eval("0 sum set 1 3 i {sum i + sum set} do sum")
        self.assertEqual(result[-1], 6)  # 0 + 1 + 2 + 3 = 6

    def test_max_as_variable(self):
        """Test using 'max' (a built-in operator) as a variable name."""
        stacker = Stacker()
        result = stacker.eval("42 max set max")
        self.assertEqual(result[-1], 42)

    def test_min_as_variable(self):
        """Test using 'min' (a built-in operator) as a variable name."""
        stacker = Stacker()
        result = stacker.eval("99 min set min")
        self.assertEqual(result[-1], 99)

    def test_operator_name_in_dolist(self):
        """Test using operator name as accumulator in dolist."""
        stacker = Stacker()
        result = stacker.eval(
            "1 product set [2 3 4] x {product x * product set} dolist product"
        )
        self.assertEqual(result[-1], 24)  # 1 * 2 * 3 * 4 = 24

    def test_mixed_operator_and_variable(self):
        """Test that operators still work when not followed by 'set'."""
        stacker = Stacker()
        result = stacker.eval("[1 2 3 4 5] sum")
        # 'sum' should be called as operator, not variable
        self.assertEqual(result[-1], 15)

    def test_variable_then_operator_same_name(self):
        """Test using a name as both variable and operator."""
        stacker = Stacker()
        stacker.eval("100 sum set")  # Set sum as variable
        result = stacker.eval("sum")  # Get variable value
        self.assertEqual(result[-1], 100)

        # Now use sum as operator
        stacker2 = Stacker()
        result2 = stacker2.eval("[1 2 3] sum")
        self.assertEqual(result2[-1], 6)


if __name__ == "__main__":
    unittest.main()
