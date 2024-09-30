from __future__ import annotations

from pathlib import Path


def _write(content, filename: Path | str) -> None:
    filename = Path(filename).resolve()
    with open(filename, "w") as f:
        f.write(content)


def _read(filename: Path | str) -> str | None:
    filename = Path(filename).resolve()
    if not filename.is_file():
        raise FileNotFoundError(f"File {filename} not found.")
    if not filename.exists():
        raise FileNotFoundError(f"File {filename} does not exist.")
    with open(filename, "r") as f:
        return f.read()


file_operators = {
    "write": {
        "func": (lambda filename, content: _write(filename, content)),
        "arg_count": 2,
        "push_result_to_stack": False,
        "desc": "Write content to file",
    },
    "read": {
        "func": (lambda filename: _read(filename)),
        "arg_count": 1,
        "push_result_to_stack": True,
        "desc": "Read content from file",
    },
}
