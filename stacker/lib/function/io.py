from __future__ import annotations


def _echo(content: str) -> None:
    """Prints the specified content to the console."""
    print(content)


def _print(content: str) -> None:
    """Prints the specified content to the console."""
    print(content)


io_operators = {
    "echo": {
        "func": (lambda content: _echo(content)),
        "arg_count": 1,
        "push_result_to_stack": False,
        "desc": "Prints the specified content to the console.",
    },
    "print": {
        "func": (lambda content: _echo(content)),
        "arg_count": 1,
        "push_result_to_stack": False,
        "desc": "Prints the specified content to the console.",
    },
}
