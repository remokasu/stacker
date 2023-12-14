from __future__ import annotations


def _eq(x1, x2):
    try:
        return x1 == x2
    except TypeError:
        raise TypeError(f"Cannot compare {x1} and {x2}.")


def _neq(x1, x2):
    try:
        return x1 != x2
    except TypeError:
        raise TypeError(f"Cannot compare {x1} and {x2}.")


def _lt(x1, x2):
    try:
        return x1 < x2
    except TypeError:
        raise TypeError(f"Cannot compare {x1} and {x2}.")


def _gt(x1, x2):
    try:
        return x1 > x2
    except TypeError:
        raise TypeError(f"Cannot compare {x1} and {x2}.")


def _le(x1, x2):
    try:
        return x1 <= x2
    except TypeError:
        raise TypeError(f"Cannot compare {x1} and {x2}.")


def _ge(x1, x2):
    try:
        return x1 >= x2
    except TypeError:
        raise TypeError(f"Cannot compare {x1} and {x2}.")


compare_operators = {
    "==": {
        "func": (lambda x1, x2: _eq(x1, x2)),
        "arg_count": 2,
        "push_result_to_stack": True,
        "desc": "Equal",
    },
    "!=": {
        "func": (lambda x1, x2: _neq(x1, x2)),
        "arg_count": 2,
        "push_result_to_stack": True,
        "desc": "Not equal",
    },
    "<=": {
        "func": (lambda x1, x2: _le(x1, x2)),
        "arg_count": 2,
        "push_result_to_stack": True,
        "desc": "Less than or equal to",
    },
    "<": {
        "func": (lambda x1, x2: _lt(x1, x2)),
        "arg_count": 2,
        "push_result_to_stack": True,
        "desc": "Less than",
    },
    ">=": {
        "func": (lambda x1, x2: _ge(x1, x2)),
        "arg_count": 2,
        "push_result_to_stack": True,
        "desc": "Greater than or equal to",
    },
    ">": {
        "func": (lambda x1, x2: _gt(x1, x2)),
        "arg_count": 2,
        "push_result_to_stack": True,
        "desc": "Greater than",
    },
    "eq": {
        "func": (lambda x1, x2: _eq(x1, x2)),
        "arg_count": 2,
        "push_result_to_stack": True,
        "desc": "Equal",
    },
    "noq": {
        "func": (lambda x1, x2: _neq(x1, x2)),
        "arg_count": 2,
        "push_result_to_stack": True,
        "desc": "Not equal",
    },
    "le": {
        "func": (lambda x1, x2: _le(x1, x2)),
        "arg_count": 2,
        "push_result_to_stack": True,
        "desc": "Less than or equal to",
    },
    "lt": {
        "func": (lambda x1, x2: _lt(x1, x2)),
        "arg_count": 2,
        "push_result_to_stack": True,
        "desc": "Less than",
    },
    "ge": {
        "func": (lambda x1, x2: _ge(x1, x2)),
        "arg_count": 2,
        "push_result_to_stack": True,
        "desc": "Greater than or equal to",
    },
    "gt": {
        "func": (lambda x1, x2: _gt(x1, x2)),
        "arg_count": 2,
        "push_result_to_stack": True,
        "desc": "Greater than",
    },
}
