from __future__ import annotations

import numpy as np

from stacker.stacker import Stacker

description = "Matrix operations plugin for Stacker"


def _add(a, b):
    return (np.array(a) + np.array(b)).tolist()


def _sub(a, b):
    return (np.array(a) - np.array(b)).tolist()


def _mul(a, b):
    return (np.array(a) * np.array(b)).tolist()


def _div(a, b):
    return (np.array(a) / np.array(b)).tolist()


def _transpose(a):
    return np.transpose(a).tolist()


def _inv(a):
    return np.linalg.inv(a).tolist()


def _det(a):
    return np.linalg.det(np.array(a)).tolist()

def _dot(a, b):
    return np.dot(np.array(a), np.array(b)).tolist()

def _rank(a):
    return np.linalg.matrix_rank(np.array(a))


def _trace(a):
    return np.trace(np.array(a))


def _ones(rows, cols):
    return np.ones((rows, cols)).tolist()


def _zeros(rows, cols):
    return np.zeros((rows, cols)).tolist()


def _diag(a):
    return np.diag(np.array(a)).tolist()



# def ndim(a) -> int:
#     print(np.ndim(a))


# def size(a) -> int:
#     print(np.ndim(a))


# def shape(a) -> tuple:
#     print(np.shape(a))


def setup(stacker: Stacker):
    stacker.register_plugin("+", _add, desc="Matrix Addition")
    stacker.register_plugin("-", _sub, desc="Matrix Subtraction")
    stacker.register_plugin("*", _mul, desc="Matrix Multiplication")
    stacker.register_plugin("/", _div, desc="Matrix Division")
    stacker.register_plugin("'", _transpose, desc="Transpose")
    stacker.register_plugin("dot", _dot, desc="Dot Product")
    stacker.register_plugin("inv", _inv, desc="Inverse")
    stacker.register_plugin("det", _det, desc="Determinant")
    stacker.register_plugin("rank", _rank, desc="Rank")
    stacker.register_plugin("trace", _trace, desc="Trace")
    stacker.register_plugin("ones", _ones, desc="Ones")
    stacker.register_plugin("zeros", _zeros, desc="Zeros")
    stacker.register_plugin("diag", _diag, desc="Diagonal")
