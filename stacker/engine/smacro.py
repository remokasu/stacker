from __future__ import annotations

import itertools
from typing import TYPE_CHECKING

from stacker.engine.data_type import Symbol

if TYPE_CHECKING:
    from stacker.stacker import Stacker

GENSYM_PREFIX = "__g"
# Process-wide so names never collide, even across `include`d interpreters.
_gensym_counter = itertools.count(1)


def gensym() -> Symbol:
    """Returns a fresh, unique symbol (the same kind of value as ``$name`` pushes)."""
    return Symbol(f"{GENSYM_PREFIX}{next(_gensym_counter)}")


class StackerMacro:
    """A Lisp-style macro: ``{args} {body} name defmacro``.

    The body runs at expansion time (on its own stack, in a child scope of the
    caller where the arguments are bound) and must leave exactly one value,
    which becomes the expansion. Block literals inside the body have the names
    bound in that scope interpolated when they are pushed.
    """

    def __init__(self, name: str, args: list[str], body: Stacker, is_prelude: bool = False) -> None:
        self.name: str = name
        self.args: list[str] = list(args)
        self.body: Stacker = body
        self.arg_count: int = len(self.args)
        self.is_prelude: bool = is_prelude

    def __repr__(self) -> str:
        return f"{{{' '.join(self.args)}}} {self.body}"
