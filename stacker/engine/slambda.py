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
        # Use shallow copy with child scope instead of deepcopy
        # This preserves variable scope chain for nested code blocks
        blockstack = copy.copy(self.blockstack)
        blockstack.variables = self.blockstack.variables.create_child_scope()
        blockstack.stack = stack_data()

        # Update nested StackerCore instances to use the new variable scope
        self._update_nested_variables(blockstack.tokens, blockstack.variables)

        for arg, value in zip(self.args, values):
            blockstack.variables[arg] = value
        self.stack.append(blockstack)
        result = blockstack._pop_and_eval(self.stack)
        return result

    def _update_nested_variables(self, tokens, new_variables):
        """Recursively update variable references in nested StackerCore instances."""
        from stacker.engine.core import StackerCore
        for token in tokens:
            if isinstance(token, StackerCore):
                token.variables = new_variables
                # Recursively update nested code blocks
                self._update_nested_variables(token.tokens, new_variables)

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
