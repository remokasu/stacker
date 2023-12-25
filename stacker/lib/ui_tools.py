from __future__ import annotations

from pkg_resources import resource_stream

from stacker.lib.config import history_file_path
from stacker.util.color import colored


def disp_logo() -> None:
    """Prints the top message."""
    colors = ["red", "green", "yellow", "lightblue", "lightmagenta", "cyan"]
    with resource_stream("stacker", "data/top.txt") as f:
        messages = f.readlines()
        for i in range(len(messages)):
            print(colored(messages[i].decode("utf-8"), colors[i]), end="")
    print("")


def disp_about() -> None:
    """Prints the about message."""
    with resource_stream("stacker", "data/about.txt") as f:
        message = f.read().decode("utf-8")
    print(message)


def disp_help() -> None:
    """Prints the help message."""
    with resource_stream("stacker", "data/help.txt") as f:
        message = f.read().decode("utf-8")
    print(message)


def delete_history() -> None:
    """Deletes the history file."""
    if history_file_path.exists():
        history_file_path.unlink()
