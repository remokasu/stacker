from __future__ import annotations

import sys
import traceback

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
            formatted_error = ErrorFormatter.format_error(
                filename=None,
                line_number=None,
                column=None,
                error_type=type(e).__name__,
                message=str(e),
                source_line=None,
                hint=self._get_error_hint(e),
            )
            print(formatted_error, file=sys.stderr)
            if self.debug:
                traceback.print_exc()
            sys.exit(1)
