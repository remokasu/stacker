from __future__ import annotations

from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from stacker.stacker import Stacker

from stacker.data_type import String, stack_data


class StackerFunction:
    """A callable object that represents a function defined in Stacker."""

    def __init__(self, args: list[str], blockstack: Stacker) -> None:
        self.args = args
        self.blockstack = blockstack
        self.arg_count = len(args)

    def __call__(self, *values) -> Any:
        values = list(values)
        if len(values) != len(self.args):
            raise ValueError(f"Expected {len(self.args)} arguments, got {len(values)}")
        # Create a new stack for the function call
        # Bind the arguments to the values
        for arg, value in zip(self.args, values):
            self.blockstack.variables[arg] = value
        self.blockstack.stack.append(self.blockstack)
        result = self.blockstack._pop_and_eval(self.blockstack.stack)
        return result
