"""`Stacker(compile=...)` and `--no-compile` say whether blocks that run often are compiled; the choice reaches every core."""

import os
import subprocess
import sys

import pytest

from stacker import Stacker


def test_an_interpreter_compiles_unless_told_otherwise():
    assert Stacker()._compiles is True
    assert Stacker(compile=False)._compiles is False


@pytest.mark.parametrize("choice", [True, False])
def test_every_core_an_interpreter_makes_takes_its_choice(choice):
    stacker = Stacker(compile=choice)
    outer = next(iter(stacker.eval("{ { {1} } }")))
    inner = outer.tokens[0]
    innermost = inner.tokens[0]  # built while `inner` is, before `inner` has all its attributes
    stacker.process_expression("{x} {x} :f defun {y} {y} lambda :g set {a} {{a a +}} :twice defmacro")
    body = stacker.sfunctions["f"]["func"].blockstack
    lambda_body = next(iter(stacker.eval("g"))).blockstack
    expansion = next(iter(stacker.eval("{3} :twice macroexpand")))
    cores = (outer, inner, innermost, body, lambda_body, expansion, Stacker(parent=stacker))
    assert [core._compiles for core in cores] == [choice] * len(cores)


@pytest.mark.parametrize("parents_choice", [True, False])
def test_a_child_core_takes_its_parents_choice_whatever_it_is_told(parents_choice):
    parent = Stacker(compile=parents_choice)
    assert Stacker(parent=parent, compile=not parents_choice)._compiles is parents_choice


def test_a_copy_keeps_the_choice():
    assert Stacker(compile=False).copy()._compiles is False
    assert Stacker().copy()._compiles is True


def test_a_block_defined_by_an_included_file_takes_the_choice(tmp_path):
    (tmp_path / "f.stk").write_text("{1} :blk set\n", encoding="utf-8")
    stacker = Stacker(compile=False)
    stacker.include(str(tmp_path / "f.stk"))
    assert next(iter(stacker.eval("blk")))._compiles is False


# `stacker.__main__` reads its arguments when it is imported and sets the process-wide
# recursion limits, so the entry point is imported in a child process, with `Stacker`
# replaced by a recorder of what the command line passes it
SPY = """
import sys
sys.argv = ["stacker", *{flags!r}, "-e", "1 2 + echo"]
import stacker.__main__ as cli
made = []
real = cli.Stacker
cli.Stacker = lambda *args, **kwargs: made.append(kwargs.get("compile")) or real(*args, **kwargs)
cli.main()
print(made)
"""


@pytest.mark.parametrize(("flags", "compiles"), [([], True), (["--no-compile"], False)])
def test_the_command_line_passes_its_choice_to_the_interpreter(flags, compiles):
    # HOME points nowhere so that a ~/.stackerrc of the developer does not run
    env = {**os.environ, "HOME": "/nonexistent", "PYTHONPATH": os.pathsep.join(p for p in sys.path if p)}
    run = subprocess.run(
        [sys.executable, "-c", SPY.format(flags=flags)],
        capture_output=True,
        text=True,
        check=False,
        env=env,
        stdin=subprocess.DEVNULL,
    )
    assert run.returncode == 0, run.stderr
    assert run.stdout.splitlines() == ["3", str([compiles])]
