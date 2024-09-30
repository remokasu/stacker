import unittest

from stacker.stacker import Stacker


class TestUnit(unittest.TestCase):
    def test_bin(self):
        stacker = Stacker()
        stacker.stack.append(1)
        stacker.stack.append(2)
        self.assertEqual(list(stacker.stack), [1, 2])
        expr = "bin"
        stacker.process_expression(expr)
        self.assertEqual(stacker.stack[-1], "0b10")
        stacker.stack.append(4.2)
        with self.assertRaises(ValueError):
            stacker.process_expression(expr)
        stacker.stack.append("abc")
        with self.assertRaises(ValueError):
            stacker.process_expression(expr)

    def test_oct(self):
        stacker = Stacker()
        stacker.stack.append(1)
        stacker.stack.append(2)
        self.assertEqual(list(stacker.stack), [1, 2])
        expr = "oct"
        stacker.process_expression(expr)
        self.assertEqual(stacker.stack[-1], "0o2")
        stacker.stack.append(4.2)
        with self.assertRaises(ValueError):
            stacker.process_expression(expr)
        stacker.stack.append("abc")
        with self.assertRaises(ValueError):
            stacker.process_expression(expr)

    def test_dec(self):
        stacker = Stacker()
        stacker.stack.append(1)
        stacker.stack.append(2)
        self.assertEqual(list(stacker.stack), [1, 2])
        expr = "dec"
        stacker.process_expression(expr)
        self.assertEqual(stacker.stack[-1], 2)
        stacker.stack.append(4.2)
        with self.assertRaises(ValueError):
            stacker.process_expression(expr)
        stacker.stack.append("abc")
        with self.assertRaises(ValueError):
            stacker.process_expression(expr)

    def test_hex(self):
        stacker = Stacker()
        stacker.stack.append(1)
        stacker.stack.append(255)
        self.assertEqual(list(stacker.stack), [1, 255])
        expr = "hex"
        stacker.process_expression(expr)
        self.assertEqual(stacker.stack[-1], "0xff")
        stacker.stack.append(4.2)
        with self.assertRaises(ValueError):
            stacker.process_expression(expr)
        stacker.stack.append("abc")
        with self.assertRaises(ValueError):
            stacker.process_expression(expr)
