from __future__ import annotations

import sys
from pathlib import Path

from stacker.error import ScriptReadError, StackerError
from stacker.runtime.exec_modes.execution_mode import ExecutionMode
from stacker.include.stk_file_read import readtxt
from stacker.lib.config import script_extension_name
from stacker.stacker import Stacker
from stacker.error_formatter import ErrorFormatter
# from stacker.util.color import colored
# from stacker.exec_modes.error import create_error_message


class ScriptMode(ExecutionMode):
    def __init__(self, rpn_calculator: Stacker):
        self.col_count = 0
        super().__init__(rpn_calculator)

    def run(self, file_path: str):
        try:
            path = Path(file_path)
            if not path.is_file() or not path.suffix == script_extension_name:
                raise ScriptReadError(
                    f"Invalid file path or file type. Please provide a valid '{script_extension_name}' file."
                )

            # Use the parent class's execute_stacker_dotfile which handles multi-line properly
            self.execute_stacker_dotfile(path)
        except Exception as e:
            # Format error using Clang-style formatter
            error_type = type(e).__name__
            message = str(e)

            # Get line number and source line from tracked information
            line_number = self.rpn_calculator.current_line
            source_line = None
            if line_number is not None and line_number in self.rpn_calculator.source_lines:
                source_line = self.rpn_calculator.source_lines[line_number]

            column = None  # We don't track column yet

            # Generate hint based on error type
            hint = self._get_error_hint(e)

            # Format the error
            formatted_error = ErrorFormatter.format_error(
                filename=str(Path(file_path).resolve()),
                line_number=line_number,
                column=column,
                error_type=error_type,
                message=message,
                source_line=source_line,
                hint=hint
            )

            print(formatted_error, file=sys.stderr)
            sys.exit(1)

    def _get_error_hint(self, error: Exception) -> str:
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

        # with path.open('r') as script_file:
        #     expression = ''
        #     for line in script_file:
        #         line = line.strip()
        #         if line.startswith('#') or not line:  # ignore comments and empty lines
        #             continue
        #         expression += line + ' '
        #         if self._is_balanced(expression):
        #             if expression[-2:] in {";]", ";)"}:
        #                 closer = expression[-1]
        #                 expression = expression[:-2] + closer
        #             self.rpn_calculator.process_expression(expression)
        #             expression = ''
