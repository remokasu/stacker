# WIP

# class Variable:
#     def __init__(self, value):
#         self.value = value

#     def __repr__(self):
#         return str(self.value)

#     def __add__(self, other):
#         if isinstance(other, Variable):
#             return Variable(self.value + other.value)
#         elif isinstance(other, (int, float)):
#             return Variable(self.value + other)
#         else:
#             raise TypeError("Unsupported operand type for +")

#     def __sub__(self, other):
#         if isinstance(other, Variable):
#             return Variable(self.value - other.value)
#         elif isinstance(other, (int, float)):
#             return Variable(self.value - other)
#         else:
#             raise TypeError("Unsupported operand type for -")

#     def __mul__(self, other):
#         if isinstance(other, Variable):
#             return Variable(self.value * other.value)
#         elif isinstance(other, (int, float)):
#             return Variable(self.value * other)
#         else:
#             raise TypeError("Unsupported operand type for *")

#     def __truediv__(self, other):
#         if isinstance(other, Variable):
#             return Variable(self.value / other.value)
#         elif isinstance(other, (int, float)):
#             return Variable(self.value / other)
#         else:
#             raise TypeError("Unsupported operand type for /")

#     def __eq__(self, other):
#         if isinstance(other, Variable):
#             return self.value == other.value
#         elif isinstance(other, (int, float)):
#             return self.value == other
#         else:
#             return False

#     def __lt__(self, other):
#         if isinstance(other, Variable):
#             return self.value < other.value
#         elif isinstance(other, (int, float)):
#             return self.value < other
#         else:
#             raise TypeError("Unsupported operand type for <")

#     def __gt__(self, other):
#         if isinstance(other, Variable):
#             return self.value > other.value
#         elif isinstance(other, (int, float)):
#             return self.value > other
#         else:
#             raise TypeError("Unsupported operand type for >")

#     def __and__(self, other):
#         if isinstance(other, Variable):
#             return Variable(bool(self.value and other.value))
#         elif isinstance(other, (int, float)):
#             return Variable(bool(self.value and other))
#         else:
#             raise TypeError("Unsupported operand type for and")

#     def __or__(self, other):
#         if isinstance(other, Variable):
#             return Variable(bool(self.value or other.value))
#         elif isinstance(other, (int, float)):
#             return Variable(bool(self.value or other))
#         else:
#             raise TypeError("Unsupported operand type for or")
