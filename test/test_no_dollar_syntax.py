"""Tests for the new syntax without $ prefix for variable names."""

import unittest
from stacker import Stacker


class TestNoDollarSyntax(unittest.TestCase):
    """Test cases for variable/function definitions without $ prefix."""

    def setUp(self):
        """Set up a fresh Stacker instance for each test."""
        self.stacker = Stacker()

    def test_set_without_dollar(self):
        """Test variable assignment without $ prefix."""
        stacker = Stacker()  # Fresh instance
        result = stacker.eval("3 x set x")
        self.assertEqual(result[-1], 3)

    def test_set_multiple_variables_without_dollar(self):
        """Test multiple variable assignments without $ prefix."""
        stacker = Stacker()  # Fresh instance
        result = stacker.eval("5 x set 10 y set x y +")
        self.assertEqual(result[-1], 15)

    def test_set_with_dollar_backward_compatibility(self):
        """Test that $ prefix still works (backward compatibility)."""
        stacker = Stacker()  # Fresh instance
        result = stacker.eval("100 $legacy set legacy")
        self.assertEqual(result[-1], 100)

    def test_set_mixed_syntax(self):
        """Test mixing $ and non-$ syntax."""
        stacker = Stacker()  # Fresh instance
        result = stacker.eval("10 $x set 20 y set x y +")
        self.assertEqual(result[-1], 30)

    def test_defun_without_dollar(self):
        """Test function definition without $ prefix."""
        stacker = Stacker()  # Fresh instance
        result = stacker.eval("{a b} {a b +} add defun 5 10 add")
        self.assertEqual(result[-1], 15)

    def test_defun_with_dollar_backward_compatibility(self):
        """Test that defun with $ prefix still works."""
        stacker = Stacker()  # Fresh instance
        result = stacker.eval("{a b} {a b *} $multiply defun 3 4 multiply")
        self.assertEqual(result[-1], 12)

    def test_defmacro_without_dollar(self):
        """Test macro definition without $ prefix."""
        stacker = Stacker()  # Fresh instance
        result = stacker.eval("{2 *} double defmacro 5 double")
        self.assertEqual(result[-1], 10)

    def test_defmacro_with_dollar_backward_compatibility(self):
        """Test that defmacro with $ prefix still works."""
        stacker = Stacker()  # Fresh instance
        result = stacker.eval("{3 +} $addThree defmacro 10 addThree")
        self.assertEqual(result[-1], 13)

    def test_do_loop_without_dollar(self):
        """Test do loop without $ prefix (variable name in do)."""
        stacker = Stacker()  # Fresh instance
        result = stacker.eval("0 sum set 1 5 i {sum i + sum set} do sum")
        # Sum of 1 to 5 = 15
        self.assertEqual(result[-1], 15)

    def test_do_loop_with_dollar_backward_compatibility(self):
        """Test that do loop with $ prefix still works."""
        stacker = Stacker()  # Fresh instance
        result = stacker.eval("0 $total set 1 3 $i {total i + total set} do total")
        # Sum of 1 to 3 = 6
        self.assertEqual(result[-1], 6)

    def test_dolist_without_dollar(self):
        """Test dolist without $ prefix (variable name in dolist)."""
        stacker = Stacker()  # Fresh instance
        result = stacker.eval("0 sum set [10 20 30] x {sum x + sum set} dolist sum")
        # Sum of 10, 20, 30 = 60
        self.assertEqual(result[-1], 60)

    def test_dolist_with_dollar_backward_compatibility(self):
        """Test that dolist with $ prefix still works."""
        stacker = Stacker()  # Fresh instance
        result = stacker.eval(
            "0 $total set [5 15 25] $x {total x + total set} dolist total"
        )
        # Sum of 5, 15, 25 = 45
        self.assertEqual(result[-1], 45)

    def test_undefined_variable_becomes_undefined_symbol(self):
        """Test that undefined variables are treated as UndefinedSymbol objects (not errors)."""
        from stacker.engine.data_type import UndefinedSymbol

        stacker = Stacker()  # Fresh instance
        result = stacker.eval("undefined_var")
        # Undefined variable should be pushed as an UndefinedSymbol
        self.assertIsInstance(result[-1], UndefinedSymbol)
        self.assertEqual(str(result[-1]), "undefined_var")

    def test_undefined_symbol_raises_error_when_used(self):
        """Test that UndefinedSymbol raises error when used in operations."""
        stacker = Stacker()  # Fresh instance
        # Using an undefined variable in arithmetic should raise an error
        with self.assertRaises(Exception):
            stacker.eval("5 undefined_var +")

    def test_string_variable_name_still_works(self):
        """Test that string-based variable names still work."""
        stacker = Stacker()  # Fresh instance
        result = stacker.eval('5 "stringvar" set stringvar')
        self.assertEqual(result[-1], 5)

    def test_equal_operator_without_dollar(self):
        """Test = operator without $ prefix."""
        stacker = Stacker()  # Fresh instance
        result = stacker.eval("42 x = x")
        self.assertEqual(result[-1], 42)

    def test_equal_operator_multiple_variables(self):
        """Test multiple variable assignments with = operator without $ prefix."""
        stacker = Stacker()  # Fresh instance
        result = stacker.eval("7 a = 8 b = a b *")
        self.assertEqual(result[-1], 56)

    def test_equal_operator_with_dollar_backward_compatibility(self):
        """Test that = operator with $ prefix still works."""
        stacker = Stacker()  # Fresh instance
        result = stacker.eval("99 $value = value")
        self.assertEqual(result[-1], 99)

    def test_equal_operator_mixed_syntax(self):
        """Test mixing $ and non-$ syntax with = operator."""
        stacker = Stacker()  # Fresh instance
        result = stacker.eval("15 $x = 25 y = x y +")
        self.assertEqual(result[-1], 40)

    def test_equal_vs_set_equivalence(self):
        """Test that = and set operators are equivalent."""
        stacker1 = Stacker()  # Fresh instance
        stacker2 = Stacker()  # Fresh instance
        result1 = stacker1.eval("10 x set 20 y set x y *")
        result2 = stacker2.eval("10 x = 20 y = x y *")
        self.assertEqual(result1[-1], result2[-1])
        self.assertEqual(result1[-1], 200)

    def test_equal_operator_in_function(self):
        """Test = operator inside function without $ prefix."""
        stacker = Stacker()  # Fresh instance
        result = stacker.eval("{n} {0 a = 1 b = 2 n i {a b + temp = b a = temp b =} do b} fib defun 10 fib")
        # Fibonacci(10) = 55
        self.assertEqual(result[-1], 55)

    def test_equal_operator_in_loop(self):
        """Test = operator in do loop without $ prefix."""
        stacker = Stacker()  # Fresh instance
        result = stacker.eval("0 total = 1 5 i {total i + total =} do total")
        # Sum of 1 to 5 = 15
        self.assertEqual(result[-1], 15)


if __name__ == "__main__":
    unittest.main()
