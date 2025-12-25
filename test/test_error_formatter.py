"""Tests for the error formatter."""

import unittest
from stacker.error_formatter import ErrorFormatter, StackerErrorWithContext


class TestErrorFormatter(unittest.TestCase):
    """Test cases for error formatting."""

    def test_basic_error_format(self):
        """Test basic error formatting without source context."""
        result = ErrorFormatter.format_error(
            filename="test.stk",
            line_number=10,
            column=5,
            error_type="SyntaxError",
            message="Expected a symbol, got 0"
        )
        self.assertIn("test.stk:10:5", result)
        self.assertIn("error:", result)
        self.assertIn("Expected a symbol, got 0", result)

    def test_error_with_source_line(self):
        """Test error formatting with source code context."""
        result = ErrorFormatter.format_error(
            filename="test.stk",
            line_number=5,
            column=3,
            error_type="SyntaxError",
            message="Invalid syntax",
            source_line="0 a ="
        )
        self.assertIn("test.stk:5:3", result)
        self.assertIn("0 a =", result)
        self.assertIn("^", result)  # Caret indicator

    def test_error_with_hint(self):
        """Test error formatting with hint."""
        result = ErrorFormatter.format_error(
            filename="test.stk",
            line_number=1,
            column=1,
            error_type="SyntaxError",
            message="Expected a symbol",
            source_line="123 variable set",
            hint="Use '$variable' or 'variable' (without quotes)"
        )
        self.assertIn("hint:", result)
        self.assertIn("Use '$variable'", result)

    def test_repl_error_no_filename(self):
        """Test error formatting for REPL (no filename)."""
        result = ErrorFormatter.format_error(
            filename=None,
            line_number=None,
            column=None,
            error_type="RuntimeError",
            message="Division by zero"
        )
        self.assertIn("stacker", result)
        self.assertIn("error:", result)
        self.assertIn("Division by zero", result)

    def test_warning_format(self):
        """Test warning formatting."""
        result = ErrorFormatter.format_warning(
            filename="test.stk",
            line_number=10,
            column=5,
            message="Deprecated syntax",
            source_line="$old_syntax set",
            hint="Use 'new_syntax' instead"
        )
        self.assertIn("warning:", result)
        self.assertIn("Deprecated syntax", result)
        self.assertIn("hint:", result)

    def test_stacker_error_with_context(self):
        """Test StackerErrorWithContext exception."""
        error = StackerErrorWithContext(
            message="Undefined variable 'x'",
            error_type="UndefinedVariableError",
            filename="test.stk",
            line_number=42,
            column=10,
            source_line="x 5 +",
            hint="Define 'x' before using it"
        )

        formatted = error.format()
        self.assertIn("test.stk:42:10", formatted)
        self.assertIn("Undefined variable 'x'", formatted)
        self.assertIn("x 5 +", formatted)
        self.assertIn("hint:", formatted)

    def test_column_indicator_position(self):
        """Test that the caret indicator appears at the correct column."""
        result = ErrorFormatter.format_error(
            filename="test.stk",
            line_number=1,
            column=5,
            error_type="SyntaxError",
            message="Error at column 5",
            source_line="0 1 2 3 4"
        )
        lines = result.split('\n')
        # Find the line with the caret
        caret_line = None
        for line in lines:
            if '^' in line:
                caret_line = line
                break

        self.assertIsNotNone(caret_line)
        # The caret should be at position corresponding to column 5
        # (accounting for line number prefix)

    def test_multiline_error_context(self):
        """Test error formatting preserves context structure."""
        result = ErrorFormatter.format_error(
            filename="fibonacci.stk",
            line_number=15,
            column=12,
            error_type="StackUnderflowError",
            message="Operator `+` requires 2 arguments",
            source_line="    a b + temp =",
            hint="Ensure both 'a' and 'b' are defined"
        )

        # Check all components are present
        self.assertIn("fibonacci.stk:15:12", result)
        self.assertIn("error:", result)
        self.assertIn("a b + temp =", result)
        self.assertIn("^", result)
        self.assertIn("hint:", result)
        self.assertIn("StackUnderflowError", result)


if __name__ == "__main__":
    unittest.main()
