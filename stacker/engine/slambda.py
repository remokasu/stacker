from __future__ import annotations

import copy
from typing import TYPE_CHECKING

from stacker.engine import recursion
from stacker.engine.data_type import stack_data

#: Name reported by the recursion guard for anonymous lambdas
LAMBDA_NAME = "<lambda>"

if TYPE_CHECKING:
    from stacker.engine.core import StackerCore


class StackerLambda:
    """A callable object that represents a function defined in Stacker."""

    def __init__(self, args: list[str], blockstack: StackerCore) -> None:
        self.args: list[str] = args
        self.blockstack: StackerCore = blockstack
        self.arg_count: int = len(args)
        self.stack: stack_data[object] = stack_data()

    def __call__(self, *values: object) -> object:
        recursion.enter(LAMBDA_NAME)
        try:
            return self._call_impl(*values)
        finally:
            recursion.leave()

    def _call_impl(self, *values: object) -> object:
        # Parity with StackerFunction: clear the local stack per call so
        # leftover multi-value results cannot accumulate across calls
        self.stack.clear()
        values_list = list(values)
        if len(values_list) != len(self.args):
            raise ValueError(f"Expected {len(self.args)} arguments, got {len(values_list)}")
        # The body keeps the scope it was made in; each call runs in a
        # child of that scope, with its own stack. A block written inside
        # the body is bound to the call's scope when the body pushes it.
        blockstack = copy.copy(self.blockstack)
        blockstack.variables = self.blockstack.variables.create_child_scope()
        blockstack.stack = stack_data()

        for arg, value in zip(self.args, values_list):
            blockstack.variables[arg] = value
        self.stack.append(blockstack)
        result = blockstack._pop_and_eval(self.stack)
        return result

    def __str__(self) -> str:
        if len(self.args) == 0:
            return "λ"
        body_str = self.blockstack.__str__()
        if len(self.args) == 1:
            return f"λ{self.args[0]}." + body_str
        else:
            return "λ" + "λ".join(self.args) + "." + body_str

    def __repr__(self) -> str:
        return self.__str__()
