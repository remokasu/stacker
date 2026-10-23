from __future__ import annotations

import copy
from typing import TYPE_CHECKING

from stacker.engine import recursion
from stacker.engine.data_type import stack_data
from stacker.error import StackerRecursionError, StackerTypeError

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

    def __call__(self, *values: object) -> list[object]:
        """Calls the lambda (``run`` does the work; this is for callers outside the interpreter).

        Args:
            *values: The arguments, in parameter order.

        Returns:
            Every value the body left on its stack, bottom first.
        """
        return self.run(list(values))

    def run(self, values_list: list[object]) -> list[object]:
        """Calls the lambda with the arguments in ``values_list``.

        A plain method, so the interpreter calls it without re-entering
        the host's call machinery (which is what bounds how deep a
        recursion can go, not the frames themselves).

        Args:
            values_list: The arguments, in parameter order.

        Returns:
            Every value the body left on its stack, bottom first (an empty
            list when it left nothing).
        """
        recursion.enter(LAMBDA_NAME)
        try:
            if len(values_list) != len(self.args):
                raise StackerTypeError(f"The lambda takes {len(self.args)} arguments, got {len(values_list)}")
            # The body keeps the scope it was made in; each call runs in a
            # child of that scope, with its own stack. A block written inside
            # the body is bound to the call's scope when the body pushes it.
            blockstack = copy.copy(self.blockstack)
            blockstack.variables = self.blockstack.variables.create_child_scope()
            blockstack.stack = stack_data()

            for arg, value in zip(self.args, values_list):
                blockstack.variables[arg] = value
            blockstack._evaluate(blockstack.tokens, stack=blockstack.stack)
            return list(blockstack.stack)


        except RecursionError:
            # The host ran out of call depth before the guard did; the innermost
            # call reports it, by name, so `try` sees the usual kind
            raise StackerRecursionError(LAMBDA_NAME, recursion.get_limit(), depth=recursion.get_depth()) from None
        finally:
            recursion.leave()

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
