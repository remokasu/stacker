from __future__ import annotations


transform_operators = {
    "enumerate": {
        "func": (lambda xs: [[i, x] for i, x in enumerate(xs)]),
        "arg_count": 1,
        "push_result_to_stack": True,
        "desc": "Pairs each element with its index: [10 20] enumerate -> [[0 10] [1 20]]",
    },
    "sorted": {
        "func": (lambda xs: sorted(xs)),
        "arg_count": 1,
        "push_result_to_stack": True,
        "desc": "Sorts a list.",
    },
    "reversed": {
        "func": (lambda xs: reversed(xs)),
        "arg_count": 1,
        "push_result_to_stack": True,
        "desc": "Reverses a list.",
    },
    "list": {
        "func": (lambda x: list(x)),
        "arg_count": 1,
        "push_result_to_stack": True,
        "desc": "Converts an iterable to a list.",
    },
    # REMOVED: "tuple" operator - () now creates code blocks, not tuples
    # Use lists [] instead of tuples for data structures
}
