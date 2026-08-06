import unittest

from stacker.stacker import Stacker


class TestUnit(unittest.TestCase):
    def test_if_1(self):
        # True
        stacker = Stacker()
        expr = "true 123 if"
        stacker.process_expression(expr)
        self.assertEqual(list(stacker.stack), [123])

    def test_if_2(self):
        stacker = Stacker()
        expr = "True 123 if"
        stacker.process_expression(expr)
        self.assertEqual(list(stacker.stack), [123])

    def test_if_3(self):
        stacker = Stacker()
        expr = "-1 $x set {0 x >} {3 5 +} if"
        stacker.process_expression(expr)
        self.assertEqual(list(stacker.stack), [8])

        # False

    def test_if_4(self):
        stacker = Stacker()
        expr = "false 123 if"
        stacker.process_expression(expr)
        self.assertEqual(list(stacker.stack), [])

    def test_if_5(self):
        stacker = Stacker()
        expr = "False 123 if"
        stacker.process_expression(expr)
        self.assertEqual(list(stacker.stack), [])

    def test_if_6(self):
        stacker = Stacker()
        expr = "-1 $x set {0 x <} {3 5 +} if"
        stacker.process_expression(expr)
        self.assertEqual(list(stacker.stack), [])

    def test_if_else(self):
        # True
        stacker = Stacker()
        expr = "true 114 514 ifelse"
        stacker.process_expression(expr)
        self.assertEqual(list(stacker.stack), [114])

        stacker = Stacker()
        expr = "True 114 514 ifelse"
        stacker.process_expression(expr)
        self.assertEqual(list(stacker.stack), [114])

        stacker = Stacker()
        expr = "True {114 514 +} {810 1008 +} ifelse"
        stacker.process_expression(expr)
        self.assertEqual(list(stacker.stack), [628])

        stacker = Stacker()
        expr = "-1 $x set 0 x > {114 514 +} {810 1008 +}  ifelse"
        stacker.process_expression(expr)
        self.assertEqual(list(stacker.stack), [628])

        # False
        stacker.stack.clear()
        expr = "false 114 514 ifelse"
        stacker.process_expression(expr)
        self.assertEqual(list(stacker.stack), [514])

        stacker.stack.clear()
        expr = "False 114 514 ifelse"
        stacker.process_expression(expr)
        self.assertEqual(list(stacker.stack), [514])

        stacker = Stacker()
        expr = "False {114 514 +} {810 1008 +} ifelse"
        stacker.process_expression(expr)
        self.assertEqual(list(stacker.stack), [1818])

    def test_if_error(self):
        # error
        stacker = Stacker()
        expr = "{1 +} {99} iferror"
        stacker.process_expression(expr)
        self.assertEqual(list(stacker.stack), [99])

        # no error
        stacker = Stacker()
        expr = "{1 1 +} {99} iferror"
        stacker.process_expression(expr)
        self.assertEqual(list(stacker.stack), [2])

    def test_iferror_does_not_catch_break(self):
        # break inside the try block must exit the enclosing loop instead of
        # triggering the catch block. BreakException derives from BaseException
        # precisely so that iferror's except Exception lets it through; if it
        # were ever changed to derive from Exception, the catch block (999)
        # would run and this test would fail.
        stacker = Stacker()
        expr = (
            "0 $s set [1 2 3 4 5] $i"
            " { {i 3 == {break} if s i + $s set} {999 $s set} iferror } dolist s"
        )
        stacker.process_expression(expr)
        self.assertEqual(stacker.stack[-1], 3)
