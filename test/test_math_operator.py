import unittest

from stacker.stacker import Stacker
import math
import cmath


class TestUnit(unittest.TestCase):
    def setUp(self):
        self.stacker = Stacker()

    # Power (^)
    def test_pow_int(self):
        self.stacker.process_expression("2 3 ^")
        self.assertEqual(self.stacker.stack[-1], 8)

    def test_pow_float(self):
        self.stacker.process_expression("2.0 3 ^")
        self.assertEqual(self.stacker.stack[-1], 8.0)

    def test_pow_complex(self):
        self.stacker.process_expression("2j 3 ^")
        self.assertEqual(self.stacker.stack[-1], 2j**3)

    # log
    def test_log_int(self):
        self.stacker.process_expression("4 log")
        self.assertEqual(self.stacker.stack[-1], math.log(4))

    def test_log_float(self):
        self.stacker.process_expression("8.0 log")
        self.assertEqual(self.stacker.stack[-1], math.log(8.0))

    def test_log_complex(self):
        self.stacker.process_expression("8j log")
        self.assertEqual(self.stacker.stack[-1], cmath.log(8j))

    # log2
    def test_log2_int(self):
        self.stacker.process_expression("4 log2")
        self.assertEqual(self.stacker.stack[-1], math.log2(4))

    def test_log2_float(self):
        self.stacker.process_expression("8.0 log2")
        self.assertEqual(self.stacker.stack[-1], math.log2(8.0))

    def test_log2_complex(self):
        self.stacker.process_expression("8j log2")
        self.assertEqual(self.stacker.stack[-1], cmath.log(8j, 2))

    # log10
    def test_log10_int(self):
        self.stacker.process_expression("4 log10")
        self.assertEqual(self.stacker.stack[-1], math.log10(4))

    def test_log10_float(self):
        self.stacker.process_expression("8.0 log10")
        self.assertEqual(self.stacker.stack[-1], math.log10(8.0))

    def test_log10_complex(self):
        self.stacker.process_expression("8j log10")
        self.assertEqual(self.stacker.stack[-1], cmath.log10(8j))

    # exp
    def test_exp_int(self):
        self.stacker.process_expression("3 exp")
        self.assertEqual(self.stacker.stack[-1], math.exp(3))

    def test_exp_float(self):
        self.stacker.process_expression("3.0 exp")
        self.assertEqual(self.stacker.stack[-1], math.exp(3.0))

    def test_exp_complex(self):
        self.stacker.process_expression("3j exp")
        self.assertEqual(self.stacker.stack[-1], cmath.exp(3j))

    # sin
    def test_sin_int(self):
        self.stacker.process_expression("30 sin")
        self.assertEqual(self.stacker.stack[-1], math.sin(30))

    def test_sin_float(self):
        self.stacker.process_expression("30.0 sin")
        self.assertEqual(self.stacker.stack[-1], math.sin(30.0))

    def test_sin_complex(self):
        self.stacker.process_expression("30j sin")
        self.assertEqual(self.stacker.stack[-1], cmath.sin(30j))

    # cos
    def test_cos_int(self):
        self.stacker.process_expression("45 cos")
        self.assertEqual(self.stacker.stack[-1], math.cos(45))

    def test_cos_float(self):
        self.stacker.process_expression("45.0 cos")
        self.assertEqual(self.stacker.stack[-1], math.cos(45.0))

    def test_cos_complex(self):
        self.stacker.process_expression("45j cos")
        self.assertEqual(self.stacker.stack[-1], cmath.cos(45j))

    # tan
    def test_tan_int(self):
        self.stacker.process_expression("60 tan")
        self.assertEqual(self.stacker.stack[-1], math.tan(60))

    def test_tan_float(self):
        self.stacker.process_expression("60.0 tan")
        self.assertEqual(self.stacker.stack[-1], math.tan(60.0))

    def test_tan_complex(self):
        self.stacker.process_expression("60j tan")
        self.assertEqual(self.stacker.stack[-1], cmath.tan(60j))

    # asin
    def test_asin_int(self):
        self.stacker.process_expression("0 asin")
        self.assertEqual(self.stacker.stack[-1], math.asin(0))

    def test_asin_float(self):
        self.stacker.process_expression("0.5 asin")
        self.assertEqual(self.stacker.stack[-1], math.asin(0.5))

    def test_asin_complex(self):
        self.stacker.process_expression("0.5j asin")
        self.assertEqual(self.stacker.stack[-1], cmath.asin(0.5j))

    # acos
    def test_acos_int(self):
        self.stacker.process_expression("0 acos")
        self.assertEqual(self.stacker.stack[-1], math.acos(0))

    def test_acos_float(self):
        self.stacker.process_expression("0.5 acos")
        self.assertEqual(self.stacker.stack[-1], math.acos(0.5))

    def test_acos_complex(self):
        self.stacker.process_expression("0.5j acos")
        self.assertEqual(self.stacker.stack[-1], cmath.acos(0.5j))

    # atan
    def test_atan_int(self):
        self.stacker.process_expression("0 atan")
        self.assertEqual(self.stacker.stack[-1], math.atan(0))

    def test_atan_float(self):
        self.stacker.process_expression("0.5 atan")
        self.assertEqual(self.stacker.stack[-1], math.atan(0.5))

    def test_atan_complex(self):
        self.stacker.process_expression("0.5j atan")
        self.assertEqual(self.stacker.stack[-1], cmath.atan(0.5j))

    # sinh
    def test_sinh_int(self):
        self.stacker.process_expression("0 sinh")
        self.assertEqual(self.stacker.stack[-1], math.sinh(0))

    def test_sinh_float(self):
        self.stacker.process_expression("0.5 sinh")
        self.assertEqual(self.stacker.stack[-1], math.sinh(0.5))

    def test_sinh_complex(self):
        self.stacker.process_expression("0.5j sinh")
        self.assertEqual(self.stacker.stack[-1], cmath.sinh(0.5j))

    # cosh
    def test_cosh_int(self):
        self.stacker.process_expression("0 cosh")
        self.assertEqual(self.stacker.stack[-1], math.cosh(0))

    def test_cosh_float(self):
        self.stacker.process_expression("0.5 cosh")
        self.assertEqual(self.stacker.stack[-1], math.cosh(0.5))

    def test_cosh_complex(self):
        self.stacker.process_expression("0.5j cosh")
        self.assertEqual(self.stacker.stack[-1], cmath.cosh(0.5j))

    # tanh
    def test_tanh_int(self):
        self.stacker.process_expression("0 tanh")
        self.assertEqual(self.stacker.stack[-1], math.tanh(0))

    def test_tanh_float(self):
        self.stacker.process_expression("0.5 tanh")
        self.assertEqual(self.stacker.stack[-1], math.tanh(0.5))

    def test_tanh_complex(self):
        self.stacker.process_expression("0.5j tanh")
        self.assertEqual(self.stacker.stack[-1], cmath.tanh(0.5j))

    # asinh
    def test_asinh_int(self):
        self.stacker.process_expression("0 asinh")
        self.assertEqual(self.stacker.stack[-1], math.asinh(0))

    def test_asinh_float(self):
        self.stacker.process_expression("0.5 asinh")
        self.assertEqual(self.stacker.stack[-1], math.asinh(0.5))

    def test_asinh_complex(self):
        self.stacker.process_expression("0.5j asinh")
        self.assertEqual(self.stacker.stack[-1], cmath.asinh(0.5j))

    # acosh
    def test_acosh_int(self):
        self.stacker.process_expression("1 acosh")
        self.assertEqual(self.stacker.stack[-1], math.acosh(1))

    def test_acosh_float(self):
        self.stacker.process_expression("1.5 acosh")
        self.assertEqual(self.stacker.stack[-1], math.acosh(1.5))

    def test_acosh_complex(self):
        self.stacker.process_expression("1.5j acosh")
        self.assertEqual(self.stacker.stack[-1], cmath.acosh(1.5j))

    # atanh
    def test_atanh_int(self):
        self.stacker.process_expression("0 atanh")
        self.assertEqual(self.stacker.stack[-1], math.atanh(0))

    def test_atanh_float(self):
        self.stacker.process_expression("0.5 atanh")
        self.assertEqual(self.stacker.stack[-1], math.atanh(0.5))

    def test_atanh_complex(self):
        self.stacker.process_expression("0.5j atanh")
        self.assertEqual(self.stacker.stack[-1], cmath.atanh(0.5j))

    # sqrt
    def test_sqrt_int(self):
        self.stacker.process_expression("9 sqrt")
        self.assertEqual(self.stacker.stack[-1], math.sqrt(9))

    def test_sqrt_float(self):
        self.stacker.process_expression("9.0 sqrt")
        self.assertEqual(self.stacker.stack[-1], math.sqrt(9.0))

    def test_sqrt_complex(self):
        self.stacker.process_expression("9j sqrt")
        self.assertEqual(self.stacker.stack[-1], cmath.sqrt(9j))

    # gcd
    def test_gcd(self):
        self.stacker.process_expression("4 2 gcd")
        self.assertEqual(self.stacker.stack[-1], math.gcd(4, 2))

    # lcm
    def test_lcm(self):
        self.stacker.process_expression("4 2 lcm")
        self.assertEqual(self.stacker.stack[-1], math.lcm(4, 2))

    # radians
    def test_radians(self):
        self.stacker.process_expression("30 radians")
        self.assertEqual(self.stacker.stack[-1], math.radians(30))

    # factorial
    def test_factorial(self):
        self.stacker.process_expression("4 !")
        self.assertEqual(self.stacker.stack[-1], math.factorial(4))

    # ceil
    def test_ceil(self):
        self.stacker.process_expression("3.2 ceil")
        self.assertEqual(self.stacker.stack[-1], math.ceil(3.2))

    # floor
    def test_floor(self):
        self.stacker.process_expression("3.8 floor")
        self.assertEqual(self.stacker.stack[-1], math.floor(3.8))

    # roundn
    def test_roundn(self):
        self.stacker.process_expression("3.51 1 roundn")
        self.assertEqual(self.stacker.stack[-1], round(3.51, 1))

    # round
    def test_round(self):
        self.stacker.process_expression("3.5 round")
        self.assertEqual(self.stacker.stack[-1], round(3.5))
