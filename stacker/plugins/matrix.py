# from __future__ import annotations

# import numpy as np

# from stacker.stacker import Stacker

# description = "Matrix operations plugin for Stacker"


# """
# A + B (matrix addition)
#     A = [1, 2; 3, 4]
#     B = [5, 6; 7, 8]
#     A + B
#     ans
#         6   8
#         10  12

# a + b (scalar addition)
#     a = 1
#     b = 2
#     c = a + b
#     c = 3
# """


# def _add(a, b):
#     if type(a) is str or type(b) is str:
#         return a + b
#     return (np.array(a) + np.array(b)).tolist()


# """
# A - B (matrix subtraction)
#     A = [1, 2; 3, 4]
#     B = [5, 6; 7, 8]
#     A - B
#     ans =
#         -4  -4
#         -4  -4

# a - b (scalar subtraction)
#     a = 1
#     b = 2
#     c = a - b
#     c = -1
# """


# def _sub(a, b):
#     return (np.array(a) - np.array(b)).tolist()


# """
# A * B (matrix multiplication)
#     A = [1, 2; 3, 4]
#     B = [5, 6; 7, 8]
#     C = A * B
#     C =
#         19  22
#         43  50

# a * b (scalar multiplication)
#     a = 1
#     b = 2
#     c = a * b
#     c = 2
# """


# def _mul(a, b):
#     if np.array(a).shape == () and np.array(b).shape == ():
#         return a * b
#     else:
#         return np.dot(a, b).tolist()

#     # _a = np.array(a)
#     # _b = np.array(b)
#     # if _a.shape == () and _b.shape == ():
#     #     return a * b
#     # else:
#     #     if _a[-1] != _b[0]:
#     #         raise ValueError(
#     #             f"Matrix dimensions must agree. Got {_a.shape} and {_b.shape}."
#     #         )
#     #     return np.dot(_a, _b).tolist()


# """
# A .* B (element-wise multiplication)
#     A = [1, 2; 3, 4]
#     B = [5, 6; 7, 8]
#     C = A .* B
#     C =
#         5   12
#         21  32
# """


# def _adamul(a, b):
#     return np.multiply(a, b).tolist()


# """
# A / B (matrix division)
#     A = [1, 2; 3, 4]
#     B = [5, 6; 7, 8]
#     A / B
#     ans =
#         3.0 -2.0
#         2.0 -1.0
#     # A * inv(B)
# """


# def _div(a, b):
#     if (
#         np.array(a).shape == () and np.array(b).shape == ()
#     ):  # scalar and scalar division
#         return a / b
#     else:
#         return np.dot(a, np.linalg.inv(b)).tolist()


# """
# A ./ B (element-wise division)
#     A = [1, 2; 3, 4]
#     B = [5, 6; 7, 8]
#     A ./ B
#     ans =
#         0.2000 0.3333
#         0.4286 0.5000

# """


# def _elemdiv(a, b):
#     return np.divide(a, b).tolist()


# """
# A \ B (left division, solve for x in Ax = B)
#     A = [1, 2; 3, 4]
#     B = [5, 6; 7, 8]
#     A \ B
#     ans =
#         -3.0000  -4.0000
#         4.0000   5.0000

# """


# def _leftdiv(a, b):
#     return np.linalg.solve(a, b).tolist()


# """
# A .\ B (element-wise left division)
# """


# def _elemldiv(a, b):
#     return np.divide(b, a).tolist()


# """
# A ^ B (matrix power)
#     A = [1, 2; 3, 4]
#     B = 2
#     A ^ B
#     ans =
#         7  10
#         15 22
# """


# def _pow(a, b):
#     if np.array(a).shape == () and np.array(b).shape == ():
#         return _elempow(a, b)
#     return np.linalg.matrix_power(a, b).tolist()


# """
# A .^ B (element-wise power)
#     A = [1, 2; 3, 4]
#     B = [5, 6; 7, 8]
#     A .^ B
#     ans =
#         1 64
#         2187 65536
# """


# def _elempow(a, b):
#     return np.power(a, b).tolist()


# """
# A | B (element logical OR)
#     A = [0 1 0 2[]
#     B = [0 0 3 -2]
#     A | B
#     ans =
#         False True False True
# """


# def _logical_or(a, b):
#     return np.logical_or(a, b).tolist()


# """
# A & B (element logical AND)
#     A = [0 1 0 2]
#     B = [0 0 3 -2]
#     A & B
#     ans =
#         False False False True
# """


# def _logical_and(a, b):
#     return np.logical_and(a, b).tolist()


# """
# ~A (logical NOT)
#     A = [0 1 0 2]
#     ~A
#     ans =
#         True False True False
# """


# def _logical_not(a):
#     return np.logical_not(a).tolist()


# """
# A xor B (logical XOR)
#     A = [0 1 0 2]

# """


# def _logical_xor(a, b):
#     return np.logical_xor(a, b).tolist()


# """
# A == B (equality)
#     A = [1, 2; 3, 4]
#     B = [1, 2; 3, 4]
#     ans =
#         True True
#         True True
# """


# def _eq(a, b):
#     return (np.array(a) == np.array(b)).tolist()


