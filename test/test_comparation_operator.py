import unittest

from stacker.stacker import Stacker


class TestUnit(unittest.TestCase):
    def test_eq(self):
        stacker = Stacker()
        stacker.push(1)
        stacker.push(1)
        self.assertEqual(list(stacker.stack), [1, 1])
        expr = "=="
        stacker.process_expression(expr)
        self.assertEqual(stacker.stack[-1], True)
        stacker.push(4.2)
        stacker.process_expression(expr)
        self.assertEqual(stacker.stack[-1], False)
        stacker.push("abc")
        stacker.process_expression(expr)
        self.assertEqual(stacker.stack[-1], False)

    def test_ne(self):
        stacker = Stacker()
        stacker.push(1)
        stacker.push(1)
        self.assertEqual(list(stacker.stack), [1, 1])
        expr = "!="
        stacker.process_expression(expr)
        self.assertEqual(stacker.stack[-1], False)
        stacker.push(4.2)
        stacker.process_expression(expr)
        self.assertEqual(stacker.stack[-1], True)
        stacker.push("abc")
        stacker.process_expression(expr)
        self.assertEqual(stacker.stack[-1], True)

    def test_gt(self):
        stacker = Stacker()
        stacker.push(1)
        stacker.push(1)
        self.assertEqual(list(stacker.stack), [1, 1])
        expr = ">"
        stacker.process_expression(expr)
        self.assertEqual(stacker.stack[-1], False)
        stacker.push(4.2)
        stacker.push(4.1)
        stacker.process_expression(expr)
        self.assertEqual(stacker.stack[-1], True)
        stacker.push("abc")
        with self.assertRaises(TypeError):
            stacker.process_expression(expr)

    def test_lt(self):
        stacker = Stacker()
        stacker.push(1)
        stacker.push(1)
        self.assertEqual(list(stacker.stack), [1, 1])
        expr = "<"
        stacker.process_expression(expr)
        self.assertEqual(stacker.stack[-1], False)
        stacker.push(4.2)
        stacker.push(4.3)
        stacker.process_expression(expr)
        self.assertEqual(stacker.stack[-1], True)
        stacker.push("abc")
        with self.assertRaises(TypeError):
            stacker.process_expression(expr)

    def test_ge(self):
        stacker = Stacker()
        stacker.push(1)
        stacker.push(1)
        self.assertEqual(list(stacker.stack), [1, 1])
        expr = ">="
        stacker.process_expression(expr)
        self.assertEqual(stacker.stack[-1], True)
        stacker.push(4.2)
        stacker.push(4.3)
        stacker.process_expression(expr)
        self.assertEqual(stacker.stack[-1], False)
        stacker.push("abc")
        with self.assertRaises(TypeError):
            stacker.process_expression(expr)

    def test_le(self):
        stacker = Stacker()
        stacker.push(1)
        stacker.push(1)
        self.assertEqual(list(stacker.stack), [1, 1])
        expr = "<="
        stacker.process_expression(expr)
        self.assertEqual(stacker.stack[-1], True)
        stacker.push(4.2)
        stacker.push(4.1)
        stacker.process_expression(expr)
        self.assertEqual(stacker.stack[-1], False)
        stacker.push("abc")
        with self.assertRaises(TypeError):
            stacker.process_expression(expr)
