"""`defun` / `defmacro` log it when they redefine a word of the program's own that another file defined."""

import logging

from stacker import Stacker
from stacker.runtime.exec_modes.script_mode import ScriptMode


def redefinitions(caplog) -> list[str]:
    return [r.getMessage() for r in caplog.records if r.getMessage().startswith("redefining")]


def run_script(tmp_path, caplog, files: dict[str, str], main: str = "main.stk") -> list[str]:
    for name, text in files.items():
        (tmp_path / name).write_text(text)
    with caplog.at_level(logging.WARNING, logger="stacker"):
        ScriptMode(Stacker()).run(str(tmp_path / main))
    return redefinitions(caplog)


class TestAWordDefinedInAnotherFile:
    def test_a_function_is_reported_with_both_places(self, tmp_path, caplog):
        logged = run_script(tmp_path, caplog, {
            "parser.stk": "{P} {P} :__call defun\n",
            "main.stk": '"parser.stk" require\n{f a} {f a} :__call defun\n',
        })
        assert logged == ["redefining word '__call' (defined at parser.stk:1) at main.stk:2"]

    def test_a_macro_is_reported_the_same_way(self, tmp_path, caplog):
        logged = run_script(tmp_path, caplog, {
            "lib.stk": "{x} {{x}} :m defmacro\n",
            "main.stk": '"lib.stk" include\n\n{x} {{x x}} :m defmacro\n',
        })
        assert logged == ["redefining word 'm' (defined at lib.stk:1) at main.stk:3"]

    def test_the_new_definition_wins(self, tmp_path, caplog):
        for name, text in {
            "lib.stk": "{a} {1} :g defun\n",
            "main.stk": '"lib.stk" require\n{a} {2} :g defun\n0 g\n',
        }.items():
            (tmp_path / name).write_text(text)
        stacker = Stacker()
        with caplog.at_level(logging.WARNING, logger="stacker"):
            ScriptMode(stacker).run(str(tmp_path / "main.stk"))
        assert list(stacker.stack) == [2]
        assert len(redefinitions(caplog)) == 1

    def test_a_built_in_taken_by_two_files_is_reported_once_as_a_word(self, tmp_path, caplog):
        logged = run_script(tmp_path, caplog, {
            "lib.stk": "{a b} {0} :+ defun\n",
            "main.stk": '"lib.stk" require\n{a b} {1} :+ defun\n',
        })
        assert logged.count("redefining built-in word '+'") == 2
        assert logged.count("redefining word '+' (defined at lib.stk:1) at main.stk:2") == 1


class TestTheReplHasNoFile:
    def test_a_file_redefining_a_repl_word_says_so(self, tmp_path, caplog):
        (tmp_path / "lib.stk").write_text("{a} {a} :g defun\n")
        stacker = Stacker()
        with caplog.at_level(logging.WARNING, logger="stacker"):
            stacker.process_expression("{a} {a 1 +} :g defun")
            stacker.process_expression(f'"{tmp_path / "lib.stk"}" include')
            stacker.process_expression("{a} {a 2 +} :g defun")
        assert redefinitions(caplog) == [
            "redefining word 'g' (defined outside any file) at lib.stk:1",
            "redefining word 'g' (defined at lib.stk:1) outside any file",
        ]

    def test_a_word_the_host_registered_says_so(self, tmp_path, caplog):
        (tmp_path / "lib.stk").write_text("{a} {a} :g defun\n")
        stacker = Stacker()
        stacker.register_sfunction("g", lambda a: a, 1)
        with caplog.at_level(logging.WARNING, logger="stacker"):
            stacker.process_expression(f'"{tmp_path / "lib.stk"}" include')
        assert redefinitions(caplog) == ["redefining word 'g' (defined by the host program) at lib.stk:1"]

    def test_a_word_the_host_registered_is_reported_from_the_repl_too(self, caplog):
        stacker = Stacker()
        stacker.register_sfunction("g", lambda a: a, 1)
        with caplog.at_level(logging.WARNING, logger="stacker"):
            stacker.process_expression("{a} {a} :g defun")
        assert redefinitions(caplog) == ["redefining word 'g' (defined by the host program) outside any file"]


class TestNothingIsLogged:
    def test_for_a_word_redefined_in_its_own_file(self, tmp_path, caplog):
        logged = run_script(tmp_path, caplog, {
            "main.stk": "{a} {1} :g defun\n{a} {2} :g defun\n{x} {{x}} :m defmacro\n{x} {{x x}} :m defmacro\n",
        })
        assert logged == []

    def test_for_a_word_redefined_in_the_repl(self, caplog):
        stacker = Stacker()
        with caplog.at_level(logging.WARNING, logger="stacker"):
            stacker.process_expression("{a} {1} :g defun")
            stacker.process_expression("{a} {2} :g defun")
        assert redefinitions(caplog) == []

    def test_for_a_prelude_word_beyond_the_prelude_warning(self, tmp_path, caplog):
        logged = run_script(tmp_path, caplog, {"main.stk": "{xs} {0} :mean defun\n"})
        assert logged == ["redefining prelude word 'mean'"]
