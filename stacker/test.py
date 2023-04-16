import unittest

from stacker import RPNCalculator


class TestRPNCalculator(unittest.TestCase):
    def setUp(self):
        self.calculator = RPNCalculator()

    def test_arithmetic_operations(self):
        test_cases = [
            ("3 4 +", 7),
            ("5 2 -", 3),
            ("3 4 *", 12),
            ("10 2 /", 5),
            ("10 3 %", 1),
            ("3 4 ^", 81),
            ("10 -5 abs +", 15)
        ]

        for expression, expected_result in test_cases:
            self.assertEqual(self.calculator.evaluate(expression), expected_result)

    def test_function_definition(self):
        self.calculator.process_expression("x = 5")
        self.calculator.process_expression("x f => x 2 +")
        self.assertEqual(self.calculator.evaluate("x f"), 7)

        self.calculator.process_expression("x = 10")
        self.calculator.process_expression("x g => x 3 *")
        self.assertEqual(self.calculator.evaluate("x g"), 30)


if __name__ == "__main__":
    unittest.main()
