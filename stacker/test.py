import cmath
import math
import unittest

from stacker import Stacker


def cpow(x1, x2):
    return cmath.exp(x2 * cmath.log(x1))


class TestStacker(unittest.TestCase):
    def setUp(self):
        self.stacker = Stacker()

    def test_arithmetic_operations(self):
        test_cases = [
            ("2 3 +", 5),
            ("10 3 -", 7),
            ("4 6 *", 24),
            ("12 4 /", 3),
            ("7 2 //", 3),
            ("9 2 %", 1),
            ("5 neg", -5),
            ("-3 abs", 3),
            ("3 2 ^", 9),
            ("3 exp", math.exp(3)),
            ("2 log", math.log(2)),
            ("30 radians sin", math.sin(math.radians(30))),
            ("45 radians cos", math.cos(math.radians(45))),
            ("60 radians tan", math.tan(math.radians(60))),
            ("5 float", 5.0),
            ("3.14 int", 3),
            ("1 1 ==", True),
            ("1 0 !=", True),
            ("1 2 <", True),
            ("3 3 <=", True),
            ("2 1 >", True),
            ("3 3 >=", True),
            ("true false and", False),
            ("true false or", True),
            ("true not", False),
            ("3 2 band", 3 & 2),
            ("3 2 bor", 3 | 2),
            ("3 2 bxor", 3 ^ 2),
            ("4 2 gcd", math.gcd(4, 2)),
            ("4 log10", math.log10(4)),
            ("4 log2", math.log2(4)),
            ("4 !", math.factorial(4)),
            ("9 sqrt", math.sqrt(9)),
            ("3.2 ceil", math.ceil(3.2)),
            ("3.8 floor", math.floor(3.8)),
            ("3.5 round", round(3.5)),
            ("3.51 1 roundn", round(3.51, 1)),
            # Add complex number test cases
            ("1+2j 2+3j +", complex(1, 2) + complex(2, 3)),
            ("1+2j 2+3j -", complex(1, 2) - complex(2, 3)),
            ("1+2j 2+3j *", complex(1, 2) * complex(2, 3)),
            ("1+2j 2+3j /", complex(1, 2) / complex(2, 3)),
            ("1+2j 2 ^", cpow(complex(1, 2), 2)),
            ("1+2j exp", cmath.exp(complex(1, 2))),
            ("1+2j log", cmath.log(complex(1, 2))),
            ("1+2j sin", cmath.sin(complex(1, 2))),
            ("1+2j cos", cmath.cos(complex(1, 2))),
            ("1+2j tan", cmath.tan(complex(1, 2))),
            ("1+2j sqrt", cmath.sqrt(complex(1, 2))),
            ("1+2j sinh", cmath.sinh(complex(1, 2))),
            ("1+2j cosh", cmath.cosh(complex(1, 2))),
            ("1+2j tanh", cmath.tanh(complex(1, 2))),
            ("1+2j asin", cmath.asin(complex(1, 2))),
            ("1+2j acos", cmath.acos(complex(1, 2))),
            ("1+2j atan", cmath.atan(complex(1, 2))),
            ("1+2j asinh", cmath.asinh(complex(1, 2))),
            ("1+2j acosh", cmath.acosh(complex(1, 2))),
            ("1+2j atanh", cmath.atanh(complex(1, 2))),
        ]

        for expression, expected in test_cases:
            self.stacker.stack.clear()
            self.stacker.process_expression(expression)
            self.assertEqual(self.stacker.stack[-1], expected)

        # for expression, expected in test_cases:
        #     self.stacker.stack.clear()
        #     self.stacker.process_expression(expression)
        #     self.assertAlmostEqual(self.stacker.stack[-1], expected)
        print("!")

    def test_variable_assignment(self):
        self.stacker.stack.clear()
        self.stacker.process_expression("a = 5")
        self.assertEqual(self.stacker.variables["a"], 5)

    def test_function_definition_and_call(self):
        self.stacker.stack.clear()
        self.stacker.process_expression("x square => x x *")
        self.stacker.process_expression("4 square")
        self.assertEqual(self.stacker.stack[-1], 16)


if __name__ == "__main__":
    unittest.main()
