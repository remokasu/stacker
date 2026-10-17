"""Every built-in word reaches the completer, `help` and `operators`, whatever its category."""

import io
from contextlib import redirect_stdout

from stacker import Stacker
from stacker.runtime.exec_modes import ReplMode


def _every_word(stacker: Stacker) -> set[str]:
    # `ans` is the REPL's; the settings words are left out of the completer on purpose
    manager = stacker.operator_manager
    return set(manager.built_in_operators) - {"ans"} - set(manager.operators["settings"])


def test_the_completer_knows_every_word():
    stacker = Stacker()
    assert _every_word(stacker) <= set(stacker.get_all_keys_for_completer())


def test_help_lists_every_word():
    stacker = Stacker()
    out = io.StringIO()
    with redirect_stdout(out):
        ReplMode(stacker)._cmd_help()
    listed = {line.strip().split(":", 1)[0] for line in out.getvalue().splitlines() if line.startswith("  ")}
    assert _every_word(stacker) <= listed


def test_operators_lists_every_word():
    stacker = Stacker()
    out = io.StringIO()
    with redirect_stdout(out):
        stacker.process_expression("operators")
    listed = {line.strip().split(":", 1)[0] for line in out.getvalue().splitlines() if line.startswith("  ")}
    assert _every_word(stacker) <= listed
