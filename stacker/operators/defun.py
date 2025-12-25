from __future__ import annotations

from typing import TYPE_CHECKING
from stacker.engine.sfunction import StackerFunction


if TYPE_CHECKING:
    from stacker.stacker import Stacker


def defun_sfunction(
    stacker: Stacker, func_name: str, fargs: list, body: Stacker
) -> None:
    function = StackerFunction(fargs, body)
    args_count = len(fargs)
    stacker.register_sfunction(
        func_name, function, args_count, push_result_to_stack=True
    )


defun_operators = {
    "defun": {
        "func": (
            lambda stacker, func_name, fargs, body: defun_sfunction(
                stacker, func_name, fargs, body
            )
        ),
        "arg_count": 3,
        "push_result_to_stack": False,
        "desc": "Defines a function.",
    },
}
