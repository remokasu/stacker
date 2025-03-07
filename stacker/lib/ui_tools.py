from __future__ import annotations

from importlib.resources import files

from stacker.lib.config import history_file_path
from stacker.util.color import colored


def disp_logo() -> None:
    """Prints the top message."""
    colors = ["red", "green", "yellow", "lightblue", "lightmagenta", "cyan"]
    with files("stacker").joinpath("data/top.txt").open("rb") as f:
        messages = f.readlines()
        for i in range(len(messages)):
            print(colored(messages[i].decode("utf-8"), colors[i]), end="")
    print("")


def disp_about() -> None:
    """Prints the about message."""
    with files("stacker").joinpath("data/about.txt").open("rb") as f:
        message = f.read().decode("utf-8")
    print(message)


def disp_help() -> None:
    """Prints the help message."""
    with files("stacker").joinpath("data/help.txt").open("rb") as f:
        message = f.read().decode("utf-8")
    print(message)


def delete_history() -> None:
    """Deletes the history file."""
    if history_file_path.exists():
        history_file_path.unlink()
