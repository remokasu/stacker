from __future__ import annotations

import itertools
from typing import TYPE_CHECKING

from stacker.data_type import Symbol
from stacker.lang.protocols import BLOCK, kind_of

if TYPE_CHECKING:
    from stacker.lang.protocols import Block

GENSYM_PREFIX = "__g"
# Process-wide so names never collide, even across `include`d interpreters.
_gensym_counter = itertools.count(1)


def gensym() -> Symbol:
    """Returns a fresh, unique symbol (the same kind of value as ``:name`` pushes)."""
    return Symbol(f"{GENSYM_PREFIX}{next(_gensym_counter)}")


def template_only(body: object) -> bool:
    """Whether ``body`` is one block literal and nothing else: the form that runs nothing at expansion time."""
    tokens = getattr(body, "tokens", None)
    return isinstance(tokens, list) and len(tokens) == 1 and kind_of(tokens[0]) == BLOCK


class StackerMacro:
    """A macro whose body runs at expansion time: ``{args} {body} :name defmacro``.

    The body runs at expansion time (on its own stack, in a child scope of the
    caller where the arguments are bound) and must leave exactly one value,
    which becomes the expansion. Block literals inside the body have the names
    bound in that scope interpolated when they are pushed.
    """

    def __init__(
        self,
        name: str,
        args: list[str],
        body: Block,
        is_prelude: bool = False,
        defined_at: tuple[str | None, int | None] | None = None,
    ) -> None:
        self.name: str = name
        self.args: list[str] = list(args)
        self.body: Block = body
        self.arg_count: int = len(self.args)
        self.is_prelude: bool = is_prelude
        #: The file and line that defined it (None in the REPL), shown when another file redefines it
        self.defined_at: tuple[str | None, int | None] | None = defined_at
        #: The expansions kept for the arguments they were made from, when the body is one block literal:
        #: such a body runs nothing at expansion time, so its expansion depends on the arguments alone.
        #: Keyed by the arguments' identities; an entry holds the arguments (so the identities stay theirs),
        #: the expansion's tokens and its bracket. None when the body is anything else, or once the macro
        #: gave up keeping them (see the machine's ``MEMO_GIVE_UP``)
        self.expansions: dict[tuple[int, ...], tuple[tuple[object, ...], list[object], str]] | None = (
            {} if template_only(body) else None
        )
        #: How many times a kept expansion was used, and the misses in a row since the last use
        self.memo_hits: int = 0
        self.memo_misses: int = 0

    def __getstate__(self) -> dict[str, object]:
        """A copy starts with no kept expansions: what it keeps is made of its own blocks."""
        state = self.__dict__.copy()
        if state["expansions"] is not None:
            state["expansions"] = {}
        state["memo_hits"] = 0
        state["memo_misses"] = 0
        return state

    def __repr__(self) -> str:
        return f"{{{' '.join(self.args)}}} {self.body}"
