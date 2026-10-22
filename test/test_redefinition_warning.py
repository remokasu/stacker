"""Giving a built-in word's name to a new word is allowed, and logged."""

import logging

from stacker import Stacker


def run(program: str, caplog) -> tuple[list[object], list[str]]:
    with caplog.at_level(logging.WARNING, logger="stacker"):
        stacker = Stacker()
        stacker.process_expression(program)
    return list(stacker.stack), [r.getMessage() for r in caplog.records]


def test_a_built_in_word_redefined_by_defun_is_logged_and_the_new_word_wins(caplog):
    values, messages = run('{a b} {"mine"} :+ defun 1 2 +', caplog)
    assert values == ["mine"]
    assert "redefining built-in word '+'" in messages


def test_a_built_in_word_redefined_by_defmacro_is_logged(caplog):
    _, messages = run("{} {{1}} :dup defmacro", caplog)
    assert "redefining built-in word 'dup'" in messages


def test_a_new_name_is_not_logged(caplog):
    _, messages = run("{} {1} :my-own-word defun", caplog)
    assert messages == []


def test_a_prelude_word_keeps_its_own_message(caplog):
    _, messages = run("{} {1} :alias defun", caplog)
    assert any("prelude word 'alias'" in m for m in messages)
