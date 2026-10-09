"""The prelude (slib) is loaded by `Stacker()` itself, in manifest order."""

import logging
from pathlib import Path

import pytest

from stacker.error import PreludeLoadError, UndefinedSymbolError
from stacker.slib import PRELUDE_FILES, load_prelude
from stacker.stacker import Stacker


def run(stacker: Stacker, *expressions: str) -> list[object]:
    result = None
    for expression in expressions:
        result = stacker.eval(expression, stack=stacker.stack)
    return list(result)


class TestAutomaticLoad:
    def test_alias_is_available_on_a_fresh_interpreter(self):
        assert run(Stacker(), "{2 *} {double} alias", "5 double") == [10]

    def test_alias_body_runs_on_the_caller_stack(self):
        # Like the pre-1.15 `defmacro`: the body may consume and leave several values.
        assert run(Stacker(), "{dup dup} {triple} alias", "7 triple") == [7, 7, 7]

    def test_prelude_function_is_available(self):
        assert run(Stacker(), "[2 4] mean") == [3.0]

    def test_prelude_words_are_recorded(self):
        stacker = Stacker()
        assert {"alias", "mean"} <= stacker._prelude["names"]
        assert "pi" not in stacker._prelude["names"]  # constants are not prelude words

    def test_prelude_macros_are_marked(self):
        assert Stacker().macros["alias"].is_prelude is True

    def test_prelude_can_be_disabled(self):
        stacker = Stacker(prelude=False)
        assert "alias" not in stacker.macros
        assert "mean" not in stacker.sfunctions
        assert stacker._prelude["enabled"] is False

    def test_code_blocks_do_not_reload_the_prelude(self):
        stacker = Stacker()
        (block,) = run(stacker, "{1 2 +}")
        assert block._prelude is stacker._prelude


class TestInclude:
    def test_included_file_can_use_the_prelude(self, tmp_path: Path):
        script = tmp_path / "lib.stk"
        script.write_text("{3 *} {thrice} alias\n", encoding="utf-8")
        stacker = Stacker()
        assert run(stacker, f'"{script}" include', "2 thrice") == [6]

    def test_include_child_inherits_disabled_prelude(self, tmp_path: Path):
        script = tmp_path / "lib.stk"
        script.write_text("{3 *} {thrice} alias\n", encoding="utf-8")
        stacker = Stacker(prelude=False)
        run(stacker, f'"{script}" include')
        # Without the prelude `alias` is an undefined word, so nothing was defined.
        assert "thrice" not in stacker.macros

    def test_include_child_of_a_disabled_prelude_cannot_call_prelude_functions(
        self, tmp_path: Path
    ):
        script = tmp_path / "lib.stk"
        script.write_text("[2 4] mean r =\n", encoding="utf-8")
        with pytest.raises(UndefinedSymbolError, match="mean"):
            Stacker(prelude=False).eval(f'"{script}" include', stack=None)

    def test_include_child_of_an_enabled_prelude_can_call_prelude_functions(
        self, tmp_path: Path
    ):
        script = tmp_path / "lib.stk"
        script.write_text("[2 4] mean r =\n", encoding="utf-8")
        stacker = Stacker()
        assert run(stacker, f'"{script}" include', "r") == [3.0]

    def test_include_does_not_undo_a_user_redefinition_of_a_prelude_word(self, tmp_path: Path):
        # The child interpreter loads its own prelude; merging it back must not
        # overwrite the parent's redefined `alias` (and must not warn).
        script = tmp_path / "lib.stk"
        script.write_text("{a} {a 1 +} {inc} defun\n", encoding="utf-8")
        stacker = Stacker()
        run(stacker, "{body name} {{9}} {alias} defmacro")  # same arity, always 9
        assert run(stacker, f'"{script}" include', "{5} {z} alias", "1 inc") == [9, 2]

    def test_include_merges_a_prelude_word_the_file_redefines(self, tmp_path: Path):
        script = tmp_path / "lib.stk"
        script.write_text("{xs} {0} {mean} defun\n", encoding="utf-8")
        stacker = Stacker()
        assert run(stacker, f'"{script}" include', "[2 4] mean") == [0]


