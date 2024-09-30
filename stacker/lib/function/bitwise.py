from __future__ import annotations


bitwise_operators = {
    "band": {
        "func": (lambda x1, x2: x1 & x2),
        "arg_count": 2,
        "push_result_to_stack": True,
        "desc": "Bitwise and",
    },
    "bor": {
        "func": (lambda x1, x2: x1 | x2),
        "arg_count": 2,
        "push_result_to_stack": True,
        "desc": "Bitwise or",
    },
    "bxor": {
        "func": (lambda x1, x2: x1 ^ x2),
        "arg_count": 2,
        "push_result_to_stack": True,
        "desc": "Bitwise xor",
    },
    "~": {
        "func": (lambda x: ~x),
        "arg_count": 1,
        "push_result_to_stack": True,
        "desc": "Bitwise invert",
    },
    ">>": {
        "func": (lambda value, n: value >> n),
        "arg_count": 2,
        "push_result_to_stack": True,
        "desc": "Bitwise right shift",
    },
    "<<": {
        "func": (lambda value, n: value << n),
        "arg_count": 2,
        "push_result_to_stack": True,
        "desc": "Bitwise left shift",
    },
}
