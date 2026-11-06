from __future__ import annotations

from collections.abc import Callable, Iterator
from dataclasses import dataclass, field
from pathlib import Path
from typing import TYPE_CHECKING

from stacker.data_type import stack_data
from stacker.error import (
    BreakException,
    IncludeError,
    UnterminatedTokenError,
    attach_include_location,
)
from stacker.syntax.parser import parse_expression, remove_start_end_quotes
from stacker.syntax.script import SCRIPT_EXTENSION, iter_expressions, read_script

if TYPE_CHECKING:
    from stacker.engine.core import StackerCore


def candidate_paths(filename: str | Path, base_dir: Path | None = None) -> list[Path]:
    """The paths an include target may stand for, in search order.

    Args:
        filename: Include target as written in the script.
        base_dir: Directory of the including file, or None when the
            includer has no file context (REPL, ``-e``).

    Returns:
        The absolute path itself, or the relative path under ``base_dir``
        (when given) and under the current working directory.
    """
    path = Path(filename)
    if path.is_absolute():
        return [path]
    search_dirs = [Path(base_dir)] if base_dir is not None else []
    search_dirs.append(Path.cwd())
    return [directory / path for directory in search_dirs]


def resolve_include_path(filename: str | Path, base_dir: Path | None = None) -> Path:
    """Resolve an include target using the search order.

    Absolute paths are taken as-is. Relative paths are searched first in
    ``base_dir`` (the including file's directory), then the current
    working directory. A future library path becomes one more entry in
    the search list.

    Args:
        filename: Include target as written in the script.
        base_dir: Directory of the including file, or None when the
            includer has no file context (REPL, ``-e``).

    Returns:
        The first existing candidate path.

    Raises:
        IncludeError: If no candidate exists (the message lists every
            tried absolute path) or the match is not a ``.stk`` file.
    """
    candidates = candidate_paths(filename, base_dir)
    for candidate in candidates:
        if candidate.is_file():
            if candidate.suffix != SCRIPT_EXTENSION:
                raise IncludeError(f"File {filename} is not a stacker script.")
            return candidate

    tried = ", ".join(str(candidate.resolve()) for candidate in candidates)
    raise IncludeError(f"File {filename} not found. Tried: {tried}")


ENTRY = "entry"  #: kind of the frame of the script the interpreter was started on
INCLUDE = "include"  #: kind of a frame of a file read by `include` / `require`


@dataclass
class Frame:
    """One file being run: its resolved path, its kind and the line of the expression it is on."""

    path: Path
    kind: str
    line: int | None = None


@dataclass
class IncludeState:
    """The per-interpreter record of what is being and has been included.

    ``stack`` holds one frame per file being run, outermost first; ``loaded``
    the resolved paths of every file run to its end, which `require`
    consults. Made once on the root core and shared by reference with every
    child core.
    """

    stack: list[Frame] = field(default_factory=list)
    loaded: set[Path] = field(default_factory=set)

    def is_including(self) -> bool:
        """True while a file read by `include` / `require` is running."""
        return any(frame.kind == INCLUDE for frame in self.stack)


def push_entry_file(stacker: StackerCore, path: Path) -> None:
    """Puts the script the interpreter was started on at the bottom of the include stack.

    A script that includes itself is then caught before it runs twice,
    and an error inside an included file can say which line of the script
    included it (the script runner keeps ``current_line`` up to date).

    Args:
        stacker: The root interpreter.
        path: The script's path.
    """
    stacker._includes.stack.append(Frame(path.resolve(), ENTRY))


def pop_entry_file(stacker: StackerCore) -> None:
    """Removes the frame ``push_entry_file`` put on the include stack."""
    stacker._includes.stack.pop()


def expressions_of(code: str, set_line: Callable[[int | None], None]) -> Iterator[str]:
    """Yields the expressions of ``code``, telling ``set_line`` each one's line first.

    Every file the interpreter runs (a script, ``~/.stackerrc``, an
    included file) reads its expressions through here. They are read
    lazily, so what comes before an unterminated construct at the end of
    the file runs before the error is raised, and the error is raised
    after ``set_line`` was given the line the construct started on.

    Args:
        code: The file's text.
        set_line: Called with the line an expression starts on, before the
            expression is yielded, and with the start line of an
            unterminated construct, before the error is raised.

    Yields:
        Each expression's text, in order.

    Raises:
        UnterminatedTokenError: The text ends inside a string, list, block
            or block comment.
    """
    expressions = iter_expressions(code)
    while True:
        try:
            line, expression = next(expressions)
        except StopIteration:
            return
        except UnterminatedTokenError as error:
            set_line(error.start_line)
            raise
        set_line(line)
        yield expression


def _already_read(target_name: str, base_dir: Path | None, loaded: set[Path]) -> bool:
    """Whether `require` of ``target_name`` has nothing to do: its file was run to its end.

    The file is the first existing candidate in search order, as
    ``resolve_include_path`` would pick it; a file read earlier and deleted
    since still counts as read.
    """
    candidates = candidate_paths(target_name, base_dir)
    existing = next((candidate for candidate in candidates if candidate.is_file()), None)
    if existing is not None:
        return existing.resolve() in loaded
    return any(candidate.resolve() in loaded for candidate in candidates)


