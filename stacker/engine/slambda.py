from __future__ import annotations

from typing import TYPE_CHECKING, Any
from stacker.engine.data_type import stack_data

if TYPE_CHECKING:
    from stacker.engine.core import StackerCore

import copy


class StackerLambda:
    """A callable object that represents a function defined in Stacker."""

    def __init__(self, args: list[str], blockstack: Stacker) -> None:
        self.args = args
        self.blockstack = blockstack
        self.arg_count = len(args)
        self.stack = stack_data()

    def __call__(self, *values) -> Any:
        values = list(values)
        if len(values) != len(self.args):
            raise ValueError(f"Expected {len(self.args)} arguments, got {len(values)}")
        blockstack = copy.deepcopy(self.blockstack)
        for arg, value in zip(self.args, values):
            blockstack.variables[arg] = value
        self.stack.append(blockstack)
        result = self.blockstack._pop_and_eval(self.stack)
        return result

    def __str__(self) -> str:
        if len(self.args) == 0:
            return "λ"
        body_str = self.blockstack.__str__()
        for arg in self.args:
            body_str = body_str.replace(f"'{arg}'", arg)
        if len(self.args) == 1:
            return f"λ{self.args[0]}." + body_str
        else:
            return "λ" + "λ".join(self.args) + "." + body_str

    def __repr__(self) -> str:
        return self.__str__()
