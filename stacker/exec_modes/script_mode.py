from __future__ import annotations

from pathlib import Path

from stacker.stacker import Stacker
from stacker.util.string_parser import (
    is_brace_balanced,
    is_tuple_balanced,
    is_array_balanced,
    is_tuple,
    is_array
)
from stacker.exec_modes.excution_mode import ExecutionMode
from stacker.lib.config import script_extension_name

class ScriptMode(ExecutionMode):

    def __init__(self, rpn_calculator: Stacker):
        super().__init__(rpn_calculator)

    def run(self, file_path: str):
        path = Path(file_path)
        if not path.is_file() or not path.suffix == script_extension_name:
            raise ValueError(f"Invalid file path or file type. Please provide a valid '{script_extension_name}' file.")

        with path.open('r') as script_file:
            expression = ''
            for line in script_file:
                line = line.strip()
                if line.startswith('#') or not line:  # ignore comments and empty lines
                    continue
                expression += line + ' '
                if self._is_balanced(expression):
                    if expression[-2:] in {";]", ";)"}:
                        closer = expression[-1]
                        expression = expression[:-2] + closer
                    self.rpn_calculator.process_expression(expression)
                    expression = ''

    def _is_balanced(self, expression: str) -> bool:
        return (
            is_array_balanced(expression) and
            is_tuple_balanced(expression) and
            is_brace_balanced(expression) and
            (expression.count('"""') % 2 == 0) and
            (expression.count("'''") % 2 == 0)
        )
