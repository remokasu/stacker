from __future__ import annotations

from stacker.exec_modes.excution_mode import ExecutionMode


class CommandLineMode(ExecutionMode):
    def run(self, expression: str):
        self.rpn_calculator.eval(expression)
