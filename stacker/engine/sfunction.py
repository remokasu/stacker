from __future__ import annotations

import copy
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from stacker.engine.core import StackerCore

from stacker.engine import recursion
from stacker.engine.data_type import stack_data


class StackerFunction:
    """A callable object that represents a function defined in Stacker."""

    def __init__(
        self, args: list[str], blockstack: StackerCore, name: str = "<anonymous>"
    ) -> None:
        self.args: list[str] = args
        self.blockstack: StackerCore = blockstack
        self.arg_count: int = len(args)
        self.name: str = name

    def __call__(self, *values: object) -> list[object]:
        """Calls the function.

        Args:
            *values: The arguments, in parameter order.

        Returns:
            Every value the body left on its stack, bottom first (an empty
            list when it left nothing).
        """
        recursion.enter(self.name)
        try:
            return self._call_impl(*values)
        finally:
            recursion.leave()

    def _call_impl(self, *values: object) -> list[object]:
        values_list = list(values)
        if len(values_list) != len(self.args):
            raise ValueError(f"Expected {len(self.args)} arguments, got {len(values_list)}")

        # The body is shared by every call: a shallow copy carries this
        # call's own scope and stack. A block written inside the body is
        # bound to this scope when the body pushes it (StackerCore._evaluate),
        # so a lambda made here keeps this call's variables.
        new_blockstack = copy.copy(self.blockstack)
        new_blockstack.variables = self.blockstack.variables.create_child_scope()
        new_blockstack.stack = stack_data()  # Each call needs its own stack

        # Set function arguments in the new child scope
        for arg, value in zip(self.args, values_list):
            new_blockstack.variables[arg] = value

        new_blockstack._evaluate(new_blockstack.tokens, stack=new_blockstack.stack)
        return list(new_blockstack.stack)
