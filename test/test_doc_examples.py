"""Every example in README.md and docs/ must run against the current interpreter.

Two kinds of examples are checked:

* REPL transcripts (``stacker:N> expression`` followed by the displayed
  stack ``[...]`` and/or printed output). Each fenced block is one session;
  a prompt numbered ``0`` starts a fresh interpreter.
* The ``Example`` column (``例`` in Japanese) of the operator tables, which
  only has to run without raising. Every row of such a table must be
  ``| word | description | `example` |``.

Examples that need a terminal, files or plugins are listed in ``SKIP`` with
the reason. A transcript step without a result line is only required to run
without raising; the README omits results in several places.

The manual under docs/ is also checked for shape: the Example tables of its
operator reference list every word of the language (constants and the
literals ``true`` / ``false`` / ``null`` included) and nothing else, its
relative links resolve, and docs/VERSION names a release. REPL-only commands
such as ``help`` are not words of the language; repl-and-cli.md lists them.
"""

from __future__ import annotations

import io
import re
from contextlib import redirect_stdout
from dataclasses import dataclass, field
from pathlib import Path

import pytest

from stacker.constant import constants
from stacker.stacker import Stacker
from stacker.syntax.lexer import analyze_terminals
from stacker.syntax.token_rules import KEYWORD_LITERALS
from stacker.util.disp import disp_default

ROOT = Path(__file__).resolve().parent.parent
README = ROOT / "README.md"
DOCS = ROOT / "docs"
# Both languages have the same pages.
LANGUAGES = ("ja", "en")

