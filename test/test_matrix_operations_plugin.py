import unittest

import numpy as np

from stacker.plugins import matrix
from stacker.stacker import Stacker


class TestMatrixOperationsPlugin(unittest.TestCase):
    def setUp(self):
        self.stacker = Stacker()
        matrix.setup(self.stacker)

    def test_matrix_add(self):
        a = [[1, 2], [3, 4]]
        b = [[5, 6], [7, 8]]
        expression = '[1 2; 3 4] [5 6; 7 8] +'
        self.stacker.stack.clear()
        self.stacker.process_expression(expression)
        expected_result = np.add(a, b).tolist()
        self.assertEqual(self.stacker.stack[-1], expected_result)
        print("\n")
        print(f"expression: {expression}")
        print(f"result: {self.stacker.stack[-1]}")

    def test_matrix_sub(self):
        a = [[1, 2], [3, 4]]
        b = [[5, 6], [7, 8]]
        expression = '[1 2; 3 4] [5 6; 7 8] -'
        self.stacker.stack.clear()
        self.stacker.process_expression(expression)
        expected_result = np.subtract(a, b).tolist()
        self.assertEqual(self.stacker.stack[-1], expected_result)
        print("\n")
        print(f"expression: {expression}")
        print(f"result: {self.stacker.stack[-1]}")

    def test_matrix_mul(self):
        a = [[1, 2], [3, 4]]
        b = [[5, 6], [7, 8]]
        expression = '[1 2; 3 4] [5 6; 7 8] *'
        self.stacker.stack.clear()
        self.stacker.process_expression(expression)
        expected_result = np.matmul(a, b).tolist()
        self.assertEqual(self.stacker.stack[-1], expected_result)
        print("\n")
        print(f"expression: {expression}")
        print(f"result: {self.stacker.stack[-1]}")

    def test_elementwise_mul(self):
        a = [[1, 2], [3, 4]]
        b = [[5, 6], [7, 8]]
        expression = '[1 2; 3 4] [5 6; 7 8] .*'
        self.stacker.stack.clear()
        self.stacker.process_expression(expression)
        expected_result = np.multiply(a, b).tolist()
        self.assertEqual(self.stacker.stack[-1], expected_result)
        print("\n")
        print(f"expression: {expression}")
        print(f"result: {self.stacker.stack[-1]}")

    def test_elementwise_div(self):
        a = [[1, 2], [3, 4]]
        b = [[5, 6], [7, 8]]
        expression = '[1 2; 3 4] [5 6; 7 8] ./'
        self.stacker.stack.clear()
        self.stacker.process_expression(expression)
        expected_result = np.divide(a, b).tolist()
        self.assertEqual(self.stacker.stack[-1], expected_result)
        print("\n")
        print(f"expression: {expression}")
        print(f"result: {self.stacker.stack[-1]}")

    def test_elementwise_div_inv(self):
        a = [[1, 2], [3, 4]]
        b = [[5, 6], [7, 8]]
        expression = '[1 2; 3 4] [5 6; 7 8] .\\'
        self.stacker.stack.clear()
        self.stacker.process_expression(expression)
        expected_result = np.divide(b, a).tolist()
        self.assertEqual(self.stacker.stack[-1], expected_result)
        print("\n")
        print(f"expression: {expression}")
        print(f"result: {self.stacker.stack[-1]}")

    def test_matrix_transpose(self):
        a = [[1, 2], [3, 4]]
        expression = '[1 2; 3 4] \''
        self.stacker.stack.clear()
        self.stacker.process_expression(expression)
        expected_result = np.transpose(a).tolist()
        self.assertEqual(self.stacker.stack[-1], expected_result)
        print("\n")
        print(f"expression: {expression}")
        print(f"result: {self.stacker.stack[-1]}")

    def test_matrix_inverse(self):
        a = [[1, 2], [3, 4]]
        expression = '[1 2; 3 4] inv'
        self.stacker.stack.clear()
        self.stacker.process_expression(expression)
        expected_result = np.linalg.inv(a).tolist()
        self.assertEqual(self.stacker.stack[-1], expected_result)
        print("\n")
        print(f"expression: {expression}")
        print(f"result: {self.stacker.stack[-1]}")

    def test_matrix_determinant(self):
        a = [[1, 2], [3, 4]]
        expression = '[1 2; 3 4] det'
        self.stacker.stack.clear()
        self.stacker.process_expression(expression)
        expected_result = np.linalg.det(a)
        self.assertEqual(self.stacker.stack[-1], expected_result)
        print("\n")
        print(f"expression: {expression}")
        print(f"result: {self.stacker.stack[-1]}")

    def test_matrix_rank(self):
        a = [[1, 2], [3, 4]]
        expression = '[1 2; 3 4] rank'
        self.stacker.stack.clear()
        self.stacker.process_expression(expression)
        expected_result = np.linalg.matrix_rank(a)
        self.assertEqual(self.stacker.stack[-1], expected_result)
        print("\n")
        print(f"expression: {expression}")
        print(f"result: {self.stacker.stack[-1]}")

    def test_matrix_trace(self):
        a = [[1, 2], [3, 4]]
        expression = '[1 2; 3 4] trace'
        self.stacker.stack.clear()
        self.stacker.process_expression(expression)
        expected_result = np.trace(a)
        self.assertEqual(self.stacker.stack[-1], expected_result)
        print("\n")
        print(f"expression: {expression}")
        print(f"result: {self.stacker.stack[-1]}")


if __name__ == '__main__':
    unittest.main()
