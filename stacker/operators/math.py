from __future__ import annotations

import math
import cmath
from typing import Callable
from fractions import Fraction


def _pow(x1: int | float | complex, x2: int | float | complex) -> int | float | complex:
    return x1**x2


def _log(x: int | float | complex) -> float | complex:
    if type(x) is complex:
        return cmath.log(x)
    else:
        return math.log(x)


def _log2(x: int | float | complex) -> float | complex:
    if type(x) is complex:
        return cmath.log(x, 2)
    else:
        return math.log(x, 2)


def _log10(x: int | float | complex) -> float | complex:
    if type(x) is complex:
        return cmath.log(x, 10)
    else:
        return math.log10(x)


def _exp(x: int | float | complex) -> float | complex:
    if type(x) is complex:
        return cmath.exp(x)
    else:
        return math.exp(x)


def _sin(x: int | float | complex) -> float | complex:
    if type(x) is complex:
        return cmath.sin(x)
    else:
        return math.sin(x)


def _cos(x: int | float | complex) -> float | complex:
    if type(x) is complex:
        return cmath.cos(x)
    else:
        return math.cos(x)


def _tan(x: int | float | complex) -> float | complex:
    if type(x) is complex:
        return cmath.tan(x)
    else:
        return math.tan(x)


def _asin(x: int | float | complex) -> float | complex:
    if type(x) is complex:
        return cmath.asin(x)
    else:
        return math.asin(x)


def _acos(x: int | float | complex) -> float | complex:
    if type(x) is complex:
        return cmath.acos(x)
    else:
        return math.acos(x)


def _atan(x: int | float | complex) -> float | complex:
    if type(x) is complex:
        return cmath.atan(x)
    else:
        return math.atan(x)


def _sinh(x: int | float | complex) -> float | complex:
    if type(x) is complex:
        return cmath.sinh(x)
    else:
        return math.sinh(x)


def _cosh(x: int | float | complex) -> float | complex:
    if type(x) is complex:
        return cmath.cosh(x)
    else:
        return math.cosh(x)


def _tanh(x: int | float | complex) -> float | complex:
    if type(x) is complex:
        return cmath.tanh(x)
    else:
        return math.tanh(x)


def _asinh(x: int | float | complex) -> float | complex:
    if type(x) is complex:
        return cmath.asinh(x)
    else:
        return math.asinh(x)


def _acosh(x: int | float | complex) -> float | complex:
    if type(x) is complex:
        return cmath.acosh(x)
    else:
        return math.acosh(x)


def _atanh(x: int | float | complex) -> float | complex:
    if type(x) is complex:
        return cmath.atanh(x)
    else:
        return math.atanh(x)


def _sqrt(x: int | float | complex) -> float | complex:
    if type(x) is complex:
        return cmath.sqrt(x)
    else:
        return math.sqrt(x)


def _gcd(x1: int, x2: int) -> int:
    return math.gcd(x1, x2)


def _lcm(x1: int, x2: int) -> int:
    return (x1 * x2) // math.gcd(x1, x2)


def _radians(deg: int | float) -> float:
    return math.radians(deg)


def _factorial(x: int) -> int:
    return math.factorial(x)


def _ceil(x: int | float) -> int:
    return math.ceil(x)


def _floor(x: int | float) -> int:
    return math.floor(x)


def _roundn(x: int | float, n: int) -> int | float:
    return round(x, n)


def _round(x: int | float) -> int:
    return round(x)


def _comb(n: int, k: int) -> int:
    return math.comb(int(n), int(k))


def _perm(n: int, k: int) -> int:
    return math.perm(int(n), int(k))


def _abs(x: int | float | complex) -> int | float:
    return abs(x)


def _cbrt(x: int | float) -> float:
    return x ** (1 / 3)


def _ncr(n: int, k: int) -> int:
    return _comb(n, k)


def _npr(n: int, k: int) -> int:
    return _perm(n, k)


def _frac(a: int, b: int) -> Fraction:
    return Fraction(a, b)


def _numeric_diff(f: Callable[[float], float], x: float) -> float:
    h = 1e-4
    return (f(x + h) - f(x - h)) / (2 * h)


