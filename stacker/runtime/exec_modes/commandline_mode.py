from __future__ import annotations

import sys
import traceback

from stacker.error import error_kind
from stacker.error_formatter import ErrorFormatter
from stacker.runtime.exec_modes.execution_mode import ExecutionMode


class CommandLineMode(ExecutionMode):
    """Runs the expression given with ``-e``."""

    def run(self, expression: str) -> None:
        try:
            self.rpn_calculator.eval(expression)
        except Exception as e:
            # Reported like the REPL does: the message, its type and a hint
            # on stderr. The expression is not quoted back, and no caret is
            # drawn: the interpreter does not record which word failed.
            filename, line_number, source_line, frames = None, None, None, []
            location = self._error_location(e)
            if location is not None:
                filename, line_number, source_line, frames = location  # type: ignore[assignment]
            formatted_error = ErrorFormatter.format_error(
                filename=filename,
                line_number=line_number,
                column=None,
                error_type=error_kind(e),
                message=str(e),
                source_line=source_line,
                hint=self._get_error_hint(e),
                frames=frames,
            )
            print(formatted_error, file=sys.stderr)
            if self.debug:
                traceback.print_exc()
            sys.exit(1)
