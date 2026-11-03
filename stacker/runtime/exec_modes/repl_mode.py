from __future__ import annotations

import logging
import sys
import traceback
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from stacker.stacker import Stacker

from prompt_toolkit import prompt
from prompt_toolkit.completion import DynamicCompleter, WordCompleter
from prompt_toolkit.history import FileHistory
from stacker.runtime.exec_modes.error import create_error_message
from stacker.runtime.exec_modes.execution_mode import REPL_COMMANDS, REPL_SETTINGS, ExecutionMode
from stacker.lib import delete_history, disp_about, disp_help
from stacker.lib.config import history_file_path
from stacker.error import error_kind
from stacker.error_formatter import ErrorFormatter
from stacker.version import __version__

# Import parser utility functions (not lexer components)
# Lexer components (TokenType, UnifiedLexer, etc.) are in stacker.syntax.lexer
from stacker.syntax.lexer import analyze_terminals


#: The heading help gives the group `operators` calls "Regular operators:"
HELP_REGULAR_HEADING = "Supported operators and functions:"


class ReplMode(ExecutionMode):
    def __init__(self, rpn_calculator: Stacker) -> None:
        super().__init__(rpn_calculator)
        # REPL-specific display settings
        self.disp_stack_mode = True
        self.disp_logo_mode = True
        self.disp_ans_mode = False
        # The commands the prompt completes; the display settings are not
        # offered (they are typed once, or kept in ~/.stackerrc)
        self.repl_commands = sorted(REPL_COMMANDS - REPL_SETTINGS)
        # The words are gathered again each time the prompt completes, so a
        # name defined since the REPL started is offered too
        self.completer = DynamicCompleter(lambda: WordCompleter(self.get_completer()))

    def get_completer(self) -> list[str]:
        """The REPL's commands and every name the interpreter knows, for completion."""
        words = self.repl_commands + self.rpn_calculator.get_all_keys_for_completer()
        return list(set(words))

    def update_completer(self) -> None:
        """Does nothing: the completer gathers the words anew each time it completes."""

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
        return __version__

    # REPL Command Handlers
    def _cmd_help(self) -> None:
        """Handle 'help' command."""
        disp_help()
        print("")
        for key, heading, descriptions in self.rpn_calculator.get_operator_groups():
            print(HELP_REGULAR_HEADING if key == "regular" else heading)
            for name, desc in descriptions.items():
                print(f"  {name}:\t{desc}")
            print("")
        print("Plugin commands:")
        for name, desc in self.rpn_calculator.get_plugin_descriptions().items():
            print(f"  {name}: {desc}")

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
        if expression in REPL_SETTINGS:
            return self._handle_repl_command(expression)
        return super()._run_stackerrc_command(expression)

    def _handle_repl_command(self, expression: str) -> bool:  # type: ignore[override]
        """Runs a line that is one of the REPL's commands.

        A command is its lowercase name alone on the line; spaces around it
        do not count. The names are reserved words of the language, so no
        program can define them (``HELP`` is an ordinary name). The names
        are listed only in ``REPL_COMMAND_NAMES`` (stacker/syntax/token_rules.py):
        a display setting is named ``enable_<x>`` / ``disable_<x>`` and turns
        the attribute ``<x>_mode`` on or off; any other command runs the
        method ``_cmd_<name>``.

        Returns:
            True if the line was a command and ran, False to evaluate it.
        """
        command = expression.strip()
        if command not in REPL_COMMANDS:
            return False
        if command in REPL_SETTINGS:
            # enable_disp_stack turns disp_stack_mode on, disable_disp_stack off
            switch, setting = command.split("_", 1)
            setattr(self, f"{setting}_mode", switch == "enable")
        else:
            getattr(self, f"_cmd_{command}")()
        return True

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
                # A construct still open -- a block, a list, a string or a
                # block comment -- takes the following lines as written,
                # joined with the line break (not " ", so a trailing `#`
                # comment cannot swallow the next line), so the REPL reads
                # what a script reads: a list spanning lines is one row,
                # and rows are written with `;`. `end` on a line of its
                # own inside an open list gives the list up; it is then
                # reported as the unterminated list it is.
                # """
                #     stacker:0> {1
                #             > 3
                #             > +}
                #     {1 3 +}
                # """
                while not (terminal := analyze_terminals(expression)).complete:
                    prompt_text = (
                        " " * (len(f"stacker:{line_count}> ") - len("> ")) + "> "
                    )
                    next_line = self.get_input(prompt_text, multiline=False)
                    if terminal.open_construct == "list" and next_line.lower() == "end":
                        break
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

            except KeyboardInterrupt:
                # Ctrl-C cancels what is being typed or run and the prompt
                # comes back; the stack stays as it is, as after an error
                print("\nKeyboardInterrupt", file=sys.stderr)
                if self.debug:
                    traceback.print_exc()
                self.rpn_calculator.clear_trace()

            except EOFError:
                print("\nSee you!")
                break

            except Exception as e:
                # Format error using Clang-style formatter
                error_type = error_kind(e)
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
