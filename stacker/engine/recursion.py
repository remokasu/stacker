"""Process-wide recursion guard for Stacker function calls (ADR-0003).

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
from stacker.lib.config import DEFAULT_RECURSION_LIMIT, MAX_RECURSION_LIMIT

_depth = 0
_limit = DEFAULT_RECURSION_LIMIT


def enter(name: str) -> None:
    """Register entry into a Stacker function call.

    Args:
        name: Function name reported when the limit is exceeded.

    Raises:
        StackerRecursionError: If the call would exceed the limit.
    """
    global _depth
    if _depth >= _limit:
        raise StackerRecursionError(name, _limit)
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


def get_limit() -> int:
    """Return the current maximum Stacker recursion depth."""
    return _limit
