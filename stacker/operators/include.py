from __future__ import annotations
from pathlib import Path

from stacker.include import include_stacker_script

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from stacker.stacker import Stacker


def include(stacker: Stacker, filename: str) -> None:
    """Includes another stacker script.

    Relative paths resolve against the including file's directory first,
    then the current working directory (ADR-0004). REPL and ``-e`` have
    no file context and fall back to cwd-only resolution.
    """
    current_file = stacker.current_file
    base_dir = Path(current_file).parent if current_file else None
    _stacker = include_stacker_script(filename, base_dir=base_dir)
    _macros = _stacker.get_macros_ref()
    _variables = _stacker.get_variables_copy()
    _sfunctions = _stacker.get_sfuntions_ref()
    stacker.macros.update(_macros)
    stacker.variables.update(_variables)
    stacker.sfunctions.update(_sfunctions)


include_operators = {
    "include": {
        "func": (lambda stacker, filename: include(stacker, filename)),
        "arg_count": 1,
        "push_result_to_stack": False,
        "desc": "Includes another stacker script.",
    },
}
