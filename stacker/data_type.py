

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