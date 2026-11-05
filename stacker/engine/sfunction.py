from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from stacker.engine.core import StackerCore

from stacker.data_type import stack_data
from stacker.engine import copier
from stacker.error import StackerRecursionError, StackerTypeError
from stacker.lang import recursion


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
        """Calls the function (``run`` does the work; this is for callers outside the interpreter).

        Args:
            *values: The arguments, in parameter order.

        Returns:
            Every value the body left on its stack, bottom first.
        """
        return self.run(list(values))

    def run(self, values_list: list[object]) -> list[object]:
        """Calls the function with the arguments in ``values_list``.

        A plain method, so the interpreter calls it without re-entering
        the host's call machinery (which is what bounds how deep a
        recursion can go, not the frames themselves).

        Args:
            values_list: The arguments, in parameter order.

        Returns:
            Every value the body left on its stack, bottom first (an empty
            list when it left nothing).
        """
        recursion.enter(self.name)
        try:
            if len(values_list) != len(self.args):
                raise StackerTypeError(f"The function `{self.name}` takes {len(self.args)} arguments, got {len(values_list)}")

            # The body is shared by every call: a shallow copy carries this
            # call's own scope and stack. A block written inside the body is
            # bound to this scope when the body pushes it (StackerCore._evaluate),
            # so a lambda made here keeps this call's variables.
            new_blockstack = copier.shallow_copy(self.blockstack)
            # The arguments are the new scope's names from its birth
            new_blockstack.variables = self.blockstack.variables.create_child_scope(
                dict(zip(self.args, values_list))
            )
            new_blockstack.stack = stack_data()  # Each call needs its own stack
            new_blockstack._evaluate(new_blockstack.tokens, stack=new_blockstack.stack)
            return list(new_blockstack.stack)

        except RecursionError:
            # The host ran out of call depth before the guard did; the innermost
            # call reports it, by name, so `try` sees the usual kind
            raise StackerRecursionError(self.name, recursion.get_limit(), depth=recursion.get_depth()) from None
        finally:
            recursion.leave()

