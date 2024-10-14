from __future__ import annotations


aggregate_operators = {
    "any": {
        "func": (lambda xs: any(xs)),
        "arg_count": 1,
        "push_result_to_stack": True,
        "desc": "Returns True if any element of an iterable is True.",
    },
    "all": {
        "func": (lambda xs: all(xs)),
        "arg_count": 1,
        "push_result_to_stack": True,
        "desc": "Returns True if all elements of an iterable are True.",
    },
    "sum": {
        "func": (lambda xs: sum(xs)),
        "arg_count": 1,
        "push_result_to_stack": True,
        "desc": "Sums a iterable.",
    },
    "len": {
        "func": (lambda xs: len(xs)),
        "arg_count": 1,
        "push_result_to_stack": True,
        "desc": "Returns the length of an iterable.",
    },
    "min": {
        "func": (lambda xs: min(xs)),
        "arg_count": 1,
        "push_result_to_stack": True,
        "desc": "Returns the minimum value in an iterable.",
    },
    "max": {
        "func": (lambda xs: max(xs)),
        "arg_count": 1,
        "push_result_to_stack": True,
        "desc": "Returns the maximum value in an iterable.",
    },
}
