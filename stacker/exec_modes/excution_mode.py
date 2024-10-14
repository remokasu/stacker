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

# from stacker.syntax.parser import is_string
from stacker.util.disp import disp_stack

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
            self.rpn_calculator.operator_manager.get_priority_keys()
        )
        # _setting_key = list(self.rpn_calculator.get_settings_ref().keys())
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

    def disp(self) -> None:
        """Print the current stack to the console."""
        _stack = self.rpn_calculator.get_stack_copy_as_list()
        disp_stack(_stack, colored=self.color_print)
        # if self.color_print is True:
        #     stack_str = disp_colored(_stack)
        #     print(stack_str)
        # else:
        #     print(f"{_stack}".replace(",", ""))

    def disp_all_valiables(self) -> None:
        variables = self.rpn_calculator.get_variables_copy()
        for key in variables.keys():
            print(f"{key} = {variables[key]}")

    def disp_ans(self) -> None:
        _stack = self.rpn_calculator.get_stack_copy_as_list()
        if len(_stack) == 0:
            return
        print(f"{_stack[-1]}")

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
