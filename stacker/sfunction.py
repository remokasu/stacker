from __future__ import annotations

from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from stacker.stacker import Stacker

from stacker.data_type import String, stack_data

import copy


class StackerFunction:
    """A callable object that represents a function defined in Stacker."""

    def __init__(self, args: list[str], blockstack: Stacker) -> None:
        self.args = args
        self.blockstack = blockstack
        self.arg_count = len(args)
        self.stack = stack_data()

    def __call__(self, *values) -> Any:
        self.stack.clear()
        values = list(values)
        if len(values) != len(self.args):
            raise ValueError(f"Expected {len(self.args)} arguments, got {len(values)}")
        blockstack = copy.deepcopy(self.blockstack)
        for arg, value in zip(self.args, values):
            blockstack.variables[arg] = value
        self.stack.append(blockstack)
        result = self.blockstack._pop_and_eval(self.stack)
        return result
