import unittest
from pathlib import Path
import tempfile
import os

from stacker.stacker import Stacker
from stacker.runtime.exec_modes.script_mode import ScriptMode


class TestInlineComments(unittest.TestCase):
    def setUp(self):
        self.stacker = Stacker()
        self.script_mode = ScriptMode(self.stacker)

    def test_simple_inline_comment(self):
        """Test that inline comments are ignored"""
        self.stacker.stack.clear()
        ans = self.stacker.eval("3 4 +  # This is a comment")
        self.assertEqual(ans[-1], 7)

    def test_inline_comment_in_script(self):
        """Test inline comments in script files"""
        script_content = """
0 counter set  # Initialize counter
counter 1 + counter set  # Increment
counter  # Push to stack
"""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.stk', delete=False) as f:
            f.write(script_content)
            temp_file = f.name

        try:
            self.script_mode.run(temp_file)
            self.assertEqual(self.stacker.stack[-1], 1)
        finally:
            os.unlink(temp_file)

    def test_multiline_function_with_inline_comments(self):
        """Test function definition across multiple lines with inline comments"""
        script_content = """
{x y}  # Parameters
{x y *}  # Function body
multiply defun  # Define function

10 20 multiply  # Call function
"""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.stk', delete=False) as f:
            f.write(script_content)
            temp_file = f.name

        try:
            self.script_mode.run(temp_file)
            self.assertEqual(self.stacker.stack[-1], 200)
        finally:
            os.unlink(temp_file)

    def test_inline_comment_inside_block(self):
        """Test inline comments inside code blocks"""
        script_content = """
{x} {
    x 2 *  # Double the value
} double defun

5 double
"""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.stk', delete=False) as f:
            f.write(script_content)
            temp_file = f.name

        try:
            self.script_mode.run(temp_file)
            self.assertEqual(self.stacker.stack[-1], 10)
        finally:
            os.unlink(temp_file)

    def test_inline_comment_with_special_chars(self):
        """Test inline comments with special characters"""
        script_content = """
3 4 +  # Comment with special chars: {}[]()'"
"""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.stk', delete=False) as f:
            f.write(script_content)
            temp_file = f.name

        try:
            self.script_mode.run(temp_file)
            self.assertEqual(self.stacker.stack[-1], 7)
        finally:
            os.unlink(temp_file)

    def test_hash_in_string_not_comment(self):
        """Test that # inside strings is not treated as comment"""
        self.stacker.stack.clear()
        ans = self.stacker.eval('"Hello # World"')
        self.assertEqual(ans[-1], "Hello # World")

    def test_hash_in_string_with_comment(self):
        """Test string with # and actual comment"""
        self.stacker.stack.clear()
        ans = self.stacker.eval('"Hash: #" # This is a comment')
        self.assertEqual(ans[-1], "Hash: #")

    def test_multiline_with_comment_after_brace(self):
        """Test comment after opening brace"""
        script_content = """
{x y}  # Parameters
{  # Start of body
    x y +  # Add them
}  # End of body
add defun

3 4 add
"""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.stk', delete=False) as f:
            f.write(script_content)
            temp_file = f.name

        try:
            self.script_mode.run(temp_file)
            self.assertEqual(self.stacker.stack[-1], 7)
        finally:
            os.unlink(temp_file)

    def test_comment_with_code_after_on_same_line(self):
        """Test that code after comment on same line is ignored"""
        script_content = """
3 4  # This is ignored + 10 20
+
"""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.stk', delete=False) as f:
            f.write(script_content)
            temp_file = f.name

        try:
            self.script_mode.run(temp_file)
            # Should be 7 (3+4), not 17 (3+4+10) or other
            self.assertEqual(self.stacker.stack[-1], 7)
        finally:
            os.unlink(temp_file)

    def test_line_comment_at_start(self):
        """Test that lines starting with # are skipped"""
        script_content = """
# This is a full line comment
3 4 +
# Another comment
"""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.stk', delete=False) as f:
            f.write(script_content)
            temp_file = f.name

        try:
            self.script_mode.run(temp_file)
            self.assertEqual(self.stacker.stack[-1], 7)
        finally:
            os.unlink(temp_file)

    def test_empty_line_after_inline_comment(self):
        """Test that inline comment doesn't affect subsequent lines"""
        script_content = """
3  # First number

4  # Second number
+  # Add them
"""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.stk', delete=False) as f:
            f.write(script_content)
            temp_file = f.name

        try:
            self.script_mode.run(temp_file)
            self.assertEqual(self.stacker.stack[-1], 7)
        finally:
            os.unlink(temp_file)


if __name__ == '__main__':
    unittest.main()
