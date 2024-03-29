from __future__ import annotations

import copy
from pathlib import Path

from prompt_toolkit import prompt
from prompt_toolkit.completion import WordCompleter

from stacker.error import ScriptReadError
from stacker.include.stk_file_read import readtxt
from stacker.lib.config import script_extension_name, stacker_dotfile
from stacker.stacker import Stacker
from stacker.syntax.parser import (
    is_array_balanced,
    is_brace_balanced,
    is_tuple_balanced,
    remove_start_end_quotes,
)
from stacker.util import colored


class ExecutionMode:
    def __init__(self, rpn_calculator: Stacker):
        self.rpn_calculator = rpn_calculator
        self.color_print = True
        self.dmode = False
        self.receved_word = [
            "help",
            "about",
            "delete_history",
            "vars",
        ]
        self.completer = WordCompleter(self.get_completer())

    def get_completer(self):
        # _reserved_word = copy.deepcopy(self.rpn_calculator.reserved_word)
        _reserved_word = list(self.receved_word)
        _operator_key = list(self.rpn_calculator.get_operators_ref().keys())
        _sfunctions_key = list(self.rpn_calculator.get_sfuntions_ref().keys())
        _variable_key = list(self.rpn_calculator.get_variables_ref().keys())
        _macro_key = list(self.rpn_calculator.get_macros_ref().keys())
        _reserved_word = list(
            set(
                _reserved_word
                + _operator_key
                + _sfunctions_key
                + _variable_key
                + _macro_key
            )
        )
        return _reserved_word

    def debug_mode(self):
        self.dmode = True

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

    def print_colored_output(self, stack_list: list) -> None:
        stack_str = colored("[", "yellow")
        for item in stack_list:
            item_str = str(item)
            item_str.replace("\n", " ")
            if item_str.startswith("[") or item_str.endswith("]"):
                stack_str += colored(item_str, "red")
                stack_str += " "
            elif item_str.startswith("(") or item_str.endswith(")"):
                stack_str += colored(item_str, "green")
                stack_str += " "
            elif item_str.replace(".", "", 1).isdigit() or (
                item_str.startswith("-") and item_str[1:].replace(".", "", 1).isdigit()
            ):
                stack_str += colored(item_str, "default")
                stack_str += " "
            elif item_str in list(self.rpn_calculator.get_variables_ref()):
                stack_str += colored(item_str, "lightblue")
                stack_str += " "
            elif isinstance(item_str, str):
                # stack_str += colored(f"'{item_str}'", 'default')
                #
                # if len(item_str) > 20:
                #     item_str = item_str[0:10] + "..."
                stack_str += colored(item_str, "green")
                stack_str += " "
            else:
                stack_str += colored(item_str, "default")
                stack_str += " "
        stack_str = stack_str[0:-2]
        stack_str += colored("]", "yellow")
        print(stack_str)

    def disp_stack(self) -> None:
        """Print the current stack to the console."""
        _stack = self.rpn_calculator.get_stack_copy_as_list()
        stack = []
        for token in _stack:
            if isinstance(token, Stacker):
                stack.append("{" + f"{token.expression}" + "}")
            else:
                stack.append(token)
        if self.color_print is True:
            self.print_colored_output(stack)
        else:
            print(stack)

    def disp_all_valiables(self) -> None:
        variables = self.rpn_calculator.get_variables_copy()
        for key in variables.keys():
            print(f"{key} = {variables[key]}")

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
