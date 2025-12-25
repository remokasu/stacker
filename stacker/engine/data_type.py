from collections import deque

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
    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def __repr__(self):
        return "VOID"

    def __bool__(self):
        return False


# Singleton instance
VOID = VoidType()


class String(str):
    def __init__(self, value: str):
        self.value = str(value)

    def __str__(self):
        return self.value

    def __add__(self, other: str) -> str:
        return self.value + other

    def __radd__(self, other: str) -> str:
        return other + self.value

    def startswith(self, value: str) -> bool:
        return self.value.startswith(value)

    def endswith(self, value: str) -> bool:
        return self.value.endswith(value)


class UndefinedSymbol(str):
    """Represents an undefined variable symbol.

    This type is used for identifiers that are not yet defined.
    When pushed to the stack, they remain as UndefinedSymbol.
    If an operation tries to use them (e.g., arithmetic), an error is raised.
    They can be consumed by 'set', 'defun', 'defmacro', 'do', 'dolist' as symbol names.
    """

    def __init__(self, name: str):
        self.name = name

    def __str__(self):
        return self.name

    def __repr__(self):
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
