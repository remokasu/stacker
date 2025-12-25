import unittest

from stacker.stacker import Stacker


class TestUnit(unittest.TestCase):
    def test_add(self):
        stacker = Stacker()
        stacker.stack.append(1)
        stacker.stack.append(2)
        expr = "+"
        # integers
        self.assertEqual(list(stacker.stack), [1, 2])
        stacker.process_expression(expr)
        self.assertEqual(stacker.stack[-1], 3)
        # floats
        stacker.stack.clear()
        stacker.stack.append(3.2)
        stacker.stack.append(4.2)
        stacker.process_expression(expr)
        self.assertEqual(stacker.stack[-1], 7.4)
        # complex numbers
        stacker.stack.clear()
        stacker.stack.append(3 + 4j)
        stacker.stack.append(4 + 3j)
        stacker.process_expression(expr)
        self.assertEqual(stacker.stack[-1], (7 + 7j))
        # strings
        stacker.stack.clear()
        stacker.stack.append("abc")
        stacker.stack.append("def")
        stacker.process_expression(expr)

    def test_sub(self):
        stacker = Stacker()
        stacker.stack.append(1)
        stacker.stack.append(2)
        expr = "-"
        # integers
        self.assertEqual(list(stacker.stack), [1, 2])
        stacker.process_expression(expr)
        self.assertEqual(stacker.stack[-1], -1)
        # floats
        stacker.stack.clear()
        stacker.stack.append(3.2)
        stacker.stack.append(4.2)
        stacker.process_expression(expr)
        self.assertEqual(stacker.stack[-1], -1.0)
        # complex numbers
        stacker.stack.clear()
        stacker.stack.append(3 + 4j)
        stacker.stack.append(4 + 3j)
        stacker.process_expression(expr)
        self.assertEqual(stacker.stack[-1], (-1 + 1j))
        # strings
        stacker.stack.clear()
        stacker.stack.append("abc")
        stacker.stack.append("def")
        with self.assertRaises(TypeError):
            stacker.process_expression(expr)

    def test_mul(self):
        stacker = Stacker()
        stacker.stack.append(1)
        stacker.stack.append(2)
        expr = "*"
        # integers
        self.assertEqual(list(stacker.stack), [1, 2])
        stacker.process_expression(expr)
        self.assertEqual(stacker.stack[-1], 2)
        # floats
        stacker.stack.clear()
        stacker.stack.append(3.2)
        stacker.stack.append(4.2)
        stacker.process_expression(expr)
        self.assertAlmostEqual(stacker.stack[-1], 13.44)
        # complex numbers
        stacker.stack.clear()
        stacker.stack.append(3 + 4j)
        stacker.stack.append(4 + 3j)
        stacker.process_expression(expr)
        self.assertAlmostEqual(stacker.stack[-1], 0 + 25j)
        # strings
        stacker.stack.clear()
        stacker.stack.append("abc")
        stacker.stack.append("def")
        with self.assertRaises(TypeError):
            stacker.process_expression(expr)

    def test_div(self):
        stacker = Stacker()
        stacker.stack.append(1)
        stacker.stack.append(2)
        expr = "/"
        # integers
        self.assertEqual(list(stacker.stack), [1, 2])
        stacker.process_expression(expr)
        self.assertEqual(stacker.stack[-1], 0.5)
        # floats
        stacker.stack.clear()
        stacker.stack.append(3.2)
        stacker.stack.append(4.2)
        stacker.process_expression(expr)
        self.assertAlmostEqual(stacker.stack[-1], 0.7619047619047619)
        # complex numbers
        stacker.stack.clear()
        stacker.stack.append(3 + 4j)
        stacker.stack.append(4 + 3j)
        stacker.process_expression(expr)
        self.assertAlmostEqual(stacker.stack[-1], 0.96 + 0.28j)
        # strings
        stacker.stack.clear()
        stacker.stack.append("abc")
        stacker.stack.append("def")
        with self.assertRaises(TypeError):
            stacker.process_expression(expr)

    def test_intdiv(self):
        stacker = Stacker()
        stacker.stack.append(1)
        stacker.stack.append(2)
        expr = "//"
        # integers
        self.assertEqual(list(stacker.stack), [1, 2])
        stacker.process_expression(expr)
        self.assertEqual(stacker.stack[-1], 0)
        # floats
        stacker.stack.clear()
        stacker.stack.append(3.2)
        stacker.stack.append(4.2)
        stacker.process_expression(expr)
        self.assertEqual(stacker.stack[-1], 0.0)
        # strings
        stacker.stack.clear()
        stacker.stack.append("abc")
        stacker.stack.append("def")
        with self.assertRaises(TypeError):
            stacker.process_expression(expr)

    def test_mod(self):
        stacker = Stacker()
        stacker.stack.append(1)
        stacker.stack.append(2)
        expr = "%"
        # integers
        self.assertEqual(list(stacker.stack), [1, 2])
        stacker.process_expression(expr)
        self.assertEqual(stacker.stack[-1], 1)
        # floats
        stacker.stack.clear()
        stacker.stack.append(3.2)
        stacker.stack.append(4.2)
        stacker.process_expression(expr)
        self.assertEqual(stacker.stack[-1], 3.2)
        # strings
        stacker.stack.clear()
        stacker.stack.append("abc")
        stacker.stack.append("def")
        with self.assertRaises(TypeError):
            stacker.process_expression(expr)

    def test_increment(self):
        stacker = Stacker()
        stacker.stack.append(1)
        expr = "++"
        # integers
        self.assertEqual(list(stacker.stack), [1])
        stacker.process_expression(expr)
        self.assertEqual(stacker.stack[-1], 2)
        # floats
        stacker.stack.clear()
        stacker.stack.append(3.2)
        stacker.process_expression(expr)
        self.assertEqual(stacker.stack[-1], 4.2)
        # strings
        stacker.stack.clear()
        stacker.stack.append("abc")
        with self.assertRaises(TypeError):
            stacker.process_expression(expr)

    def test_decrement(self):
        stacker = Stacker()
        stacker.stack.append(1)
        expr = "--"
        # integers
        self.assertEqual(list(stacker.stack), [1])
        stacker.process_expression(expr)
        self.assertEqual(stacker.stack[-1], 0)
        # floats
        stacker.stack.clear()
        stacker.stack.append(3.2)
        stacker.process_expression(expr)
        self.assertEqual(stacker.stack[-1], 2.2)
        # strings
        stacker.stack.clear()
        stacker.stack.append("abc")
        with self.assertRaises(TypeError):
            stacker.process_expression(expr)
