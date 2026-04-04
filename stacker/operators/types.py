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
    "int?": {
        "func": (lambda x: isinstance(x, int) and not isinstance(x, bool)),
        "arg_count": 1,
        "push_result_to_stack": True,
        "desc": "Returns true if the value is an int",
    },
    "float?": {
        "func": (lambda x: isinstance(x, float)),
        "arg_count": 1,
        "push_result_to_stack": True,
        "desc": "Returns true if the value is a float",
    },
    "str?": {
        "func": (lambda x: isinstance(x, str)),
        "arg_count": 1,
        "push_result_to_stack": True,
        "desc": "Returns true if the value is a string",
    },
    "bool?": {
        "func": (lambda x: isinstance(x, bool)),
        "arg_count": 1,
        "push_result_to_stack": True,
        "desc": "Returns true if the value is a bool",
    },
    "complex?": {
        "func": (lambda x: isinstance(x, complex)),
        "arg_count": 1,
        "push_result_to_stack": True,
        "desc": "Returns true if the value is a complex number",
    },
    "list?": {
        "func": (lambda x: isinstance(x, list)),
        "arg_count": 1,
        "push_result_to_stack": True,
        "desc": "Returns true if the value is a list",
    },
    "number?": {
        "func": (lambda x: isinstance(x, (int, float, complex)) and not isinstance(x, bool)),
        "arg_count": 1,
        "push_result_to_stack": True,
        "desc": "Returns true if the value is a number (int, float, or complex)",
    },
}
