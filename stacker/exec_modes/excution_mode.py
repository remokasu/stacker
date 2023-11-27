from __future__ import annotations

import copy

from stacker.util import colored
from stacker.stacker import Stacker

from prompt_toolkit.completion import WordCompleter
from prompt_toolkit import prompt


class ExecutionMode:
    def __init__(self, rpn_calculator: Stacker):
        self.rpn_calculator = rpn_calculator
        self.completer = WordCompleter(self.get_completer())
        self.color_print = True
        self.dmode = False

    def get_completer(self):
        _reserved_word = copy.deepcopy(self.rpn_calculator.reserved_word)
        _operator_key = list(self.rpn_calculator.operator.keys())
        _variable_key = list(self.rpn_calculator.variables.keys())
        _macro_key = list(self.rpn_calculator.macros.keys())
        _reserved_word = list(set(
            _reserved_word +
            _operator_key +
            _variable_key +
            _macro_key
        ))
        return _reserved_word

    def debug_mode(self):
        self.dmode = True

    def get_multiline_input(self, prompt="") -> str:
        lines = []
        while True:
            line = input(prompt)
            if line.endswith("\\"):
                line = line[:-1]  # バックスラッシュを取り除く
                lines.append(line)
                prompt = ""  # 2行目以降のプロンプトは空にする
            else:
                lines.append(line)
                break
        return "\n".join(lines)

    def run(self):
        raise NotImplementedError("Subclasses must implement the 'run' method")

    def print_colored_output(self, stack_list) -> None:
        stack_str = colored("[", 'yellow')
        for item in stack_list:
            item_str = str(item)
            item_str.replace('\n', ' ')
            # print(item_str)
            if item_str.startswith('[') or item_str.endswith(']'):
                stack_str += colored(item_str, 'red')
                stack_str += ", "
            elif item_str.startswith('(') or item_str.endswith(')'):
                stack_str += colored(item_str, 'green')
                stack_str += ", "
            elif item_str.replace('.', '', 1).isdigit() or (item_str.startswith('-') and item_str[1:].replace('.', '', 1).isdigit()):
                stack_str += colored(item_str, 'default')
                stack_str += ", "
            elif item_str in list(self.rpn_calculator.variables.keys()):
                stack_str += colored(item_str, 'lightblue')
                stack_str += ", "
            elif isinstance(item_str, str):
                # stack_str += colored(f"'{item_str}'", 'default')
                #
                # if len(item_str) > 20:
                #     item_str = item_str[0:10] + "..."
                stack_str += colored(item_str, 'green')
                stack_str += ", "
            else:
                stack_str += colored(item_str, 'default')
                stack_str += ", "
        stack_str = stack_str[0:-2]
        stack_str += colored("]", 'yellow')
        print(stack_str)

    def show_stack(self) -> None:
        """ Print the current stack to the console.
        """
        tokens = self.rpn_calculator.get_stack()
        if len(tokens) == 0:
            return
        stack = []
        for token in tokens:
            if isinstance(token, Stacker):
                stack.append(token.sub_expression)
            else:
                stack.append(token)

        if self.color_print is True:
            self.print_colored_output(stack)
        else:
            print(stack)
