import unittest

from stacker.stacker import Stacker


class TestUnit(unittest.TestCase):
    def test_and(self):
        stacker = Stacker()
        stacker.push(True)
        stacker.push(True)
        self.assertEqual(list(stacker.stack), [True, True])
        expr = "and"
        stacker.process_expression(expr)
        self.assertEqual(stacker.stack[-1], True)
        stacker.push(False)
        stacker.process_expression(expr)
        self.assertEqual(stacker.stack[-1], False)
        stacker.push("abc")
        stacker.process_expression(expr)
        self.assertEqual(stacker.stack[-1], False)

    def test_or(self):
        stacker = Stacker()
        stacker.push(True)
        stacker.push(True)
        self.assertEqual(list(stacker.stack), [True, True])
        expr = "or"
        stacker.process_expression(expr)
        self.assertEqual(stacker.stack[-1], True)
        stacker.push(False)
        stacker.process_expression(expr)
        self.assertEqual(stacker.stack[-1], True)
        stacker.push("abc")
        stacker.process_expression(expr)
        self.assertEqual(stacker.stack[-1], True)

    def test_not(self):
        stacker = Stacker()
        stacker.push(True)
        self.assertEqual(list(stacker.stack), [True])
        expr = "not"
        stacker.process_expression(expr)
        self.assertEqual(stacker.stack[-1], False)
        stacker.push(False)
        stacker.process_expression(expr)
        self.assertEqual(stacker.stack[-1], True)