class TestLoader:
    def test_reloading_the_prelude_keeps_the_recorded_names(self):
        stacker = Stacker()
        assert {"alias", "mean"} <= stacker._prelude["names"]
        load_prelude(stacker)
        assert {"alias", "mean"} <= stacker._prelude["names"]
        assert run(stacker, "{2 *} {double} alias", "5 double") == [10]

    def test_manifest_order_is_followed(self, tmp_path: Path):
        (tmp_path / "a.stk").write_text("{} {{1}} {one} defmacro\n", encoding="utf-8")
        (tmp_path / "b.stk").write_text("{} {{one 1 +}} {two} defmacro\n", encoding="utf-8")
        stacker = Stacker(prelude=False)
        load_prelude(stacker, directory=tmp_path, files=("a.stk", "b.stk"))
        assert run(stacker, "two") == [2]
        assert stacker._prelude["names"] == {"one", "two"}

    def test_unlisted_file_is_skipped_with_a_warning(self, tmp_path: Path, caplog):
        (tmp_path / "a.stk").write_text("1 x =\n", encoding="utf-8")
        (tmp_path / "zz.stk").write_text("2 y =\n", encoding="utf-8")
        stacker = Stacker(prelude=False)
        with caplog.at_level(logging.WARNING, logger="stacker"):
            load_prelude(stacker, directory=tmp_path, files=("a.stk",))
        assert "y" not in stacker.variables
        assert "zz.stk" in caplog.text

    def test_failing_file_raises_and_logs(self, tmp_path: Path, caplog):
        (tmp_path / "bad.stk").write_text("1 +\n", encoding="utf-8")
        stacker = Stacker(prelude=False)
        with (
            caplog.at_level(logging.ERROR, logger="stacker"),
            pytest.raises(PreludeLoadError, match="bad.stk"),
        ):
            load_prelude(stacker, directory=tmp_path, files=("bad.stk",))
        assert "bad.stk" in caplog.text
        assert stacker._prelude["loading"] is False

    def test_every_shipped_prelude_file_is_listed(self):
        from stacker.slib import PRELUDE_DIR

        shipped = sorted(p.name for p in PRELUDE_DIR.glob("*.stk"))
        assert shipped == sorted(PRELUDE_FILES)


class TestRedefinitionWarning:
    def test_redefining_a_prelude_macro_warns(self, caplog):
        stacker = Stacker()
        with caplog.at_level(logging.WARNING, logger="stacker"):
            run(stacker, "{} {{1}} alias defmacro")
        assert "redefining prelude word 'alias'" in caplog.text

    def test_redefining_a_prelude_function_warns(self, caplog):
        stacker = Stacker()
        with caplog.at_level(logging.WARNING, logger="stacker"):
            run(stacker, "{xs} {0} mean defun")
        assert "redefining prelude word 'mean'" in caplog.text

    def test_set_over_a_prelude_word_warns_every_time(self, caplog):
        stacker = Stacker()
        with caplog.at_level(logging.WARNING, logger="stacker"):
            run(stacker, "1 $mean set 2 $mean set")
        assert caplog.text.count("redefining prelude word 'mean'") == 2

    def test_defining_a_new_word_does_not_warn(self, caplog):
        stacker = Stacker()
        with caplog.at_level(logging.WARNING, logger="stacker"):
            run(stacker, "{} {{1}} fresh defmacro 5 x =")
        assert "redefining" not in caplog.text

    def test_loading_the_prelude_itself_does_not_warn(self, caplog):
        with caplog.at_level(logging.WARNING, logger="stacker"):
            Stacker()
        assert "redefining" not in caplog.text


def test_macros_listing_marks_prelude_words(capsys):
    stacker = Stacker()
    stacker.eval("{} {{1}} {mine} defmacro macros", stack=stacker.stack)
    out = capsys.readouterr().out
    assert "alias: {body name}" in out and "(prelude)" in out
    assert "mine: {}" in out


def test_funcs_listing_marks_prelude_words(capsys):
    stacker = Stacker()
    stacker.eval("{a} {a} {mine} defun funcs", stack=stacker.stack)
    out = capsys.readouterr().out
    assert "mean:" in out and "(prelude)" in out
    assert "mine:" in out and out.count("(prelude)") == 1
