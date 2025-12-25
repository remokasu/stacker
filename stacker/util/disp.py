from __future__ import annotations


from stacker.util import colored
from stacker.engine.data_type import String

from typing import Any


class CustomPrinter:
    def __init__(self, value: Any, color: str):
        self.value = value
        self.color = color

    def __str__(self):
        return colored(str(self.value), self.color)

    def __repr__(self):
        return str(self.value)


class CustomIntPrinter(CustomPrinter):
    def __init__(self, value: int, color: str):
        self.value = value
        self.color = color


class CustomFloatPrinter(CustomPrinter):
    def __init__(self, value: float, color: str):
        self.value = value
        self.color = color


class CustromComplexPrinter(CustomPrinter):
    def __init__(self, value: complex, color: str):
        self.value = value
        self.color = color


class CustomStrPrinter(CustomPrinter):
    def __init__(self, value: str, color: str):
        self.value = value
        self.color = color


class CustomBoolPrinter(CustomPrinter):
    def __init__(self, value: bool, color: str):
        self.value = value
        self.color = color

    def __str__(self):
        return colored(str(self.value).lower(), self.color)

    def __repr__(self):
        return str(self.value).lower()


class CustomListPrinter(CustomPrinter):
    def __init__(self, value: list, color: str):
        # self.value = [custom_print(item) for item in value]
        self.value = value
        self.color = color

    def __str__(self):
        _temp = list(map(custom_print, self.value))
        return colored(str(_temp).replace(",", ""), self.color)

    def __repr__(self):
        return str(self.value).replace(",", "")


# REMOVED: CustomTuplePrinter - () now creates code blocks, not tuples
# Tuples are no longer a primary data type in Stacker


class OperatorPrinter(CustomPrinter):
    def __init__(self, value: Any, color: str):
        self.value = value
        self.color = color

    def __str__(self):
        return colored(str(self.value), self.color)

    def __repr__(self):
        return str(self.value)


class CustomBlockPrinter(CustomPrinter):
    def __init__(self, value: Any, color: str):
        self.value = value
        self.color = color

    def __str__(self):
        return colored(str(self.value), self.color)

    def __repr__(self):
        return str(self.value)


class CustomStringPrinter(CustomPrinter):
    def __init__(self, value: Any, color: str):
        self.value = value
        self.color = color

    def __str__(self):
        return colored("'" + str(self.value) + "'", self.color)

    def __repr__(self):
        return self.__str__()


class CutomCallablePrinter(CustomPrinter):
    def __init__(self, value: Any, color: str):
        self.value = value
        self.color = color

    def __str__(self):
        return colored(str(self.value), self.color)

    def __repr__(self):
        return str(self.value)


color_map = {
    "int": "default",
    "float": "default",
    "complex": "default",
    "str": "default",  # variable symbol
    "String": "lightgreen",
    "bool": "lightblue",
    "list": "red",
    # "tuple": "red",  # REMOVED: Tuples no longer supported
    "block": "cyan",
    "callable": "yellow",
}


def custom_print(value: Any) -> CustomPrinter:
    from stacker.stacker import Stacker

    if isinstance(value, bool):
        return CustomBoolPrinter(value, color_map["bool"])
    if isinstance(value, int):
        return CustomIntPrinter(value, color_map["int"])
    if isinstance(value, float):
        return CustomFloatPrinter(value, color_map["float"])
    if isinstance(value, complex):
        return CustromComplexPrinter(value, color_map["complex"])
    if isinstance(value, String):
        return CustomStringPrinter(value, color_map["String"])
    if isinstance(value, str):
        return CustomStrPrinter(value, color_map["str"])
    if isinstance(value, list):
        return CustomListPrinter(value, color_map["list"])
    # REMOVED: tuple handling - () now creates code blocks
    if isinstance(value, Stacker):
        return CustomBlockPrinter(value, color_map["block"])
    if callable(value):
        return CutomCallablePrinter(value, color_map["callable"])
    return value


def disp_colored(stack_list: list) -> str:
    stack_str = colored("[", "yellow")
    for item in stack_list:
        stack_str += str(custom_print(item))
        stack_str += " "
    stack_str = stack_str[0:-1]
    stack_str += colored("]", "yellow")
    return stack_str


def disp_default(stack_list: list) -> str:
    return f"{stack_list}".replace(",", "")


def disp_stack(stack_list, colored: bool = False):
    if colored:
        print(disp_colored(stack_list))
    else:
        print(disp_default(stack_list))