@dataclass
class Started:
    """A file the rule let through, about to run: what ``include_file`` and the machine's `include` do alike.

    ``start_include`` applies the rule and makes one. The caller marks the
    file as running with ``begin``, runs ``expressions`` one by one on
    ``runner``, and when the file is over calls ``stop``, then ``end`` if it
    ran to its end or ``tag`` on the error that stopped it.
    """

    runner: StackerCore  #: the child core the file's expressions run on
    expressions: Iterator[str]  #: the file's expressions, read as they come (each one's line is set first)
    resolved: Path  #: the file's resolved path
    source_lines: dict[int, str]  #: the file's lines, for the error report
    frames: list[tuple[str, int | None]]  #: the files that included it, innermost first, with their lines
    state: IncludeState  #: the interpreter's include state
    running: Frame  #: the file's frame on the include stack

    def begin(self) -> None:
        """Puts the file on the include stack: it is running, and a file that includes it again is circular."""
        self.state.stack.append(self.running)

    def stop(self) -> None:
        """Takes the file off the include stack: it is no longer running, however it ended."""
        self.state.stack.pop()

    def end(self, file_stack: stack_data[object]) -> None:
        """The file ran to its end: what it left is dropped and named, and `require` remembers it."""
        self.runner.warn_values_left(self.resolved.name, file_stack)  # what a file leaves is dropped; it is named first
        self.state.loaded.add(self.resolved)

    def tag(self, error: BaseException) -> None:
        """Records on ``error`` (a `break` too) where in the file it was raised."""
        attach_include_location(
            error, str(self.resolved), self.running.line, self.source_lines.get(self.running.line or 0), self.frames
        )


def start_include(core: StackerCore, filename: str, once: bool) -> Started | None:
    """Applies the rule of `include` and `require` to ``filename`` and prepares the file to run.

    The one place the rule is written: the path is resolved from the
    including file's directory, then the current directory; a file already
    running is circular; a `require` of a file run to its end has nothing
    to do; the entry script's line is recorded for the error report; and a
    child core of ``core`` is made to run the file, in ``core``'s scope for
    `include` and in the root scope for `require`, carrying the file's own
    position.

    Args:
        core: The core that executed the word (its ``current_file`` is
            where relative paths resolve from).
        filename: The path as written in the script.
        once: True for `require`.

    Returns:
        The file, ready to run; None when `require` has nothing to do (the
        file is not even opened).

    Raises:
        IncludeError: The file is not found, is not a ``.stk`` file, or is
            already being included (a circular include).
    """
    base_dir = Path(core.current_file).parent if core.current_file else None
    target_name = remove_start_end_quotes(filename)
    state: IncludeState = core._includes
    if once and _already_read(target_name, base_dir, state.loaded):
        return None
    found = resolve_include_path(target_name, base_dir)
    resolved = found.resolve()
    if any(frame.path == resolved for frame in state.stack):
        raise IncludeError(f"Circular include detected: {filename}")

    code = read_script(found)
    # The entry script's line is the expression the script runner is on
    # (the line that includes, or that calls the function that includes).
    # It is recorded now, before a nested include moves the root's line on
    if state.stack and state.stack[-1].kind == ENTRY:
        root = core
        while root.parent is not None:
            root = root.parent
        state.stack[-1].line = root.current_line
    frames = [(str(frame.path), frame.line) for frame in reversed(state.stack)]

    # A child core runs the file: it carries the file's own position, and
    # `require` gives it the root scope wherever the word is written
    runner = type(core)(parent=core)
    if once:
        runner.variables = core.variables.root()
    runner.current_file = str(resolved)
    source_lines = dict(enumerate(code.splitlines(), start=1))
    runner.source_lines = source_lines
    running = Frame(resolved, INCLUDE)

    def set_line(line: int | None) -> None:
        running.line = line
        runner.current_line = line

    return Started(runner, expressions_of(code, set_line), resolved, source_lines, frames, state, running)


def include_file(core: StackerCore, filename: str, once: bool = False) -> None:
    """Runs a script here, in ``core``'s interpreter: the `include` and `require` words.

    The file is read expression by expression, as a script is, and each
    expression is evaluated by a child core of ``core``: in ``core``'s
    scope for `include`, in the root scope for `require`. Nothing is
    copied. The file starts with an empty stack and what it leaves there
    is dropped. While it runs, relative paths resolve against its own
    directory and an error raised inside it is tagged with its file and
    line (see ``attach_include_location``). The rule is ``start_include``'s.

    Args:
        core: The core that executed the word (its ``current_file`` is
            where relative paths resolve from).
        filename: The path as written in the script.
        once: True for `require`: a file already run to its end in this
            interpreter is not run again, nor even opened.

    Raises:
        IncludeError: The file is not found, is not a ``.stk`` file, or is
            already being included (a circular include).
    """
    started = start_include(core, filename, once)
    if started is None:
        return
    started.begin()
    file_stack: stack_data[object] = stack_data()
    try:
        for expression in started.expressions:
            started.runner.evaluate(parse_expression(expression), stack=file_stack)
    except (Exception, BreakException) as error:  # a `break` is tagged too; SystemExit passes
        started.tag(error)
        raise
    finally:
        started.stop()
    started.end(file_stack)
