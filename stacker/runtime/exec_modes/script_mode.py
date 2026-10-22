from __future__ import annotations

import sys
import traceback
from pathlib import Path

from stacker.error import error_kind, ScriptReadError
from stacker.runtime.exec_modes.execution_mode import ExecutionMode
from stacker.lib.config import script_extension_name
from stacker.stacker import Stacker
from stacker.error_formatter import ErrorFormatter
# from stacker.util.color import colored
# from stacker.exec_modes.error import create_error_message


class ScriptMode(ExecutionMode):
    def __init__(self, rpn_calculator: Stacker):
        self.col_count = 0
        super().__init__(rpn_calculator)

    def run(self, file_path: str) -> None:
        try:
            path = Path(file_path)
            if not path.is_file() or not path.suffix == script_extension_name:
                raise ScriptReadError(
                    f"Invalid file path or file type. Please provide a valid '{script_extension_name}' file."
                )

            self.rpn_calculator.main_script = str(path.resolve())
            # Use the parent class's execute_stacker_dotfile which handles multi-line properly
            self.execute_stacker_dotfile(path)
            self.rpn_calculator.warn_values_left(path.name, self.rpn_calculator.stack)
        except Exception as e:
            # Format error using Clang-style formatter
            error_type = error_kind(e)
            message = str(e)

            # Get line number and source line from tracked information
            filename = str(Path(file_path).resolve())
            line_number = self.rpn_calculator.current_line
            source_line = None
            if line_number is not None and line_number in self.rpn_calculator.source_lines:
                source_line = self.rpn_calculator.source_lines[line_number]
            frames: list[str] = []
            # An error inside an included file is reported at its own line
            location = self._error_location(e)
            if location is not None:
                filename, line_number, source_line, frames = location  # type: ignore[assignment]

            column = None  # We don't track column yet

            # Generate hint based on error type
            hint = self._get_error_hint(e)

            # Format the error
            formatted_error = ErrorFormatter.format_error(
                filename=filename,
                line_number=line_number,
                column=column,
                error_type=error_type,
                message=message,
                source_line=source_line,
                hint=hint,
                frames=frames,
            )

            print(formatted_error, file=sys.stderr)

            # Parity with ReplMode: show the Python traceback in debug mode
            if self.debug:
                traceback.print_exc()
            sys.exit(1)
