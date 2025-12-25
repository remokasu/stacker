from __future__ import annotations

from pathlib import Path

from stacker.include.stk_file_read import readtxt
from stacker.stacker import Stacker

# Import parser utility functions (not lexer components)
# Lexer components (TokenType, UnifiedLexer, etc.) are in stacker.syntax.lexer
from stacker.syntax.parser import (
    is_array_balanced,
    is_brace_balanced,
    # is_tuple_balanced,  # REMOVED: () now creates code blocks, use is_brace_balanced
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

    def disp_all_variables(self) -> None:
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
        lines = code.splitlines()

        # Set source file and store all source lines for error reporting
        self.rpn_calculator.current_file = str(path.resolve())
        for line_num, line_text in enumerate(lines, start=1):
            self.rpn_calculator.source_lines[line_num] = line_text

        i = 0
        expression_start_line = None  # Track which line the expression started on

        while i < len(lines):
            line = lines[i].strip()
            line_number = i + 1  # 1-indexed line numbers

            # Skip empty lines and comments
            if not line or line.startswith("#"):
                i += 1
                continue

            # Track the first line of the expression
            if not expression.strip():
                expression_start_line = line_number

            # Remove inline comments from the line before adding to expression
            # Find # that is not inside a string
            clean_line = line
            if '#' in line:
                in_string = False
                quote_char = None
                for j, char in enumerate(line):
                    if char in ('"', "'") and (j == 0 or line[j-1] != '\\'):
                        if not in_string:
                            in_string = True
                            quote_char = char
                        elif char == quote_char:
                            in_string = False
                            quote_char = None
                    elif char == '#' and not in_string:
                        clean_line = line[:j].rstrip()
                        break

            expression += clean_line + " "

            if self._is_balanced(expression):
                if self._is_complete_expression(expression):
                    if expression[-2:] in {";]", ";)"}:
                        closer = expression[-1]
                        expression = expression[:-2] + closer
                    # Set current line before processing expression
                    self.rpn_calculator.current_line = expression_start_line
                    self.rpn_calculator.process_expression(expression)
                    expression = ""
                    expression_start_line = None

            i += 1

    def _is_balanced(self, expression: str) -> bool:
        # Inline comments are already removed before calling this method
        return (
            is_array_balanced(expression)
            # REMOVED: is_tuple_balanced - () now handled by is_brace_balanced
            and is_brace_balanced(expression)  # Handles both {} and () code blocks
            and (expression.count('"""') % 2 == 0)
            and (expression.count("'''") % 2 == 0)
        )

    def _is_complete_expression(self, expression: str) -> bool:
        """Check if the expression is complete and ready to execute.

        Some commands like 'do', 'dolist', 'times' require arguments that may
        span multiple lines. We need to check if all required arguments are present.
        """
        from stacker.syntax.parser import parse_expression, is_code_block

        try:
            tokens = parse_expression(expression.strip())
            if not tokens:
                return True

            # Commands that require a code block and symbol/values before execution
            block_consuming_commands = {"do", "dolist", "times"}

            # Check if the last token is a block-consuming command
            last_token = tokens[-1] if tokens else None
            if last_token not in block_consuming_commands:
                return True

            # For 'do': expects start_value end_value symbol {body} do
            if last_token == "do":
                if len(tokens) < 5:
                    return False
                # Check if there's a code block before 'do'
                return is_code_block(str(tokens[-2]))

            # For 'dolist': expects list symbol {body} dolist
            if last_token == "dolist":
                if len(tokens) < 4:
                    return False
                # Check if there's a code block before 'dolist'
                return is_code_block(str(tokens[-2]))

            # For 'times': expects {body} n times
            if last_token == "times":
                if len(tokens) < 3:
                    return False
                # Check if there's a code block two positions before 'times'
                return is_code_block(str(tokens[-3]))

            return True
        except Exception:
            # If parsing fails, assume it's incomplete
            return False
