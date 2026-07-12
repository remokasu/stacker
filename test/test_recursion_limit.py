"""Tests for the Stacker-level recursion depth guard (1.12.0).

Infinite recursion must stop with StackerRecursionError (never a
segfault), the error names the offending function, and the limit is
configurable per run with --recursion-limit.

Deep-recursion cases run `python -m stacker` in a subprocess because the
sys.setrecursionlimit backstop is configured in __main__ (the test
runner process keeps Python's small default limit).
"""

import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

from stacker.engine import recursion
from stacker.error import StackerRecursionError
from stacker.stacker import Stacker

REPO_ROOT = Path(__file__).resolve().parent.parent

INFINITE_RECURSION = "{n} {n 1 + rundeep} $rundeep defun\n0 rundeep\n"

DEEP_LEGAL_RECURSION = (
    "{n} {n 0 <= {0} {n 1 - deepok} ifelse} $deepok defun\n1000 deepok echo\n"
)


def _run_stacker(args, script_content=None, timeout=120):
    """Run `python -m stacker` in a subprocess, optionally with a script."""
    cmd = [sys.executable, "-m", "stacker", *args]
    if script_content is not None:
        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".stk", delete=False, dir=REPO_ROOT
        ) as f:
            f.write(script_content)
            script_path = f.name
        cmd.append(script_path)
    try:
        return subprocess.run(
            cmd, capture_output=True, text=True, timeout=timeout, cwd=REPO_ROOT
        )
    finally:
        if script_content is not None:
            Path(script_path).unlink()


class TestRecursionGuardSubprocess(unittest.TestCase):
    def test_infinite_recursion_errors_instead_of_segfault(self):
        result = _run_stacker([], script_content=INFINITE_RECURSION)
        self.assertGreaterEqual(result.returncode, 0, "process must not die on a signal")
        combined = result.stdout + result.stderr
        self.assertIn("StackerRecursionError", combined)
        self.assertIn("Maximum recursion depth", combined)
        self.assertIn("rundeep", combined)

    def test_deep_recursion_within_default_limit_passes(self):
        result = _run_stacker([], script_content=DEEP_LEGAL_RECURSION)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("0", result.stdout)

    def test_cli_flag_lowers_the_limit(self):
        deep_20 = (
            "{n} {n 0 <= {0} {n 1 - go20} ifelse} $go20 defun\n20 go20 echo\n"
        )
        result = _run_stacker(["--recursion-limit", "10"], script_content=deep_20)
        combined = result.stdout + result.stderr
        self.assertIn("StackerRecursionError", combined)
        self.assertIn("(10)", combined)

    def test_cli_flag_rejects_out_of_range_values(self):
        for bad in ["0", "-5", "999999"]:
            with self.subTest(value=bad):
                result = _run_stacker(["--recursion-limit", bad, "-e", "1 1 +"])
                self.assertEqual(result.returncode, 2)  # argparse error
                self.assertIn("--recursion-limit", result.stderr)


class TestRecursionGuardInProcess(unittest.TestCase):
    def setUp(self):
        self._original_limit = recursion.get_limit()

    def tearDown(self):
        recursion.set_limit(self._original_limit)
        recursion._depth = 0  # Whitebox reset in case a test leaked

    def test_named_function_in_error(self):
        recursion.set_limit(5)
        stacker = Stacker()
        stacker.process_expression("{n} {n 1 + selfcall} $selfcall defun")
        with self.assertRaises(StackerRecursionError) as ctx:
            stacker.process_expression("0 selfcall")
        self.assertEqual(ctx.exception.name, "selfcall")
        self.assertIn("`selfcall`", str(ctx.exception))

    def test_lambda_reported_as_lambda(self):
        recursion.set_limit(5)
        stacker = Stacker()
        stacker.process_expression("{x} {x recl} lambda $recl set")
        with self.assertRaises(StackerRecursionError) as ctx:
            stacker.process_expression("1 recl")
        self.assertEqual(ctx.exception.name, "<lambda>")

    def test_counter_does_not_leak_after_error(self):
        recursion.set_limit(5)
        stacker = Stacker()
        stacker.process_expression("{n} {n 1 + boom} $boom defun")
        with self.assertRaises(StackerRecursionError):
            stacker.process_expression("0 boom")
        # The guard must be fully unwound: a shallow call succeeds
        stacker.process_expression("{x} {x 1 +} $inc defun")
        stacker.process_expression("41 inc")
        self.assertEqual(stacker.pop(), 42)

    def test_set_limit_validation(self):
        for bad in (0, -1, recursion.MAX_RECURSION_LIMIT + 1):
            with self.subTest(value=bad):
                with self.assertRaises(ValueError):
                    recursion.set_limit(bad)


if __name__ == "__main__":
    unittest.main()
