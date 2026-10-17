"""An error inside an included file is reported at that file's line, followed by `included from` lines."""

import re
from pathlib import Path

import pytest

from stacker import Stacker
from stacker.runtime.exec_modes import CommandLineMode, ScriptMode

ANSI = re.compile(r"\x1b\[[0-9;]*m")


def write(tmp_path: Path, name: str, text: str) -> Path:
    path = tmp_path / name
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")
    return path


@pytest.fixture
def project(tmp_path: Path) -> dict[str, Path]:
    helpers = write(tmp_path, "lib/helpers.stk", "1 2 +\n10 total +\n")
    geometry = write(tmp_path, "lib/geometry.stk", '"helpers.stk" include\n')
    main = write(tmp_path, "main.stk", '"x" echo\n"lib/geometry.stk" include\n')
    return {"helpers": helpers, "geometry": geometry, "main": main}


def run_script(path: Path, capsys) -> str:
    with pytest.raises(SystemExit):
        ScriptMode(Stacker()).run(str(path))
    return ANSI.sub("", capsys.readouterr().err)


def test_a_script_reports_the_inner_file_and_the_including_lines(project, capsys):
    err = run_script(project["main"], capsys).splitlines()
    assert err[0] == f"{project['helpers'].resolve()}:2: error: `total` is not defined."
    assert err[1] == "  [UndefinedSymbolError]"
    assert err[3] == "2 | 10 total +"
    assert err[4] == f"  included from {project['geometry'].resolve()}:1"
    assert err[5] == f"  included from {project['main'].resolve()}:2"
    assert err[6].startswith("hint:")


def test_the_command_line_omits_the_entry_frame(project, capsys, monkeypatch):
    monkeypatch.chdir(project["main"].parent)
    with pytest.raises(SystemExit):
        CommandLineMode(Stacker()).run('"lib/geometry.stk" include')
    err = ANSI.sub("", capsys.readouterr().err).splitlines()
    assert err[0] == f"{project['helpers'].resolve()}:2: error: `total` is not defined."
    assert err[4] == f"  included from {project['geometry'].resolve()}:1"
    assert err[5].startswith("hint:")


def test_an_error_after_the_include_is_reported_at_the_includers_line(tmp_path: Path, capsys):
    write(tmp_path, "lib.stk", "1 :a set\n")
    main = write(tmp_path, "main.stk", '"lib.stk" include 1 0 /\n')
    err = run_script(main, capsys).splitlines()
    assert err[0].startswith(f"{main.resolve()}:1: error:")
    assert not any("included from" in line for line in err)


def test_a_missing_nested_include_is_reported_in_the_including_file(tmp_path: Path, capsys):
    geometry = write(tmp_path, "geometry.stk", '"nope.stk" include\n')
    main = write(tmp_path, "main.stk", f'"{geometry}" include\n')
    err = run_script(main, capsys).splitlines()
    assert err[0].startswith(f"{geometry.resolve()}:1: error: File nope.stk not found")
    assert f"  included from {main.resolve()}:1" in err


def test_an_include_inside_a_function_names_the_calling_line(tmp_path: Path, capsys):
    lib = write(tmp_path, "lib.stk", "\n\nzzz\n")
    main = write(tmp_path, "main.stk", f'{{}} {{"{lib}" include}} :f defun\n\nf\n')
    err = run_script(main, capsys).splitlines()
    assert err[0] == f"{lib.resolve()}:3: error: `zzz` is not defined."
    assert f"  included from {main.resolve()}:3" in err


def test_an_unterminated_block_is_reported_at_its_line_in_the_inner_file(tmp_path: Path, capsys):
    lib = write(tmp_path, "lib.stk", "1\n{ 2\n")
    main = write(tmp_path, "main.stk", f'"{lib}" include\n')
    err = run_script(main, capsys).splitlines()
    assert err[0].startswith(f"{lib.resolve()}:2: error: Unterminated")


def test_a_host_error_carries_the_position_too(tmp_path: Path, capsys):
    lib = write(tmp_path, "lib.stk", "1 0 /\n")
    main = write(tmp_path, "main.stk", f'"{lib}" include\n')
    err = run_script(main, capsys).splitlines()
    assert err[0] == f"{lib.resolve()}:1: error: division by zero"
    assert err[1] == "  [ZeroDivisionError]"


def test_the_message_itself_is_unchanged(tmp_path: Path):
    lib = write(tmp_path, "lib.stk", "zzz\n")
    stacker = Stacker()
    with pytest.raises(Exception) as info:
        stacker.eval(f'"{lib}" include')
    assert str(info.value) == "`zzz` is not defined."
    assert info.value.include_location[0] == str(lib.resolve())
