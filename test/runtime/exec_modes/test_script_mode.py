"""Tests for how the script runner reports a script that fails: the whole text on standard error."""

from __future__ import annotations

import pytest

from stacker.runtime.exec_modes.script_mode import ScriptMode
from stacker.stacker import Stacker

FAILING_SCRIPTS = [
    pytest.param(
        {"main.stk": '1 2 +\n"x" drop\nfoo\n'},
        "main.stk",
        "<DIR>/main.stk:3: error: `foo` is not defined.\n"
        "  [UndefinedSymbolError]\n"
        "  | \n"
        "3 | foo\n"
        "hint: To use the name itself, write `:foo` or `{foo}`\n",
        id="a line of the script",
    ),
    pytest.param(
        {"main.stk": '"a" drop\n{1 2\n3\n'},
        "main.stk",
        "<DIR>/main.stk:2: error: Unterminated block starting at line 2\n"
        "  [UnterminatedTokenError]\n"
        "  | \n"
        "2 | {1 2\n",
        id="unterminated at the end",
    ),
    pytest.param(
        {"main.stk": '1 drop\n"inc.stk" include\n', "inc.stk": "1 drop\nbar\n"},
        "main.stk",
        "<DIR>/inc.stk:2: error: `bar` is not defined.\n"
        "  [UndefinedSymbolError]\n"
        "  | \n"
        "2 | bar\n"
        "  included from <DIR>/main.stk:2\n"
        "hint: To use the name itself, write `:bar` or `{bar}`\n",
        id="a line of an included file",
    ),
    pytest.param(
        {"main.stk": "# a comment\n\n{\n  1 drop\n  foo\n} eval\n"},
        "main.stk",
        "<DIR>/main.stk:3: error: `foo` is not defined.\n"
        "  [UndefinedSymbolError]\n"
        "  | \n"
        "3 | {\n"
        "hint: To use the name itself, write `:foo` or `{foo}`\n",
        id="inside a block over several lines",
    ),
    pytest.param(
        {"main.stk": '# start\n\n1 drop\n\t"tab" drop\n"日本語" bar\n'},
        "main.stk",
        "<DIR>/main.stk:5: error: `bar` is not defined.\n"
        "  [UndefinedSymbolError]\n"
        "  | \n"
        '5 | "日本語" bar\n'
        "hint: To use the name itself, write `:bar` or `{bar}`\n",
        id="after blank lines, a comment and a tab",
    ),
    pytest.param(
        {
            "main.stk": '"lib.stk" include\n1 drop\nbroken\n',
            "lib.stk": "{} {1 drop nope} :broken defun\n",
        },
        "main.stk",
        "<DIR>/main.stk:3: error: `nope` is not defined.\n"
        "  [UndefinedSymbolError]\n"
        "  | \n"
        "3 | broken\n"
        "hint: To use the name itself, write `:nope` or `{nope}`\n",
        id="in a function an included file defines",
    ),
    pytest.param(
        {"main.stk": "1 drop\nbreak\n"},
        "main.stk",
        "<DIR>/main.stk:2: error: `break` can only be used inside a loop\n"
        "  [StackerSyntaxError]\n"
        "  | \n"
        "2 | break\n",
        id="break outside a loop",
    ),
    pytest.param(
        {"main.stk": b'"\xe9t\xe9" echo\n'},
        "main.stk",
        "<DIR>/main.stk: error: <DIR>/main.stk is not UTF-8 text at line 1: invalid continuation byte\n"
        "  [ScriptReadError]\n",
        id="not UTF-8",
    ),
    pytest.param(
        {"main.txt": "1\n"},
        "main.txt",
        "<DIR>/main.txt: error: Invalid file path or file type. Please provide a valid '.stk' file.\n"
        "  [ScriptReadError]\n",
        id="not a .stk file",
    ),
]


@pytest.mark.parametrize("files, script, expected", FAILING_SCRIPTS)
def test_a_failing_script_is_reported_on_standard_error(
    files, script, expected, tmp_path, capsys
):
    directory = tmp_path.resolve()
    for name, content in files.items():
        path = directory / name
        if isinstance(content, bytes):
            path.write_bytes(content)
        else:
            path.write_text(content, encoding="utf-8")
    with pytest.raises(SystemExit) as info:
        ScriptMode(Stacker()).run(str(directory / script))
    captured = capsys.readouterr()
    assert info.value.code == 1
    assert captured.err == expected.replace("<DIR>", str(directory))
    assert captured.out == ""


def test_a_script_given_by_a_relative_path_is_reported_by_its_absolute_path(
    tmp_path, capsys, monkeypatch
):
    directory = (tmp_path / "scripts").resolve()
    directory.mkdir()
    (directory / "main.stk").write_text("1 drop\nfoo\n", encoding="utf-8")
    monkeypatch.chdir(tmp_path)
    with pytest.raises(SystemExit):
        ScriptMode(Stacker()).run("scripts/main.stk")
    assert capsys.readouterr().err.startswith(
        f"{directory}/main.stk:2: error: `foo` is not defined.\n"
    )
