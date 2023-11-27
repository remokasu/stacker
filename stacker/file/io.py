from __future__ import annotations

from pathlib import Path


def write_file(filename: Path | str, content, mode='w', interactive_mode=False) -> None:
    filename = Path(filename).resolve()
    try:
        with open(filename, mode) as f:
            f.write(content)
    except Exception as e:
        if interactive_mode:
            print("Error while writing to file.")
        else:
            raise Exception(e)

def read_file(filename: Path | str, mode='r', interactive_mode=False) -> str | None:
    filename = Path(filename).resolve()
    if not filename.is_file():
        if interactive_mode:
            print(f"File {filename} not found.")
            return
        else:
            raise FileNotFoundError(f"File {filename} not found.")
    if not filename.exists():
        if interactive_mode:
            print(f"File {filename} not found.")
            return
        else:
            raise FileNotFoundError(f"File {filename} not found.")
    try:
        with open(filename, 'r') as f:
            return f.read()
    except Exception as e:
        if interactive_mode:
            print(e)
            return
        else:
            raise Exception(e)
