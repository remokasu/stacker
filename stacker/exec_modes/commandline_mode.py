from __future__ import annotations

import sys

from stacker.exec_modes.error import create_error_message
from stacker.exec_modes.excution_mode import ExecutionMode


class CommandLineMode(ExecutionMode):
    def run(self, expression: str):
        try:
            self.rpn_calculator.eval(expression)
        except Exception as e:
            print(f"{type(e).__name__}: {e}")
            trace = self.rpn_calculator.get_trace_copy()
            if len(trace) == 0:
                sys.exit(1)
            if len(trace) > 4:
                error_trace = trace[-4:]
            else:
                error_trace = trace
            print(create_error_message(error_trace))
            sys.exit(1)
