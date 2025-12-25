"""Tests for file operators (write-to-file, read-from-file, append-to-file, read-lines, file-exists)."""

import unittest
import tempfile
import os
from stacker.stacker import Stacker


class TestFileOperators(unittest.TestCase):
    def setUp(self):
        self.stacker = Stacker()
        self.stacker.stack.clear()
        # Create a temporary directory for test files
        self.temp_dir = tempfile.mkdtemp()

    def tearDown(self):
        # Clean up temporary directory
        import shutil

        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def get_temp_file(self, name="test.txt"):
        """Get a path to a temporary file."""
        return os.path.join(self.temp_dir, name)

    def test_write_to_file_basic(self):
        """Test writing to a file."""
        filepath = self.get_temp_file("write_test.txt")
        self.stacker.process_expression(f"'Hello World' '{filepath}' write-to-file")

        # Verify file was created and contains the content
        self.assertTrue(os.path.exists(filepath))
        with open(filepath, "r") as f:
            content = f.read()
        self.assertEqual(content, "Hello World")

    def test_write_to_file_number(self):
        """Test writing a number to a file."""
        filepath = self.get_temp_file("number_test.txt")
        self.stacker.process_expression(f"42 '{filepath}' write-to-file")

        with open(filepath, "r") as f:
            content = f.read()
        self.assertEqual(content, "42")

    def test_write_to_file_overwrites(self):
        """Test that write-to-file overwrites existing content."""
        filepath = self.get_temp_file("overwrite_test.txt")

        # Write first content
        self.stacker.process_expression(f"'First' '{filepath}' write-to-file")

        # Write second content (should overwrite)
        self.stacker.process_expression(f"'Second' '{filepath}' write-to-file")

        with open(filepath, "r") as f:
            content = f.read()
        self.assertEqual(content, "Second")

    def test_read_from_file_basic(self):
        """Test reading from a file."""
        filepath = self.get_temp_file("read_test.txt")

        # Create a file with content
        with open(filepath, "w") as f:
            f.write("Hello from file")

        self.stacker.process_expression(f"'{filepath}' read-from-file")
        result = self.stacker.stack[-1]
        self.assertEqual(result, "Hello from file")

    def test_read_from_file_multiline(self):
        """Test reading multiline content from a file."""
        filepath = self.get_temp_file("multiline_test.txt")

        content = "Line 1\nLine 2\nLine 3"
        with open(filepath, "w") as f:
            f.write(content)

        self.stacker.process_expression(f"'{filepath}' read-from-file")
        result = self.stacker.stack[-1]
        self.assertEqual(result, content)

    def test_append_to_file_basic(self):
        """Test appending to a file."""
        filepath = self.get_temp_file("append_test.txt")

        # Write initial content
        self.stacker.process_expression(f"'Hello' '{filepath}' write-to-file")

        # Append content
        self.stacker.process_expression(f"' World' '{filepath}' append-to-file")

        with open(filepath, "r") as f:
            content = f.read()
        self.assertEqual(content, "Hello World")

    def test_append_to_file_creates_if_not_exists(self):
        """Test that append creates file if it doesn't exist."""
        filepath = self.get_temp_file("new_append_test.txt")

        self.stacker.process_expression(f"'New content' '{filepath}' append-to-file")

        self.assertTrue(os.path.exists(filepath))
        with open(filepath, "r") as f:
            content = f.read()
        self.assertEqual(content, "New content")

    def test_append_to_file_multiple_times(self):
        """Test appending to a file multiple times."""
        filepath = self.get_temp_file("multi_append_test.txt")

        self.stacker.process_expression(f"'A' '{filepath}' write-to-file")
        self.stacker.process_expression(f"'B' '{filepath}' append-to-file")
        self.stacker.process_expression(f"'C' '{filepath}' append-to-file")

        with open(filepath, "r") as f:
            content = f.read()
        self.assertEqual(content, "ABC")

    def test_read_lines_basic(self):
        """Test reading lines from a file."""
        filepath = self.get_temp_file("lines_test.txt")

        with open(filepath, "w") as f:
            f.write("Line 1\nLine 2\nLine 3")

        self.stacker.process_expression(f"'{filepath}' read-lines")
        result = self.stacker.stack[-1]
        self.assertEqual(result, ["Line 1", "Line 2", "Line 3"])

    def test_read_lines_empty_file(self):
        """Test reading lines from an empty file."""
        filepath = self.get_temp_file("empty_test.txt")

        with open(filepath, "w") as f:
            f.write("")

        self.stacker.process_expression(f"'{filepath}' read-lines")
        result = self.stacker.stack[-1]
        self.assertEqual(result, [])

    def test_read_lines_single_line(self):
        """Test reading a single line from a file."""
        filepath = self.get_temp_file("single_line_test.txt")

        with open(filepath, "w") as f:
            f.write("Only one line")

        self.stacker.process_expression(f"'{filepath}' read-lines")
        result = self.stacker.stack[-1]
        self.assertEqual(result, ["Only one line"])

    def test_read_lines_trailing_newline(self):
        """Test reading lines with trailing newline."""
        filepath = self.get_temp_file("trailing_newline_test.txt")

        with open(filepath, "w") as f:
            f.write("Line 1\nLine 2\n")

        self.stacker.process_expression(f"'{filepath}' read-lines")
        result = self.stacker.stack[-1]
        # Trailing newline should result in 2 lines, not 3
        self.assertEqual(result, ["Line 1", "Line 2"])

    def test_file_exists_true(self):
        """Test file-exists returns true for existing file."""
        filepath = self.get_temp_file("exists_test.txt")

        # Create the file
        with open(filepath, "w") as f:
            f.write("content")

        self.stacker.process_expression(f"'{filepath}' file-exists")
        result = self.stacker.stack[-1]
        self.assertTrue(result)

    def test_file_exists_false(self):
        """Test file-exists returns false for non-existent file."""
        filepath = self.get_temp_file("nonexistent.txt")

        self.stacker.process_expression(f"'{filepath}' file-exists")
        result = self.stacker.stack[-1]
        self.assertFalse(result)

    def test_file_exists_directory(self):
        """Test file-exists with a directory."""
        # The temp_dir should exist
        self.stacker.process_expression(f"'{self.temp_dir}' file-exists")
        result = self.stacker.stack[-1]
        self.assertTrue(result)

    def test_write_read_roundtrip(self):
        """Test writing and reading back produces same content."""
        filepath = self.get_temp_file("roundtrip_test.txt")
        test_content = "Test content for roundtrip"

        self.stacker.process_expression(f"'{test_content}' '{filepath}' write-to-file")
        self.stacker.stack.clear()
        self.stacker.process_expression(f"'{filepath}' read-from-file")

        result = self.stacker.stack[-1]
        self.assertEqual(result, test_content)


if __name__ == "__main__":
    unittest.main()
