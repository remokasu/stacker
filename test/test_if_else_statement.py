import unittest

from stacker.stacker import Stacker


class TestUnit(unittest.TestCase):
    def test_if(self):
        # True
        stacker = Stacker()
        expr = "123 true if"
        stacker.process_expression(expr)
        self.assertEqual(list(stacker.stack), [123])

        stacker = Stacker()
        expr = "123 True if"
        stacker.process_expression(expr)
        self.assertEqual(list(stacker.stack), [123])

        stacker = Stacker()
        expr = "-1 $x set {3 5 +} {0 x >} if"
        stacker.process_expression(expr)
        self.assertEqual(list(stacker.stack), [8])

        # False
        stacker.stack.clear()
        expr = "123 false if"
        stacker.process_expression(expr)
        self.assertEqual(list(stacker.stack), [])

        stacker.stack.clear()
        expr = "123 False if"
        stacker.process_expression(expr)
        self.assertEqual(list(stacker.stack), [])

        stacker = Stacker()
        expr = "-1 $x set {3 5 +} {0 x <} if"
        stacker.process_expression(expr)
        self.assertEqual(list(stacker.stack), [])

    def test_if_else(self):
        # True
        stacker = Stacker()
        expr = "114 514 true ifelse"
        stacker.process_expression(expr)
        self.assertEqual(list(stacker.stack), [114])

        stacker = Stacker()
        expr = "114 514 True ifelse"
        stacker.process_expression(expr)
        self.assertEqual(list(stacker.stack), [114])

        stacker = Stacker()
        expr = "{114 514 +} {810 1008 +} True ifelse"
        stacker.process_expression(expr)
        self.assertEqual(list(stacker.stack), [628])

        stacker = Stacker()
        expr = "-1 $x set {114 514 +} {810 1008 +} {0 x >} ifelse"
        stacker.process_expression(expr)
        self.assertEqual(list(stacker.stack), [628])

        # False
        stacker.stack.clear()
        expr = "114 514 false ifelse"
        stacker.process_expression(expr)
        self.assertEqual(list(stacker.stack), [514])

        stacker.stack.clear()
        expr = "114 514 False ifelse"
        stacker.process_expression(expr)
        self.assertEqual(list(stacker.stack), [514])

        stacker = Stacker()
        expr = "{114 514 +} {810 1008 +} False ifelse"
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
