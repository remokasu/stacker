"""Shallow copies of an interpreter core, made the way this host runs fastest.

A block runs as a shallow copy of its core (``StackerCore._bound_to``), and
so does every call of a function or a lambda. ``shallow_copy`` is one of
two ways of making that copy, chosen when this module is imported (see
``prefers_generated_copier`` for what was measured where):

- the dictionary update, ``object.__new__(cls)`` then ``__dict__.update``:
  one call into the host, the way the interpreter always copied
- a generated copier, a function of one ``dst.name = src.name`` line per
  attribute: ordinary code, which a tracing JIT follows and inlines (on
  PyPy the update was the one call the JIT could not look into, paid for
  every block and every call). One copier is generated per class and
  attribute count, from the names of the first instance of that shape it
  sees (the root core has one attribute more than its children); an
  instance with as many attributes under other names, or with a name that
  cannot be written in source, is copied by the dictionary update

Both make the same copy: the new instance shares every attribute's object
with the original, and the caller gives it a scope and a stack of its own.
Only the order of the copy's attributes can differ (a copier writes them in
the order of its shape's first instance), and nothing reads that order. A
subclass's own ``__copy__`` is not consulted.
"""

from __future__ import annotations

import keyword
import sys
from collections.abc import Callable
from typing import TypeVar

Core = TypeVar("Core")
Copier = Callable[[object, object], None]

#: class -> attribute count -> its copier, or None when a name cannot be written in source
_copiers: dict[type, dict[int, Copier | None]] = {}
#: marks a shape not seen yet, as distinct from one whose copier is None
_UNSEEN = object()
#: The CPython version from which the generated copier measured faster than the dictionary update
GENERATED_FROM = (3, 13)


def _writable(name: object, cls: type) -> bool:
    """Whether ``dst.<name> = src.<name>`` in the generated source reads and writes just that attribute.

    Args:
        name: A key of an instance's ``__dict__``.
        cls: The class of that instance.

    Returns:
        True for a plain ASCII identifier (the compiler would fold any other
        spelling into one) that is not a keyword, not a dunder (``__dict__``
        is a descriptor, ``__debug__`` cannot be assigned) and not a name
        the class has, which the copy would read in place of a missing
        attribute.
    """
    return (
        type(name) is str
        and name.isascii()
        and name.isidentifier()
        and not keyword.iskeyword(name)
        and not (name.startswith("__") and name.endswith("__"))
        and not hasattr(cls, name)
    )


def _generate(cls: type, names: tuple[object, ...]) -> Copier | None:
    """A function assigning every attribute in ``names`` from ``src`` to ``dst``, or None.

    Only names that are plain attributes of ``cls``'s instances are written
    into the generated source: an instance with any other attribute name
    (``setattr(core, "a b", 1)``) is copied by the dictionary update instead.

    Args:
        cls: The class of the instances of this shape.
        names: The attribute names of one shape of instance.

    Returns:
        The copier, or None when a name cannot be written.
    """
    if not all(_writable(name, cls) for name in names):
        return None
    body = "".join(f"    dst.{name} = src.{name}\n" for name in names) or "    pass\n"
    code = compile(f"def copy_attributes(src, dst):\n{body}", f"<shallow copier of {cls.__name__}>", "exec")
    namespace: dict[str, object] = {}
    exec(code, namespace)  # noqa: S102  the source is made of attribute names checked above, nothing else
    return namespace["copy_attributes"]  # type: ignore[return-value]


def by_generated_copier(core: Core) -> Core:
    """The shallow copy of ``core`` by the copier of its shape, or by the dictionary update when it has none.

    Args:
        core: The interpreter core to copy.

    Returns:
        The shallow copy; nothing here keeps a reference to it.
    """
    cls = type(core)
    attributes = core.__dict__
    shapes = _copiers.get(cls)
    if shapes is None:
        shapes = _copiers[cls] = {}
    copier = shapes.get(len(attributes), _UNSEEN)
    if copier is _UNSEEN:
        copier = shapes[len(attributes)] = _generate(cls, tuple(attributes))
    new = object.__new__(cls)
    if copier is not None:
        try:
            copier(core, new)
            return new
        except AttributeError:
            # the same number of attributes under other names: the copier
            # stopped at one this instance lacks, so it is copied the slow way
            new = object.__new__(cls)
    new.__dict__.update(attributes)
    return new


def by_dictionary_update(core: Core) -> Core:
    """The shallow copy of ``core`` by one dictionary update.

    Args:
        core: The interpreter core to copy.

    Returns:
        The shallow copy; nothing here keeps a reference to it.
    """
    new = object.__new__(type(core))
    new.__dict__.update(core.__dict__)
    return new


def prefers_generated_copier(implementation: str, version: tuple[int, ...], gil_enabled: bool) -> bool:
    """Whether a host of this kind copies a core faster by the generated copier than by the dictionary update.

    Measured with loops, recursion, macros and calls against the copy of
    1.28.1: PyPy 3.11 ran five to sixteen times faster
    by the generated copier; CPython 3.13 ran function calls a quarter
    faster and nothing slower; CPython 3.10 ran code that binds a block on
    every iteration a tenth slower, so CPython before ``GENERATED_FROM``
    keeps the dictionary update. A build without the global interpreter
    lock was not measured and keeps it too.

    Args:
        implementation: ``sys.implementation.name``.
        version: ``sys.version_info``, or its leading numbers.
        gil_enabled: Whether the build has the global interpreter lock.

    Returns:
        True to copy by the generated copier.
    """
    if implementation == "pypy":
        return True
    return gil_enabled and tuple(version[:2]) >= GENERATED_FROM


_GENERATED = prefers_generated_copier(
    sys.implementation.name, sys.version_info, getattr(sys, "_is_gil_enabled", lambda: True)()
)
#: The way this host copies a core (see prefers_generated_copier); the engine calls it through this name
shallow_copy = by_generated_copier if _GENERATED else by_dictionary_update
