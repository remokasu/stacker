from __future__ import annotations


def _input() -> str:
    """Prints the specified content to the console."""
    string = input()
    return f'"{string}"'


io_operators = {
    "echo": {
        "func": (lambda content: print(content)),
        "arg_count": 1,
        "push_result_to_stack": False,
        "desc": "Prints the specified content to the console.",
    },
    "printc": {
        "func": (lambda content: print(content, end="")),
        "arg_count": 1,
        "push_result_to_stack": False,
        "desc": "Prints the specified content to the console.",
    },
    "newline": {
        "func": (lambda: print("")),
        "arg_count": 0,
        "push_result_to_stack": False,
        "desc": "Prints the specified content to the console.",
    },
    "input": {
        "func": (lambda: _input()),
        "arg_count": 0,
        "push_result_to_stack": True,
        "desc": "Prints the specified content to the console.",
    },
}
