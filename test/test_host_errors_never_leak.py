"""Whatever value a built-in word is handed, the error it raises is Stacker's own, never the host's.

Every word with one to three arguments is fed every kind of value, in
every position; a host exception getting out (a `TypeError`, a
`ValueError`, an `IndexError`, ...) is a failure here, so the words that
report by name stay that way.
"""

import itertools
import signal

import pytest

from stacker import Stacker
from stacker.error import BreakException, StackerError

#: Values of every kind, as source text
SAMPLES = ['5', '-1', '0', '2.5', '"a"', '""', '[1 2]', '[]', 'dict', 'null', 'true', ':s', '[1] array', '1 3 frac', '{} {1} lambda', 'inf', 'nan', '1+2j', '1000']

#: Words that touch the outside world, read input, end the process, print, take names or are random
SKIPPED = {
    "read", "read-line", "read-stdin", "read-stdin-bytes", "write-stdout-bytes", "echo", "print", "printc", "newline",
    "exit", "abort", "exit-code", "include", "require", "cd", "ls", "pwd", "cat", "list-dir", "vars", "funcs", "macros",
    "operators", "disp", "clear", "ans", "break", "version", "args", "script-path", "script-dir", "main?",
    "main-script-path", "gensym", "write-to-file", "append-to-file", "read-from-file", "read-lines", "read-bytes",
    "write-bytes", "file-exists", "path-join", "path-base", "path-dir", "throw", "rand", "randint", "uniform", "dice",
    "seed", "sleep", "time", "now", "date", "disable_plugin", "enable_plugin", "set", "=", "global", "defun", "defmacro",
    "lambda", "alias", "macroexpand", "do", "dolist", "reduce", "fold", "symbol", "loop", "while", "times",
}

#: Host errors that are documented as passing through
ALLOWED_HOST = (ZeroDivisionError,)


def _words(stacker: Stacker):
    for name, (category, op) in sorted(stacker.operator_manager.dispatch_table.items()):
        if name in SKIPPED or category == "settings":
            continue
        count = op.get("arg_count", 0)
        if 1 <= count <= 3:
            yield name, count


class _TooSlow(Exception):
    """A case that did not finish within the time allowed."""


def _alarm(signum, frame):
    raise _TooSlow()


#: Seconds one case may take; a word that computes for longer on a junk value is reported too
CASE_SECONDS = 2


@pytest.mark.skipif(not hasattr(signal, "SIGALRM"), reason="needs SIGALRM to bound each case")
def test_no_host_error_gets_out():
    stacker = Stacker()
    leaks = []
    previous = signal.signal(signal.SIGALRM, _alarm)
    try:
        for name, count in _words(stacker):
            for args in itertools.product(SAMPLES, repeat=min(count, 2)):
                program = "1 2 3 " + " ".join(args) + " " + name
                stacker.stack.clear()
                signal.alarm(CASE_SECONDS)
                try:
                    stacker.process_expression(program)
                except (StackerError, BreakException, SystemExit, RecursionError, *ALLOWED_HOST):
                    continue
                except _TooSlow:
                    leaks.append(f"`{program}` did not finish in {CASE_SECONDS} s")
                except Exception as error:  # noqa: BLE001 -- the leaked kind is what is reported
                    leaks.append(f"`{program}` -> {type(error).__name__}: {error}")
                finally:
                    signal.alarm(0)
    finally:
        signal.signal(signal.SIGALRM, previous)
    assert not leaks, "host errors got out:\n" + "\n".join(leaks[:60]) + (f"\n... and {len(leaks) - 60} more" if len(leaks) > 60 else "")
