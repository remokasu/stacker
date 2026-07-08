"""Performance guard for script-mode line accumulation.

The line loop feeds an incremental TerminalScanner, so one expression
spanning N lines costs O(total size), not O(N^2). Regression here showed
up as an 8,000-row array taking >90s (vs 0.17s before); these tests pin
generous absolute bounds far above the expected linear-time cost.
"""

import os
import tempfile
import time
import unittest

from stacker.stacker import Stacker
from stacker.runtime.exec_modes.script_mode import ScriptMode

#: Generous wall-clock bound; linear-time accumulation stays well under
#: this, while a quadratic regression exceeds it by an order of magnitude.
TIME_LIMIT_SECONDS = 10.0

#: Lines per multi-line construct — large enough that O(N^2) rescanning
#: visibly explodes, small enough to keep the suite fast when healthy.
LINE_COUNT = 3000


class TestMultilineAccumulationPerformance(unittest.TestCase):
    def _run_script(self, content):
        stacker = Stacker()
        script_mode = ScriptMode(stacker)
        with tempfile.NamedTemporaryFile(mode="w", suffix=".stk", delete=False) as f:
            f.write(content)
            temp_file = f.name
        try:
            start = time.perf_counter()
            script_mode.execute_stacker_dotfile(temp_file)
            elapsed = time.perf_counter() - start
        finally:
            os.unlink(temp_file)
        return stacker, elapsed

    def test_large_multiline_array_is_linear(self):
        # Rows without explicit ";" form one flat array in script mode
        content = "[1 2 3\n" + "4 5 6\n" * (LINE_COUNT - 2) + "7 8 9]\n"
        stacker, elapsed = self._run_script(content)
        self.assertLess(elapsed, TIME_LIMIT_SECONDS)
        self.assertEqual(len(stacker.stack), 1)
        self.assertEqual(len(stacker.stack[-1]), 3 * LINE_COUNT)

    def test_large_multiline_string_is_linear(self):
        content = '"""\n' + "text line\n" * LINE_COUNT + '"""\n'
        stacker, elapsed = self._run_script(content)
        self.assertLess(elapsed, TIME_LIMIT_SECONDS)
        self.assertEqual(len(stacker.stack), 1)
        self.assertEqual(stacker.stack[-1].count("text line"), LINE_COUNT)

    def test_large_multiline_block_comment_is_linear(self):
        content = "#|\n" + "commentary\n" * LINE_COUNT + "|#\n42\n"
        stacker, elapsed = self._run_script(content)
        self.assertLess(elapsed, TIME_LIMIT_SECONDS)
        self.assertEqual(list(stacker.stack), [42])


if __name__ == "__main__":
    unittest.main()
