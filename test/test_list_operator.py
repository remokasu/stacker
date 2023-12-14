import unittest

from stacker.stacker import Stacker


class TestUnit(unittest.TestCase):
    def test_seq(self):
        stacker = Stacker()
        stacker.push(1)
        stacker.push(5)
        self.assertEqual(list(stacker.stack), [1, 5])
        expr = "seq"
        stacker.process_expression(expr)
        self.assertEqual(list(stacker.stack), [[1, 2, 3, 4, 5]])
        stacker.push(1.1)
        stacker.push(4.2)
        with self.assertRaises(TypeError):
            stacker.process_expression(expr)

    def test_range(self):
        stacker = Stacker()
        stacker.push(1)
        stacker.push(5)
        self.assertEqual(list(stacker.stack), [1, 5])
        expr = "range"
        stacker.process_expression(expr)
        self.assertEqual(list(stacker.stack), [[1, 2, 3, 4]])
        stacker.push(1.1)
        stacker.push(4.2)
        with self.assertRaises(TypeError):
            stacker.process_expression(expr)

    def test_len(self):
        stacker = Stacker()
        stacker.push([1, 2, 3, 4, 5])
        self.assertEqual(list(stacker.stack), [[1, 2, 3, 4, 5]])
        expr = "len"
        stacker.process_expression(expr)
        self.assertEqual(list(stacker.stack), [5])
        stacker.push(1.1)
        with self.assertRaises(TypeError):
            stacker.process_expression(expr)

    def test_min(self):
        stacker = Stacker()
        stacker.push([1, 2, 3, 4, 5])
        self.assertEqual(list(stacker.stack), [[1, 2, 3, 4, 5]])
        expr = "min"
        stacker.process_expression(expr)
        self.assertEqual(list(stacker.stack), [1])
        stacker.push(1.1)
        with self.assertRaises(TypeError):
            stacker.process_expression(expr)

    def test_max(self):
        stacker = Stacker()
        stacker.push([1, 2, 3, 4, 5])
        self.assertEqual(list(stacker.stack), [[1, 2, 3, 4, 5]])
        expr = "max"
        stacker.process_expression(expr)
        self.assertEqual(list(stacker.stack), [5])
        stacker.push(1.1)
        with self.assertRaises(TypeError):
            stacker.process_expression(expr)

    def test_sum(self):
        stacker = Stacker()
        stacker.push([1, 2, 3, 4, 5])
        self.assertEqual(list(stacker.stack), [[1, 2, 3, 4, 5]])
        expr = "sum"
        stacker.process_expression(expr)
        self.assertEqual(list(stacker.stack), [15])
        stacker.push(1.1)
        with self.assertRaises(TypeError):
            stacker.process_expression(expr)
