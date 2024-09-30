from __future__ import annotations

from pathlib import Path

from prompt_toolkit.completion import WordCompleter

from stacker.include.stk_file_read import readtxt
from stacker.stacker import Stacker
from stacker.syntax.parser import (
    is_array_balanced,
    is_brace_balanced,
    is_tuple_balanced,
    remove_start_end_quotes,
)
from stacker.util import colored

# from stacker.syntax.parser import is_string
from stacker.data_type import String
from typing import Any

# def simple_format(arr):
#     """
#     Format the specified list as a simple string.
#     Example:
#         [[2.999999999999992, -1.9999999999999942], [1.9999999999999947, -0.9999999999999964]]
#         -> [[3.0000, -2.0000], [2.0000, -1.0000]]
#     """

#     def format_number(x):
#         if isinstance(x, int):
#             return str(x)
#         if isinstance(x, str):
#             return x
#         if isinstance(x, bool):
#             return str(x).lower()
#         return f"{x:.4f}"

#     def format_recursive(item):
#         if not isinstance(item, list):
#             return format_number(item)
#         elif isinstance(item, list):
#             return [format_recursive(subitem) for subitem in item]
#         elif isinstance(item, tuple):
#             return tuple(format_recursive(subitem) for subitem in item)
#         else:
#             return item
#         # else:
#         #     formatted_items = [format_recursive(subitem) for subitem in item]
#         #     return "[" + " ".join(formatted_items) + "]"

#     return format_recursive(arr)


