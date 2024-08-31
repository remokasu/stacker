import unittest

import numpy as np

from stacker.plugins import matrix
from stacker.stacker import Stacker


class TestMatrixOperationsPlugin(unittest.TestCase):
    def setUp(self):
        self.stacker = Stacker()
        matrix.setup(self.stacker)

    # ================================
    # +
    # ================================
    def test_matrix_add(self):
        expression = "[1 2; 3 4] [5 6; 7 8] +"
        self.stacker.stack.clear()
        self.stacker.process_expression(expression)
        # expected_result = (a + b).tolist()
        expected_result = [[6, 8], [10, 12]]
        self.assertEqual(self.stacker.stack[-1], expected_result)
        print("\n")
        print(f"expression: {expression}")
        print(f"result: {self.stacker.stack[-1]}")

    def test_scalar_add(self):
        expression = "1 2 +"
        self.stacker.stack.clear()
        self.stacker.process_expression(expression)
        expected_result = 3
        self.assertEqual(self.stacker.stack[-1], expected_result)

    # ================================
    # -
    # ================================
    def test_matrix_sub(self):
        expression = "[1 2; 3 4] [5 6; 7 8] -"
        self.stacker.stack.clear()
        self.stacker.process_expression(expression)
        # expected_result = (a - b).tolist()
        expected_result = [[-4, -4], [-4, -4]]
        self.assertEqual(self.stacker.stack[-1], expected_result)

    def test_scalar_sub(self):
        expression = "1 2 -"
        self.stacker.stack.clear()
        self.stacker.process_expression(expression)
        expected_result = -1
        self.assertEqual(self.stacker.stack[-1], expected_result)

    # ================================
    # *
    # ================================
    def test_matrix_mul(self):
        expression = "[1 2; 3 4] [5 6; 7 8] *"
        self.stacker.stack.clear()
        self.stacker.process_expression(expression)
        # expected_result = (np.dot(a, b)).tolist()
        expected_result = [[19, 22], [43, 50]]
        self.assertEqual(self.stacker.stack[-1], expected_result)
        print("\n")
        print(f"expression: {expression}")
        print(f"result: {self.stacker.stack[-1]}")

    def test_scalar_mul(self):
        expression = "4 2 *"
        self.stacker.stack.clear()
        self.stacker.process_expression(expression)
        expected_result = 8
        self.assertEqual(self.stacker.stack[-1], expected_result)

    # ================================
    # .*
    # ================================
    def test_elementwise_mul(self):
        expression = "[1 2; 3 4] [5 6; 7 8] .*"
        self.stacker.stack.clear()
        self.stacker.process_expression(expression)
        # expected_result = np.multiply(a, b).tolist()
        expected_result = [[5, 12], [21, 32]]
        self.assertEqual(self.stacker.stack[-1], expected_result)
        print("\n")
        print(f"expression: {expression}")
        print(f"result: {self.stacker.stack[-1]}")

    def test_scalar_elementwise_mul(self):
        expression = "2 3 .*"
        self.stacker.stack.clear()
        self.stacker.process_expression(expression)
        expected_result = 6
        self.assertEqual(self.stacker.stack[-1], expected_result)

    # ================================
    # /
    # ================================
    def test_matrix_div(self):
        a = [[1, 2], [3, 4]]
        b = [[5, 6], [7, 8]]
        expression = "[1 2; 3 4] [5 6; 7 8] /"
        self.stacker.stack.clear()
        self.stacker.process_expression(expression)
        # expected_result = np.divide(a, b).tolist()
        result = self.stacker.stack[-1]
        expected_result = [[3.0, -2.0], [2.0, -1.0]]

        for sub_list1, sub_list2 in zip(result, expected_result):
            for a, b in zip(sub_list1, sub_list2):
                self.assertAlmostEqual(a, b, places=5)

        # self.assertEqual(self.stacker.stack[-1], expected_result)
        print("\n")
        print(f"expression: {expression}")
        print(f"result: {self.stacker.stack[-1]}")

    def test_scalar_div(self):
        expression = "4 2 /"
        self.stacker.stack.clear()
        self.stacker.process_expression(expression)
        expected_result = 2
        self.assertEqual(self.stacker.stack[-1], expected_result)

    # ================================
    # ./
    # ================================
    def test_elementwise_div(self):
        a = [[1, 2], [3, 4]]
        b = [[5, 6], [7, 8]]
        expression = "[1 2; 3 4] [5 6; 7 8] ./"
        self.stacker.stack.clear()
        self.stacker.process_expression(expression)
        result = self.stacker.stack[-1]
        expected_result = [[0.2000, 0.3333], [0.4286, 0.5000]]

        for sub_list1, sub_list2 in zip(result, expected_result):
            for a, b in zip(sub_list1, sub_list2):
                self.assertAlmostEqual(a, b, delta=1e-4)

        print("\n")
        print(f"expression: {expression}")
        print(f"result: {self.stacker.stack[-1]}")

    def test_scalar_elementwise_div(self):
        expression = "4 2 ./"
        self.stacker.stack.clear()
        self.stacker.process_expression(expression)
        expected_result = 2
        self.assertEqual(self.stacker.stack[-1], expected_result)

    # def test_elementwise_div_inv(self):
    #     a = [[1, 2], [3, 4]]
    #     b = [[5, 6], [7, 8]]
    #     expression = "[1 2; 3 4] [5 6; 7 8] .\\"
    #     self.stacker.stack.clear()
    #     self.stacker.process_expression(expression)
    #     expected_result = np.divide(b, a).tolist()
    #     self.assertEqual(self.stacker.stack[-1], expected_result)
    #     print("\n")
    #     print(f"expression: {expression}")
    #     print(f"result: {self.stacker.stack[-1]}")

    # ================================
    # ^
    # ================================
    def test_matrix_power(self):
        expression = "[1 2; 3 4] 3 ^"
        self.stacker.stack.clear()
        self.stacker.process_expression(expression)
        self.stacker.process_expression(expression)
        result = self.stacker.stack[-1]
        expected_result = [[37, 54], [81, 118]]
        self.assertEqual(result, expected_result)

    def test_scalar_power(self):
        expression = "2 3 ^"
        self.stacker.stack.clear()
        self.stacker.process_expression(expression)
        result = self.stacker.stack[-1]
        expected_result = 8
        self.assertEqual(result, expected_result)

    # ================================
    # .^
    # ================================
    def test_elementwise_power(self):
        expression = "[1 2; 3 4] 3 .^"
        self.stacker.stack.clear()
        self.stacker.process_expression(expression)
        result = self.stacker.stack[-1]
        expected_result = [[1, 8], [27, 64]]
        self.assertEqual(result, expected_result)
        print("\n")
        print(f"expression: {expression}")
        print(f"result: {self.stacker.stack[-1]}")

    def test_scalar_elementwise_power(self):
        expression = "2 3 .^"
        self.stacker.stack.clear()
        self.stacker.process_expression(expression)
        result = self.stacker.stack[-1]
        expected_result = 8
        self.assertEqual(result, expected_result)

    def test_matrix_transpose(self):
        a = [[1, 2], [3, 4]]
        expression = "[1 2; 3 4] '"
        self.stacker.stack.clear()
        self.stacker.process_expression(expression)
        expected_result = np.transpose(a).tolist()
        self.assertEqual(self.stacker.stack[-1], expected_result)
        print("\n")
        print(f"expression: {expression}")
        print(f"result: {self.stacker.stack[-1]}")

    def test_matrix_inverse(self):
        a = [[1, 2], [3, 4]]
        expression = "[1 2; 3 4] inv"
        self.stacker.stack.clear()
        self.stacker.process_expression(expression)
        expected_result = np.linalg.inv(a).tolist()
        self.assertEqual(self.stacker.stack[-1], expected_result)
        print("\n")
        print(f"expression: {expression}")
        print(f"result: {self.stacker.stack[-1]}")

    def test_matrix_determinant(self):
        a = [[1, 2], [3, 4]]
        expression = "[1 2; 3 4] det"
        self.stacker.stack.clear()
        self.stacker.process_expression(expression)
        expected_result = np.linalg.det(a)
        self.assertEqual(self.stacker.stack[-1], expected_result)
        print("\n")
        print(f"expression: {expression}")
        print(f"result: {self.stacker.stack[-1]}")

    def test_matrix_rank(self):
        a = [[1, 2], [3, 4]]
        expression = "[1 2; 3 4] rank"
        self.stacker.stack.clear()
        self.stacker.process_expression(expression)
        expected_result = np.linalg.matrix_rank(a)
        self.assertEqual(self.stacker.stack[-1], expected_result)
        print("\n")
        print(f"expression: {expression}")
        print(f"result: {self.stacker.stack[-1]}")

    def test_matrix_trace(self):
        a = [[1, 2], [3, 4]]
        expression = "[1 2; 3 4] trace"
        self.stacker.stack.clear()
        self.stacker.process_expression(expression)
        expected_result = np.trace(a).tolist()
        self.assertEqual(self.stacker.stack[-1], expected_result)
        print("\n")
        print(f"expression: {expression}")
        print(f"result: {self.stacker.stack[-1]}")


if __name__ == "__main__":
    unittest.main()
