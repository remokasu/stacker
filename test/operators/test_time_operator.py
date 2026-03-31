import unittest
import time

from stacker.stacker import Stacker


class TestUnit(unittest.TestCase):
    def setUp(self):
        self.stacker = Stacker()

    def test_time_returns_float(self):
        self.stacker.stack.clear()
        ans = self.stacker.eval("time")
        self.assertIsInstance(ans[-1], float)

    def test_time_is_reasonable(self):
        before = time.time()
        self.stacker.stack.clear()
        ans = self.stacker.eval("time")
        after = time.time()
        self.assertGreaterEqual(ans[-1], before)
        self.assertLessEqual(ans[-1], after)

    def test_time_result_is_positive(self):
        self.stacker.stack.clear()
        ans = self.stacker.eval("time")
        self.assertGreater(ans[-1], 0)
