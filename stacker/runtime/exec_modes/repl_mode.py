from __future__ import annotations

import logging
import sys
import traceback

from prompt_toolkit import prompt
from prompt_toolkit.completion import WordCompleter
from prompt_toolkit.history import FileHistory
from importlib.metadata import version
from stacker.runtime.exec_modes.error import create_error_message
from stacker.runtime.exec_modes.execution_mode import ExecutionMode
from stacker.lib import delete_history, disp_about, disp_help
from stacker.lib.config import history_file_path
from stacker.error_formatter import ErrorFormatter

# Import parser utility functions (not lexer components)
# Lexer components (TokenType, UnifiedLexer, etc.) are in stacker.syntax.lexer
from stacker.syntax.parser import (
    is_array,
    is_array_balanced,
    is_brace,
    is_brace_balanced,
    is_code_block,
    # is_tuple,  # REMOVED: Tuples no longer supported
    # is_tuple_balanced,  # REMOVED: Use is_brace_balanced for () blocks
)


class ReplMode(ExecutionMode):
    def __init__(self, rpn_calculator):
        super().__init__(rpn_calculator)
        # REPL-specific display settings
        self.disp_stack_mode = True
        self.disp_logo_mode = True
        self.disp_ans_mode = False
        # REPL-specific command list
        self.repl_commands = [
            "help",
            "about",
            "delete_history",
        ]
        # Initialize completer
        self.completer = WordCompleter(self.get_completer())

    def get_completer(self):
        """Get completion words for REPL prompt."""
        _reserved_word = list(self.repl_commands)
        _operator_key = list(self.rpn_calculator.get_all_keys_for_completer())
        _priority_operators_key = list(
            self.rpn_calculator.operator_manager.get_priority_keys()
        )
        _sfunctions_key = list(self.rpn_calculator.get_sfuntions_ref().keys())
        _variable_key = list(self.rpn_calculator.get_variables_ref().keys())
        _macro_key = list(self.rpn_calculator.get_macros_ref().keys())
        _reserved_word = list(
            set(
                _reserved_word
                + _operator_key
                + _priority_operators_key
                + _sfunctions_key
                + _variable_key
                + _macro_key
            )
        )
        return _reserved_word

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

    def get_version(self) -> str:
        return version("pystacker")

    # REPL Command Handlers
    def _cmd_help(self) -> None:
        """Handle 'help' command."""
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
        print("System operators:")
        for (
            operator_name,
            operator_descriptions,
        ) in self.rpn_calculator.operator_manager.get_system_descriptions().items():
            print(f"  {operator_name}:\t{operator_descriptions}")
        print("")
        print("Plugin commands:")
        for (
            plugin_name,
            plugin_descriptions,
        ) in self.rpn_calculator.plugin_descriptions.items():
            print(f"  {plugin_name}: {plugin_descriptions}")

    def _cmd_about(self) -> None:
        """Handle 'about' command."""
        disp_about()

    def _cmd_delete_history(self) -> None:
        """Handle 'delete_history' command."""
        delete_history()

    def _get_error_hint(self, error: Exception) -> str | None:
        """Generate helpful hint based on error type."""
        error_type = type(error).__name__
        message = str(error)

        if "UndefinedSymbol" in error_type:
            # Extract variable name from message
            if "`" in message:
                var_name = message.split("`")[1]
                return f"Define '{var_name}' before using it: '0 {var_name} ='"
        elif "IndexError" in error_type and "pop from an empty deque" in message:
            return "Stack underflow: Not enough elements on the stack for this operation"
        elif "ZeroDivisionError" in error_type:
            return "Cannot divide by zero"
        elif "TypeError" in error_type:
            if "concatenate str" in message:
                return "Cannot mix string and number types. Convert one to match the other"

        return None

    def _handle_repl_command(self, expression: str) -> bool:
        """
        Handle REPL-specific commands.
        Returns True if command was handled, False otherwise.
        """
        expr_lower = expression.lower()

        # Simple command handlers
        if expr_lower == "help":
            self._cmd_help()
            return True
        if expr_lower == "about":
            self._cmd_about()
            return True
        if expr_lower == "delete_history":
            self._cmd_delete_history()
            return True

        # Display mode commands
        if expr_lower == "enable_disp_stack":
            self.disp_stack_mode = True
            return True
        if expr_lower == "disable_disp_stack":
            self.disp_stack_mode = False
            return True
        if expr_lower == "enable_disp_logo":
            self.disp_logo_mode = True
            return True
        if expr_lower == "disable_disp_logo":
            self.disp_logo_mode = False
            return True
        if expr_lower == "enable_disp_ans":
            self.disp_ans_mode = True
            return True
        if expr_lower == "disable_disp_ans":
            self.disp_ans_mode = False
            return True

        return False

    def run(self):
        stacker_version = self.get_version()
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

                if is_array(expression) or is_code_block(expression):
                    # """
                    #     # List
                    #     stacker:0> [1 2 3
                    #                 3 4 5]
                    #     [1 2 3; 3 4 5]
                    #
                    #     # Code Block
                    #     stacker:0> (1 2 3
                    #                 3 4 5)
                    #     (1 2 3; 3 4 5)
                    # """
                    while not is_array_balanced(expression) or not is_brace_balanced(
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
                            if is_array_balanced(expression) or is_brace_balanced(
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

                # Handle REPL-specific commands
                if self._handle_repl_command(expression):
                    continue

                # Process as normal RPN expression
                self.rpn_calculator.process_expression(expression)
                if self.disp_ans_mode is True:
                    self.disp_ans()
                if self.disp_stack_mode is True:
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
                # Format error using Clang-style formatter
                error_type = type(e).__name__
                message = str(e)

                # Generate hint based on error type
                hint = self._get_error_hint(e)

                # Format the error (REPL mode doesn't have file/line info)
                formatted_error = ErrorFormatter.format_error(
                    filename=None,  # REPL has no file
                    line_number=None,  # REPL has no line numbers
                    column=None,
                    error_type=error_type,
                    message=message,
                    source_line=None,
                    hint=hint
                )

                print(formatted_error, file=sys.stderr)

                # Show trace only in debug mode
                if self.debug:
                    trace = self.rpn_calculator.get_trace_copy()
                    if len(trace) > 0:
                        if len(trace) > 4:
                            error_trace = trace[-4:]
                        else:
                            error_trace = trace
                        print(create_error_message(error_trace), file=sys.stderr)
                    traceback.print_exc()

                self.rpn_calculator.clear_trace()
            # self.update_completer()
            line_count = self.rpn_calculator.get_stack_length()
