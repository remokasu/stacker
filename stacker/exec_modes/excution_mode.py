from __future__ import annotations

import copy

from stacker.util import colored
from stacker.stacker import Stacker

from prompt_toolkit.completion import WordCompleter
from prompt_toolkit import prompt


class ExecutionMode:
    def __init__(self, rpn_calculator: Stacker):
        self.rpn_calculator = rpn_calculator
        self._operator_key = list(self.rpn_calculator.operator.keys())
        self._variable_key = list(self.rpn_calculator.variables.keys())
        self._reserved_word = copy.deepcopy(self.rpn_calculator.reserved_word)
        self._reserved_word = (self._reserved_word + self._operator_key + self._variable_key)
        self.completer = WordCompleter(self._reserved_word)
        self.color_print = True
        self.dmode = False

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
