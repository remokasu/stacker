def _exit():
    raise SystemExit


exit_operators = {
    "exit": {
        "func": (lambda: _exit()),
        "arg_count": 0,
        "push_result_to_stack": False,
        "desc": "Exits the program.",
    },
}
