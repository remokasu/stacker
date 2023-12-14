from __future__ import annotations


def _neg(x):
    try:
        return -x
    except TypeError:
        raise TypeError(f"Cannot negate {x}")


alge_operators = {
    "neg": {
        "func": (lambda x: _neg(x)),
        "arg_count": 1,
        "push_result_to_stack": True,
        "desc": "Negate",
    },
}
