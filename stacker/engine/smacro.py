from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from stacker.stacker import Stacker


class StackerMacro:
    """A callable object that represents a macro defined in Stacker."""

    def __init__(self, name: str, blockstack: Stacker) -> None:
        self.name = name
        self.blockstack = blockstack
        self.arg_count = 0

    def __call__(self) -> Stacker:
        return self.blockstack
