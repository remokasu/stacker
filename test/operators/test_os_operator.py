"""Tests for OS operators (ls, cd, pwd, cat)."""

import unittest
import tempfile
import os
from io import StringIO
from unittest.mock import patch
from stacker.stacker import Stacker


class TestOSOperators(unittest.TestCase):
    def setUp(self):
        self.stacker = Stacker()
        self.stacker.stack.clear()
        # Store original working directory
        self.original_dir = os.getcwd()
        # Create a temporary directory for test files
        self.temp_dir = tempfile.mkdtemp()

    def tearDown(self):
        # Restore original working directory
        os.chdir(self.original_dir)
        # Clean up temporary directory
        import shutil

        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_pwd_returns_current_directory(self):
        """Test pwd returns current working directory."""
        self.stacker.process_expression("pwd")
        result = self.stacker.stack[-1]
        self.assertEqual(result, os.getcwd())
        self.assertIsInstance(result, str)

    def test_cd_changes_directory(self):
        """Test cd changes the current directory."""
        # Change to temp directory
        self.stacker.process_expression(f"'{self.temp_dir}' cd")

        # Verify directory changed
        self.assertEqual(os.getcwd(), self.temp_dir)

    def test_cd_and_pwd(self):
        """Test cd followed by pwd."""
        self.stacker.process_expression(f"'{self.temp_dir}' cd")
        self.stacker.process_expression("pwd")

        result = self.stacker.stack[-1]
        self.assertEqual(result, self.temp_dir)

    def test_ls_lists_files(self):
        """Test ls lists files in current directory."""
        # Change to temp directory and create some files
        os.chdir(self.temp_dir)
        open(os.path.join(self.temp_dir, "file1.txt"), "w").close()
        open(os.path.join(self.temp_dir, "file2.txt"), "w").close()

        self.stacker.process_expression("ls")
        result = self.stacker.stack[-1]

        self.assertIsInstance(result, list)
        self.assertIn("file1.txt", result)
        self.assertIn("file2.txt", result)

    def test_ls_empty_directory(self):
        """Test ls in an empty directory."""
        # Create an empty subdirectory
        empty_dir = os.path.join(self.temp_dir, "empty")
        os.makedirs(empty_dir)
        os.chdir(empty_dir)

        self.stacker.process_expression("ls")
        result = self.stacker.stack[-1]

        self.assertIsInstance(result, list)
        self.assertEqual(len(result), 0)

    def test_cat_prints_file_content(self):
        """Test cat prints file content."""
        # Create a test file
        filepath = os.path.join(self.temp_dir, "cat_test.txt")
        with open(filepath, "w") as f:
            f.write("Hello from cat")

        with patch("sys.stdout", new=StringIO()) as fake_out:
            self.stacker.process_expression(f"'{filepath}' cat")
            output = fake_out.getvalue()
            self.assertIn("Hello from cat", output)

    def test_cat_multiline_content(self):
        """Test cat with multiline content."""
        filepath = os.path.join(self.temp_dir, "multiline_cat.txt")
        content = "Line 1\nLine 2\nLine 3"
        with open(filepath, "w") as f:
            f.write(content)

        with patch("sys.stdout", new=StringIO()) as fake_out:
            self.stacker.process_expression(f"'{filepath}' cat")
            output = fake_out.getvalue()
            self.assertEqual(output.strip(), content)

    def test_ls_does_not_modify_stack_before_operation(self):
        """Test ls pushes result to stack."""
        self.stacker.process_expression("1 2 3")
        initial_length = len(self.stacker.stack)

        self.stacker.process_expression("ls")

        # ls should push result, so stack length should increase
        self.assertEqual(len(self.stacker.stack), initial_length + 1)

    def test_cd_does_not_push_to_stack(self):
        """Test cd does not push result to stack."""
        self.stacker.process_expression("1 2 3")
        initial_length = len(self.stacker.stack)

        self.stacker.process_expression(f"'{self.temp_dir}' cd")

        # cd consumes the path from stack but doesn't push result
        self.assertEqual(len(self.stacker.stack), initial_length)

    def test_pwd_pushes_to_stack(self):
        """Test pwd pushes current directory to stack."""
        self.stacker.process_expression("1 2 3")
        initial_length = len(self.stacker.stack)

        self.stacker.process_expression("pwd")

        # pwd should push result
        self.assertEqual(len(self.stacker.stack), initial_length + 1)


if __name__ == "__main__":
    unittest.main()
