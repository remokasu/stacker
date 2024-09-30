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
