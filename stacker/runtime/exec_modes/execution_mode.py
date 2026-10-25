from __future__ import annotations

import sys
from pathlib import Path

from stacker.include.stk_file_read import readtxt
from stacker.stacker import Stacker

from stacker.error import UnterminatedTokenError, UserError, attach_include_location, error_kind, include_location_of
from stacker.error_formatter import ErrorFormatter
from stacker.include.include import pop_entry_file, push_entry_file
from stacker.syntax.parser import remove_start_end_quotes
from stacker.syntax.script import iter_expressions

# from stacker.syntax.parser import is_string
from stacker.util.disp import disp_stack, plain_text

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


#: The REPL's display settings, which ~/.stackerrc may hold.
REPL_SETTINGS = frozenset(
    {
        "enable_disp_stack",
        "disable_disp_stack",
        "enable_disp_logo",
        "disable_disp_logo",
        "enable_disp_ans",
        "disable_disp_ans",
    }
)
#: Every command the REPL handles itself (ReplMode._handle_repl_command).
REPL_COMMANDS = REPL_SETTINGS | {"help", "about", "delete_history"}


class ExecutionMode:
    def __init__(self, rpn_calculator: Stacker):
        self.rpn_calculator = rpn_calculator
        self.color_print = True
        self.debug = False

    def debug_mode(self) -> None:
        self.debug = True

    def _get_error_hint(self, error: Exception) -> str | None:
        """Generate helpful hint based on error type."""
        if isinstance(error, UserError):
            return None  # the program's own error says what it means
        error_type = type(error).__name__
        message = str(error)

        # Undefined variable/symbol errors
        if "UndefinedSymbol" in error_type or "UndefinedVariable" in error_type:
            # Extract the name from the message
            if "`" in message:
                var_name = message.split("`")[1]
                return f"To use the name itself, write `:{var_name}` or `{{{var_name}}}`"

        # A block that had to leave a value left nothing
        elif "NoValueProduced" in error_type:
            if "left nothing on the stack" in message:
                return "Make the block leave a value on the stack"
            return "Make the block leave a value on the stack, or use `dolist` for side-effect-only iteration"

        # A function left more values than its context takes
        elif "ResultCount" in error_type:
            return "To keep several values for each element, collect them into one inside the function (e.g. 2 listn)"

        # Stack underflow errors
        elif "StackUnderflow" in error_type:
            # Message already contains operator and arg count info
            return "Check that you have enough values on the stack before calling this operator"
        elif "IndexError" in error_type and "pop from an empty deque" in message:
            return "Stack underflow: Not enough elements on the stack for this operation"

        # Division errors
        elif "ZeroDivisionError" in error_type:
            return "Cannot divide by zero. Check your divisor value"

        # Type errors
        elif "TypeError" in error_type:
            if "concatenate str" in message or "can only concatenate str" in message:
                return "Cannot mix string and number types. Use 'str' to convert numbers to strings"
            elif "unsupported operand type" in message:
                if "+" in message:
                    return "The '+' operator requires compatible types (both numbers or both strings)"
                elif "*" in message:
                    return "Multiplication requires numeric types or string * int"
                elif "-" in message or "/" in message:
                    return "Arithmetic operators require numeric types"
                return "Check that the operator receives compatible argument types"
            elif "not subscriptable" in message:
                return "Cannot index into this type. Use `nth` to read an element of a list or a string"
            elif "not callable" in message:
                return "This value cannot be called as a function"

        # Key errors (variable not found)
        elif "KeyError" in error_type:
            # Extract key name from message
            key = message.strip("'\"")
            return f"Variable '{key}' is not defined. Define it first: '0 {key} ='"

        # Syntax errors
        elif "SyntaxError" in error_type or "StackerSyntaxError" in error_type:
            if "bracket" in message.lower() or "paren" in message.lower():
                return "Check for matching brackets: {} for code blocks, [] for lists"
            elif "quote" in message.lower():
                return "Check for matching quotes in strings"

        # File errors (a file word raises its own error from the host's)
        elif isinstance(error.__cause__, FileNotFoundError) or "FileNotFoundError" in error_type:
            return "File not found. Check the file path is correct"
        elif isinstance(error.__cause__, PermissionError) or "PermissionError" in error_type:
            return "Permission denied. Check file permissions"

        # Attribute errors
        elif "AttributeError" in error_type:
            return "This value does not have the requested attribute or method"

        return None

    def get_multiline_input(self, prompt: str = "") -> str:
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

    def run(self) -> None:
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

    def disp_all_variables(self) -> None:
        variables = self.rpn_calculator.get_variables_copy()
        for key in variables.keys():
            print(f"{key} = {variables[key]}")

    def disp_ans(self) -> None:
        """Prints the top of the stack as the stack display shows it, without colors."""
        _stack = self.rpn_calculator.get_stack_copy_as_list()
        if len(_stack) == 0:
            return
        print(plain_text(_stack[-1]))

    def execute_stacker_dotfile(self, filename: str | Path, stackerrc: bool = False) -> None:
        """Runs a script expression by expression.

        Args:
            filename: Script to run.
            stackerrc: True for ~/.stackerrc, whose REPL commands go to
                ``_run_stackerrc_command`` instead of the interpreter.

        Raises:
            UnterminatedTokenError: The file ends inside an open construct;
                ``current_line`` names the line it started on.
        """
        path = Path(remove_start_end_quotes(str(filename)))
        code = readtxt(path)
        calculator = self.rpn_calculator
        # ~/.stackerrc runs before the REPL, -e or the script: what it sets
        # as the current file must not outlive it (relative includes and
        # `script-path` would otherwise point at the rc file)
        before = (calculator.current_file, calculator.current_line, dict(calculator.source_lines))

        # Set source file and store all source lines for error reporting
        calculator.current_file = str(path.resolve())
        for line_num, line_text in enumerate(code.splitlines(), start=1):
            calculator.source_lines[line_num] = line_text

        # The script is the bottom frame of the include stack: a file that
        # includes it is caught as circular, and an error inside an
        # included file can name the line here that included it
        push_entry_file(calculator, path)
        expressions = iter_expressions(code)
        try:
            while True:
                try:
                    line_number, expression = next(expressions)
                except StopIteration:
                    break
                except UnterminatedTokenError as error:
                    # The file ends inside an open construct: report its line
                    # (an unterminated text handed to `parse` keeps the
                    # expression's own line)
                    calculator.current_line = error.start_line
                    raise
                calculator.current_line = line_number
                if not (stackerrc and self._run_stackerrc_command(expression)):
                    calculator.process_expression(expression)
        except Exception as error:
            if stackerrc:
                # The rc's position is put back below; the report needs it
                # (an error inside a file the rc includes keeps its own).
                # The rc is the outermost file, so there are no including frames
                attach_include_location(
                    error,
                    calculator.current_file or str(path.resolve()),
                    calculator.current_line,
                    calculator.source_lines.get(calculator.current_line or 0),
                    [],
                )
            raise
        finally:
            pop_entry_file(calculator)
            if stackerrc:
                calculator.current_file, calculator.current_line, source_lines = before
                calculator.source_lines.clear()
                calculator.source_lines.update(source_lines)

    def run_stackerrc(self, path: str | Path) -> None:
        """Runs ~/.stackerrc before the REPL, ``-e`` or a script.

        An error in it is reported on standard error the way a script's
        is (the file, the line, the kind, a hint) and ends the run with
        status 1: the definitions the rc was to make are missing, so what
        follows would fail further on, in stranger ways.

        Args:
            path: The rc file.

        Raises:
            SystemExit: With status 1, after reporting an error the rc raised.
        """
        try:
            self.execute_stacker_dotfile(path, stackerrc=True)
        except Exception as error:
            filename: str | None = str(Path(path).resolve())
            line_number: int | None = None
            source_line: str | None = None
            frames: list[str] = []
            location = self._error_location(error)
            if location is not None:
                filename, line_number, source_line, frames = location
            formatted_error = ErrorFormatter.format_error(
                filename=filename,
                line_number=line_number,
                column=None,
                error_type=error_kind(error),
                message=str(error),
                source_line=source_line,
                hint=self._get_error_hint(error),
                frames=frames,
            )
            print(formatted_error, file=sys.stderr)
            sys.exit(1)

    def _error_location(
        self, error: BaseException
    ) -> tuple[str | None, int | None, str | None, list[str]] | None:
        """Where an error raised inside an included file happened, for the display.

        Args:
            error: The exception being reported.

        Returns:
            ``(file, line, source_line, frames)`` when the error carries an
            include position (``frames`` are the ``path:line`` of the
            including files, innermost first, without the ones that have
            no line); None for an error raised outside any included file.
        """
        found = include_location_of(error)
        if found is None:
            return None
        (file, line, source_line), include_frames = found
        frames = [f"{path}:{frame_line}" for path, frame_line in include_frames if frame_line is not None]
        return file, line, source_line, frames

    def _run_stackerrc_command(self, expression: str) -> bool:
        """Handles a REPL command found in ~/.stackerrc.

        Outside the REPL there is nothing for it to act on, so it is skipped.
        The REPL applies the display settings (see ReplMode).

        Returns:
            True if ``expression`` was a REPL command, False to evaluate it.
        """
        return expression.lower() in REPL_COMMANDS
