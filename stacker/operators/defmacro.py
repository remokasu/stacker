from __future__ import annotations

from typing import TYPE_CHECKING

from stacker.engine.smacro import StackerMacro

if TYPE_CHECKING:
    from stacker.stacker import Stacker


def define_macro(stacker: Stacker, name: str, body: Stacker) -> None:
    """Defines a macro."""
    macro = StackerMacro(name, body)
    stacker.register_macro(name, macro)


macro_operators = {
    "defmacro": {
        "func": (lambda stacker, name, body: define_macro(stacker, name, body)),
        "arg_count": 2,
        "push_result_to_stack": False,
        "desc": "Defines a macro.",
    },
}
