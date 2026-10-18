import unittest

from stacker.stacker import Stacker


class TestApply(unittest.TestCase):
    def setUp(self):
        self.stacker = Stacker()

    def test_apply_addition(self):
        ans = self.stacker.eval("[3 4] {+} apply")
        self.assertEqual(ans[-1], 7)

    def test_apply_multiply(self):
        ans = self.stacker.eval("[2 3] {*} apply")
        self.assertEqual(ans[-1], 6)

    def test_apply_single_arg(self):
        ans = self.stacker.eval("[5] {2 *} apply")
        self.assertEqual(ans[-1], 10)

    def test_apply_with_lambda(self):
        ans = self.stacker.eval("[7] {x} {x 3 +} lambda apply")
        self.assertEqual(ans[-1], 10)

    def test_apply_three_args(self):
        # [1 2 3] => 1 2 3 on stack, then sum via two additions
        # Use a code block that adds three values
        ans = self.stacker.eval("[1 2 3] {+ +} apply")
        self.assertEqual(ans[-1], 6)

    def test_apply_recursive_map(self):
        # my-map defined recursively; the lambda held in `lf` is passed on as a value
        self.stacker.eval(
            "{xs lf} {xs empty? {[]} {xs car lf eval  xs cdr lf my-map  cons} ifelse}"
            " :my-map defun"
        )
        ans = self.stacker.eval("[1 2 3] {x} {x 2 *} lambda my-map")
        self.assertEqual(ans[-1], [2, 4, 6])

    def test_apply_recursive_filter(self):
        # my-filter defined recursively
        self.stacker.eval(
            "{xs pred} {xs empty? {[]} {xs car pred eval"
            "  {xs car xs cdr pred my-filter cons}"
            "  {xs cdr pred my-filter}"
            "  ifelse} ifelse}"
            " :my-filter defun"
        )
        ans = self.stacker.eval("[1 2 3 4 5] {x} {x 2 % 0 ==} lambda my-filter")
        self.assertEqual(ans[-1], [2, 4])
