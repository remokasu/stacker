from __future__ import annotations


# def xor(x1, x2):
#     try:
#         return (x1 ^ x2)
#     except TypeError:
#         raise TypeError("Cannot Logical xor {} and {}".format(type(x1), type(x2)))


logic_operators = {
    "and": {
        "func": (lambda x1, x2: x1 and x2),
        "arg_count": 2,
        "push_result_to_stack": True,
        "desc": "Logical and",
    },
    "or": {
        "func": (lambda x1, x2: x1 or x2),
        "arg_count": 2,
        "push_result_to_stack": True,
        "desc": "Logical or",
    },
    "not": {
        "func": (lambda x: not x),
        "arg_count": 1,
        "push_result_to_stack": True,
        "desc": "Logical not",
    },
    "&&": {
        "func": (lambda x1, x2: x1 and x2),
        "arg_count": 2,
        "push_result_to_stack": True,
        "desc": "Logical and",
    },
    "||": {
        "func": (lambda x1, x2: x1 or x2),
        "arg_count": 2,
        "push_result_to_stack": True,
        "desc": "Logical or",
    },
}
