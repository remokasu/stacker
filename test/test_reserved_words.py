"""The REPL's commands are reserved words: a program cannot name anything after them, and writes them only at the REPL's prompt."""

from __future__ import annotations

import pytest

from stacker import Stacker
from stacker.error import ReservedWordError, StackerSyntaxError, UndefinedSymbolError
from stacker.runtime.exec_modes.repl_mode import ReplMode
from stacker.runtime.exec_modes.script_mode import ScriptMode
from stacker.syntax.token_rules import REPL_COMMAND_NAMES

THE_REPL_COMMANDS = {
    "help",
    "about",
    "delete_history",
    "enable_disp_stack",
    "disable_disp_stack",
    "enable_disp_logo",
    "disable_disp_logo",
    "enable_disp_ans",
    "disable_disp_ans",
}


@pytest.fixture
def stacker() -> Stacker:
    return Stacker()


def test_the_reserved_words_are_the_repl_commands():
    assert REPL_COMMAND_NAMES == THE_REPL_COMMANDS


def test_reserved_word_error_is_a_stacker_syntax_error():
    assert issubclass(ReservedWordError, StackerSyntaxError)


BINDINGS = [
    pytest.param("1 :help set", id="set"),
    pytest.param("1 :help =", id="="),
    pytest.param("1 :help global", id="global"),
    pytest.param("{} {1} :help defun", id="defun"),
    pytest.param("{n} {{n}} :help defmacro", id="defmacro"),
    pytest.param("{1} :help alias", id="alias"),
    pytest.param("{help} {help} :f defun", id="a function's argument"),
    pytest.param("{help} {{help}} :m defmacro", id="a macro's argument"),
    pytest.param("{help} {help} lambda", id="a lambda's argument"),
    pytest.param("0 2 :help {1} do", id="do"),
    pytest.param("[1 2] :help {1} dolist", id="dolist"),
    pytest.param("[1 2] 0 :help :x {x} reduce", id="reduce's accumulator"),
    pytest.param("[1 2] 0 :acc :help {acc} fold", id="fold's element"),
    pytest.param("{help} macroexpand", id="macroexpand"),
]


@pytest.mark.parametrize("code", BINDINGS)
def test_no_word_binds_a_reserved_word(stacker, code):
    with pytest.raises(ReservedWordError, match="`help`.*REPL command"):
        stacker.eval(code)


@pytest.mark.parametrize("name", sorted(THE_REPL_COMMANDS))
def test_every_repl_command_is_reserved(stacker, name):
    with pytest.raises(ReservedWordError):
        stacker.eval(f"1 :{name} set")
    with pytest.raises(ReservedWordError):
        stacker.eval(f"{{{name}}} {{1}} :f defun")


def test_a_reserved_word_in_a_function_body_fails_when_the_function_runs(stacker):
    stacker.eval("{} {help} :f defun")
    with pytest.raises(ReservedWordError):
        stacker.eval("f")


@pytest.mark.parametrize("mode_class", [ReplMode, ScriptMode])
def test_the_error_gets_no_hint(mode_class):
    error = ReservedWordError(
        "`help` is a REPL command: type it alone at the REPL's prompt"
    )
    assert mode_class._get_error_hint(None, error) is None


def test_a_reserved_word_cannot_be_bound_in_an_included_file(stacker, tmp_path):
    script = tmp_path / "defines.stk"
    script.write_text("{} {1} :about defun\n", encoding="utf-8")
    with pytest.raises(ReservedWordError):
        stacker.eval(f'"{script}" include')


USES = [
    pytest.param("help", id="alone"),
    pytest.param("1 help", id="after a value"),
    pytest.param("{help} eval", id="in a block"),
    pytest.param(":help eval", id="as a symbol to eval"),
    pytest.param("[help]", id="in a list literal"),
    pytest.param("{help} sum", id="in a block an aggregate reads"),
]


@pytest.mark.parametrize("code", USES)
def test_a_reserved_word_written_in_a_program_says_it_is_a_repl_command(stacker, code):
    with pytest.raises(ReservedWordError, match="`help` is a REPL command"):
        stacker.eval(code)


def test_try_names_the_kind_of_the_error(stacker):
    assert list(stacker.eval('{about} {"kind" get} try')) == ["ReservedWordError"]


def test_a_reserved_word_can_still_be_written_as_data(stacker):
    assert [str(value) for value in stacker.eval(':help "help" {help} code-text')] == [
        "help",
        "help",
        "{help}",
    ]


def test_the_reservation_is_for_the_lowercase_names_only(stacker):
    assert list(stacker.eval("{} {1} :HELP defun HELP 2 :Help set Help")) == [1, 2]


def test_an_unknown_name_is_still_undefined(stacker):
    with pytest.raises(UndefinedSymbolError):
        stacker.eval("helpme")


REGISTRATIONS = [
    pytest.param(
        lambda stacker: stacker.register_sfunction("help", None, 0),
        id="register_sfunction",
    ),
    pytest.param(
        lambda stacker: stacker.register_macro("help", None), id="register_macro"
    ),
    pytest.param(
        lambda stacker: stacker.register_parameter("help", 1), id="register_parameter"
    ),
    pytest.param(
        lambda stacker: stacker.register_plugin("help", lambda: 1), id="register_plugin"
    ),
]


@pytest.mark.parametrize("register", REGISTRATIONS)
def test_the_python_api_cannot_name_anything_after_a_reserved_word(stacker, register):
    with pytest.raises(ReservedWordError, match="`help`.*REPL command"):
        register(stacker)
    assert "help" not in stacker.sfunctions
    assert "help" not in stacker.macros
    assert "help" not in stacker.plugins
    assert "help" not in stacker.variables


def test_the_python_api_can_use_the_uppercase_name(stacker):
    stacker.register_plugin("HELP", lambda: "plugin")
    stacker.register_parameter("Help", "parameter")
    assert list(stacker.eval("HELP Help")) == ["plugin", "parameter"]


@pytest.mark.parametrize("name", sorted(THE_REPL_COMMANDS))
def test_the_python_api_refuses_every_repl_command(stacker, name):
    with pytest.raises(ReservedWordError):
        stacker.register_parameter(name, 1)
    with pytest.raises(ReservedWordError):
        stacker.register_plugin(name, lambda: 1)


LITERALS = ["true", "false", "null", "True", "False", "None"]

NAMED_REGISTRATIONS = [
    pytest.param(
        lambda stacker, name: stacker.register_sfunction(name, None, 0),
        id="register_sfunction",
    ),
    pytest.param(
        lambda stacker, name: stacker.register_macro(name, None), id="register_macro"
    ),
    pytest.param(
        lambda stacker, name: stacker.register_parameter(name, 1),
        id="register_parameter",
    ),
    pytest.param(
        lambda stacker, name: stacker.register_plugin(name, lambda: 1),
        id="register_plugin",
    ),
]


@pytest.mark.parametrize("register", NAMED_REGISTRATIONS)
@pytest.mark.parametrize("name", LITERALS)
def test_the_python_api_cannot_name_anything_after_a_literal(stacker, name, register):
    with pytest.raises(
        StackerSyntaxError,
        match=f"cannot bind `{name}`: it is a literal, not a variable",
    ):
        register(stacker, name)
    assert name not in stacker.sfunctions
    assert name not in stacker.macros
    assert name not in stacker.plugins
    assert name not in stacker.variables
