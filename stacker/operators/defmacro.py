from __future__ import annotations

from typing import TYPE_CHECKING

from stacker.engine.smacro import StackerMacro

if TYPE_CHECKING:
    from stacker.stacker import Stacker


def define_macro(stacker: Stacker, name: str, args: list[str], body: Stacker) -> None:
    """Registers a Lisp-style macro on ``stacker``.

    Args:
        stacker: Interpreter the macro is defined in.
        name: Macro name.
        args: Argument names, bound in the expansion scope.
        body: Code block run at expansion time.
    """
    macro = StackerMacro(name, args, body, is_prelude=stacker._prelude["loading"])
    stacker.register_macro(name, macro)


macro_operators = {
    "defmacro": {
        "func": (lambda stacker, name, args, body: define_macro(stacker, name, args, body)),
        "arg_count": 3,
        "push_result_to_stack": False,
        "desc": "Defines a macro: {args} {body} :name defmacro",
    },
}
