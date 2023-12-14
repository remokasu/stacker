from __future__ import annotations

import math
import random
from typing import Callable

import numpy as np


def _pow(x1, x2):
    try:
        return np.power(x1, x2).tolist()
    except TypeError:
        raise TypeError(f"Cannot raise {x1} to the power of {x2}.")


def _log(x):
    try:
        return np.log(x).tolist()
    except TypeError:
        raise TypeError(f"Cannot take log of {x}.")


def _log2(x):
    try:
        return np.log2(x).tolist()
    except TypeError:
        raise TypeError(f"Cannot take log2 of {x}.")


def _log10(x):
    try:
        return np.log10(x).tolist()
    except TypeError:
        raise TypeError(f"Cannot take log10 of {x}.")


def _exp(x):
    try:
        return np.exp(x).tolist()
    except TypeError:
        raise TypeError(f"Cannot take exp of {x}.")


def _sin(x):
    try:
        return np.sin(x).tolist()
    except TypeError:
        raise TypeError(f"Cannot take sin of {x}.")


def _cos(x):
    try:
        return np.cos(x).tolist()
    except TypeError:
        raise TypeError(f"Cannot take cos of {x}.")


def _tan(x):
    try:
        return np.tan(x).tolist()
    except TypeError:
        raise TypeError(f"Cannot take tan of {x}.")


def _asin(x):
    try:
        return np.arcsin(x).tolist()
    except TypeError:
        raise TypeError(f"Cannot take asin of {x}.")


def _acos(x):
    try:
        return np.arccos(x).tolist()
    except TypeError:
        raise TypeError(f"Cannot take acos of {x}.")


def _atan(x):
    try:
        return np.arctan(x).tolist()
    except TypeError:
        raise TypeError(f"Cannot take atan of {x}.")


def _sinh(x):
    try:
        return np.sinh(x).tolist()
    except TypeError:
        raise TypeError(f"Cannot take sinh of {x}.")


def _cosh(x):
    try:
        return np.cosh(x).tolist()
    except TypeError:
        raise TypeError(f"Cannot take cosh of {x}.")


def _tanh(x):
    try:
        return np.tanh(x).tolist()
    except TypeError:
        raise TypeError(f"Cannot take tanh of {x}.")


def _asinh(x):
    try:
        return np.arcsinh(x).tolist()
    except TypeError:
        raise TypeError(f"Cannot take asinh of {x}.")


def _acosh(x):
    try:
        return np.arccosh(x).tolist()
    except TypeError:
        raise TypeError(f"Cannot take acosh of {x}.")


def _atanh(x):
    try:
        return np.arctanh(x).tolist()
    except TypeError:
        raise TypeError(f"Cannot take atanh of {x}.")


def _sqrt(x):
    try:
        return np.sqrt(x).tolist()
    except TypeError:
        raise TypeError(f"Cannot take sqrt of {x}.")


def _gcd(x1, x2):
    try:
        return np.gcd(x1, x2).tolist()
    except TypeError:
        raise TypeError(f"Cannot take gcd of {x1} and {x2}.")


def _lcm(x1, x2):
    try:
        return np.lcm(x1, x2).tolist()
    except TypeError:
        raise TypeError(f"Cannot take lcm of {x1} and {x2}.")


def _radians(deg):
    try:
        return np.radians(deg).tolist()
    except TypeError:
        raise TypeError(f"Cannot convert {deg} to radians")


def _factorial(x):
    # TODO Type check
    try:
        return np.math.factorial(x)
    except TypeError:
        raise TypeError(f"Cannot take factorial of {x}.")


def _ceil(x):
    try:
        return np.ceil(x).tolist()
    except TypeError:
        raise TypeError(f"Cannot take ceil of {x}.")


def _floor(x):
    try:
        return np.floor(x).tolist()
    except TypeError:
        raise TypeError(f"Cannot take floor of {x}.")


def _roundn(x, n):
    try:
        return round(x, n)
    except TypeError:
        raise TypeError(f"Cannot round {x} to {n}.")


def _round(x):
    try:
        return round(x)
    except TypeError:
        raise TypeError(f"Cannot round {x}.")


def _comb(n: int, k: int):
    if not isinstance(n, int) or not isinstance(k, int):
        raise TypeError(f"Cannot take comb of {n} and {k}.")
    try:
        return math.comb(int(n), int(k))
    except TypeError:
        raise TypeError(f"Cannot take comb of {n} and {k}.")


def _perm(n: int, k: int) -> int:
    if not isinstance(n, int) or not isinstance(k, int):
        raise TypeError(f"Cannot take perm of {n} and {k}.")
    try:
        return math.perm(int(n), int(k))
    except TypeError:
        raise TypeError(f"Cannot take perm of {n} and {k}.")


def _abs(x):
    try:
        return np.abs(x).tolist()
    except TypeError:
        raise TypeError(f"Cannot take abs of {x}.")


# def factorial(x) -> int:
#     return math.factorial(int(x))


def _cbrt(x):
    try:
        return np.cbrt(x).tolist()
    except TypeError:
        raise TypeError(f"Cannot take cbrt of {x}.")


def _ncr(n, k):
    try:
        return _comb(n, k)
    except TypeError:
        raise TypeError(f"Cannot take ncr of {n} and {k}.")


def _npr(n, k):
    try:
        return _perm(n, k)
    except TypeError:
        raise TypeError(f"Cannot take npr of {n} and {k}.")


def _numeric_diff(f: Callable, x: float) -> float:
    h = 1e-4
    try:
        return (f(x + h) - f(x - h)) / (2 * h)
    except TypeError:
        raise TypeError(f"Cannot take numeric_diff of {f} and {x}.")


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
}
