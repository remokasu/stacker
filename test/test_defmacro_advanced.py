import unittest

from stacker.stacker import Stacker


class TestStacker(unittest.TestCase):
    def setUp(self):
        self.stacker = Stacker()

    def test_macro_no_args(self):
        self.stacker.stack.clear()
        self.stacker.eval("{1 2 +} $three defmacro")
        ans = self.stacker.eval("three")
        self.assertEqual(ans[-1], 3)

    def test_macro_multiple_calls(self):
        self.stacker.stack.clear()
        self.stacker.eval("{2 *} $double defmacro")
        ans = self.stacker.eval("3 double")
        self.assertEqual(ans[-1], 6)
        self.stacker.stack.clear()
        ans = self.stacker.eval("5 double")
        self.assertEqual(ans[-1], 10)

    def test_macro_composed(self):
        self.stacker.stack.clear()
        self.stacker.eval("{2 *} $double defmacro")
        self.stacker.eval("{3 +} $add3 defmacro")
        ans = self.stacker.eval("4 double add3")
        self.assertEqual(ans[-1], 11)

    def test_macro_with_stack_ops(self):
        self.stacker.stack.clear()
        self.stacker.eval("{dup *} $square defmacro")
        ans = self.stacker.eval("5 square")
        self.assertEqual(ans[-1], 25)

    def test_macro_redefine(self):
        self.stacker.stack.clear()
        self.stacker.eval("{2 *} $double defmacro")
        ans = self.stacker.eval("3 double")
        self.assertEqual(ans[-1], 6)
        self.stacker.stack.clear()
        self.stacker.eval("{3 *} $double defmacro")
        ans = self.stacker.eval("3 double")
        self.assertEqual(ans[-1], 9)

    def test_macro_in_loop(self):
        self.stacker.stack.clear()
        self.stacker.eval("{2 *} $double defmacro")
        ans = self.stacker.eval("1 $x set 1 4 $i {x double $x set} do x")
        self.assertEqual(ans[-1], 16)
