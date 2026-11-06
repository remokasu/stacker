"""What the lower layers know of the engine's values: a kind mark on the class, and the shapes they read.

The engine's classes carry a mark, ``stacker_kind``, as a class attribute;
a value's kind is read from its class with ``kind_of``, so the display, the
type word and the collection words tell a block or a lambda apart without
importing the engine. The protocols name the attributes the language's
values and the value words read of a block and of the running core; they
are for type checking only.
"""

from __future__ import annotations

from typing import Protocol

from stacker.lang.scope import ScopedVariables

#: The class attribute that marks an engine value's kind
KIND_ATTRIBUTE = "stacker_kind"
#: The kinds marked
BLOCK = "block"
LAMBDA = "lambda"


def kind_of(value: object) -> str | None:
    """The kind mark on ``value``'s class (``BLOCK``, ``LAMBDA``), or None for any other value.

    Read from the class, not the instance: a value whose ``__getattr__``
    answers everything (a mock a plugin pushed) has no kind.
    """
    return getattr(type(value), KIND_ATTRIBUTE, None)


class Block(Protocol):
    """A code block value, as a macro holds its body."""

    tokens: list[object]
    bracket_type: str
    variables: ScopedVariables


class WordTables(Protocol):
    """The word tables of an interpreter, as the words that change or list them see them."""

    def words_changed(self) -> None: ...

    def get_groups(self) -> list[tuple[str, str, dict[str, object]]]: ...


class CoreView(Protocol):
    """The running core, as the system and settings words read it: its position, its scope and its tables."""

    parent: CoreView | None
    variables: ScopedVariables
    current_file: str | None
    arguments: list[str]
    main_script: str | None
    sfunctions: dict[str, object]
    macros: dict[str, object]
    plugins: dict[str, object]
    operator_manager: WordTables
    _prelude: dict[str, object]  #: the prelude's bookkeeping (`funcs` marks the words it defined); the core's own name
