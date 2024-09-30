##############################################################################
# Higher-order functions
##############################################################################


from __future__ import annotations


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
}
