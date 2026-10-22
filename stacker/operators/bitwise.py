from __future__ import annotations

from stacker.error import ValidationError
from stacker.operators.arguments import integer_argument


def _trailing_zeros(x: object) -> int:
    """``n trailing-zeros``: how many zero bits are below the lowest one bit of ``n``."""
    n = integer_argument("trailing-zeros", x)
    if n == 0:
        raise ValidationError("`trailing-zeros` of 0 is undefined: 0 has no one bit")
    return (n & -n).bit_length() - 1


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
    "bit-length": {
        "func": (lambda x: integer_argument("bit-length", x).bit_length()),
        "arg_count": 1,
        "push_result_to_stack": True,
        "desc": "The bits needed to write an integer (0 for 0; a negative number counts as its absolute value)",
    },
    "popcount": {
        "func": (lambda x: integer_argument("popcount", x).bit_count()),
        "arg_count": 1,
        "push_result_to_stack": True,
        "desc": "The number of one bits in an integer (a negative number counts as its absolute value)",
    },
    "trailing-zeros": {
        "func": _trailing_zeros,
        "arg_count": 1,
        "push_result_to_stack": True,
        "desc": "The number of zero bits below the lowest one bit of an integer (0 is an error)",
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
