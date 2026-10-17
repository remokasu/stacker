from __future__ import annotations

from pathlib import Path

from stacker.include.stk_file_read import readtxt
from stacker.stacker import Stacker

from stacker.error import UnterminatedTokenError
from stacker.syntax.lexer import TerminalScanner
from stacker.syntax.parser import remove_start_end_quotes

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

        # File errors
        elif "FileNotFoundError" in error_type:
            return "File not found. Check the file path is correct"
        elif "PermissionError" in error_type:
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
        """Import a stacker script and return the stacker object.

        Args:
            filename: Script to run.
            stackerrc: True for ~/.stackerrc, whose REPL commands go to
                ``_run_stackerrc_command`` instead of the interpreter.
        """
        path = Path(remove_start_end_quotes(str(filename)))
        code = readtxt(path)
        expression = ""
        lines = code.splitlines()

        # Set source file and store all source lines for error reporting
        self.rpn_calculator.current_file = str(path.resolve())
        for line_num, line_text in enumerate(lines, start=1):
            self.rpn_calculator.source_lines[line_num] = line_text

        i = 0
        expression_start_line = None  # Track which line the expression started on
        # Incremental scanner: feeds only the newly appended chunk, so a
        # multi-line expression stays O(total size) instead of re-scanning
        # the whole accumulated buffer on every line
        scanner = TerminalScanner()

        while i < len(lines):
            line_number = i + 1  # 1-indexed line numbers

            if scanner.state().complete:
                line = lines[i].strip()
                # Skip blank lines between expressions
                if not expression and not line:
                    i += 1
                    continue
                # Track the first line of the expression
                if not expression:
                    expression_start_line = line_number
                chunk = line + "\n"
            else:
                # Inside an open string / block comment / bracket: keep the
                # raw line so string content (including newlines) survives
                chunk = lines[i] + "\n"

            expression += chunk
            state = scanner.feed(chunk)

            if state.complete:
                candidate = expression.strip()
                if candidate:
                    if candidate[-2:] in {";]", ";)"}:
                        closer = candidate[-1]
                        candidate = candidate[:-2] + closer
                    # Set current line before processing expression
                    self.rpn_calculator.current_line = expression_start_line
                    if not (stackerrc and self._run_stackerrc_command(candidate)):
                        self.rpn_calculator.process_expression(candidate)
                    expression = ""
                    expression_start_line = None
                    scanner = TerminalScanner()

            i += 1

        # Unterminated construct at end of file: report the absolute line
        if expression.strip():
            _, state = scanner.finalize()
            if not state.complete:
                start = expression_start_line
                if start is not None and state.start_line is not None:
                    start = start + state.start_line - 1
                self.rpn_calculator.current_line = start
                raise UnterminatedTokenError(state.open_construct, start)

    def _run_stackerrc_command(self, expression: str) -> bool:
        """Handles a REPL command found in ~/.stackerrc.

        Outside the REPL there is nothing for it to act on, so it is skipped.
        The REPL applies the display settings (see ReplMode).

        Returns:
            True if ``expression`` was a REPL command, False to evaluate it.
        """
        return expression.lower() in REPL_COMMANDS
