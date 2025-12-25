import unittest

from stacker.stacker import Stacker


class TestStacker(unittest.TestCase):
    def setUp(self):
        self.stacker = Stacker()

    def test_test_lambda_1(self):
        self.stacker.stack.clear()
        ans = self.stacker.eval("[1 2 3] {x} {x 2 *} lambda map")
        self.assertEqual(ans[-1], [2, 4, 6])

    # REMOVED: test_test_lambda_2 - () now creates code blocks, not tuples
    # Use [1 2 3] for lists instead

    def test_test_lambda_3(self):
        self.stacker.stack.clear()
        ans = self.stacker.eval("{1 2 3} {x} {x 2 *} lambda map")
        self.assertEqual(list(ans[-1]), [2, 4, 6])

    def test_test_lambda_factorial(self):
        self.stacker.stack.clear()
        ans = self.stacker.eval(
            """
{ n } {
    n 1 <=
    { 1 }
    { n n 1 - fact * }
    ifelse
} lambda $fact set
5 fact eval
"""
        )
        self.assertEqual(ans[-1], 120)