# """
# A
# """

# """
# A' (transpose)
#     A = [1, 2; 3, 4]
#     B = A'
#     B =
#         1 3
#         2 4
# """


# def _transpose(a):
#     return np.transpose(a).tolist()


# """
# A.' (conjugate transpose)
#     A = [1, 2; 3, 4]
#     B = A.'
#     B =
#         1 3
#         2 4
# """


# def _ctranspose(a):
#     return np.conjugate(np.transpose(a)).tolist()


# """
# inv(A) (inverse)
#     A = [1, 2; 3, 4]
#     B = inv(A)
#     B =
#         -2  1
#         1.5 -0.5
# """


# def _inv(a):
#     return np.linalg.inv(a).tolist()


# """
# det(A) (determinant)
#     A = [1, 2; 3, 4]
#     B = det(A)
#     B = -2
# """


# def _det(a):
#     return np.linalg.det(np.array(a)).tolist()


# """
# dot(A, B) (dot product)
# """


# def _dot(a, b):
#     _a = np.array(a)
#     _b = np.array(b)
#     if _a[-1] != _b[0]:
#         raise ValueError(
#             f"Matrix dimensions must agree. Got {_a.shape} and {_b.shape}."
#         )
#     return np.dot(_a, _b).tolist()


# """
# rank(A) (rank)
#     A = [1, 2; 3, 4]
#     B = rank(A)
#     B = 2

# """


# def _rank(a):
#     return int(np.linalg.matrix_rank(np.array(a)))


# """
# trace(A) (trace)
#     A = [1, 2; 3, 4]
#     B = trace(A)
#     B = 5
# """


# def _trace(a):
#     return int(np.trace(np.array(a)))


# """
# ones(m, n) (ones)
#     A = ones(2, 3)
#     A =
#         1 1 1
#         1 1 1
# """


# def _ones(*args):
#     return np.ones(args).tolist()


# """
# zeros(m, n) (zeros)
#     A = zeros(2, 3)
#     A =
#         0 0 0
#         0 0 0
# """


# def _zeros(*args):
#     return np.zeros(args).tolist()


# """
# diag(A) (diagonal)
#     A = [1, 2; 3, 4]
#     B = diag(A)
#     B =
#         1
#         4
# """


# def _diag(*args):
#     return np.diag(*args).tolist()


# # def ndim(a) -> int:
# #     if not isinstance(a, np.ndarray):
# #         return np.ndim(a)
# #     else:
# #         return np.ndim(np.array(a))


# # def size(a) -> int:
# #     if not isinstance(a, np.ndarray):
# #         return np.size(a)
# #     else:
# #         return np.size(np.array(a))


# # def shape(a) -> tuple:
# #     if not isinstance(a, np.ndarray):
# #         return np.shape(a)
# #     else:
# #         return np.shape(np.array(a))


# def _all(a) -> bool:
#     return bool(np.all(a))


# def _any(a) -> bool:
#     return bool(np.any(a))


# def setup(stacker: Stacker):
#     stacker.register_plugin("+", _add, desc="Matrix Addition")
#     stacker.register_plugin("-", _sub, desc="Matrix Subtraction")
#     stacker.register_plugin("*", _mul, desc="Matrix Multiplication")
#     stacker.register_plugin(".*", _adamul, desc="Element-wise Multiplication")
#     stacker.register_plugin("/", _div, desc="Matrix Division")
#     stacker.register_plugin("./", _elemdiv, desc="Element-wise Division")
#     stacker.register_plugin("\\", _leftdiv, desc="Left Division")  # \
#     stacker.register_plugin(".\\", _elemldiv, desc="Element-wise Left Division")  # .\
#     stacker.register_plugin("^", _pow, desc="Matrix Power")
#     stacker.register_plugin(".^", _elempow, desc="Element-wise Power")
#     stacker.register_plugin("or", _logical_or, desc="Logical OR")
#     stacker.register_plugin("and", _logical_and, desc="Logical AND")
#     stacker.register_plugin("not", _logical_not, desc="Logical NOT")
#     stacker.register_plugin("xor", _logical_xor, desc="Logical XOR")
#     stacker.register_plugin("==", _eq, desc="Equality")
#     stacker.register_plugin("'", _transpose, desc="Transpose")
#     stacker.register_plugin("dot", _dot, desc="Dot Product")
#     stacker.register_plugin("inv", _inv, desc="Inverse")
#     stacker.register_plugin("det", _det, desc="Determinant")
#     stacker.register_plugin("rank", _rank, desc="Rank")
#     stacker.register_plugin("trace", _trace, desc="Trace")
#     stacker.register_plugin("ones", _ones, desc="Ones")
#     stacker.register_plugin("zeros", _zeros, desc="Zeros")
#     stacker.register_plugin("diag", _diag, desc="Diagonal")
#     # stacker.register_plugin("ndim", ndim, desc="Number of Dimensions")
#     # stacker.register_plugin("size", size, desc="Size")
#     # stacker.register_plugin("shape", shape, desc="Shape")
#     stacker.register_plugin("all", _all, desc="All")
#     stacker.register_plugin("any", _any, desc="Any")


def setup(stacker):
    pass
