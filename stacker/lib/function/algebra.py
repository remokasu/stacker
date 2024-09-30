from __future__ import annotations


alge_operators = {
    "neg": {
        "func": (lambda x: -x),
        "arg_count": 1,
        "push_result_to_stack": True,
        "desc": "Negate",
    },
}
