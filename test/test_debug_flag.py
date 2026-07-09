"""Regression tests for --debug in script mode (audit #14).

The flag was wired into ExecutionMode.debug but ScriptMode.run never
read it, so failing scripts printed identical output with and without
--debug. It must now print the Python traceback like the REPL does.
"""

import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent

FAILING_SCRIPT = "1 0 /\n"


def _run(args):
    with tempfile.NamedTemporaryFile(
        mode="w", suffix=".stk", delete=False, dir=REPO_ROOT
    ) as f:
        f.write(FAILING_SCRIPT)
        path = f.name
    try:
        return subprocess.run(
            [sys.executable, "-m", "stacker", *args, path],
            capture_output=True,
            text=True,
            timeout=60,
            cwd=REPO_ROOT,
        )
    finally:
        Path(path).unlink()


class TestDebugFlagInScriptMode(unittest.TestCase):
    def test_debug_prints_traceback_on_error(self):
        result = _run(["--debug"])
        self.assertIn("Traceback", result.stderr)

    def test_without_debug_no_traceback(self):
        result = _run([])
        self.assertNotIn("Traceback", result.stderr)
        self.assertIn("error", result.stderr)  # Formatted error still shown


if __name__ == "__main__":
    unittest.main()
