"""A script that leaves values on its stack, and a global variable that hides a word, are logged."""

import logging

import pytest

from stacker import Stacker
from stacker.runtime.exec_modes.script_mode import ScriptMode


def messages(caplog):
    return [r.getMessage() for r in caplog.records]


def run_script(tmp_path, text, caplog, name="main.stk"):
    path = tmp_path / name
    path.write_text(text)
    with caplog.at_level(logging.WARNING, logger="stacker"):
        stacker = Stacker()
        ScriptMode(stacker).run(str(path))
    return stacker, messages(caplog)


class TestValuesLeftAtTheEnd:
    def test_one_value_is_named(self, tmp_path, caplog):
        _, logged = run_script(tmp_path, '"x" echo 3\n', caplog)
        assert logged == ["1 value left on the stack at the end of main.stk: 3"]

    def test_many_values_show_the_top_three_and_a_count(self, tmp_path, caplog):
        _, logged = run_script(tmp_path, '1 2 3 4 "five"\n', caplog)
        assert logged == ["5 values left on the stack at the end of main.stk: 3, 4, 'five' (and 2 more below)"]

    def test_a_long_value_is_cut_short(self, tmp_path, caplog):
        _, logged = run_script(tmp_path, '"x" 500 * 1\n', caplog)
        assert len(logged) == 1 and logged[0].endswith("... , 1") is False and "..." in logged[0] and len(logged[0]) < 200

    def test_a_clean_end_logs_nothing(self, tmp_path, caplog):
        _, logged = run_script(tmp_path, "1 2 + drop\n", caplog)
        assert logged == []

    def test_a_required_file_that_leaves_values_is_named(self, tmp_path, caplog):
        (tmp_path / "lib.stk").write_text("{} {1} :one defun 7\n")
        stacker, logged = run_script(tmp_path, '"lib.stk" require one drop\n', caplog)
        assert logged == ["1 value left on the stack at the end of lib.stk: 7"]
        assert list(stacker.stack) == []

    def test_the_repl_logs_nothing(self, caplog):
        with caplog.at_level(logging.WARNING, logger="stacker"):
            Stacker().process_expression("1 2 3")
        assert messages(caplog) == []


class TestAGlobalThatHidesAWord:
    @pytest.mark.parametrize("program", ["5 :all set", "5 :all =", "5 :len global", "1 3 :i {5 :all set} do"])
    def test_a_new_global_with_a_words_name_is_logged_once(self, program, caplog):
        with caplog.at_level(logging.WARNING, logger="stacker"):
            Stacker().process_expression(program)
        hidden = "all" if "all" in program else "len"
        assert messages(caplog) == [f"redefining built-in word '{hidden}'"]

    @pytest.mark.parametrize("program", ["{} {5 :all set all} :f defun f", "1 3 :len {len} do", "5 :my-total set", "5 :all set 6 :all set"])
    def test_a_local_a_loop_variable_a_fresh_name_and_an_update_are_not_logged_again(self, program, caplog):
        with caplog.at_level(logging.WARNING, logger="stacker"):
            Stacker().process_expression(program)
        assert messages(caplog).count("redefining built-in word 'all'") <= 1
        if "my-total" in program or "do" in program and "len" in program or "defun" in program:
            assert messages(caplog) == []

    def test_a_prelude_word_keeps_its_message_for_a_new_global_only(self, caplog):
        with caplog.at_level(logging.WARNING, logger="stacker"):
            Stacker().process_expression("5 :alias set 6 :alias set")
        assert messages(caplog) == ["redefining prelude word 'alias'"]

    def test_a_local_with_a_prelude_words_name_is_not_logged(self, caplog):
        with caplog.at_level(logging.WARNING, logger="stacker"):
            Stacker().process_expression("{} {5 :alias set} :f defun f")
        assert messages(caplog) == []
