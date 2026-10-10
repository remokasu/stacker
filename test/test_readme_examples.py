"""Every example in README.md must run against the current interpreter.

Two kinds of examples are checked:

* REPL transcripts (``stacker:N> expression`` followed by the displayed
  stack ``[...]`` and/or printed output). Each fenced block is one session;
  a prompt numbered ``0`` starts a fresh interpreter.
* The ``Example`` column of the operator tables, which only has to run
  without raising.

Examples that need a terminal, files or plugins are listed in ``SKIP`` with
the reason. A transcript step without a result line is only required to run
without raising; the README omits results in several places.
"""

from __future__ import annotations

import io
import re
from contextlib import redirect_stdout
from dataclasses import dataclass, field
from pathlib import Path

import pytest

from stacker.stacker import Stacker
from stacker.syntax.lexer import analyze_terminals
from stacker.util.disp import disp_default

README = Path(__file__).resolve().parent.parent / "README.md"

# Examples that cannot run inside the test process, with the reason.
SKIP: dict[str, str] = {
    '"my_script.stk" include': "needs a script file",
    '"file.stk" include': "needs a script file",
    "read": "reads standard input",
    "input": "reads standard input",
    '"hoge" disable_plugin': "needs a plugin",
    "exit": "terminates the interpreter",
    '"file.txt" read-from-file': "needs a file",
    '"input.txt" read-from-file': "needs a file",
    '3 "output.txt" write-to-file': "writes a file",
    '3 "output.txt" append-to-file': "writes a file",
    "break": "only meaningful inside a loop",
    '{0 >} {"neg" echo} {unless} macroexpand': "uses the `unless` macro defined in the text",
}

# Operator-table examples run on this stack, so stack words have operands.
# Table examples are only required not to raise; their results are not checked.
TABLE_STACK = "1 2 3 4 5"

PROMPT = re.compile(r"^\s*stacker:(\d+)>\s?(.*)$")
CONTINUATION = re.compile(r"^\s*(\.\.\.\s*)?>\s?")  # `... > more input`
# Settings handled by the REPL itself, not by the interpreter.
REPL_COMMANDS = {
    "about", "delete_history", "end", "help",
    "enable_disp_ans", "disable_disp_ans",
    "enable_disp_logo", "disable_disp_logo",
    "enable_disp_stack", "disable_disp_stack",
}
STACK_LINE = re.compile(r"^\s*\[.*\]\s*$")
TABLE_ROW = re.compile(r"^\|\s*(\S[^|]*?)\s*\|[^|]*\|\s*`([^`]*)`\s*\|\s*$")


@dataclass
class Step:
    """One REPL input and what the README says follows it."""

    line: int
    prompt_number: int
    expression: str
    expected_stack: str | None = None
    expected_output: list[str] = field(default_factory=list)


def _read_transcripts() -> list[tuple[int, list[Step]]]:
    """Returns (start line, steps) for every fenced block with prompts."""
    sessions: list[tuple[int, list[Step]]] = []
    steps: list[Step] = []
    in_fence = False
    block_start = 0
    for number, raw in enumerate(README.read_text(encoding="utf-8").splitlines(), 1):
        if raw.strip().startswith("```"):
            if in_fence and steps:
                sessions.append((block_start, steps))
            in_fence = not in_fence
            steps = []
            block_start = number
            continue
        if not in_fence:
            continue
        prompt = PROMPT.match(raw)
        if prompt:
            steps.append(Step(number, int(prompt.group(1)), prompt.group(2).strip()))
            continue
        if not steps:
            continue
        current = steps[-1]
        if not analyze_terminals(current.expression).complete:
            current.expression += "\n" + CONTINUATION.sub("", raw.strip())
        elif STACK_LINE.match(raw) and current.expected_stack is None:
            current.expected_stack = raw.strip()
        elif raw.strip():
            current.expected_output.append(raw.strip())
    return sessions


def _transcript_cases() -> list[pytest.param]:
    cases = []
    for start, steps in _read_transcripts():
        cases.append(pytest.param(steps, id=f"README:{start}"))
    assert cases, "no REPL transcripts found in README.md; did its format change?"
    return cases


@pytest.mark.parametrize("steps", _transcript_cases())
def test_repl_transcript(steps: list[Step]) -> None:
    stacker = Stacker()
    for step in steps:
        # Later steps depend on the skipped one, so the rest of the block is
        # skipped too; the message names the line so the gap is visible.
        if step.expression in SKIP:
            pytest.skip(f"README.md:{step.line}: {SKIP[step.expression]}")
        if step.expression in REPL_COMMANDS:
            pytest.skip(f"README.md:{step.line}: REPL-only command")
        if step.prompt_number == 0 and step is not steps[0]:
            stacker = Stacker()  # a prompt numbered 0 starts a new session
        buffer = io.StringIO()
        with redirect_stdout(buffer):
            stacker.process_expression(step.expression)
        if step.expected_stack is not None:
            shown = disp_default(list(stacker.stack))
            assert shown == step.expected_stack, (
                f"README.md:{step.line}: `{step.expression}` displays {shown}"
            )
        printed = [line for line in buffer.getvalue().splitlines() if line.strip()]
        expected = [line for line in step.expected_output if not line.startswith("#")]
        if expected:
            assert printed == expected, (
                f"README.md:{step.line}: `{step.expression}` printed {printed}"
            )


def _table_cases() -> list[pytest.param]:
    cases = []
    for number, raw in enumerate(README.read_text(encoding="utf-8").splitlines(), 1):
        row = TABLE_ROW.match(raw)
        if not row or row.group(1) in ("Operator", "Command"):
            continue
        for example in re.split(r"`,\s*`", row.group(2)):
            cases.append(pytest.param(example, id=f"README:{number}:{row.group(1)}"))
    assert cases, "no operator-table examples found in README.md; did its format change?"
    return cases


@pytest.mark.parametrize("example", _table_cases())
def test_operator_table_example_runs(example: str) -> None:
    if example in SKIP:
        pytest.skip(SKIP[example])
    stacker = Stacker()
    with redirect_stdout(io.StringIO()):
        stacker.process_expression(TABLE_STACK)
        stacker.process_expression(example)
