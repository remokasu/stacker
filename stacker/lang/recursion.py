"""Process-wide depth guard for Stacker recursion.

The machine keeps its own return stack, so a Stacker recursion does not
by itself cost the host any call depth: an activation (a call, a block
run by a word, a loop's body, a macro's expansion ...) is an entry on
that stack. The limit bounds the memory those entries take, and what it
buys is the named error: a recursion that never returns is stopped
quickly, as a StackerRecursionError naming the word, instead of growing
until the process has no memory left. ``--recursion-limit 0`` takes the
ceiling away, and only memory then bounds a recursion that stays inside
the machine.

The depth and the limit live at module level rather than per instance
because one process runs every Stacker instance (including child
interpreters created by ``include``), and that memory is shared.

The host's own call depth is spent only where a Python function runs
Stacker code (a wrapper registered over a word, a function called from
Python). The command line sets that depth to HOST_RECURSION_LIMIT, and
a recursion that runs out of it is reported as a StackerRecursionError
too, with the depth it reached.

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

import sys

from stacker.error import StackerRecursionError

#: Default maximum depth of the machine's return stack; overridable per run with --recursion-limit
DEFAULT_RECURSION_LIMIT = 100_000
#: The depth the command line gives the host (the value it has had since 1.12.0; a value's structure is
#: shown to about a third of it before "too deep to show")
HOST_RECURSION_LIMIT = 46_000
#: The limit that means no limit (``--recursion-limit 0``)
NO_LIMIT = 0

_depth = 0  # the depth of the activation running (written by the machine), or of the calls made from Python
_limit = DEFAULT_RECURSION_LIMIT
_asked = DEFAULT_RECURSION_LIMIT  # the limit as set, 0 for none (what get_limit reports)


def _no_arms() -> int:
    """Outside the machine: no arm of `if` is running in place."""
    return 0


#: Set by the machine: the arms of `if` the running activation runs in place, counted in the depth but not in
#: ``_depth`` (a reader adds them, so the machine need not write the depth at each arm)
_arms = _no_arms


def enter(name: str, kind: str = "function") -> None:
    """Registers entry into a Stacker function call made from Python (``StackerFunction.__call__`` and its kin).

    The machine counts its own activations; this is for the calls made
    around it, so that a call made from Python counts as one level.

    Args:
        name: Function or macro name reported when the limit is exceeded.
        kind: ``"function"`` or ``"macro"``; only affects the error message.

    Raises:
        StackerRecursionError: If the call would exceed the limit.
    """
    global _depth
    if _depth + _arms() >= _limit:
        raise StackerRecursionError(name, _asked, kind)
    _depth += 1


def leave() -> None:
    """Registers exit from a call ``enter`` counted (call from finally)."""
    global _depth
    if _depth > 0:
        _depth -= 1


def restore(depth: int) -> None:
    """Puts the depth back to ``depth``, the value a machine run began with.

    Called when a run ends: an exit or an interrupt that left the run
    without taking its activations down one by one is set right here.

    Args:
        depth: The depth to put back.
    """
    global _depth
    _depth = depth


def set_limit(limit: int) -> None:
    """Sets the maximum depth of the machine's return stack for this process.

    Args:
        limit: New limit, 1 or more; ``NO_LIMIT`` (0) for none, when the
            depth is bounded by memory alone.

    Raises:
        ValueError: If the limit is negative.
    """
    global _limit, _asked
    if limit < 0:
        raise ValueError(f"recursion limit must be 0 (no limit) or more, got {limit}")
    _asked = limit
    _limit = sys.maxsize if limit == NO_LIMIT else limit


def get_depth() -> int:
    """Return the depth of the return stack now: the activations on the way, the arms run in place among them."""
    return _depth + _arms()


def get_limit() -> int:
    """Return the current maximum depth as set: 0 when there is none."""
    return _asked
