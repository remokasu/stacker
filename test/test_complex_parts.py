"""`real`, `imag`, `conj`, `arg` and `polar` read and make complex numbers."""

import cmath
import math

import pytest

from stacker import Stacker
from stacker.error import StackerTypeError


def run(*lines: str) -> list[object]:
    stacker = Stacker()
    for line in lines:
        stacker.process_expression(line)
    return list(stacker.stack)


@pytest.mark.parametrize(
    "program, expected",
    [
        ("3+4j real", [3.0]),
        ("3+4j imag", [4.0]),
        ("3+4j conj", [3 - 4j]),
        ("3+4j abs", [5.0]),
        ("3 real", [3]),
        ("3 imag", [0]),
        ("2.5 real 2.5 imag", [2.5, 0]),
        ("1 2 frac real", [run("1 2 frac")[0]]),
        ("3 conj", [3]),
        ("true real", [True]),
    ],
)
def test_real_imag_conj_work_on_every_number(program, expected):
    assert run(program) == expected


def test_arg_is_the_angle():
    assert run("1j arg")[0] == pytest.approx(math.pi / 2)
    assert run("-1 arg")[0] == pytest.approx(math.pi)
    assert run("1 arg 0 arg") == [0.0, 0.0]
    assert run("-1+0j arg")[0] == pytest.approx(math.pi)


def test_polar_makes_a_complex_number_from_a_length_and_an_angle():
    z, = run("2 0 polar")
    assert z == pytest.approx(2 + 0j)
    z, = run("1 pi 2 / polar")
    assert z == pytest.approx(cmath.rect(1, math.pi / 2))
    assert run("1 pi 2 / polar arg")[0] == pytest.approx(math.pi / 2)


def test_fft_style_round_trip_has_no_square_root_error():
    assert run("3+4j real") == [3.0]
    assert run("3+4j dup conj * real") == [25.0]


@pytest.mark.parametrize("program, word", [('"a" real', "real"), ("[1] imag", "imag"), ("null conj", "conj"), ('"x" arg', "arg"), ('"r" 0 polar', "polar"), ("1 1j polar", "polar")])
def test_a_value_that_is_not_a_number_names_the_word(program, word):
    with pytest.raises(StackerTypeError) as info:
        run(program)
    assert f"`{word}`" in str(info.value)


def test_a_symbol_is_reported_as_a_symbol():
    with pytest.raises(StackerTypeError, match="cannot use the symbol `z`"):
        run(":z real")
