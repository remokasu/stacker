"""`main?` tells the script the command line ran from a file it included."""

from stacker import Stacker
from stacker.runtime.exec_modes.script_mode import ScriptMode


def test_the_repl_counts_as_main():
    stacker = Stacker()
    stacker.process_expression("main? main-script-path")
    assert list(stacker.stack) == [True, None]


def test_the_script_is_main_and_an_included_file_is_not(tmp_path):
    lib = tmp_path / "lib.stk"
    lib.write_text("main? :lib-main set\n{} {main?} :lib-says defun\n")
    main = tmp_path / "main.stk"
    main.write_text('"lib.stk" require lib-main lib-says main? main-script-path\n')
    stacker = Stacker()
    ScriptMode(stacker).run(str(main))
    assert list(stacker.stack) == [False, False, True, str(main.resolve())]
