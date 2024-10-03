from __future__ import annotations

from typing import TYPE_CHECKING
from stacker.slambda import StackerLambda


if TYPE_CHECKING:
    from stacker.stacker import Stacker


def _lambda(stacker: Stacker, fargs: list, body: Stacker) -> None:
    return StackerLambda(fargs, body)


lambda_operators = {
    "lambda": {
        "func": lambda fargs, body: StackerLambda(fargs, body),
        "arg_count": 2,
        "push_result_to_stack": True,
        "desc": "Defines a function.",
    },
}
