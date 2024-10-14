from __future__ import annotations

import logging
import sys
import traceback

from pkg_resources import get_distribution
from prompt_toolkit import prompt
from prompt_toolkit.completion import WordCompleter
from prompt_toolkit.history import FileHistory

from stacker.exec_modes.error import create_error_message
from stacker.exec_modes.excution_mode import ExecutionMode
from stacker.lib import delete_history, disp_about, disp_help
from stacker.lib.config import history_file_path
from stacker.syntax.parser import (
    is_array,
    is_array_balanced,
    is_brace,
    is_brace_balanced,
    is_tuple,
    is_tuple_balanced,
)


class ReplMode(ExecutionMode):
    def update_completer(self):
        self.completer = WordCompleter(self.get_completer())

    def get_input(self, prompt_text: str, multiline: bool):
        try:
            return prompt(
                prompt_text,
                history=FileHistory(history_file_path),
                completer=self.completer,
                multiline=multiline,
            )
        except EOFError:
            print("\nSee you!")
            sys.exit()

    def run(self):
        stacker_version = get_distribution("pystacker").version
        print(f"Stacker {stacker_version} on {sys.platform}")
        print('Type "help" to get more information.')

        line_count = 0
        while True:
            try:
                expression = self.get_input(f"stacker:{line_count}> ", multiline=False)
                if expression[-2:] in {";]", ";)"}:
                    closer = expression[-1]
                    expression = expression[:-2] + closer

                if is_brace(expression):
                    # """
                    #     # Brace
                    #     stacker:0> {1
                    #                 3
                    #                 +}
                    #     {1 3 +}
                    # """
                    while not is_brace_balanced(expression):
                        prompt_text = (
                            " " * (len(f"stacker:{line_count}> ") - len("> ")) + "> "
                        )
                        next_line = self.get_input(prompt_text, multiline=False)
                        expression += " " + next_line
                        if next_line in {"}"}:
                            if is_brace_balanced(expression):
                                break

                if is_array(expression) or is_tuple(expression):
                    # """
                    #     # List
                    #     stacker:0> [1 2 3
                    #                 3 4 5]
                    #     [1 2 3; 3 4 5]
                    #
                    #     # Tuple
                    #     stacker:0> (1 2 3
                    #                 3 4 5)
                    #     (1 2 3; 3 4 5)
                    # """
                    while not is_array_balanced(expression) or not is_tuple_balanced(
                        expression
                    ):
                        prompt_text = (
                            " " * (len(f"stacker:{line_count}> ") - len("> ")) + "> "
                        )
                        next_line = self.get_input(prompt_text, multiline=False)
                        if next_line.lower() == ("end"):
                            break
                        if next_line in {"]", ")"}:
                            expression += next_line
                            if is_array_balanced(expression) or is_tuple_balanced(
                                expression
                            ):
                                if expression[-2:] in {";]", ";)"}:
                                    closer = expression[-1]
                                    expression = expression[:-2] + closer
                                break
                        if next_line[-2:] in {";]", ";)"}:
                            closer = next_line[-1]
                            next_line = next_line[:-2] + closer
                        if not expression.endswith(";"):
                            expression += "; " + next_line
                        else:
                            expression += " " + next_line

                # # Process to continue until the input starting with double quotation or single quotation is closed
                # while (
                #     (expression.startswith('"""') and expression.count('"""') % 2 != 0) or
                #     (expression.startswith("'''") and expression.count("'''") % 2 != 0)
                # ):
                #     """
                #         stacker:0> '''
                #         stacker:0> This is a multi-line
                #         stacker:0> input example.
                #         stacker:0> '''
                #         ['\nThis is a multi-line\ninput example.\n']
                #     """
                #     prompt_text = " " * (len(f"stacker:{line_count}> ") - len("> ")) + "> "
                #     next_line = self.get_input(prompt_text, multiline=False)
                #     expression += "\n" + next_line

                logging.debug("input expression: %s", expression)

                if expression.lower() == "help":
                    disp_help()
                    print("")
                    print("Supported operators and functions:")
                    regular_operator_descriptions = {}
                    regular_operator_descriptions.update(
                        self.rpn_calculator.operator_manager.get_regular_descriptions()
                    )
                    regular_operator_descriptions.update(
                        self.rpn_calculator.operator_manager.get_priority_descriptions()
                    )
                    for (
                        operator_name,
                        operator_descriptions,
                    ) in regular_operator_descriptions.items():
                        print(f"  {operator_name}:\t{operator_descriptions}")
                    print("")
                    print("Stack operators:")
                    for (
                        operator_name,
                        operator_descriptions,
                    ) in self.rpn_calculator.operator_manager.get_stack_descriptions().items():
                        print(f"  {operator_name}:\t{operator_descriptions}")
                    print("")
                    print("Settings operators:")
                    for (
                        operator_name,
                        operator_descriptions,
                    ) in self.rpn_calculator.operator_manager.get_settings_descriptions().items():
                        print(f"  {operator_name}:\t{operator_descriptions}")
                    print("")
                    print("Plugin commands:")
                    for (
                        plugin_name,
                        plugin_descriptions,
                    ) in self.rpn_calculator.plugin_descriptions.items():
                        print(f"  {plugin_name}: {plugin_descriptions}")
                    continue
                if expression.lower() == "about":
                    disp_about()
                    continue
                if expression.lower() == "delete_history":
                    delete_history()
                    continue
                if expression.lower() == "vars":
                    self.disp_all_valiables()
                    continue
                self.rpn_calculator.process_expression(expression)
                if self.rpn_calculator.disp_ans_mode is True:
                    self.disp_ans()
                if self.rpn_calculator.disp_stack_mode is True:
                    self.disp()
                # else:
                #     if self.rpn_calculator.get_stack_length() > 0:
                #         print(self.rpn_calculator.get_stack_copy_as_list()[-1])
                #     else:
                #         print(self.rpn_calculator.get_stack_copy_as_list())
                self.rpn_calculator.clear_trace()

            except EOFError:
                print("\nSee you!")
                break

            except Exception as e:
                print(f"{type(e).__name__}: {e}")
                trace = self.rpn_calculator.get_trace_copy()
                if len(trace) == 0:
                    sys.exit(1)
                if len(trace) > 4:
                    error_trace = trace[-4:]
                else:
                    error_trace = trace
                print(create_error_message(error_trace))
                if self.debug:
                    traceback.print_exc()
                self.rpn_calculator.clear_trace()
            # self.update_completer()
            line_count = self.rpn_calculator.get_stack_length()
