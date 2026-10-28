"""Process-wide recursion guard for Stacker function calls.

The real resource being guarded is the process's C stack, which is shared
by every Stacker instance (including child interpreters created by
``include``), so both the depth counter and the limit live at module
level rather than per instance.

``enter``/``leave`` are plain functions instead of a context manager on
purpose: they sit on the function-call hot path (recursive workloads call
them once per level), and a generator-based context manager would add
measurable overhead. Callers must pair them with try/finally:

    recursion.enter(self.name)
    try:
        ...
    finally:
        recursion.leave()

``enter`` checks before incrementing, so a rejected call never needs an
unwind and the counter cannot leak on the error path.
"""

from __future__ import annotations

from stacker.error import StackerRecursionError

# Measured on CPython 3.13: the engine's true recursion ceiling is the
# interpreter's C-recursion protection (independent of
# sys.setrecursionlimit), which stops this engine's call chain at 2000
# Stacker levels with a plain RecursionError. The limits below stay under
# that ceiling so the guard's named StackerRecursionError always fires
# first for a function body without nested blocks. Blocks nested inside
# a function (if, ifelse, while, ...) cost host depth of their own, so a
# deeply nested body reaches the host's limit before the guard does; a
# function call then reports it as a StackerRecursionError that names
# the function and the depth reached.
#
# Default maximum Stacker-level recursion depth for user-defined
# functions and lambdas; overridable per run with --recursion-limit
DEFAULT_RECURSION_LIMIT = 1500
# Hard cap for --recursion-limit; larger values are rejected (kept 10%
# below the measured C-recursion ceiling of 2000)
MAX_RECURSION_LIMIT = 1800
# Upper bound of measured Python frames per Stacker recursion level;
# sizes the sys.setrecursionlimit backstop for non-function recursion
RECURSION_FRAMES_PER_LEVEL = 20
# Headroom on top of the backstop for engine base frames and operators
RECURSION_BACKSTOP_MARGIN = 10_000

_depth = 0
_limit = DEFAULT_RECURSION_LIMIT


def enter(name: str, kind: str = "function") -> None:
    """Register entry into a Stacker function call or macro expansion.

    Args:
        name: Function or macro name reported when the limit is exceeded.
        kind: ``"function"`` or ``"macro"``; only affects the error message.

    Raises:
        StackerRecursionError: If the call would exceed the limit.
    """
    global _depth
    if _depth >= _limit:
        raise StackerRecursionError(name, _limit, kind)
    _depth += 1


def leave() -> None:
    """Register exit from a Stacker function call (call from finally)."""
    global _depth
    if _depth > 0:
        _depth -= 1


def set_limit(limit: int) -> None:
    """Set the maximum Stacker recursion depth for this process.

    Args:
        limit: New limit; must be between 1 and MAX_RECURSION_LIMIT.

    Raises:
        ValueError: If the limit is out of range.
    """
    global _limit
    if not 1 <= limit <= MAX_RECURSION_LIMIT:
        raise ValueError(
            f"recursion limit must be between 1 and {MAX_RECURSION_LIMIT}, "
            f"got {limit}"
        )
    _limit = limit


def get_depth() -> int:
    """Return the number of Stacker function calls currently on the way."""
    return _depth


def get_limit() -> int:
    """Return the current maximum Stacker recursion depth."""
    return _limit
