import unittest

from stacker.stacker import Stacker


class TestUnit(unittest.TestCase):
    def test_band(self):
        stacker = Stacker()
        stacker.push(1)
        stacker.push(2)
        self.assertEqual(list(stacker.stack), [1, 2])
        expr = "band"
        stacker.process_expression(expr)
        self.assertEqual(stacker.stack[-1], 0)
        stacker.push(4.2)
        with self.assertRaises(TypeError):
            stacker.process_expression(expr)
        stacker.push("abc")
        stacker.push("edf")
        with self.assertRaises(TypeError):
            stacker.process_expression(expr)

    def test_bor(self):
        stacker = Stacker()
        stacker.push(1)
        stacker.push(2)
        self.assertEqual(list(stacker.stack), [1, 2])
        expr = "bor"
        stacker.process_expression(expr)
        self.assertEqual(stacker.stack[-1], 3)
        stacker.push(4.2)
        with self.assertRaises(TypeError):
            stacker.process_expression(expr)
        stacker.push("abc")
        stacker.push("edf")
        with self.assertRaises(TypeError):
            stacker.process_expression(expr)

    def test_bxor(self):
        stacker = Stacker()
        stacker.push(1)
        stacker.push(2)
        self.assertEqual(list(stacker.stack), [1, 2])
        expr = "bxor"
        stacker.process_expression(expr)
        self.assertEqual(stacker.stack[-1], 3)
        stacker.push(4.2)
        with self.assertRaises(TypeError):
            stacker.process_expression(expr)
        stacker.push("abc")
        stacker.push("edf")
        with self.assertRaises(TypeError):
            stacker.process_expression(expr)

    def test_bnot(self):
        stacker = Stacker()
        stacker.push(1)
        self.assertEqual(list(stacker.stack), [1])
        expr = "~"
        stacker.process_expression(expr)
        self.assertEqual(stacker.stack[-1], -2)
        stacker.push(4.2)
        with self.assertRaises(TypeError):
            stacker.process_expression(expr)
        stacker.push("abc")
        with self.assertRaises(TypeError):
            stacker.process_expression(expr)

    def test_lshift(self):
        stacker = Stacker()
        stacker.push(1)
        stacker.push(2)
        self.assertEqual(list(stacker.stack), [1, 2])
        expr = "<<"
        stacker.process_expression(expr)
        self.assertEqual(stacker.stack[-1], 4)
        stacker.push(4.2)
        with self.assertRaises(TypeError):
            stacker.process_expression(expr)
        stacker.push("abc")
        stacker.push("edf")
        with self.assertRaises(TypeError):
            stacker.process_expression(expr)

    def test_rshift(self):
        stacker = Stacker()
        stacker.push(8)
        stacker.push(2)
        self.assertEqual(list(stacker.stack), [8, 2])
        expr = ">>"
        stacker.process_expression(expr)
        self.assertEqual(stacker.stack[-1], 2)
        stacker.push(4.2)
        with self.assertRaises(TypeError):
            stacker.process_expression(expr)
        stacker.push("abc")
        stacker.push("edf")
        with self.assertRaises(TypeError):
            stacker.process_expression(expr)
