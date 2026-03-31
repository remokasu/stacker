import unittest

from stacker.stacker import Stacker


class TestStacker(unittest.TestCase):
    def setUp(self):
        self.stacker = Stacker()

    def test_recursive_factorial(self):
        self.stacker.stack.clear()
        self.stacker.eval(
            "{n} {n 1 <= {1} {n n 1 - fact *} ifelse} $fact defun"
        )
        ans = self.stacker.eval("5 fact")
        self.assertEqual(ans[-1], 120)

    def test_recursive_fibonacci(self):
        self.stacker.stack.clear()
        self.stacker.eval(
            "{n} {n 2 < {n} {n 1 - fib n 2 - fib +} ifelse} $fib defun"
        )
        ans = self.stacker.eval("10 fib")
        self.assertEqual(ans[-1], 55)

    def test_multi_arg_function(self):
        self.stacker.stack.clear()
        self.stacker.eval("{a b} {a b * a b + +} $f defun")
        ans = self.stacker.eval("3 4 f")
        self.assertEqual(ans[-1], 19)

    def test_function_calls_function(self):
        self.stacker.stack.clear()
        self.stacker.eval("{x} {x 2 *} $double defun")
        self.stacker.eval("{x} {x double double} $quadruple defun")
        ans = self.stacker.eval("3 quadruple")
        self.assertEqual(ans[-1], 12)

    def test_function_with_local_variable(self):
        self.stacker.stack.clear()
        self.stacker.eval("{x} {x 1 + $tmp set tmp tmp *} $f defun")
        ans = self.stacker.eval("4 f")
        self.assertEqual(ans[-1], 25)

    def test_function_does_not_pollute_global_scope(self):
        self.stacker.stack.clear()
        self.stacker.eval("10 $x set")
        self.stacker.eval("{x} {x 99 + $x set x} $f defun")
        self.stacker.eval("5 f")
        ans = self.stacker.eval("x")
        self.assertEqual(ans[-1], 10)

    def test_multiple_function_definitions(self):
        self.stacker.stack.clear()
        self.stacker.eval("{x} {x 1 +} $inc defun")
        self.stacker.eval("{x} {x 1 -} $dec defun")
        ans = self.stacker.eval("5 inc inc dec")
        self.assertEqual(ans[-1], 6)

    def test_function_returning_list(self):
        # リストはリテラルしか含めないので listn で構築する
        self.stacker.stack.clear()
        self.stacker.eval("{n} {n n 2 * n 3 * 3 listn} $triple defun")
        ans = self.stacker.eval("3 triple")
        self.assertEqual(ans[-1], [3, 6, 9])