class ExecutionMode:
    def __init__(self, rpn_calculator: Stacker):
        self.rpn_calculator = rpn_calculator
        self.color_print = True
        self.debug = False
        self.receved_word = [
            "help",
            "about",
            # "delete_history",
            "vars",
        ]
        self.completer = WordCompleter(self.get_completer())

    def get_completer(self):
        # _reserved_word = copy.deepcopy(self.rpn_calculator.reserved_word)
        _reserved_word = list(self.receved_word)
        _operator_key = list(self.rpn_calculator.get_all_keys_for_completer())
        _priority_operators_key = list(
            self.rpn_calculator.get_priority_operators_ref().keys()
        )
        # _setting_key = list(self.rpn_calculator.get_settings_operators_ref().keys())
        _sfunctions_key = list(self.rpn_calculator.get_sfuntions_ref().keys())
        _variable_key = list(self.rpn_calculator.get_variables_ref().keys())
        _macro_key = list(self.rpn_calculator.get_macros_ref().keys())
        _reserved_word = list(
            set(
                _reserved_word
                + _operator_key
                + _priority_operators_key
                # + _setting_key
                + _sfunctions_key
                + _variable_key
                + _macro_key
            )
        )
        return _reserved_word

    def debug_mode(self):
        self.debug = True

    def get_multiline_input(self, prompt="") -> str:
        lines = []
        while True:
            line = input(prompt)
            if line.endswith("\\"):
                line = line[:-1]  # remove trailing backslash
                lines.append(line)
                prompt = ""  # no prompt for subsequent lines
            else:
                lines.append(line)
                break
        return "\n".join(lines)

    def run(self):
        raise NotImplementedError("Subclasses must implement the 'run' method")

    def print_colored_output(self, stack_list: list) -> str:
        stack_str = colored("[", "yellow")
        for item in stack_list:
            stack_str += str(custom_print(item))
            stack_str += " "
            # item_str = str(item)
            # item_str.replace("\n", " ")
            # if item_str.startswith("[") or item_str.endswith("]"):
            #     stack_str += colored(item_str, "red")
            #     stack_str += " "
            # elif item_str.startswith("(") or item_str.endswith(")"):
            #     stack_str += colored(item_str, "green")
            #     stack_str += " "
            # elif item_str.startswith("{") or item_str.endswith("}"):
            #     stack_str += colored(item_str, "cyan")
            #     stack_str += " "
            # elif item_str.replace(".", "", 1).isdigit() or (
            #     item_str.startswith("-") and item_str[1:].replace(".", "", 1).isdigit()
            # ):
            #     stack_str += colored(item_str, "default")
            #     stack_str += " "
            # elif item_str in list(self.rpn_calculator.get_variables_ref()):
            #     stack_str += colored(item_str, "lightblue")
            #     stack_str += " "
            # elif isinstance(item_str, str):
            #     # stack_str += colored(f"'{item_str}'", 'default')
            #     #
            #     # if len(item_str) > 20:
            #     #     item_str = item_str[0:10] + "..."
            #     if not is_string(item_str):
            #         item_str = f"'{item_str}'"
            #     else:
            #         item_str = f"'{item_str[1:-1]}'"
            #     stack_str += colored(item_str, "green")
            #     stack_str += " "
            # else:
            #     stack_str += colored(item_str, "default")
            #     stack_str += " "
        stack_str = stack_str[0:-2]
        stack_str += colored("]", "yellow")
        return stack_str

    def disp_stack(self) -> None:
        """Print the current stack to the console."""
        _stack = self.rpn_calculator.get_stack_copy_as_list()
        # stack = []
        # for token in _stack:
        #     if isinstance(token, Stacker):
        #         stack.append(str(token))
        #     elif isinstance(token, list):
        #         # stack.append(f"{simple_format(token)}".replace(",", ""))
        #         token = list(map(self._bool_to_str, token))
        #         stack.append(f"{token}".replace(",", ""))
        #     elif isinstance(token, tuple):
        #         stack.append(f"{token}".replace(",", ""))
        #     elif isinstance(token, bool):
        #         stack.append(str(token).lower())
        #     else:
        #         # try:
        #         #     stack.append(simple_format(token))
        #         # except Exception:
        #         #     stack.append(token)
        #         stack.append(token)
        if self.color_print is True:
            stack_str = self.print_colored_output(_stack)
            print(stack_str)
        else:
            print(f"{_stack}".replace(",", ""))

    def _bool_to_str(self, value: bool) -> str:
        if isinstance(value, bool):
            return CustomBoolPrinter(value, "lightblue")
        return value

    def disp_all_valiables(self) -> None:
        variables = self.rpn_calculator.get_variables_copy()
        for key in variables.keys():
            print(f"{key} = {variables[key]}")

    def disp_ans(self) -> None:
        _stack = self.rpn_calculator.get_stack_copy_as_list()
        if len(_stack) == 0:
            return
        print(f"{_stack[-1]}")
        # ans = _stack[-1]
        # if isinstance(ans, list):
        #     print(f"ans = \n    {simple_format(ans)}")
        # elif isinstance(ans, Stacker):
        #     pass
        # else:
        #     print(f"ans = {simple_format(ans)}")

    def execute_stacker_dotfile(self, filename: str | Path) -> None:
        """Import a stacker script and return the stacker object."""
        path = Path(remove_start_end_quotes(str(filename)))
        code = readtxt(path)
        expression = ""
        for line in code.splitlines():
            line = line.strip()
            expression += line + " "
            if self._is_balanced(expression):
                if expression[-2:] in {";]", ";)"}:
                    closer = expression[-1]
                    expression = expression[:-2] + closer
                self.rpn_calculator.process_expression(expression)
                expression = ""

    def _is_balanced(self, expression: str) -> bool:
        return (
            is_array_balanced(expression)
            and is_tuple_balanced(expression)
            and is_brace_balanced(expression)
            and (expression.count('"""') % 2 == 0)
            and (expression.count("'''") % 2 == 0)
        )


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


class CustomTuplePrinter(CustomPrinter):
    def __init__(self, value: tuple, color: str):
        # self.value = [custom_print(item) for item in value]
        self.value = value
        self.color = color

    def __str__(self):
        return colored(str(self.value).replace(",", ""), self.color)

    def __repr__(self):
        return str(self.value).replace(",", "")


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


color_map = {
    "int": "default",
    "float": "default",
    "complex": "default",
    "str": "default",  # variable symbol
    "String": "lightgreen",
    "bool": "lightblue",
    "list": "red",
    "tuple": "red",
    "block": "cyan",
}


def custom_print(value: Any) -> CustomPrinter:
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
    if isinstance(value, tuple):
        return CustomTuplePrinter(value, color_map["tuple"])
    if isinstance(value, Stacker):
        return CustomBlockPrinter(value, color_map["block"])
    return value
