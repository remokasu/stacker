from __future__ import annotations

from stacker.operators.arguments import integer_argument


bitwise_operators = {
    "band": {
        "func": (lambda x1, x2: integer_argument("band", x1) & integer_argument("band", x2)),
        "arg_count": 2,
        "push_result_to_stack": True,
        "desc": "Bitwise and",
    },
    "bor": {
        "func": (lambda x1, x2: integer_argument("bor", x1) | integer_argument("bor", x2)),
        "arg_count": 2,
        "push_result_to_stack": True,
        "desc": "Bitwise or",
    },
    "bxor": {
        "func": (lambda x1, x2: integer_argument("bxor", x1) ^ integer_argument("bxor", x2)),
        "arg_count": 2,
        "push_result_to_stack": True,
        "desc": "Bitwise xor",
    },
    "~": {
        "func": (lambda x: ~integer_argument("~", x)),
        "arg_count": 1,
        "push_result_to_stack": True,
        "desc": "Bitwise invert",
    },
    ">>": {
        "func": (lambda value, n: integer_argument(">>", value) >> integer_argument(">>", n)),
        "arg_count": 2,
        "push_result_to_stack": True,
        "desc": "Bitwise right shift",
    },
    "<<": {
        "func": (lambda value, n: integer_argument("<<", value) << integer_argument("<<", n)),
        "arg_count": 2,
        "push_result_to_stack": True,
        "desc": "Bitwise left shift",
    },
}
