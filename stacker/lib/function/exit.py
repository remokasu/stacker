import sys


exit_operators = {
    "exit": {
        "func": (lambda: sys.exit(0)),
        "arg_count": 0,
        "push_result_to_stack": False,
        "desc": "Exits the program.",
    },
    "abort": {
        "func": (lambda: sys.exit(1)),
        "arg_count": 0,
        "push_result_to_stack": False,
        "desc": "Aborts the program.",
    },
}
