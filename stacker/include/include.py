from __future__ import annotations


from pathlib import Path
from stacker.util.string_parser import parse_expression

def include_stacker_script(filename: str | Path) -> 'Stacker':
    """Import a stacker script and return the stacker object."""

    if isinstance(filename, str):
        filename = Path(filename).resolve()
    if not filename.is_file():
        raise FileNotFoundError(f"File {filename} not found.")
    if not filename.exists():
        raise FileNotFoundError(f"File {filename} not found.")
    if filename.suffix != ".stk":
        raise ValueError(f"File {filename} is not a stacker script.")

    with open(filename, 'r') as file:
        script_content = file.read()

    from stacker.stacker import Stacker
    stacker = Stacker()
    stacker.process_expression(script_content)
    return stacker

# if __name__ == "__main__":
#     s = include_stacker_script("test.stk")