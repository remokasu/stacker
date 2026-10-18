"""`script-path` and `script-dir` name the file that is running; ~/.stackerrc leaves no file behind."""

from stacker import Stacker
from stacker.runtime.exec_modes.execution_mode import ExecutionMode
from stacker.runtime.exec_modes.script_mode import ScriptMode


def test_they_are_null_outside_a_file():
    stacker = Stacker()
    stacker.process_expression("script-path script-dir")
    assert list(stacker.stack) == [None, None]


def test_a_script_sees_its_own_absolute_path(tmp_path):
    main = tmp_path / "main.stk"
    main.write_text("script-path script-dir\n")
    stacker = Stacker()
    ScriptMode(stacker).run(str(main))
    assert list(stacker.stack) == [str(main.resolve()), str(tmp_path.resolve())]


def test_an_included_file_sees_itself_and_a_function_its_defining_file(tmp_path):
    lib = tmp_path / "lib"
    lib.mkdir()
    # (what an included file leaves on the stack is dropped, so the path is kept in a variable)
    (lib / "helper.stk").write_text("script-path :helper-path set\n{} {script-path} :where defun\n")
    main = tmp_path / "main.stk"
    main.write_text('"lib/helper.stk" include helper-path where script-path\n')
    stacker = Stacker()
    ScriptMode(stacker).run(str(main))
    helper = str((lib / "helper.stk").resolve())
    assert list(stacker.stack) == [helper, helper, str(main.resolve())]


def test_the_rc_file_does_not_stay_the_current_file(tmp_path):
    rc = tmp_path / "rc.stk"
    rc.write_text("1 :from-rc set\n")
    stacker = Stacker()
    ExecutionMode(stacker).execute_stacker_dotfile(rc, stackerrc=True)
    assert stacker.current_file is None
    assert stacker.source_lines == {}
    stacker.process_expression("from-rc script-path")
    assert list(stacker.stack) == [1, None]
