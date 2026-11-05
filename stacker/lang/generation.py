"""A counter that tells a compiled block when a scope it may run in has changed shape.

A compiled block resolves each of its names once and keeps the result: a
macro, a variable, a word, a literal, an undefined name. Two things can
make a result stale. A word table of the interpreter changing (a macro,
function or plugin defined or removed, an operator replaced) is counted by
that interpreter's ``OperatorManager.generation``. The other is counted
here, for the whole process: ``bindings`` advances whenever a scope that
already existed gains or loses a name (a new variable, a deleted one),
because a name resolved as a word may be a variable now that hides it.

A scope born with its names (a call's arguments, a loop variable, given
to the constructor) does not count: a block looks at the scopes it runs
in when it starts (a loop body, run again in a scope of the same shape,
skips that look after its first iteration: ``stacker.engine.inline``).
A name set in such a scope later does count, so a
function that sets a local advances the counter on every call; the
block that called it then looks at its scopes again, which is cheap.

``epoch`` advances on either kind of change, for every interpreter in the
process: a compiled block compares it once after each word it runs, and
looks at the two counters above only when it moved.

Read the counters as ``generation.bindings`` and ``generation.epoch``,
through the module: a name imported from it is a copy of the value at
import time. The counters are advanced with ``+= 1`` and, like the
recursion depth in ``recursion``, assume one thread runs the interpreter.
"""

bindings = 0
epoch = 0


def bindings_changed() -> None:
    """Records that an existing scope gained or lost a name."""
    global bindings, epoch
    bindings += 1
    epoch += 1


def words_changed() -> None:
    """Records that a word table of some interpreter changed.

    Called by ``OperatorManager.words_changed``, which also counts the
    change in that interpreter's own ``generation``; nothing else calls it.
    """
    global epoch
    epoch += 1
