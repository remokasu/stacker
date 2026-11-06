"""The REPL colors the stack by the kind of each value; the text itself comes from the language."""

from __future__ import annotations

import io

from stacker.data_type import Array, String
from stacker.lang import text as lang_text
from stacker.lang.protocols import BLOCK
from stacker.runtime.color import COLORS
from stacker.runtime.display import (
    PALETTE,
    STACK_COLOR,
    colored_text,
    disp_colored,
    disp_stack,
)

YELLOW, MAGENTA, LIGHT_MAGENTA, LIGHT_GREEN, DEFAULT, RESET = (
    COLORS["yellow"],
    COLORS["magenta"],
    COLORS["lightmagenta"],
    COLORS["lightgreen"],
    COLORS["default"],
    COLORS["reset"],
)


def test_every_kind_has_a_color_the_terminal_knows():
    kinds = {
        lang_text.INT,
        lang_text.FLOAT,
        lang_text.COMPLEX,
        lang_text.SYMBOL,
        lang_text.STRING,
        lang_text.BOOL,
        lang_text.NULL,
        lang_text.LIST,
        lang_text.ARRAY,
        lang_text.DICT,
        lang_text.CALLABLE,
        BLOCK,
    }
    assert set(PALETTE) == kinds
    assert set(PALETTE.values()) | {STACK_COLOR} <= set(COLORS)


def test_each_piece_is_colored_by_its_kind_and_separators_are_not():
    value = {"a": 1, "b": Array([2, 3])}
    assert colored_text(value) == (
        f"{LIGHT_MAGENTA}{{{RESET}"
        f"{LIGHT_GREEN}'a'{RESET} {DEFAULT}1{RESET} {LIGHT_GREEN}'b'{RESET} "
        f"{MAGENTA}[{RESET}{DEFAULT}2{RESET} {DEFAULT}3{RESET}{MAGENTA}]{RESET}"
        f"{LIGHT_MAGENTA}}}{RESET}"
    )


def test_a_value_of_an_unknown_kind_is_left_uncolored():
    class Odd:
        def __str__(self) -> str:
            return "odd!"

    assert colored_text(Odd()) == "odd!"


def test_the_stack_brackets_are_yellow_and_items_are_space_separated():
    assert disp_colored([]) == f"{YELLOW}[{RESET}{YELLOW}]{RESET}"
    assert disp_colored([1, String("x")]) == f"{YELLOW}[{RESET}{DEFAULT}1{RESET} {LIGHT_GREEN}'x'{RESET}{YELLOW}]{RESET}"


def test_disp_stack_prints_to_the_given_stream_colored_or_plain():
    colored, plain = io.StringIO(), io.StringIO()
    disp_stack([1, String("x")], colored=True, file=colored)
    disp_stack([1, String("x")], file=plain)
    assert colored.getvalue() == disp_colored([1, String("x")]) + "\n"
    assert plain.getvalue() == "[1 'x']\n"
