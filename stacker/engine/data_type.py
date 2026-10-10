from __future__ import annotations

from collections import deque
from functools import total_ordering

# class Operator:
#     def __init__(self, name, func):
#         self.name = name
#         self.func = func

#     def __call__(self, *args):
#         return self.func(*args)

#     def __repr__(self):
#         return f"{self.name}"

#     def __str__(self):
#         return f"{self.name}"


# class Number:
#     def __init__(self, value):
#         self.value = value

#     def __repr__(self):
#         return f"{self.value}"

#     def __str__(self):
#         return f"{self.value}"


# class String:
#     def __init__(self, value):
#         self.value = value

#     def __repr__(self):
#         return f"{self.value}"

#     def __str__(self):
#         return f"{self.value}"


# class Array:
#     def __init__(self, value):
#         self.value = value

#     def __repr__(self):
#         return f"{self.value}"

#     def __str__(self):
#         return f"{self.value}"

#     def __getitem__(self, item):
#         return self.value[item]


# class Tuple:
#     def __init__(self, value):
#         self.value = value

#     def __repr__(self):
#         return f"{self.value}"

#     def __str__(self):
#         return f"{self.value}"

#     def __getitem__(self, item):
#         return self.value[item]


# class BlockStack:
#     def __init__(self):
#         self.stack = []

#     def __repr__(self):
#         return f"{self.stack}"

#     def __str__(self):
#         return f"{self.stack}"

#     def push(self, item):
#         self.stack.append(item)

#     def pop(self):
#         return self.stack.pop()

#     def peek(self):
#         return self.stack[-1]


stack_data = deque
# stack_data = list


class VoidType:
    """
    Sentinel value to indicate a function has no return value.
    Used to distinguish void functions from functions that explicitly return None.
    """
    _instance: VoidType | None = None

    def __new__(cls) -> VoidType:
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def __repr__(self) -> str:
        return "VOID"

    def __bool__(self) -> bool:
        return False


# Singleton instance
VOID = VoidType()


class String(str):
    def __init__(self, value: str) -> None:
        self.value = str(value)

    def __str__(self) -> str:
        return self.value

    def __add__(self, other: str) -> str:
        return self.value + other

    def __radd__(self, other: str) -> str:
        return other + self.value

    def startswith(self, value: str) -> bool:  # type: ignore[override]
        return self.value.startswith(value)

    def endswith(self, value: str) -> bool:  # type: ignore[override]
        return self.value.endswith(value)


@total_ordering
class Symbol:
    """A name as a value.

    ``$x``, a bare name at a name position, ``gensym`` and ``symbol`` push
    one. A symbol is not a ``str``: it never compares equal to a string and
    is never looked up by its text. Two symbols are equal when their names
    are. Instances are immutable and may be shared freely.

    Attributes:
        name: The bare name.
    """

    __slots__ = ("name",)

    def __init__(self, name: str) -> None:
        object.__setattr__(self, "name", name)

    def __setattr__(self, key: str, value: object) -> None:
        raise AttributeError("Symbol is immutable")

    def __delattr__(self, key: str) -> None:
        raise AttributeError("Symbol is immutable")

    def __eq__(self, other: object) -> bool:
        return isinstance(other, Symbol) and other.name == self.name

    def __lt__(self, other: object) -> bool:
        if not isinstance(other, Symbol):
            return NotImplemented
        return self.name < other.name

    def __hash__(self) -> int:
        return hash(self.name)

    def __str__(self) -> str:
        return self.name

    def __repr__(self) -> str:
        return f"Symbol({self.name!r})"

    def __copy__(self) -> Symbol:
        return self

    def __deepcopy__(self, memo: dict[int, object]) -> Symbol:
        return self


class UndefinedSymbol(str):
    """Represents an undefined variable symbol.

    This type is used for identifiers that are not yet defined.
    When pushed to the stack, they remain as UndefinedSymbol.
    If an operation tries to use them (e.g., arithmetic), an error is raised.
    When one reaches a name position (`set`, `=`, `global`, `defun`, `defmacro`,
    `macroexpand`, and the names before the block of `do`, `dolist`, `reduce`,
    `fold`) it is used as that name. Normally a bare name written in such a
    position is already read as a name and never becomes an UndefinedSymbol.
    """

    def __init__(self, name: str) -> None:
        self.name = name

    def __str__(self) -> str:
        return self.name

    def __repr__(self) -> str:
        return f"UndefinedSymbol({self.name!r})"


if __name__ == "__main__":
    s = String("hello")
    assert isinstance(s, str) is True
    assert isinstance(s, String) is True
    assert issubclass(String, str) is True

    s = "world"
    assert isinstance(s, str) is True
    assert isinstance(s, String) is False

    s1 = String("hello")
    s2 = String("world")
    s3 = s1 + s2
    print(s3)
    assert isinstance(s3, str) is True
