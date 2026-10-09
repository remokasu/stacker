from __future__ import annotations
from pathlib import Path

from stacker.include import include_stacker_script

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from stacker.stacker import Stacker


def include(stacker: Stacker, filename: str) -> None:
    """Includes another stacker script.

    Relative paths resolve against the including file's directory first,
    then the current working directory. REPL and ``-e`` have
    no file context and fall back to cwd-only resolution.
    """
    current_file = stacker.current_file
    base_dir = Path(current_file).parent if current_file else None
    _stacker = include_stacker_script(
        filename, base_dir=base_dir, prelude=stacker._prelude["enabled"]
    )
    # The child loaded its own copy of the prelude. Those definitions must
    # not overwrite the parent's (the user may have redefined a prelude
    # word); only what the included file itself defined is merged.
    prelude_objects = _stacker._prelude["objects"]

    def user_defined(items: dict[str, object]) -> dict[str, object]:
        return {
            name: value
            for name, value in items.items()
            if prelude_objects.get(name) is not value
        }

    stacker.macros.update(user_defined(_stacker.get_macros_ref()))
    stacker.variables.update(user_defined(_stacker.get_variables_copy()))
    stacker.sfunctions.update(user_defined(_stacker.get_sfuntions_ref()))


include_operators = {
    "include": {
        "func": (lambda stacker, filename: include(stacker, filename)),
        "arg_count": 1,
        "push_result_to_stack": False,
        "desc": "Includes another stacker script.",
    },
}
