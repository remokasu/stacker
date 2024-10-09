import unittest

from stacker.stacker import Stacker


class TestStacker(unittest.TestCase):
    def setUp(self):
        self.stacker = Stacker()

    def test_function_definition_and_call_1(self):
        self.stacker.stack.clear()
        self.stacker.eval("{x} {x 2 + x 3 * +} $f defun")
        ans = self.stacker.eval("4 f")
        self.assertEqual(ans[-1], 18)

    def test_function_definition_and_call_2(self):
        self.stacker.stack.clear()
        self.stacker.eval("{xs} {xs sum} $test_sum defun")
        ans = self.stacker.eval("[1 2 3] test_sum")
        self.assertEqual(ans[-1], 6)

    def test_function_definition_and_call_3(self):
        self.stacker.stack.clear()
        self.stacker.eval("{xs} {xs sum} $test_sum defun")
        ans = self.stacker.eval("{[4 5 6]} test_sum")
        self.assertEqual(ans[-1], 15)

    def test_function_definition_and_call_4(self):
        self.stacker.stack.clear()
        self.stacker.eval("{xs} {xs sum} $test_sum defun")
        ans = self.stacker.eval("{(7 8 9)} test_sum")
        self.assertEqual(ans[-1], 24)
