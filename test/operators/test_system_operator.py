"""Tests for system operators (vars, funcs, macros, operators)."""

import unittest
from io import StringIO
from unittest.mock import patch

from stacker.stacker import Stacker


class TestSystemOperators(unittest.TestCase):
    def setUp(self):
        self.stacker = Stacker()

    def test_vars_no_variables(self):
        """Test vars when no user variables are defined."""
        # Clear stack
        self.stacker.stack.clear()

        # Only built-in constants should exist
        with patch("sys.stdout", new=StringIO()) as fake_out:
            self.stacker.process_expression("vars")
            output = fake_out.getvalue()
            # Built-in constants should be present
            self.assertIn("e =", output)
            self.assertIn("pi =", output)
            self.assertIn("true =", output)
            self.assertIn("false =", output)

    def test_vars_with_user_variables(self):
        """Test vars with user-defined variables."""
        self.stacker.stack.clear()
        self.stacker.process_expression("5 $x set")
        self.stacker.process_expression("10 $y set")
        self.stacker.process_expression("'hello' $msg set")

        with patch("sys.stdout", new=StringIO()) as fake_out:
            self.stacker.process_expression("vars")
            output = fake_out.getvalue()
            self.assertIn("x = 5", output)
            self.assertIn("y = 10", output)
            self.assertIn("msg = hello", output)

    def test_funcs_no_functions(self):
        """Test funcs when no functions are defined."""
        self.stacker.stack.clear()

        with patch("sys.stdout", new=StringIO()) as fake_out:
            self.stacker.process_expression("funcs")
            output = fake_out.getvalue()
            self.assertIn("No functions defined", output)

    def test_funcs_with_user_functions(self):
        """Test funcs with user-defined functions."""
        self.stacker.stack.clear()
        self.stacker.process_expression("{x} {x x *} $square defun")
        self.stacker.process_expression("{x y} {x y +} $add defun")

        with patch("sys.stdout", new=StringIO()) as fake_out:
            self.stacker.process_expression("funcs")
            output = fake_out.getvalue()
            self.assertIn("square", output)
            self.assertIn("add", output)
            self.assertIn("['x']", output)
            self.assertIn("['x', 'y']", output)

    def test_funcs_execution(self):
        """Test that defined functions actually work."""
        self.stacker.stack.clear()
        self.stacker.process_expression("{x} {x x *} $square defun")
        self.stacker.process_expression("5 square")
        self.assertEqual(self.stacker.stack[-1], 25)

    def test_macros_no_macros(self):
        """Test macros when no macros are defined."""
        self.stacker.stack.clear()

        with patch("sys.stdout", new=StringIO()) as fake_out:
            self.stacker.process_expression("macros")
            output = fake_out.getvalue()
            self.assertIn("No macros defined", output)

    def test_macros_with_user_macros(self):
        """Test macros with user-defined macros."""
        self.stacker.stack.clear()
        self.stacker.process_expression("{x} {x x *} $sqr defmacro")

        with patch("sys.stdout", new=StringIO()) as fake_out:
            self.stacker.process_expression("macros")
            output = fake_out.getvalue()
            self.assertIn("sqr", output)
            # Macros display the blockstack
            self.assertIn("{", output)

    def test_operators_display(self):
        """Test operators command displays operator categories."""
        self.stacker.stack.clear()

        with patch("sys.stdout", new=StringIO()) as fake_out:
            self.stacker.process_expression("operators")
            output = fake_out.getvalue()

            # Check for major sections
            self.assertIn("Regular operators:", output)
            self.assertIn("Stack operators:", output)
            self.assertIn("Settings operators:", output)

            # Check for some specific operators
            self.assertIn("+", output)  # Arithmetic
            self.assertIn("dup", output)  # Stack
            self.assertIn("if", output)  # Control flow

    def test_operators_includes_system_operators(self):
        """Test that operators command includes system operators."""
        self.stacker.stack.clear()

        with patch("sys.stdout", new=StringIO()) as fake_out:
            self.stacker.process_expression("operators")
            output = fake_out.getvalue()

            # System operators should be listed
            self.assertIn("vars", output)
            self.assertIn("funcs", output)
            self.assertIn("macros", output)
            self.assertIn("operators", output)

    def test_vars_in_script_mode(self):
        """Test that vars works in script mode (not just REPL)."""
        # This tests that system operators are part of the language
        from stacker.runtime.exec_modes import ScriptMode
        import tempfile
        import os

        # Create a temporary script file
        with tempfile.NamedTemporaryFile(mode="w", suffix=".stk", delete=False) as f:
            f.write("5 $x set\n")
            f.write("10 $y set\n")
            f.write("vars\n")
            script_path = f.name

        try:
            stacker = Stacker()
            script_mode = ScriptMode(stacker)

            with patch("sys.stdout", new=StringIO()) as fake_out:
                script_mode.run(script_path)
                output = fake_out.getvalue()
                self.assertIn("x = 5", output)
                self.assertIn("y = 10", output)
        finally:
            os.unlink(script_path)

    def test_vars_does_not_modify_stack(self):
        """Test that vars command does not modify the stack."""
        self.stacker.stack.clear()
        self.stacker.process_expression("1 2 3")
        self.assertEqual(list(self.stacker.stack), [1, 2, 3])

        with patch("sys.stdout", new=StringIO()):
            self.stacker.process_expression("vars")

        # Stack should remain unchanged
        self.assertEqual(list(self.stacker.stack), [1, 2, 3])

    def test_funcs_does_not_modify_stack(self):
        """Test that funcs command does not modify the stack."""
        self.stacker.stack.clear()
        self.stacker.process_expression("1 2 3")
        self.assertEqual(list(self.stacker.stack), [1, 2, 3])

        with patch("sys.stdout", new=StringIO()):
            self.stacker.process_expression("funcs")

        # Stack should remain unchanged
        self.assertEqual(list(self.stacker.stack), [1, 2, 3])


if __name__ == "__main__":
    unittest.main()
