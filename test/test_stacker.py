import cmath
import math
import unittest

from stacker.stacker import Stacker

from stacker.syntax.lexer import lex_string
from stacker.engine.data_type import String


def cpow(x1, x2):
    return cmath.exp(x2 * cmath.log(x1))


class TestUnit(unittest.TestCase):
    def setUp(self):
        self.stacker = Stacker()

    def test_lex_string(self):
        expr = "1 2 3 [4 5 6] 7 8 (9 10 11) a1 b1 c1 {1 2 +} '1+1' eval"
        exprs = [
            "1",
            "2",
            "3",
            "[4 5 6]",
            "7",
            "8",
            "(9 10 11)",
            "a1",
            "b1",
            "c1",
            "{1 2 +}",
            "'1+1'",
            "eval",
        ]
        result = lex_string(expr)
        self.assertEqual(result, exprs)

    def test_lex_string_2(self):
        expr = "'1+1' eval"
        exprs = ["'1+1'", "eval"]
        result = lex_string(expr)
        print(result)
        self.assertEqual(result, exprs)


class TestStacker(unittest.TestCase):
    def setUp(self):
        self.stacker = Stacker()

    def test_operations(self):
        test_cases = [
            ("2 3 +", 5),
            ("10 3 -", 7),
            ("4 6 *", 24),
            ("12 4 /", 3),
            ("7 2 //", 3),
            ("9 2 %", 1),
            ("5 neg", -5),
            ("3 neg abs", 3),
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
            ("8 2 >>", 2),
            ("2 2 <<", 8),
            ("5 ~", -6),
            ("5 bin", "0b101"),
            ("10 oct", "0o12"),
            ("0b101010 dec", 42),
            ("255 hex", "0xff"),
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
            ("(1+2j) (2+3j) +", complex(1, 2) + complex(2, 3)),
            ("(1+2j) (2+3j) -", complex(1, 2) - complex(2, 3)),
            ("(1+2j) (2+3j) *", complex(1, 2) * complex(2, 3)),
            ("(1+2j) (2+3j) /", complex(1, 2) / complex(2, 3)),
            ("(1+2j) 2 ^", complex(1, 2) ** 2),
            ("(1+2j) exp", cmath.exp(complex(1, 2))),
            ("(1+2j) log", cmath.log(complex(1, 2))),
            ("(1+2j) sin", cmath.sin(complex(1, 2))),
            ("(1+2j) cos", cmath.cos(complex(1, 2))),
            ("(1+2j) tan", cmath.tan(complex(1, 2))),
            ("(1+2j) sqrt", cmath.sqrt(complex(1, 2))),
            ("(1+2j) sinh", cmath.sinh(complex(1, 2))),
            ("(1+2j) cosh", cmath.cosh(complex(1, 2))),
            ("(1+2j) tanh", cmath.tanh(complex(1, 2))),
            ("(1+2j) asin", cmath.asin(complex(1, 2))),
            ("(1+2j) acos", cmath.acos(complex(1, 2))),
            ("(1+2j) atan", cmath.atan(complex(1, 2))),
            ("(1+2j) asinh", cmath.asinh(complex(1, 2))),
            ("(1+2j) acosh", cmath.acosh(complex(1, 2))),
            ("(1+2j) atanh", cmath.atanh(complex(1, 2))),
            ("4 2 lcm", math.lcm(4, 2)),
            ("27 cbrt", 27 ** (1 / 3)),
            ("5 2 ncr", math.comb(5, 2)),
            ("5 2 npr", math.perm(5, 2)),
        ]

        for expression, expected in test_cases:
            self.stacker.stack.clear()
            try:
                self.stacker.process_expression(expression)
            except Exception:
                print("error!!", expression)
                assert False
            try:
                self.assertEqual(self.stacker.stack[-1], expected)
            except Exception:
                print("error!!", expression)
                assert False
        for expression, expected in test_cases:
            self.stacker.stack.clear()
            self.stacker.process_expression(expression)
            self.assertAlmostEqual(self.stacker.stack[-1], expected)

    def test_long_rpn(self):
        self.stacker.stack.clear()
        expression = " 8 3 5 * 2 / + 7 4 + neg 2 ^ 1 3 + * -"
        self.stacker.process_expression(expression)
        self.assertEqual(self.stacker.stack[-1], -468.5)

    def test_stack_operations(self):
        # Test 'copy' operation
        # self.stacker.stack.clear()
        # self.stacker.process_expression("1 2 3 4 5")
        # self.stacker.process_expression("1 copy")
        # self.assertEqual(self.stacker.stack, [1, 2, 3, 4, 5, 2])

        # Test 'pop' operation
        self.stacker.stack.clear()
        self.stacker.process_expression("1 2 3 4 5")
        self.stacker.process_expression("drop")
        self.assertEqual(list(self.stacker.stack), [1, 2, 3, 4])

        # Test 'dup' operation
        self.stacker.stack.clear()
        self.stacker.process_expression("1 2 3 4 5")
        self.stacker.process_expression("dup")
        self.assertEqual(list(self.stacker.stack), [1, 2, 3, 4, 5, 5])

        # Test 'rev' operation
        self.stacker.stack.clear()
        self.stacker.process_expression("1 2 3 4 5")
        self.assertEqual(list(self.stacker.stack), [1, 2, 3, 4, 5])
        self.stacker.process_expression("rev")
        self.assertEqual(list(self.stacker.stack), [5, 4, 3, 2, 1])

    def test_variable_assignment(self):
        self.stacker.stack.clear()
        self.stacker.process_expression("5 $a set")
        self.assertEqual(self.stacker.variables["a"], 5)

    def test_function_definition_and_call(self):
        self.stacker.stack.clear()
        self.stacker.process_expression("{x} {x x *} $f defun")
        self.stacker.process_expression("4 f")
        self.assertEqual(self.stacker.stack[-1], 16)

    def test_input(self):
        # int
        self.stacker.process_expression("5")
        self.assertEqual(self.stacker.stack[-1], 5)
        self.assertEqual(type(self.stacker.stack[-1]), int)

        # float
        self.stacker.process_expression("5.0")
        self.assertEqual(self.stacker.stack[-1], 5.0)
        self.assertEqual(type(self.stacker.stack[-1]), float)

        self.stacker.process_expression("3.")
        self.assertEqual(self.stacker.stack[-1], 3.0)
        self.assertEqual(type(self.stacker.stack[-1]), float)

        # str
        self.stacker.process_expression("'hoge'")
        self.assertEqual(self.stacker.stack[-1], "hoge")
        self.assertEqual(type(self.stacker.stack[-1]), String)

        # REMOVED: tuple test - () now creates code blocks, not tuples

        # list
        self.stacker.process_expression("[1 2 3]")
        self.assertEqual(self.stacker.stack[-1], [1, 2, 3])
        self.assertEqual(type(self.stacker.stack[-1]), list)

        # complex
        self.stacker.process_expression("4j")
        self.assertEqual(self.stacker.stack[-1], complex(4j))
        self.assertEqual(type(self.stacker.stack[-1]), complex)

        ...

    def test_list_input(self):
        # # Standard list input
        # self.stacker.process_expression("[1, 2, 3]")
        # self.assertEqual(self.stacker.stack[-1], [1, 2, 3])

        # self.stacker.process_expression(
        #     "[1, 2, 3], [4, 5, 6], [7, 8, 9], [10, 11, 12]"
        # )
        # self.assertEqual(self.stacker.stack[-1], [10, 11, 12])
        # self.assertEqual(self.stacker.stack[-2], [7, 8, 9])
        # self.assertEqual(self.stacker.stack[-3], [4, 5, 6])
        # self.assertEqual(self.stacker.stack[-4], [1, 2, 3])

        # self.stacker.process_expression(
        #     "[[1, 2, 3], [4, 5, 6], [7, 8, 9], [10, 11, 12]]"
        # )
        # self.assertEqual(self.stacker.stack[-1], [[1, 2, 3], [4, 5, 6], [7, 8, 9], [10, 11, 12]])

        self.stacker.process_expression("[1 2 3]")
        self.assertEqual(self.stacker.stack[-1], [1, 2, 3])

        self.stacker.process_expression("[1 2 3] 4")
        self.assertEqual(self.stacker.stack[-1], 4)
        self.assertEqual(self.stacker.stack[-2], [1, 2, 3])

        # Custom format list input with float
        self.stacker.process_expression("[1.0 2.0 3.0]")
        self.assertEqual(self.stacker.stack[-1], [1.0, 2.0, 3.0])

        # Multiline input
        self.stacker.process_expression("[1 2 3 ; 4 5 6]")
        self.assertEqual(self.stacker.stack[-1], [[1, 2, 3], [4, 5, 6]])

        self.stacker.process_expression("[1 2 3; 4 5 6; 7 8 9]")
        self.assertEqual(self.stacker.stack[-1], [[1, 2, 3], [4, 5, 6], [7, 8, 9]])

        self.stacker.process_expression("[1 2 3; 4 5 6; 7 8 9] 5 6")
        self.assertEqual(self.stacker.stack[-1], 6)
        self.assertEqual(self.stacker.stack[-2], 5)
        self.assertEqual(self.stacker.stack[-3], [[1, 2, 3], [4, 5, 6], [7, 8, 9]])

    # REMOVED: test_tuple_input - () now creates code blocks, not tuples
    # All tuple-related assertions removed

    # REMOVED: Tuple multiline input tests
    # Tuples no longer exist - () now creates code blocks identical to {}
    # Use lists [] for data structures instead

    # valiable
    def test_variable_assign_1(self):
        self.stacker.stack.clear()
        self.stacker.process_expression("123 $a set")
        self.stacker.process_expression("a")
        self.assertEqual(self.stacker.pop_and_eval(self.stacker.stack), 123)

    def test_variable_assign_2(self):
        self.stacker.stack.clear()
        self.stacker.process_expression("{30 50 +} $b set")
        self.stacker.process_expression("b")
        # self.stacker.process_expression("pop")
        self.assertEqual(self.stacker.pop_and_eval(self.stacker.stack), 80)

    # blockstack
    def test_blockstack(self):
        self.stacker.stack.clear()
        self.stacker.process_expression("1 {3 {4 5 +} *} +")
        self.assertEqual(self.stacker.stack[-1], 28)

    # eval
    def test_eval_str(self):
        self.stacker.stack.clear()
        self.stacker.process_expression("'3 5 +' eval")
        self.assertEqual(self.stacker.stack[-1], 8)

        self.stacker.stack.clear()
        self.stacker.process_expression("5 eval")
        self.assertEqual(self.stacker.stack[-1], 5)

    def test_eval_block(self):
        self.stacker.stack.clear()
        self.stacker.process_expression("{3 5 +} eval")
        self.assertEqual(self.stacker.stack[-1], 8)

        self.stacker.stack.clear()
        self.stacker.process_expression("{3 5} {*} eval")
        self.assertEqual(self.stacker.stack[-1], 15)

    def test_eval_list(self):
        self.stacker.stack.clear()
        self.stacker.process_expression("'[3 5 6]' eval")
        self.assertEqual(self.stacker.stack[-1], [3, 5, 6])

    # REMOVED: test_eval_tuple - () now creates code blocks, not tuples

    def test_eval_variable(self):
        self.stacker.stack.clear()
        self.stacker.process_expression("5 $a set")
        self.stacker.process_expression("a eval")
        self.assertEqual(self.stacker.stack[-1], 5)


if __name__ == "__main__":
    unittest.main()