math_operators = {
    "^": {
        "func": (lambda x1, x2: _pow(x1, x2)),
        "arg_count": 2,
        "push_result_to_stack": True,
        "desc": "Power",
    },
    "log": {
        "func": (lambda x: _log(x)),
        "arg_count": 1,
        "push_result_to_stack": True,
        "desc": "Logarithm",
    },
    "log2": {
        "func": (lambda x: _log2(x)),
        "arg_count": 1,
        "push_result_to_stack": True,
        "desc": "Logarithm base 2",
    },
    "log10": {
        "func": (lambda x: _log10(x)),
        "arg_count": 1,
        "push_result_to_stack": True,
        "desc": "Logarithm base 10",
    },
    "exp": {
        "func": (lambda x: _exp(x)),
        "arg_count": 1,
        "push_result_to_stack": True,
        "desc": "Exponential",
    },
    "sin": {
        "func": (lambda x: _sin(x)),
        "arg_count": 1,
        "push_result_to_stack": True,
        "desc": "Sine",
    },
    "cos": {
        "func": (lambda x: _cos(x)),
        "arg_count": 1,
        "push_result_to_stack": True,
        "desc": "Cosine",
    },
    "tan": {
        "func": (lambda x: _tan(x)),
        "arg_count": 1,
        "push_result_to_stack": True,
        "desc": "Tangent",
    },
    "asin": {
        "func": (lambda x: _asin(x)),
        "arg_count": 1,
        "push_result_to_stack": True,
        "desc": "Arcsine",
    },
    "acos": {
        "func": (lambda x: _acos(x)),
        "arg_count": 1,
        "push_result_to_stack": True,
        "desc": "Arccosine",
    },
    "atan": {
        "func": (lambda x: _atan(x)),
        "arg_count": 1,
        "push_result_to_stack": True,
        "desc": "Arctangent",
    },
    "sinh": {
        "func": (lambda x: _sinh(x)),
        "arg_count": 1,
        "push_result_to_stack": True,
        "desc": "Hyperbolic sine",
    },
    "cosh": {
        "func": (lambda x: _cosh(x)),
        "arg_count": 1,
        "push_result_to_stack": True,
        "desc": "Hyperbolic cosine",
    },
    "tanh": {
        "func": (lambda x: _tanh(x)),
        "arg_count": 1,
        "push_result_to_stack": True,
        "desc": "Hyperbolic tangent",
    },
    "asinh": {
        "func": (lambda x: _asinh(x)),
        "arg_count": 1,
        "push_result_to_stack": True,
        "desc": "Hyperbolic arcsine",
    },
    "acosh": {
        "func": (lambda x: _acosh(x)),
        "arg_count": 1,
        "push_result_to_stack": True,
        "desc": "Hyperbolic arccosine",
    },
    "atanh": {
        "func": (lambda x: _atanh(x)),
        "arg_count": 1,
        "push_result_to_stack": True,
        "desc": "Hyperbolic arctangent",
    },
    "sqrt": {
        "func": (lambda x: _sqrt(x)),
        "arg_count": 1,
        "push_result_to_stack": True,
        "desc": "Square root",
    },
    "gcd": {
        "func": (lambda x1, x2: _gcd(x1, x2)),
        "arg_count": 2,
        "push_result_to_stack": True,
        "desc": "Greatest common divisor",
    },
    "lcm": {
        "func": (lambda x1, x2: _lcm(x1, x2)),
        "arg_count": 2,
        "push_result_to_stack": True,
        "desc": "Least common multiple",
    },
    "radians": {
        "func": (lambda deg: _radians(deg)),
        "arg_count": 1,
        "push_result_to_stack": True,
        "desc": "Convert degrees to radians",
    },
    "!": {
        "func": (lambda x: _factorial(x)),
        "arg_count": 1,
        "push_result_to_stack": True,
        "desc": "Factorial",
    },
    "ceil": {
        "func": (lambda x: _ceil(x)),
        "arg_count": 1,
        "push_result_to_stack": True,
        "desc": "Ceiling",
    },
    "floor": {
        "func": (lambda x: _floor(x)),
        "arg_count": 1,
        "push_result_to_stack": True,
        "desc": "Floor",
    },
    "comb": {
        "func": (lambda n, k: _comb(n, k)),
        "arg_count": 2,
        "push_result_to_stack": True,
        "desc": "Combinations",
    },
    "perm": {
        "func": (lambda n, k: _perm(n, k)),
        "arg_count": 2,
        "push_result_to_stack": True,
        "desc": "Permutations",
    },
    "abs": {
        "func": (lambda x: _abs(x)),
        "arg_count": 1,
        "push_result_to_stack": True,
        "desc": "Absolute value",
    },
    "cbrt": {
        "func": (lambda x: _cbrt(x)),
        "arg_count": 1,
        "push_result_to_stack": True,
        "desc": "Cube root",
    },
    "ncr": {
        "func": (lambda n, k: _ncr(n, k)),
        "arg_count": 2,
        "push_result_to_stack": True,
        "desc": "Combinations",
    },
    "npr": {
        "func": (lambda n, k: _npr(n, k)),
        "arg_count": 2,
        "push_result_to_stack": True,
        "desc": "Permutations",
    },
    "roundn": {
        "func": (lambda x1, x2: _roundn(x1, x2)),
        "arg_count": 2,
        "push_result_to_stack": True,
        "desc": "Round to n decimal places",
    },
    "round": {
        "func": (lambda x: _round(x)),
        "arg_count": 1,
        "push_result_to_stack": True,
        "desc": "Round to nearest integer",
    },
    "frac": {
        "func": (lambda a, b: _frac(a, b)),
        "arg_count": 2,
        "push_result_to_stack": True,
        "desc": "Fraction",
    },
}
