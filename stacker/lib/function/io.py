from __future__ import annotations


def _echo(content: str) -> None:
    """Prints the specified content to the console."""
    print(content)


def _echo2(content: str) -> None:
    """Prints the specified content to the console."""
    print(content, end="")


def _input() -> str:
    """Prints the specified content to the console."""
    string = input()
    return f'"{string}"'


io_operators = {
    "echo": {
        "func": (lambda content: _echo(content)),
        "arg_count": 1,
        "push_result_to_stack": False,
        "desc": "Prints the specified content to the console.",
    },
    "ECHO": {
        "func": (lambda content: _echo2(content)),
        "arg_count": 1,
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
