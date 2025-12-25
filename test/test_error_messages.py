"""
Test improved error messages and error handling.

This test suite verifies that error messages are informative and helpful.
"""

import unittest
from stacker.stacker import Stacker
from stacker.error import StackUnderflowError


class TestErrorMessages(unittest.TestCase):
    """Test error messages for various error conditions."""

    def setUp(self):
        """Set up test fixtures."""
        self.stacker = Stacker()

    def test_stack_underflow_error(self):
        """Test that StackUnderflowError is raised with operator info."""
        self.stacker.stack.clear()
        with self.assertRaises(StackUnderflowError) as context:
            self.stacker.process_expression("+")

        error_msg = str(context.exception)
        self.assertIn("+", error_msg)
        self.assertIn("2", error_msg)  # + requires 2 arguments

    def test_stack_underflow_with_partial_args(self):
        """Test stack underflow when some but not all arguments are present."""
        self.stacker.stack.clear()
        with self.assertRaises(StackUnderflowError) as context:
            self.stacker.process_expression("1 +")  # + needs 2 args, only 1 provided

        error_msg = str(context.exception)
        self.assertIn("+", error_msg)

    def test_type_error_string_number_addition(self):
        """Test type error when trying to add string and number."""
        self.stacker.stack.clear()
        with self.assertRaises(TypeError) as context:
            self.stacker.process_expression('"hello" 42 +')

        error_msg = str(context.exception)
        # Should mention the type incompatibility
        self.assertTrue(
            "concatenate" in error_msg or "incompatible" in error_msg.lower()
        )

    def test_zero_division_error(self):
        """Test division by zero error."""
        self.stacker.stack.clear()
        with self.assertRaises(ZeroDivisionError):
            self.stacker.process_expression("10 0 /")

    def test_stack_underflow_multiple_operators(self):
        """Test stack underflow with different operators."""
        # Arithmetic operators raise StackUnderflowError
        arithmetic_operators = [
            ("*", 2),
            ("-", 2),
            ("+", 2),
            ("/", 2),
        ]

        for operator, expected_args in arithmetic_operators:
            with self.subTest(operator=operator):
                self.stacker.stack.clear()
                with self.assertRaises(StackUnderflowError) as context:
                    self.stacker.process_expression(operator)

                error_msg = str(context.exception)
                self.assertIn(operator, error_msg)
                self.assertIn(str(expected_args), error_msg)

    def test_stack_operators_underflow(self):
        """Test that stack manipulation operators raise errors on underflow."""
        # Stack operators have their own error types (SwapError, DupError, etc.)
        # but they should still report underflow conditions
        from stacker.error import SwapError, DupError, RotError

        test_cases = [
            ("swap", SwapError, 2),
            ("dup", DupError, 1),
            ("rot", RotError, 3),
        ]

        for operator, error_type, min_required in test_cases:
            with self.subTest(operator=operator):
                self.stacker.stack.clear()
                with self.assertRaises(error_type):
                    self.stacker.process_expression(operator)

    def test_successful_operations_no_error(self):
        """Test that correct operations don't raise errors."""
        test_cases = [
            ("1 2 +", 3),
            ("5 3 -", 2),
            ("4 3 *", 12),
            ("10 2 /", 5),
            ('"hello" " " + "world" +', "hello world"),
        ]

        for expr, expected in test_cases:
            with self.subTest(expr=expr):
                self.stacker.stack.clear()
                self.stacker.process_expression(expr)
                result = self.stacker.stack[-1]
                self.assertEqual(result, expected)

    def test_type_error_with_operator_info(self):
        """Test that TypeError includes operator information."""
        self.stacker.stack.clear()
        with self.assertRaises(TypeError) as context:
            self.stacker.process_expression('"text" 5 -')

        error_msg = str(context.exception)
        # Should mention the operator or the incompatibility
        self.assertTrue(
            "-" in error_msg or "incompatible" in error_msg.lower()
        )


class TestStackUnderflowErrorClass(unittest.TestCase):
    """Test the StackUnderflowError class itself."""

    def test_error_message_format(self):
        """Test that StackUnderflowError formats message correctly."""
        error = StackUnderflowError("test_op", 3)
        msg = str(error)

        self.assertIn("test_op", msg)
        self.assertIn("3", msg)
        self.assertIn("arguments", msg.lower())

    def test_error_with_different_arg_counts(self):
        """Test error messages with different argument counts."""
        test_cases = [
            ("op1", 1),
            ("op2", 2),
            ("op3", 5),
        ]

        for op, count in test_cases:
            with self.subTest(op=op, count=count):
                error = StackUnderflowError(op, count)
                msg = str(error)
                self.assertIn(op, msg)
                self.assertIn(str(count), msg)


if __name__ == "__main__":
    unittest.main()
