"""Where the words that talk to the outside world read from and write to.

A ``Console`` is the interpreter's view of the standard streams. The
default one looks ``sys.stdout``, ``sys.stderr``, ``sys.stdin`` and the
built-in ``input`` up each time it is asked, so a stream replaced after
the interpreter was made (a redirect, a test double) is honoured, as it
always was. A program embedding the interpreter passes its own console
to ``Stacker(console=...)``; the words then write there instead.

The console in effect is a context variable set by the interpreter's
entry points (``eval``, ``process_expression``, ``run_file``, ``include``
and ``require``) for as long as they run, so a word reads it with the
module functions below and never needs the interpreter object. Outside
any entry point the default console is in effect: ``Stacker.evaluate``
is not an entry point and runs under whatever console its caller has, and
a new thread starts with the default console, so code run there goes
through an entry point of its own. A plugin word that prints writes to
``stdout()`` from this module, so its output follows the interpreter's.

`exit`, `abort` and `exit-code` are not on the console: they raise
``SystemExit`` as they always did, and a program embedding the
interpreter catches it as it would from any other Python code.
"""

from __future__ import annotations

import builtins
import sys
from contextvars import ContextVar, Token
from typing import TextIO


class Console:
    """The standard streams as the words see them: ``sys`` looked up at each call.

    Subclass it, or use ``StreamConsole``, to send a program's output
    elsewhere. Every method must return a stream (never None), and
    ``input_line`` must return one line without its line break and raise
    ``EOFError`` at the end of input: that is what `read` relies on.
    """

    def stdout(self) -> TextIO:
        """The stream `echo`, `print`, `disp`, `vars` and their kin write to."""
        return sys.stdout

    def stderr(self) -> TextIO:
        """The stream `echo-err` and `print-err` write to."""
        return sys.stderr

    def stdin(self) -> TextIO:
        """The stream `read-line`, `read-stdin` and the byte words read from."""
        return sys.stdin

    def input_line(self) -> str:
        """One line of input for `read`, without its line break.

        The default is the built-in ``input`` itself, which flushes the
        output first and offers line editing on a terminal; it reads
        ``sys.stdin``, not ``stdin()``, so a subclass that takes `read`
        elsewhere overrides this method too.

        Raises:
            EOFError: The input has ended.
        """
        return builtins.input()

    def __copy__(self) -> Console:
        """A console is shared, never copied: a copied interpreter writes where the original does."""
        return self

    def __deepcopy__(self, memo: dict[int, object]) -> Console:
        """A console is shared, never copied (a stream cannot be deep-copied)."""
        return self


class StreamConsole(Console):
    """A console writing to and reading from the streams given to it.

    A stream left as None falls back to the ``sys`` stream of the same
    name, looked up at each call.

    Args:
        stdout: Where normal output goes.
        stderr: Where error output goes.
        stdin: Where `read`, `read-line` and `read-stdin` read from.
    """

    def __init__(
        self,
        stdout: TextIO | None = None,
        stderr: TextIO | None = None,
        stdin: TextIO | None = None,
    ) -> None:
        self._stdout = stdout
        self._stderr = stderr
        self._stdin = stdin

    def stdout(self) -> TextIO:
        """The ``stdout`` given, else ``sys.stdout``."""
        return self._stdout if self._stdout is not None else super().stdout()

    def stderr(self) -> TextIO:
        """The ``stderr`` given, else ``sys.stderr``."""
        return self._stderr if self._stderr is not None else super().stderr()

    def stdin(self) -> TextIO:
        """The ``stdin`` given, else ``sys.stdin``."""
        return self._stdin if self._stdin is not None else super().stdin()

    def input_line(self) -> str:
        """One line of ``stdin`` without its line break, read as the built-in ``input`` reads a file.

        Standard error and then standard output are flushed first, so a
        prompt written with `printc` shows before the input is waited
        for; a stream that cannot be flushed is passed over, as ``input``
        does.

        Raises:
            EOFError: The input has ended.
            RuntimeError: There is no input stream (``sys.stdin`` is None).
        """
        for stream in (self.stderr(), self.stdout()):
            try:
                stream.flush()
            except (AttributeError, OSError, ValueError):
                pass
        source = self.stdin()
        if source is None:
            raise RuntimeError("input(): lost sys.stdin")
        line = source.readline()
        if line == "":
            raise EOFError("EOF when reading a line")
        return line.removesuffix("\n")


#: The console in effect when no interpreter entry point is running
DEFAULT_CONSOLE = Console()

_active: ContextVar[Console] = ContextVar("stacker_console", default=DEFAULT_CONSOLE)


def current() -> Console:
    """The console in effect for the running code."""
    return _active.get()


def activate(console: Console) -> Token[Console]:
    """Makes ``console`` the one in effect until ``deactivate`` is given the returned token."""
    return _active.set(console)


def deactivate(token: Token[Console]) -> None:
    """Restores the console that was in effect before the matching ``activate``."""
    _active.reset(token)


def stdout() -> TextIO:
    """The stream normal output goes to, for the running code."""
    return current().stdout()


def stderr() -> TextIO:
    """The stream error output goes to, for the running code."""
    return current().stderr()


def stdin() -> TextIO:
    """The stream input is read from, for the running code."""
    return current().stdin()


def input_line() -> str:
    """One line of input without its line break, for the running code; ``EOFError`` at the end."""
    return current().input_line()
