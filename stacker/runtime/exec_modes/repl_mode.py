from __future__ import annotations

import logging
import sys
import traceback
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from stacker.stacker import Stacker

from prompt_toolkit import prompt
from prompt_toolkit.completion import WordCompleter
from prompt_toolkit.history import FileHistory
from importlib.metadata import version
from stacker.runtime.exec_modes.error import create_error_message
from stacker.runtime.exec_modes.execution_mode import REPL_SETTINGS, ExecutionMode
from stacker.lib import delete_history, disp_about, disp_help
from stacker.lib.config import history_file_path
from stacker.error_formatter import ErrorFormatter

# Import parser utility functions (not lexer components)
# Lexer components (TokenType, UnifiedLexer, etc.) are in stacker.syntax.lexer
from stacker.syntax.lexer import analyze_terminals
from stacker.syntax.parser import is_array


class ReplMode(ExecutionMode):
    def __init__(self, rpn_calculator: Stacker) -> None:
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

    def get_completer(self) -> list[str]:
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

    def update_completer(self) -> None:
        self.completer = WordCompleter(self.get_completer())

    def get_input(self, prompt_text: str, multiline: bool) -> str:
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

    def get_version(self) -> str:  # type: ignore[override]
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
        manager = self.rpn_calculator.operator_manager
        for title, descriptions in (
            ("Higher-order operators:", manager.get_hof_descriptions()),
            ("Aggregate operators:", manager.get_aggregate_descriptions()),
            ("Transform operators:", manager.get_transform_descriptions()),
        ):
            print(title)
            for operator_name, operator_descriptions in descriptions.items():
                print(f"  {operator_name}:\t{operator_descriptions}")
            print()
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

    def _run_stackerrc_command(self, expression: str) -> bool:
        """Applies a display setting from ~/.stackerrc as if it were typed.

        help, about and delete_history are skipped: they are not settings,
        and would otherwise run on every start.
        """
        if expression.lower() in REPL_SETTINGS:
            return self._handle_repl_command(expression)
        return super()._run_stackerrc_command(expression)

    def _handle_repl_command(self, expression: str) -> bool:  # type: ignore[override]
        """
        Handle REPL-specific commands.
        Returns True if command was handled, False otherwise.
        A new command also goes into REPL_COMMANDS (execution_mode.py).
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

    def run(self) -> None:
        stacker_version = self.get_version()
        print(f"Stacker {stacker_version} on {sys.platform}")
        print('Type "help" to get more information.')

        line_count = 0
        while True:
            try:
                expression = self.get_input(f"stacker:{line_count}> ", multiline=False)

                # Continuation input is judged by the lexer scan core
                # (analyze_terminals) so strings, comments, and brackets
                # cannot diverge from what the tokenizer will accept
                # (e.g. braces inside a `#| |#` comment are inert).
                # REPL input is human-typed and bounded, so re-scanning
                # the whole expression per line is fine here; only the
                # script line loop needs the incremental TerminalScanner
                aborted = False
                if is_array(expression):
                    # """
                    #     # List: rows are joined with ";"
                    #     stacker:0> [1 2 3
                    #                 3 4 5]
                    #     [1 2 3; 3 4 5]
                    # """
                    while not (terminal := analyze_terminals(expression)).complete:
                        prompt_text = (
                            " " * (len(f"stacker:{line_count}> ") - len("> ")) + "> "
                        )
                        next_line = self.get_input(prompt_text, multiline=False)
                        if next_line.lower() == "end":
                            aborted = True
                            break
                        if terminal.open_construct in {
                            "string",
                            "block comment",
                        }:
                            # Inside a string/comment spanning rows: keep
                            # the raw line, no row separator
                            expression += "\n" + next_line
                            continue
                        if next_line in {"]", ")"}:
                            expression += next_line
                            if analyze_terminals(expression).complete:
                                break
                            continue
                        # Join with "\n" (not " ") so a trailing '#'
                        # comment on the previous line cannot swallow
                        # the row separator or this line
                        if not expression.endswith(";"):
                            expression += ";\n" + next_line
                        else:
                            expression += "\n" + next_line

                # Generic continuation for any construct still open —
                # blocks, strings, and block comments (subsumes the
                # former `{`-specific loop):
                # """
                #     stacker:0> {1
                #             > 3
                #             > +}
                #     {1 3 +}
                # """
                if not aborted:
                    while not analyze_terminals(expression).complete:
                        prompt_text = (
                            " " * (len(f"stacker:{line_count}> ") - len("> ")) + "> "
                        )
                        next_line = self.get_input(prompt_text, multiline=False)
                        expression += "\n" + next_line

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

                # The REPL has no file or line of its own; an error inside
                # an included file is reported at that file's line
                filename, line_number, source_line, frames = None, None, None, []
                location = self._error_location(e)
                if location is not None:
                    filename, line_number, source_line, frames = location  # type: ignore[assignment]
                formatted_error = ErrorFormatter.format_error(
                    filename=filename,
                    line_number=line_number,
                    column=None,
                    error_type=error_type,
                    message=message,
                    source_line=source_line,
                    hint=hint,
                    frames=frames,
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
