import unittest

from stacker.stacker import Stacker


class TestUnit(unittest.TestCase):
    def test_drop(self):
        stacker = Stacker()
        stacker.push(1)
        stacker.push(2)
        stacker.push(3)
        self.assertEqual(list(stacker.stack), [1, 2, 3])
        expr = "drop"
        stacker.process_expression(expr)
        self.assertEqual(list(stacker.stack), [1, 2])

    def test_dup(self):
        stacker = Stacker()
        stacker.push(1)
        stacker.push(2)
        stacker.push(3)
        self.assertEqual(list(stacker.stack), [1, 2, 3])
        expr = "dup"
        stacker.process_expression(expr)
        self.assertEqual(list(stacker.stack), [1, 2, 3, 3])

    # def test_copy(self):
    #     stacker = Stacker()
    #     stacker.push(1)
    #     stacker.push(2)
    #     stacker.push(3)
    #     self.assertEqual(list(stacker.stack), [1, 2, 3])
    #     expr = "1 copy"
    #     stacker.process_expression(expr)
    #     self.assertEqual(list(stacker.stack), [1, 2, 3, 2])

    def test_swap(self):
        stacker = Stacker()
        stacker.push(1)
        stacker.push(2)
        stacker.push(3)
        stacker.push(4)
        self.assertEqual(list(stacker.stack), [1, 2, 3, 4])
        expr = "swap"
        stacker.process_expression(expr)
        self.assertEqual(list(stacker.stack), [1, 2, 4, 3])

    # def test_pluck(self):
    #     stacker = Stacker()
    #     stacker.push(1)
    #     stacker.push(2)
    #     stacker.push(3)
    #     stacker.push(4)
    #     self.assertEqual(list(stacker.stack), [1, 2, 3, 4])
    #     expr = "1 pluck"
    #     stacker.process_expression(expr)
    #     self.assertEqual(list(stacker.stack), [1, 3, 4, 2])

    def test_insert(self):
        stacker = Stacker()
        stacker.push(1)
        stacker.push(2)
        stacker.push(3)
        stacker.push(4)
        self.assertEqual(list(stacker.stack), [1, 2, 3, 4])
        expr = "1 5 ins"
        stacker.process_expression(expr)
        self.assertEqual(list(stacker.stack), [1, 5, 2, 3, 4])

    def test_rev(self):
        stacker = Stacker()
        stacker.push(1)
        stacker.push(2)
        stacker.push(3)
        stacker.push(4)
        self.assertEqual(list(stacker.stack), [1, 2, 3, 4])
        expr = "rev"
        stacker.process_expression(expr)
        self.assertEqual(list(stacker.stack), [4, 3, 2, 1])

    def test_rot(self):
        stacker = Stacker()
        stacker.push(1)
        stacker.push(2)
        stacker.push(3)
        stacker.push(4)
        self.assertEqual(list(stacker.stack), [1, 2, 3, 4])
        expr = "1 rot"
        stacker.process_expression(expr)
        self.assertEqual(list(stacker.stack), [4, 1, 2, 3])
        expr = "2 rot"
        stacker.process_expression(expr)
        self.assertEqual(list(stacker.stack), [2, 3, 4, 1])

    def test_rotl(self):
        stacker = Stacker()
        stacker.push(1)
        stacker.push(2)
        stacker.push(3)
        stacker.push(4)
        self.assertEqual(list(stacker.stack), [1, 2, 3, 4])
        expr = "1 rotl"
        stacker.process_expression(expr)
        self.assertEqual(list(stacker.stack), [2, 3, 4, 1])
        expr = "2 rotl"
        stacker.process_expression(expr)
        self.assertEqual(list(stacker.stack), [4, 1, 2, 3])

    def test_pick(self):
        stacker = Stacker()
        stacker.push(1)
        stacker.push(2)
        stacker.push(3)
        stacker.push(4)
        self.assertEqual(list(stacker.stack), [1, 2, 3, 4])
        expr = "1 pick"
        stacker.process_expression(expr)
        self.assertEqual(list(stacker.stack), [1, 2, 3, 4, 2])
        expr = "2 pick"
        stacker.process_expression(expr)
        self.assertEqual(list(stacker.stack), [1, 2, 3, 4, 2, 3])
        expr = "-1 pick"
        stacker.process_expression(expr)
        self.assertEqual(list(stacker.stack), [1, 2, 3, 4, 2, 3, 3])
        expr = "-8 pick"
        with self.assertRaises(IndexError):
            stacker.process_expression(expr)
        expr = "8 pick"
        with self.assertRaises(IndexError):
            stacker.process_expression(expr)

    def test_count(self):
        stacker = Stacker()
        stacker.push(1)
        stacker.push(2)
        stacker.push(3)
        stacker.push("A")
        stacker.push("B")
        stacker.push("C")
        self.assertEqual(list(stacker.stack), [1, 2, 3, "A", "B", "C"])
        expr = "'A' count"
        stacker.process_expression(expr)
        self.assertEqual(list(stacker.stack), [1, 2, 3, "A", "B", "C", 1])

    def test_clear(self):
        stacker = Stacker()
        stacker.push(1)
        stacker.push(2)
        stacker.push(3)
        stacker.push(4)
        self.assertEqual(list(stacker.stack), [1, 2, 3, 4])
        expr = "clear"
        stacker.process_expression(expr)
        self.assertEqual(list(stacker.stack), [])
