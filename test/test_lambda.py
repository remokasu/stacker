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


class TestLambdaStackAccumulation(unittest.TestCase):
    """Regression: a lambda's local stack must not
    accumulate leftover values across calls (StackerFunction clears its
    stack per call; StackerLambda used to skip that)."""

    def test_lambda_stack_does_not_grow_across_calls(self):
        stacker = Stacker()
        stacker.eval("{x} {x x} lambda $dupfn set")
        fn = stacker.variables["dupfn"]
        stacker.eval("5 dupfn")
        first_len = len(fn.stack)
        stacker.eval("3 dupfn")
        stacker.eval("9 dupfn")
        self.assertEqual(len(fn.stack), first_len)