# Examples that cannot run inside the test process, with the reason.
SKIP: dict[str, str] = {
    '"my_script.stk" include': "needs a script file",
    '"file.stk" include': "needs a script file",
    '"file.stk" require': "needs a script file",
    "read": "reads standard input",
    "read-line": "reads standard input",
    "read-stdin": "reads standard input",
    "read-stdin-bytes": "reads standard input",
    "[72 105 10] write-stdout-bytes": "writes raw bytes to standard output",
    '"image.png" read-bytes': "needs a file",
    '[72 105] "out.bin" write-bytes': "writes a file",
    '"hoge" disable_plugin': "needs a plugin",
    "exit": "terminates the interpreter",
    '"file.txt" read-from-file': "needs a file",
    '"input.txt" read-from-file': "needs a file",
    '3 "output.txt" write-to-file': "writes a file",
    '3 "output.txt" append-to-file': "writes a file",
    "break": "only meaningful inside a loop",
    '".." cd': "changes the working directory of the test process",
    '"file.txt" cat': "needs a file",
    '"input.txt" read-lines': "needs a file",
    "1 exit-code": "terminates the interpreter",
    "abort": "terminates the interpreter",
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
# The last header cell of a three-column table whose rows are
# `| word | description | `example` |`.
EXAMPLE_HEADERS = {"Example", "例"}
# A table cell boundary; `\|` is a pipe inside a cell (e.g. the `||` operator).
CELL_SEPARATOR = re.compile(r"(?<!\\)\|")
SEPARATOR_ROW = re.compile(r"^\s*\|[\s:|-]+\|\s*$")  # `|---|:---:|`
# A Markdown link target, e.g. the `syntax.md` in `[Syntax](syntax.md)`.
LINK_TARGET = re.compile(r"\]\(([^)\s]+)\)")


def _name(path: Path) -> str:
    """Returns the path as written in messages, relative to the repository."""
    return path.relative_to(ROOT).as_posix()


def _pages() -> list[Path]:
    """Returns every page of the manual, in a stable order."""
    return [path for language in LANGUAGES for path in sorted((DOCS / language).glob("*.md"))]


def _documents() -> list[Path]:
    """Returns every document whose examples are run."""
    return [README, *_pages()]


@dataclass
class Step:
    """One REPL input and what the document says follows it."""

    source: str
    line: int
    prompt_number: int
    expression: str
    expected_stack: str | None = None
    expected_output: list[str] = field(default_factory=list)

    @property
    def where(self) -> str:
        return f"{self.source}:{self.line}"


def _read_transcripts(path: Path) -> list[tuple[int, list[Step]]]:
    """Returns (start line, steps) for every fenced block with prompts."""
    sessions: list[tuple[int, list[Step]]] = []
    steps: list[Step] = []
    in_fence = False
    block_start = 0
    for number, raw in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
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
            steps.append(
                Step(_name(path), number, int(prompt.group(1)), prompt.group(2).strip())
            )
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
    for path in _documents():
        for start, steps in _read_transcripts(path):
            cases.append(pytest.param(steps, id=f"{_name(path)}:{start}"))
    assert cases, "no REPL transcripts found in README.md; did its format change?"
    return cases


@pytest.mark.parametrize("steps", _transcript_cases())
def test_repl_transcript(steps: list[Step]) -> None:
    stacker = Stacker()
    for step in steps:
        # Later steps depend on the skipped one, so the rest of the block is
        # skipped too; the message names the line so the gap is visible.
        if step.expression in SKIP:
            pytest.skip(f"{step.where}: {SKIP[step.expression]}")
        if step.expression in REPL_COMMANDS:
            pytest.skip(f"{step.where}: REPL-only command")
        if step.prompt_number == 0 and step is not steps[0]:
            stacker = Stacker()  # a prompt numbered 0 starts a new session
        buffer = io.StringIO()
        with redirect_stdout(buffer):
            stacker.process_expression(step.expression)
        if step.expected_stack is not None:
            shown = disp_default(list(stacker.stack))
            assert shown == step.expected_stack, (
                f"{step.where}: `{step.expression}` displays {shown}"
            )
        printed = [line for line in buffer.getvalue().splitlines() if line.strip()]
        expected = [line for line in step.expected_output if not line.startswith("#")]
        if expected:
            assert printed == expected, (
                f"{step.where}: `{step.expression}` printed {printed}"
            )


def _table_cells(raw: str) -> list[str] | None:
    """Returns the cells of a Markdown table row with `\\|` unescaped, or None."""
    line = raw.strip()
    if len(line) < 2 or not line.startswith("|") or not line.endswith("|"):
        return None
    return [cell.strip().replace("\\|", "|") for cell in CELL_SEPARATOR.split(line[1:-1])]


def _example_table_rows(path: Path) -> list[tuple[int, list[str]]]:
    """Returns (line, cells) for the body rows of every Example table.

    An Example table has three columns and its header ends in an
    ``EXAMPLE_HEADERS`` cell; other tables (options, constants without
    examples, two-column "place | example" lists, ...) are not run.
    """
    rows = []
    header: list[str] | None = None
    for number, raw in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
        cells = _table_cells(raw)
        if cells is None:
            header = None
        elif header is None:
            header = cells
        elif len(header) == 3 and header[2] in EXAMPLE_HEADERS and not SEPARATOR_ROW.match(raw):
            rows.append((number, cells))
    return rows


def _row_examples(cells: list[str]) -> list[str] | None:
    """Returns the examples of `| word | description | `a`, `b` |`, or None."""
    if len(cells) != 3 or not cells[0]:
        return None
    example = cells[2]
    if len(example) < 2 or not (example.startswith("`") and example.endswith("`")):
        return None
    return re.split(r"`,\s*`", example[1:-1])


def _table_rows(path: Path) -> list[tuple[int, str, list[str]]]:
    """Returns (line, first cell, examples) for every well-formed Example row."""
    rows = []
    for number, cells in _example_table_rows(path):
        examples = _row_examples(cells)
        if examples is not None:
            rows.append((number, cells[0], examples))
    return rows


def test_example_tables_are_well_formed() -> None:
    # A row that does not parse would silently drop out of every check below,
    # e.g. an example with an unescaped `|` splits into four cells.
    malformed = [
        f"{_name(path)}:{number}"
        for path in _documents()
        for number, cells in _example_table_rows(path)
        if _row_examples(cells) is None
    ]
    assert not malformed, (
        f"Example-table rows must be `| word | description | `example` |`: {malformed}"
    )


def _table_cases() -> list[pytest.param]:
    cases = []
    for path in _documents():
        for number, word, examples in _table_rows(path):
            for example in examples:
                cases.append(pytest.param(example, id=f"{_name(path)}:{number}:{word}"))
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


def _language_words() -> set[str]:
    """Returns every word a fresh interpreter knows without user definitions."""
    stacker = Stacker()
    return (
        set(stacker.operator_manager.built_in_operators)
        # No public accessor for the prelude's names; the `funcs` word reads it too.
        | set(stacker._prelude["names"])
        | set(constants)
        | {word for word in KEYWORD_LITERALS if word.islower()}  # true / false / null
    )


def _documented_words(path: Path) -> set[str]:
    """Returns the words listed in the first column of the reference tables.

    One row may list several spellings of the same word, e.g. `reduce`, `fold`.
    """
    words = set()
    for _, first, _ in _table_rows(path):
        words.update(word.strip().strip("`") for word in first.split(", "))
    return words


@pytest.mark.parametrize("language", LANGUAGES)
def test_operator_reference_lists_every_word(language: str) -> None:
    reference = DOCS / language / "operators.md"
    if not reference.exists():
        pytest.skip(f"{_name(reference)} is not written yet")
    documented = _documented_words(reference)
    words = _language_words()
    assert not words - documented, (
        f"{_name(reference)} does not list {sorted(words - documented)}"
    )
    assert not documented - words, (
        f"{_name(reference)} lists words that do not exist: {sorted(documented - words)}"
    )


def _outside_fences(text: str) -> str:
    """Returns the text without fenced code blocks, which may show sample links."""
    kept = []
    in_fence = False
    for line in text.splitlines():
        if line.strip().startswith("```"):
            in_fence = not in_fence
        elif not in_fence:
            kept.append(line)
    return "\n".join(kept)


@pytest.mark.parametrize(
    "path", [README, DOCS / "README.md", *_pages()], ids=lambda path: _name(path)
)
def test_relative_links_resolve(path: Path) -> None:
    if not path.exists():
        pytest.skip(f"{_name(path)} is not written yet")
    for target in LINK_TARGET.findall(_outside_fences(path.read_text(encoding="utf-8"))):
        if target.startswith(("http://", "https://", "mailto:", "#")):
            continue
        linked = path.parent / target.split("#", 1)[0]
        assert linked.exists(), f"{_name(path)} links to missing {target}"


def test_docs_version_names_a_release() -> None:
    version = DOCS / "VERSION"
    if not version.exists():
        pytest.skip("docs/VERSION is not written yet")
    text = version.read_text(encoding="utf-8").strip()
    assert re.fullmatch(r"1\.\d+\.\d+", text), f"docs/VERSION is {text!r}, not 1.X.Y"
