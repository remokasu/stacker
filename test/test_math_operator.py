import unittest

from stacker.stacker import Stacker


class TestUnit(unittest.TestCase):
    def test_pow(self):
        stacker = Stacker()
        stacker.push(2)
        stacker.push(3)
        self.assertEqual(list(stacker.stack), [2, 3])
        expr = "^"
        stacker.process_expression(expr)
        self.assertEqual(stacker.stack[-1], 8)
        stacker.push(2)
        stacker.process_expression(expr)
        self.assertEqual(stacker.stack[-1], 64)
        stacker.push("abc")
        with self.assertRaises(TypeError):
            stacker.process_expression(expr)
