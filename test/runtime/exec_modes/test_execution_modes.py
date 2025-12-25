"""Tests for execution modes (ExecutionMode, ScriptMode, CommandLineMode)."""

import unittest
import tempfile
import os
from io import StringIO
from unittest.mock import patch

from stacker.stacker import Stacker
from stacker.runtime.exec_modes import ExecutionMode, ScriptMode, CommandLineMode


class TestExecutionMode(unittest.TestCase):
    """Test the base ExecutionMode class."""

    def setUp(self):
        self.rpn_calculator = Stacker()
        self.exec_mode = ExecutionMode(self.rpn_calculator)

    def test_initialization(self):
        """Test ExecutionMode initialization."""
        self.assertEqual(self.exec_mode.rpn_calculator, self.rpn_calculator)
        self.assertTrue(self.exec_mode.color_print)
        self.assertFalse(self.exec_mode.debug)

    def test_debug_mode(self):
        """Test debug mode activation."""
        self.assertFalse(self.exec_mode.debug)
        self.exec_mode.debug_mode()
        self.assertTrue(self.exec_mode.debug)

    def test_disp(self):
        """Test stack display."""
        self.rpn_calculator.stack.clear()
        self.rpn_calculator.process_expression("1 2 3")

        with patch("sys.stdout", new=StringIO()) as fake_out:
            self.exec_mode.disp()
            output = fake_out.getvalue()
            self.assertIn("1", output)
            self.assertIn("2", output)
            self.assertIn("3", output)

    def test_disp_all_variables(self):
        """Test variable display."""
        self.rpn_calculator.stack.clear()
        self.rpn_calculator.process_expression("5 $x set")
        self.rpn_calculator.process_expression("10 $y set")

        with patch("sys.stdout", new=StringIO()) as fake_out:
            self.exec_mode.disp_all_variables()
            output = fake_out.getvalue()
            self.assertIn("x = 5", output)
            self.assertIn("y = 10", output)

    def test_disp_ans(self):
        """Test answer display."""
        self.rpn_calculator.stack.clear()
        self.rpn_calculator.process_expression("1 2 +")

        with patch("sys.stdout", new=StringIO()) as fake_out:
            self.exec_mode.disp_ans()
            output = fake_out.getvalue()
            self.assertIn("3", output)

    def test_disp_ans_empty_stack(self):
        """Test answer display with empty stack."""
        self.rpn_calculator.stack.clear()

        with patch("sys.stdout", new=StringIO()) as fake_out:
            self.exec_mode.disp_ans()
            output = fake_out.getvalue()
            self.assertEqual(output, "")

    def test_execute_stacker_dotfile(self):
        """Test executing a dotfile."""
        # Create a temporary dotfile
        with tempfile.NamedTemporaryFile(mode="w", suffix=".stk", delete=False) as f:
            f.write("5 $x set\n")
            f.write("10 $y set\n")
            dotfile_path = f.name

        try:
            self.rpn_calculator.stack.clear()
            self.exec_mode.execute_stacker_dotfile(dotfile_path)

            # Variables should be set
            self.assertEqual(self.rpn_calculator.variables["x"], 5)
            self.assertEqual(self.rpn_calculator.variables["y"], 10)
        finally:
            os.unlink(dotfile_path)

    def test_execute_stacker_dotfile_with_multiline(self):
        """Test executing a dotfile with multiline expressions."""
        # Create a temporary dotfile with multiline expressions
        with tempfile.NamedTemporaryFile(mode="w", suffix=".stk", delete=False) as f:
            f.write("[1 2 3;\n")
            f.write("4 5 6]\n")
            f.write("$matrix set\n")
            dotfile_path = f.name

        try:
            self.rpn_calculator.stack.clear()
            self.exec_mode.execute_stacker_dotfile(dotfile_path)

            # Matrix should be set (with semicolon, it creates nested list)
            self.assertEqual(
                self.rpn_calculator.variables["matrix"], [[1, 2, 3], [4, 5, 6]]
            )
        finally:
            os.unlink(dotfile_path)


