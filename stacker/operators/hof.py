##############################################################################
# Higher-order functions
##############################################################################


from __future__ import annotations


from functools import reduce as py_reduce


hof_operators = {
    "map": {
        "func": (lambda func, xs: map(func, xs)),
        "arg_count": 2,
        "push_result_to_stack": True,
        "desc": "Applies a block, lambda or symbol to each element: [1 2 3] {2 *} map",
    },
    "filter": {
        "func": (lambda func, xs: filter(func, xs)),
        "arg_count": 2,
        "push_result_to_stack": True,
        "desc": "Keeps the elements for which a block, lambda or symbol is true: [1 2 3] {2 >} filter",
    },
    "zip": {
        "func": (lambda xs, ys: [[x, y] for x, y in zip(xs, ys)]),
        "arg_count": 2,
        "push_result_to_stack": True,
        "desc": "Pairs the elements of two lists: [1 2] [3 4] zip -> [[1 3] [2 4]]",
    },
    "reduce": {
        "func": (lambda func, init, xs: py_reduce(func, xs, init)),
        "arg_count": 3,
        "push_result_to_stack": True,
        "desc": "Folds a list into one value with two bound names: [1 2 3] 0 acc x {acc x +} reduce",
    },
    "fold": {
        "func": (lambda func, init, xs: py_reduce(func, xs, init)),
        "arg_count": 3,
        "push_result_to_stack": True,
        "desc": "Same as reduce: [1 2 3] 0 acc x {acc x +} fold",
    },
}
