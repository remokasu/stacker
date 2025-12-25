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
        "desc": "Applies a function to each element of a list.",
    },
    "filter": {
        "func": (lambda func, xs: filter(func, xs)),
        "arg_count": 2,
        "push_result_to_stack": True,
        "desc": "Filters a list based on a predicate function.",
    },
    "zip": {
        "func": (lambda xs, ys: zip(xs, ys)),
        "arg_count": 2,
        "push_result_to_stack": True,
        "desc": "Zips two lists together.",
    },
    "reduce": {
        "func": (lambda func, init, xs: py_reduce(func, xs, init)),
        "arg_count": 3,
        "push_result_to_stack": True,
        "desc": "Reduces a list to a single value using a binary function.",
    },
    "fold": {
        "func": (lambda func, init, xs: py_reduce(func, xs, init)),
        "arg_count": 3,
        "push_result_to_stack": True,
        "desc": "Alias for reduce. Folds a list to a single value using a binary function.",
    },
}