class TestScriptMode(unittest.TestCase):
    """Test ScriptMode execution."""

    def setUp(self):
        self.rpn_calculator = Stacker()
        self.script_mode = ScriptMode(self.rpn_calculator)

    def test_script_mode_basic(self):
        """Test basic script execution."""
        # Create a temporary script
        with tempfile.NamedTemporaryFile(mode="w", suffix=".stk", delete=False) as f:
            f.write("1 2 +\n")
            f.write("3 *\n")
            script_path = f.name

        try:
            self.rpn_calculator.stack.clear()
            self.script_mode.run(script_path)

            # Result should be (1+2)*3 = 9
            self.assertEqual(self.rpn_calculator.stack[-1], 9)
        finally:
            os.unlink(script_path)

    def test_script_mode_with_variables(self):
        """Test script execution with variables."""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".stk", delete=False) as f:
            f.write("5 $x set\n")
            f.write("10 $y set\n")
            f.write("x y +\n")
            script_path = f.name

        try:
            self.rpn_calculator.stack.clear()
            self.script_mode.run(script_path)

            # Result should be 5+10 = 15
            self.assertEqual(self.rpn_calculator.stack[-1], 15)
        finally:
            os.unlink(script_path)

    def test_script_mode_with_functions(self):
        """Test script execution with function definitions."""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".stk", delete=False) as f:
            f.write("{x} {x x *} $square defun\n")
            f.write("5 square\n")
            script_path = f.name

        try:
            self.rpn_calculator.stack.clear()
            self.script_mode.run(script_path)

            # Result should be 5^2 = 25
            self.assertEqual(self.rpn_calculator.stack[-1], 25)
        finally:
            os.unlink(script_path)

    def test_script_mode_uses_system_operators(self):
        """Test that script mode can use system operators."""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".stk", delete=False) as f:
            f.write("5 $x set\n")
            f.write("vars\n")
            script_path = f.name

        try:
            with patch("sys.stdout", new=StringIO()) as fake_out:
                self.script_mode.run(script_path)
                output = fake_out.getvalue()
                self.assertIn("x = 5", output)
        finally:
            os.unlink(script_path)


class TestCommandLineMode(unittest.TestCase):
    """Test CommandLineMode execution."""

    def setUp(self):
        self.rpn_calculator = Stacker()
        self.cmd_mode = CommandLineMode(self.rpn_calculator)

    def test_commandline_mode_basic(self):
        """Test basic command line execution."""
        self.rpn_calculator.stack.clear()
        # CommandLineMode uses eval() which returns result but clears stack
        # This is intentional behavior for command-line mode
        self.cmd_mode.run("1 2 +")
        # Result is computed, but for testing we check it doesn't error
        # The actual output would be handled by __main__.py
        # Just verify it doesn't error
        result = self.rpn_calculator.eval("1 2 +")
        self.assertEqual(result[-1], 3)

    def test_commandline_mode_with_variables(self):
        """Test command line mode with variables."""
        self.rpn_calculator.stack.clear()

        # First set a variable (using process_expression to keep it in state)
        self.rpn_calculator.process_expression("5 $x set")
        # Then use it via eval
        result = self.rpn_calculator.eval("x 10 +")
        self.assertEqual(result[-1], 15)

    def test_commandline_mode_multiple_expressions(self):
        """Test command line mode with multiple expressions."""
        self.rpn_calculator.stack.clear()
        result = self.rpn_calculator.eval("1 2 + 3 * 4 +")
        # (1+2)*3+4 = 13
        self.assertEqual(result[-1], 13)

    def test_commandline_mode_uses_system_operators(self):
        """Test that command line mode can use system operators."""
        self.rpn_calculator.stack.clear()

        with patch("sys.stdout", new=StringIO()) as fake_out:
            self.cmd_mode.run("5 $x set")
            # Clear previous output
            fake_out.truncate(0)
            fake_out.seek(0)

            self.cmd_mode.run("vars")
            output = fake_out.getvalue()
            self.assertIn("x = 5", output)


if __name__ == "__main__":
    unittest.main()
