import unittest

from stacker.stacker import Stacker


class TestUnit(unittest.TestCase):
    def test_neg(self):
        stacker = Stacker()
        stacker.push(1)
        self.assertEqual(stacker.stack[-1], 1)
        expr = "neg"
        stacker.process_expression(expr)
        self.assertEqual(stacker.stack[-1], -1)
        stacker.push(4.2)
        stacker.process_expression(expr)
        self.assertEqual(stacker.stack[-1], -4.2)
        stacker.push("abc")
        with self.assertRaises(TypeError):
            stacker.process_expression(expr)
