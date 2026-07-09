import os
import subprocess
import sys
import tempfile
import unittest

from stacker.stacker import Stacker
from pathlib import Path
from stacker.error import IncludeError
from stacker.include.include import include_stacker_script
from stacker.runtime.exec_modes.script_mode import ScriptMode


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


class TestIncludeResolution(unittest.TestCase):
    """Relative includes resolve against the including file's directory
    first, then the cwd (SPEC-0003 / ADR-0004)."""

    def setUp(self):
        self._old_cwd = os.getcwd()
        self.addCleanup(os.chdir, self._old_cwd)

    def _write(self, directory, name, content):
        path = Path(directory) / name
        path.write_text(content)
        return path

    def _run_script(self, script_path):
        stacker = Stacker()
        ScriptMode(stacker).execute_stacker_dotfile(script_path)
        return stacker

    def test_resolves_relative_to_including_file(self):
        # Audit bug #10: running from another cwd used to break this
        with tempfile.TemporaryDirectory() as d, tempfile.TemporaryDirectory() as other:
            self._write(d, "lib.stk", "10 $libval set\n")
            main = self._write(d, "main.stk", '"lib.stk" include\nlibval\n')
            os.chdir(other)
            stacker = self._run_script(main)
            self.assertEqual(stacker.stack[-1], 10)

    def test_nested_include_uses_each_files_directory(self):
        with tempfile.TemporaryDirectory() as d, tempfile.TemporaryDirectory() as other:
            sub = Path(d) / "sub"
            sub.mkdir()
            self._write(sub, "c.stk", "7 $cval set\n")
            self._write(sub, "b.stk", '"c.stk" include\n')
            main = self._write(d, "main.stk", '"sub/b.stk" include\ncval\n')
            os.chdir(other)
            stacker = self._run_script(main)
            self.assertEqual(stacker.stack[-1], 7)

    def test_including_file_directory_takes_precedence_over_cwd(self):
        with tempfile.TemporaryDirectory() as d, tempfile.TemporaryDirectory() as other:
            self._write(d, "lib.stk", "1 $which set\n")
            self._write(other, "lib.stk", "2 $which set\n")
            main = self._write(d, "main.stk", '"lib.stk" include\nwhich\n')
            os.chdir(other)
            stacker = self._run_script(main)
            self.assertEqual(stacker.stack[-1], 1)

    def test_falls_back_to_cwd(self):
        with tempfile.TemporaryDirectory() as d, tempfile.TemporaryDirectory() as other:
            main = self._write(d, "main.stk", '"lib.stk" include\nlibval\n')
            self._write(other, "lib.stk", "3 $libval set\n")
            os.chdir(other)
            stacker = self._run_script(main)
            self.assertEqual(stacker.stack[-1], 3)

    def test_repl_like_include_uses_cwd(self):
        # No file context (current_file is None): cwd-only resolution
        with tempfile.TemporaryDirectory() as other:
            self._write(other, "lib.stk", "4 $libval set\n")
            os.chdir(other)
            stacker = Stacker()
            stacker.process_expression('"lib.stk" include')
            stacker.process_expression("libval")
            self.assertEqual(stacker.stack[-1], 4)

    def test_not_found_lists_tried_paths(self):
        with tempfile.TemporaryDirectory() as d, tempfile.TemporaryDirectory() as other:
            main = self._write(d, "main.stk", '"missing.stk" include\n')
            os.chdir(other)
            with self.assertRaises(IncludeError) as ctx:
                self._run_script(main)
            message = str(ctx.exception)
            self.assertIn("Tried:", message)
            self.assertIn(str(Path(d) / "missing.stk"), message)
            self.assertIn(str(Path(other).resolve() / "missing.stk"), message)


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
