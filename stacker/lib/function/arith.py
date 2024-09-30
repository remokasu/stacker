from __future__ import annotations


arith_operators = {
    "+": {
        "func": (lambda x1, x2: x1 + x2),
        "arg_count": 2,
        "push_result_to_stack": True,
        "desc": "Add",
    },
    "-": {
        "func": (lambda x1, x2: x1 - x2),
        "arg_count": 2,
        "push_result_to_stack": True,
        "desc": "Subtract",
    },
    "*": {
        "func": (lambda x1, x2: x1 * x2),
        "arg_count": 2,
        "push_result_to_stack": True,
        "desc": "Multiply",
    },
    "//": {
        "func": (lambda x1, x2: x1 // x2),
        "arg_count": 2,
        "push_result_to_stack": True,
        "desc": "Integer divide",
    },
    "/": {
        "func": (lambda x1, x2: x1 / x2),
        "arg_count": 2,
        "push_result_to_stack": True,
        "desc": "Divide",
    },
    "%": {
        "func": (lambda x1, x2: x1 % x2),
        "arg_count": 2,
        "push_result_to_stack": True,
        "desc": "Mod",
    },
    "++": {
        "func": (lambda x: x + 1),
        "arg_count": 1,
        "push_result_to_stack": True,
        "desc": "Increment",
    },
    "--": {
        "func": (lambda x: x - 1),
        "arg_count": 1,
        "push_result_to_stack": True,
        "desc": "Decrement",
    },
}
