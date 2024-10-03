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

    def test_split_space(self):
        stacker = Stacker()
        expr = """'a b c' ' ' split"""
        stacker.process_expression(expr)
        self.assertEqual(list(stacker.stack), ["a", "b", "c"])

    def test_split_comma(self):
        stacker = Stacker()
        expr = """'a,b,c' ',' split"""
        stacker.process_expression(expr)
        self.assertEqual(list(stacker.stack), ["a", "b", "c"])

    def test_nth_list(self):
        stacker = Stacker()
        expr = "[1 2 3] 1 nth"
        stacker.process_expression(expr)
        self.assertEqual(list(stacker.stack), [[1, 2, 3], 2])

    def test_nth_tuple(self):
        stacker = Stacker()
        expr = "(1 2 3) 1 nth"
        stacker.process_expression(expr)
        self.assertEqual(list(stacker.stack), [(1, 2, 3), 2])

    def test_nth_string(self):
        stacker = Stacker()
        expr = "'abc' 1 nth"
        stacker.process_expression(expr)
        self.assertEqual(list(stacker.stack), ["abc", "b"])

    def test_read_from_string(self):
        stacker = Stacker()
        expr = "'3 4 +' read-from-string"
        stacker.process_expression(expr)
        self.assertEqual(stacker.stack[-1].tokens, [3, 4, "+"])

    def test_sub(self):
        stacker = Stacker()
        expr = "5 sub"
        stacker.process_expression(expr)
        self.assertEqual(stacker.stack[-1].tokens, [5])

    def test_subn(self):
        stacker = Stacker()
        expr = "1 2 3 3 subn"
        stacker.process_expression(expr)
        self.assertEqual(stacker.stack[-1].tokens, [1, 2, 3])
