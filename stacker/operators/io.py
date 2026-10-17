from __future__ import annotations

from stacker.util.disp import display_text

io_operators = {
    "echo": {
        "func": (lambda content: print(display_text(content))),
        "arg_count": 1,
        "push_result_to_stack": False,
        "desc": "Prints the specified content to the console.",
    },
    "print": {
        "func": (lambda content: print(display_text(content))),
        "arg_count": 1,
        "push_result_to_stack": False,
        "desc": "Prints the specified content to the console.",
    },
    "printc": {
        "func": (lambda content: print(display_text(content), end="")),
        "arg_count": 1,
        "push_result_to_stack": False,
        "desc": "Prints the specified content to the console without a newline.",
    },
    "newline": {
        "func": (lambda: print("")),
        "arg_count": 0,
        "push_result_to_stack": False,
        "desc": "Prints a newline to the console.",
    },
    # "input": {
    #     "func": (lambda: _input()),
    #     "arg_count": 0,
    #     "push_result_to_stack": True,
    #     "desc": "Reads a line of input from the console.",
    # },
}
