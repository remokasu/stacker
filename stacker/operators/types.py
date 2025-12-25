from __future__ import annotations


type_operators = {
    "int": {
        "func": (lambda x: int(x)),
        "arg_count": 1,
        "push_result_to_stack": True,
        "desc": "Convert to int",
    },
    "float": {
        "func": (lambda x: float(x)),
        "arg_count": 1,
        "push_result_to_stack": True,
        "desc": "Convert to float",
    },
    "str": {
        "func": (lambda x: str(x)),
        "arg_count": 1,
        "push_result_to_stack": True,
        "desc": "Convert to str",
    },
    "bool": {
        "func": (lambda x: bool(x)),
        "arg_count": 1,
        "push_result_to_stack": True,
        "desc": "Convert to bool",
    },
    "complex": {
        "func": (lambda x: complex(x)),
        "arg_count": 1,
        "push_result_to_stack": True,
        "desc": "Convert to complex",
    },
    "type": {
        "func": (lambda x: type(x)),
        "arg_count": 1,
        "push_result_to_stack": True,
        "desc": "Get type",
    },
}
