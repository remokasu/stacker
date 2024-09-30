import unittest

from stacker.stacker import Stacker
from pathlib import Path
from stacker.error import IncludeError
from stacker.include.include import include_stacker_script


# class TestImportStacker(unittest.TestCase):
#     def test_include(self):
#         filename = "test/src_test/test.stk"
#         stacker = Stacker()
#         stacker.stack.clear()
#         stacker.process_expression(f"'{filename}' include")
#         stacker.process_expression("5 increment")
#         self.assertEqual(stacker.stack[-1], 6)
class TestImportStacker(unittest.TestCase):
    def test_include(self):
        filename = "test/src_test/test.stk"
        stacker = Stacker()
        stacker.stack.clear()
        stacker.process_expression(f"'{filename}' include")
        stacker.process_expression("5 increment")
        self.assertEqual(stacker.stack[-1], 6)

    def test_include_stacker_script_valid(self):
        filename = "test/src_test/test.stk"
        stacker = include_stacker_script(filename)
        self.assertIsInstance(stacker, Stacker)

    def test_include_stacker_script_invalid_extension(self):
        filename = "test/src_test/test.txt"
        with self.assertRaises(IncludeError) as context:
            include_stacker_script(filename)
        self.assertIn("File test/src_test/test.txt not found.", str(context.exception))

    def test_include_stacker_script_file_not_found(self):
        filename = "test/src_test/non_existent.stk"
        with self.assertRaises(IncludeError) as context:
            include_stacker_script(filename)
        self.assertIn(
            "File test/src_test/non_existent.stk not found", str(context.exception)
        )

    def test_include_stacker_script_invalid_path(self):
        filename = Path("test/src_test/test.stk")
        stacker = include_stacker_script(filename)
        self.assertIsInstance(stacker, Stacker)


if __name__ == "__main__":
    unittest.main()
