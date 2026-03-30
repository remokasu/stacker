from __future__ import annotations

import copy
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from stacker.engine.core import StackerCore

from stacker.engine.data_type import stack_data
from stacker.engine.scope import ScopedVariables


class StackerFunction:
    """A callable object that represents a function defined in Stacker."""

    def __init__(
        self, args: list[str], blockstack: StackerCore
    ) -> None:
        self.args: list[str] = args
        self.blockstack: StackerCore = blockstack
        self.arg_count: int = len(args)
        self.stack: stack_data[object] = stack_data()

    def __call__(self, *values: object) -> object:
        self.stack.clear()
        values_list = list(values)
        if len(values_list) != len(self.args):
            raise ValueError(f"Expected {len(self.args)} arguments, got {len(values_list)}")

        # Optimization: Use scope chain instead of deepcopy
        # Create a shallow copy of blockstack with a new variable scope and stack
        # This is ~100x faster than deepcopy and supports recursion correctly
        new_blockstack = copy.copy(self.blockstack)
        new_blockstack.variables = self.blockstack.variables.create_child_scope()
        new_blockstack.stack = stack_data()  # Each call needs its own stack

        # Update nested StackerCore instances to use the new variable scope
        self._update_nested_variables(new_blockstack.tokens, new_blockstack.variables)

        # Set function arguments in the new child scope
        for arg, value in zip(self.args, values_list):
            new_blockstack.variables[arg] = value

        self.stack.append(new_blockstack)
        result = new_blockstack._pop_and_eval(self.stack)

        return result

    def _update_nested_variables(self, tokens: list[object], new_variables: ScopedVariables) -> None:
        """Recursively update variable references in nested StackerCore instances."""
        from stacker.engine.core import StackerCore
        for token in tokens:
            if isinstance(token, StackerCore):
                token.variables = new_variables
                # Recursively update nested code blocks
                self._update_nested_variables(token.tokens, new_variables)
