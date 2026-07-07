import subprocess
import sys
import tempfile
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


class TestCircularInclude(unittest.TestCase):
    """Circular includes must raise IncludeError instead of recursing
    until the interpreter crashes."""

    def _run_include_in_subprocess(self, entry: Path) -> "subprocess.CompletedProcess":
        # Run in a subprocess so a regression (unbounded recursion or an
        # interpreter crash) cannot take down the test runner itself.
        code = (
            "from stacker.include.include import include_stacker_script\n"
            "from stacker.error import IncludeError\n"
            "try:\n"
            f"    include_stacker_script({str(entry)!r})\n"
            "except IncludeError as e:\n"
            "    print('INCLUDE_ERROR:', e)\n"
        )
        return subprocess.run(
            [sys.executable, "-c", code],
            capture_output=True,
            text=True,
            timeout=60,
        )

    def test_mutual_circular_include_raises(self):
        with tempfile.TemporaryDirectory() as d:
            c1 = Path(d) / "c1.stk"
            c2 = Path(d) / "c2.stk"
            c1.write_text(f'"{c2}" include\n')
            c2.write_text(f'"{c1}" include\n')
            result = self._run_include_in_subprocess(c1)
            self.assertIn("INCLUDE_ERROR:", result.stdout)
            self.assertIn("Circular include", result.stdout)

    def test_self_include_raises(self):
        with tempfile.TemporaryDirectory() as d:
            c1 = Path(d) / "self.stk"
            c1.write_text(f'"{c1}" include\n')
            result = self._run_include_in_subprocess(c1)
            self.assertIn("INCLUDE_ERROR:", result.stdout)

    def test_sequential_include_of_same_file_still_works(self):
        # Including the same file twice sequentially is legal
        with tempfile.TemporaryDirectory() as d:
            lib = Path(d) / "lib.stk"
            main = Path(d) / "main.stk"
            lib.write_text("1\n")
            main.write_text(f'"{lib}" include\n"{lib}" include\n')
            stacker = include_stacker_script(main)
            self.assertIsInstance(stacker, Stacker)


if __name__ == "__main__":
    unittest.main()
