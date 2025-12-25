"""Tests for random operators (rand, randint, uniform, dice)."""

import unittest
import random
from stacker.stacker import Stacker


class TestRandomOperators(unittest.TestCase):
    def setUp(self):
        self.stacker = Stacker()
        self.stacker.stack.clear()

    def test_rand_returns_float_between_0_and_1(self):
        """Test rand returns a float between 0 and 1."""
        random.seed(42)
        self.stacker.process_expression("rand")
        result = self.stacker.stack[-1]
        self.assertIsInstance(result, float)
        self.assertGreaterEqual(result, 0.0)
        self.assertLessEqual(result, 1.0)

    def test_rand_multiple_calls(self):
        """Test rand produces different values on multiple calls."""
        self.stacker.process_expression("rand rand")
        val1 = self.stacker.stack[-2]
        val2 = self.stacker.stack[-1]
        # Very unlikely to be equal (but theoretically possible)
        self.assertIsInstance(val1, float)
        self.assertIsInstance(val2, float)

    def test_randint_basic(self):
        """Test randint with basic range."""
        random.seed(42)
        self.stacker.process_expression("1 10 randint")
        result = self.stacker.stack[-1]
        self.assertIsInstance(result, int)
        self.assertGreaterEqual(result, 1)
        self.assertLessEqual(result, 10)

    def test_randint_same_values(self):
        """Test randint with same min and max."""
        self.stacker.process_expression("5 5 randint")
        result = self.stacker.stack[-1]
        self.assertEqual(result, 5)

    def test_randint_negative_range(self):
        """Test randint with negative range."""
        random.seed(42)
        self.stacker.process_expression("-10 -1 randint")
        result = self.stacker.stack[-1]
        self.assertIsInstance(result, int)
        self.assertGreaterEqual(result, -10)
        self.assertLessEqual(result, -1)

    def test_uniform_basic(self):
        """Test uniform with basic range."""
        random.seed(42)
        self.stacker.process_expression("0.0 1.0 uniform")
        result = self.stacker.stack[-1]
        self.assertIsInstance(result, float)
        self.assertGreaterEqual(result, 0.0)
        self.assertLessEqual(result, 1.0)

    def test_uniform_larger_range(self):
        """Test uniform with larger range."""
        random.seed(42)
        self.stacker.process_expression("10.5 20.5 uniform")
        result = self.stacker.stack[-1]
        self.assertIsInstance(result, float)
        self.assertGreaterEqual(result, 10.5)
        self.assertLessEqual(result, 20.5)

    def test_uniform_negative_range(self):
        """Test uniform with negative range."""
        random.seed(42)
        self.stacker.process_expression("-5.0 -1.0 uniform")
        result = self.stacker.stack[-1]
        self.assertIsInstance(result, float)
        self.assertGreaterEqual(result, -5.0)
        self.assertLessEqual(result, -1.0)

    def test_dice_1d6(self):
        """Test rolling 1 six-sided die."""
        random.seed(42)
        self.stacker.process_expression("1 6 dice")
        result = self.stacker.stack[-1]
        self.assertIsInstance(result, int)
        self.assertGreaterEqual(result, 1)
        self.assertLessEqual(result, 6)

    def test_dice_3d6(self):
        """Test rolling 3 six-sided dice."""
        random.seed(42)
        self.stacker.process_expression("3 6 dice")
        result = self.stacker.stack[-1]
        self.assertIsInstance(result, int)
        self.assertGreaterEqual(result, 3)  # minimum: 1+1+1
        self.assertLessEqual(result, 18)  # maximum: 6+6+6

    def test_dice_2d20(self):
        """Test rolling 2 twenty-sided dice."""
        random.seed(42)
        self.stacker.process_expression("2 20 dice")
        result = self.stacker.stack[-1]
        self.assertIsInstance(result, int)
        self.assertGreaterEqual(result, 2)  # minimum: 1+1
        self.assertLessEqual(result, 40)  # maximum: 20+20

    def test_dice_deterministic(self):
        """Test dice with seed produces consistent results."""
        random.seed(12345)
        self.stacker.process_expression("3 6 dice")
        result1 = self.stacker.stack[-1]

        self.stacker.stack.clear()
        random.seed(12345)
        self.stacker.process_expression("3 6 dice")
        result2 = self.stacker.stack[-1]

        self.assertEqual(result1, result2)


if __name__ == "__main__":
    unittest.main()
