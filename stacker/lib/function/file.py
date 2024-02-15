from __future__ import annotations

from pathlib import Path


def _write(content, filename: Path | str) -> None:
    filename = Path(filename).resolve()
    try:
        with open(filename, "w") as f:
            f.write(content)
    except Exception as e:
        raise type(e)(f"Error writing to file {filename}: {e}")


def _append(content, filename: Path | str) -> None:
    filename = Path(filename).resolve()
    try:
        with open(filename, "a") as f:
            f.write(content)
    except Exception as e:
        raise type(e)(f"Error writing to file {filename}: {e}")


def _read(filename: Path | str) -> str | None:
    filename = Path(filename).resolve()
    if not filename.is_file():
        raise FileNotFoundError(f"File {filename} not found.")
    if not filename.exists():
        raise FileNotFoundError(f"File {filename} does not exist.")
    try:
        with open(filename, "r") as f:
            return f.read()
    except Exception as e:
        raise type(e)(f"Error reading file {filename}: {e}")


file_operators = {
    "write": {
        "func": (lambda filename, content: _write(filename, content)),
        "arg_count": 2,
        "push_result_to_stack": False,
        "desc": "Write content to file",
    },
    # "append": {
    #     "func": (lambda filename, content: _append(filename, content)),
    #     "arg_count": 2,
    #     "push_result_to_stack": False,
    #     "desc": "Append content to file",
    # },
    "read": {
        "func": (lambda filename: _read(filename)),
        "arg_count": 1,
        "push_result_to_stack": True,
        "desc": "Read content from file",
    },
}
