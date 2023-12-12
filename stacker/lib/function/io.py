from __future__ import annotations

from stacker.file import read_file, write_file


def _raad(filename: str, mode: str) -> str:
    """Reads a file."""
    content = read_file(filename, mode=mode, repl_mode=True)
    return content


def _write(filename: str, content, mode: str) -> None:
    """Writes a file."""
    write_file(filename, content, mode=mode, repl_mode=True)


def _echo(content: str) -> None:
    """Prints the specified content to the console."""
    print(content)


def _print(content: str) -> None:
    """Prints the specified content to the console."""
    print(content)


io_operators = {
    # "read": {
    #     "func": (lambda filename, mode: _raad(filename, mode)),
    #     "arg_count": 2,
    #     "push_result_to_stack": True,
    #     "desc": "Reads a file.",
    # },
    # "write": {
    #     "func": (lambda filename, content, mode: _write(filename, content, mode)),
    #     "arg_count": 3,
    #     "push_result_to_stack": False,
    #     "desc": "Writes a file.",
    # },
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
