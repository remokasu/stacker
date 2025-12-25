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

    def test_len(self):
        stacker = Stacker()
        stacker.push([1, 2, 3, 4, 5])
        self.assertEqual(list(stacker.stack), [[1, 2, 3, 4, 5]])
        expr = "len"
        stacker.process_expression(expr)
        # self.assertEqual(list(stacker.stack), [[1, 2, 3, 4, 5], 5])
        self.assertEqual(list(stacker.stack), [5])

    def test_min(self):
        stacker = Stacker()
        stacker.push([1, 2, 3, 4, 5])
        self.assertEqual(list(stacker.stack), [[1, 2, 3, 4, 5]])
        expr = "min"
        stacker.process_expression(expr)
        # self.assertEqual(list(stacker.stack), [[1, 2, 3, 4, 5], 1])
        self.assertEqual(list(stacker.stack), [1])

    def test_max(self):
        stacker = Stacker()
        stacker.push([1, 2, 3, 4, 5])
        self.assertEqual(list(stacker.stack), [[1, 2, 3, 4, 5]])
        expr = "max"
        stacker.process_expression(expr)
        # self.assertEqual(list(stacker.stack), [[1, 2, 3, 4, 5], 5])
        self.assertEqual(list(stacker.stack), [5])

    def test_sum(self):
        stacker = Stacker()
        stacker.push([1, 2, 3, 4, 5])
        self.assertEqual(list(stacker.stack), [[1, 2, 3, 4, 5]])
        expr = "sum"
        stacker.process_expression(expr)
        self.assertEqual(list(stacker.stack), [15])
