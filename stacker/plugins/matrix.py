from __future__ import annotations

import numpy as np

from stacker.stacker import Stacker

description = "Matrix operations plugin for Stacker"


def is_matrix(value):
    return isinstance(value, list) and len(value) > 0 and isinstance(value[0], list)


def is_matrix_or_vector(value):
    if not isinstance(value, list):
        return False
    if len(value) == 0:
        return False
    return isinstance(value[0], list) or isinstance(value[0], (int, float))


def matrix_add(a, b):
    if is_matrix_or_vector(a) and is_matrix_or_vector(b):
        return np.add(a, b).tolist()
    elif not is_matrix_or_vector(a) and not is_matrix_or_vector(b):
        return a + b
    else:
        raise ValueError(
            "Both operands must be matrices (or vectors) for matrix addition."
        )


def matrix_sub(a, b):
    if is_matrix_or_vector(a) and is_matrix_or_vector(b):
        return np.subtract(a, b).tolist()
    elif not is_matrix_or_vector(a) and not is_matrix_or_vector(b):
        return a - b
    else:
        raise ValueError(
            "Both operands must be matrices (or vectors) for matrix subtraction."
        )


def matrix_mul(a, b):
    if is_matrix_or_vector(a) and is_matrix_or_vector(b):
        return np.matmul(a, b).tolist()
    elif not is_matrix_or_vector(a) and not is_matrix_or_vector(b):
        return a * b
    else:
        raise ValueError(
            "Both operands must be matrices (or vectors) for matrix multiplication."
        )


def elementwise_mul(a, b):
    return np.multiply(a, b).tolist()


def elementwise_div(a, b):
    return np.divide(a, b).tolist()


def elementwise_div_inv(a, b):
    return np.divide(b, a).tolist()


def matrix_transpose(a):
    return np.transpose(a).tolist()


def matrix_inverse(a):
    return np.linalg.inv(a).tolist()


def matrix_determinant(a):
    return np.linalg.det(a)


def matrix_rank(a):
    return np.linalg.matrix_rank(a)


def matrix_trace(a):
    return np.trace(a)


def ones(rows, cols):
    return np.ones((rows, cols)).tolist()


def zeros(rows, cols):
    return np.zeros((rows, cols)).tolist()


def diag(a):
    if is_matrix(a):
        return np.diag(a).tolist()
    elif isinstance(a, list) and all(isinstance(elem, (int, float)) for elem in a):
        return np.diag(a).tolist()
    else:
        raise ValueError("Input must be a matrix or a list of numbers.")


# def ndim(a) -> int:
#     print(np.ndim(a))


# def size(a) -> int:
#     print(np.ndim(a))


# def shape(a) -> tuple:
#     print(np.shape(a))


def setup(stacker: Stacker):
    stacker.register_plugin("+", matrix_add, desc=description)
    stacker.register_plugin("-", matrix_sub, desc=description)
    stacker.register_plugin("*", matrix_mul, desc=description)
    stacker.register_plugin(".*", elementwise_mul, desc=description)
    stacker.register_plugin("./", elementwise_div, desc=description)
    stacker.register_plugin(".\\", elementwise_div_inv, desc=description)
    stacker.register_plugin("'", matrix_transpose, desc=description)
    stacker.register_plugin("inv", matrix_inverse, desc=description)
    stacker.register_plugin("det", matrix_determinant, desc=description)
    stacker.register_plugin("rank", matrix_rank, desc=description)
    stacker.register_plugin("trace", matrix_trace, desc=description)
    stacker.register_plugin("ones", ones, desc=description)
    stacker.register_plugin("zeros", zeros, desc=description)
    stacker.register_plugin("diag", diag, desc=description)
