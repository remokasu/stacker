from __future__ import annotations

import numpy as np
import math
import random

from typing import Callable


def pow(x1, x2):
    return np.power(x1, x2).tolist()


def log(x):
    return np.log(x).tolist()


def log2(x):
    return np.log2(x).tolist()


def log10(x):
    return np.log10(x).tolist()


def exp(x):
    return np.exp(x).tolist()


def sin(x):
    return np.sin(x).tolist()


def cos(x):
    return np.cos(x).tolist()


def tan(x):
    return np.tan(x).tolist()


def asin(x):
    return np.arcsin(x).tolist()


def acos(x):
    return np.arccos(x).tolist()


def atan(x):
    return np.arctan(x).tolist()


def sinh(x):
    return np.sinh(x).tolist()


def cosh(x):
    return np.cosh(x).tolist()


def tanh(x):
    return np.tanh(x).tolist()


def asinh(x):
    return np.arcsinh(x).tolist()


def acosh(x):
    return np.arccosh(x).tolist()


def atanh(x):
    return np.arctanh(x).tolist()


def sqrt(x):
    return np.sqrt(x).tolist()


def gcd(x1, x2):
    return np.gcd(x1, x2).tolist()


def lcm(x1, x2):
    return np.lcm(x1, x2).tolist()


def radians(deg):
    return np.radians(deg).tolist()


def factorial(x):
    # TODO Type check
    return np.math.factorial(x)


def ceil(x):
    return np.ceil(x).tolist()


def floor(x):
    return np.floor(x).tolist()


def rand() -> float:
    return random.random()


def randint(x1: int, x2: int) -> int:
    return random.randint(int(x1), int(x2))


def uniform(x1: float, x2: float) -> float:
    return random.uniform(float(x1), float(x2))


def dice(num_dice: int, num_faces: int) -> int:
    # Roll dice (e.g., 3d6)
    return sum(random.randint(1, int(num_faces)) for _ in range(int(num_dice)))


def comb(n: int, k: int):
    return math.comb(int(n), int(k))


def perm(n: int, k: int) -> int:
    return math.perm(int(n), int(k))


# def factorial(x) -> int:
#     return math.factorial(int(x))


def numeric_diff(f: Callable, x: float) -> float:
    h = 1e-4
    return (f(x + h) - f(x - h)) / (2 * h)
