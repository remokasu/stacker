from __future__ import annotations


compare_operators = {
    "==": {
        "func": (lambda x1, x2: x1 == x2),
        "arg_count": 2,
        "push_result_to_stack": True,
        "desc": "Equal",
    },
    "!=": {
        "func": (lambda x1, x2: x1 != x2),
        "arg_count": 2,
        "push_result_to_stack": True,
        "desc": "Not equal",
    },
    "<=": {
        "func": (lambda x1, x2: x1 <= x2),
        "arg_count": 2,
        "push_result_to_stack": True,
        "desc": "Less than or equal to",
    },
    "<": {
        "func": (lambda x1, x2: x1 < x2),
        "arg_count": 2,
        "push_result_to_stack": True,
        "desc": "Less than",
    },
    ">=": {
        "func": (lambda x1, x2: x1 >= x2),
        "arg_count": 2,
        "push_result_to_stack": True,
        "desc": "Greater than or equal to",
    },
    ">": {
        "func": (lambda x1, x2: x1 > x2),
        "arg_count": 2,
        "push_result_to_stack": True,
        "desc": "Greater than",
    },
    "eq": {
        "func": (lambda x1, x2: x1 == x2),
        "arg_count": 2,
        "push_result_to_stack": True,
        "desc": "Equal",
    },
    "neq": {
        "func": (lambda x1, x2: x1 != x2),
        "arg_count": 2,
        "push_result_to_stack": True,
        "desc": "Not equal",
    },
    "le": {
        "func": (lambda x1, x2: x1 <= x2),
        "arg_count": 2,
        "push_result_to_stack": True,
        "desc": "Less than or equal to",
    },
    "lt": {
        "func": (lambda x1, x2: x1 < x2),
        "arg_count": 2,
        "push_result_to_stack": True,
        "desc": "Less than",
    },
    "ge": {
        "func": (lambda x1, x2: x1 >= x2),
        "arg_count": 2,
        "push_result_to_stack": True,
        "desc": "Greater than or equal to",
    },
    "gt": {
        "func": (lambda x1, x2: x1 > x2),
        "arg_count": 2,
        "push_result_to_stack": True,
        "desc": "Greater than",
    },
}
