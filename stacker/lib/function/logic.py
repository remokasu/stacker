from __future__ import annotations


def _and(x1, x2):
    try:
        return x1 and x2
    except TypeError:
        raise TypeError(f"Cannot Logical and {x1} and {x2}.")


def _or(x1, x2):
    try:
        return x1 or x2
    except TypeError:
        raise TypeError(f"Cannot Logical or {x1} and {x2}.")


# def xor(x1, x2):
#     try:
#         return (x1 ^ x2)
#     except TypeError:
#         raise TypeError("Cannot Logical xor {} and {}".format(type(x1), type(x2)))


def _not(x):
    try:
        return not x
    except TypeError:
        raise TypeError(f"Cannot Logical not {x}.")


logic_operators = {
    "and": {
        "func": (lambda x1, x2: _and(x1, x2)),
        "arg_count": 2,
        "push_result_to_stack": True,
        "desc": "Logical and",
    },
    "or": {
        "func": (lambda x1, x2: _or(x1, x2)),
        "arg_count": 2,
        "push_result_to_stack": True,
        "desc": "Logical or",
    },
    "not": {
        "func": (lambda x: _not(x)),
        "arg_count": 1,
        "push_result_to_stack": True,
        "desc": "Logical not",
    },
    "&&": {
        "func": (lambda x1, x2: _and(x1, x2)),
        "arg_count": 2,
        "push_result_to_stack": True,
        "desc": "Logical and",
    },
    "||": {
        "func": (lambda x1, x2: _or(x1, x2)),
        "arg_count": 2,
        "push_result_to_stack": True,
        "desc": "Logical or",
    },
}
