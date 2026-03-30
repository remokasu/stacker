from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING

from stacker.error import IncludeError
from stacker.include.stk_file_read import readtxt
from stacker.syntax.parser import remove_start_end_quotes

if TYPE_CHECKING:
    from stacker.stacker import Stacker


def include_stacker_script(filename: str | Path) -> Stacker:
    """Import a stacker script and return the stacker object."""
    if isinstance(filename, str):
        filename = remove_start_end_quotes(filename)
        # filename = Path(filename).resolve()
        filename = Path(filename)
    if not filename.is_file():
        raise IncludeError(f"File {filename} not found.")
    if not filename.exists():
        raise IncludeError(f"File {filename} not found.")
    if filename.suffix != ".stk":
        raise IncludeError(f"File {filename} is not a stacker script.")

    # with open(filename, 'r') as file:
    # script_content = file.read()

    script_content = readtxt(filename)

    from stacker.stacker import Stacker

    stacker = Stacker()
    stacker.process_expression(script_content)
    return stacker
