"""Tests for what making an interpreter core does to the host process."""

import sys

import pytest

from stacker import Stacker

pytestmark = pytest.mark.skipif(
    not hasattr(sys, "set_int_max_str_digits"),
    reason="the host has no limit on the digits of an integer's text",
)

HOST_DEFAULT_LIMIT = 4300  #: the host's own limit, which a host may put back


@pytest.fixture
def host_digit_limit():
    """Puts the host's digit limit back as it was once the test ends."""
    before = sys.get_int_max_str_digits()
    yield
    sys.set_int_max_str_digits(before)


def test_making_an_interpreter_lifts_the_host_digit_limit(host_digit_limit):
    sys.set_int_max_str_digits(HOST_DEFAULT_LIMIT)
    Stacker()
    assert sys.get_int_max_str_digits() == 0


@pytest.mark.parametrize(
    "code",
    [
        "{1} eval",
        "{} {1} :f defun f",
        "[1 2] {1 +} map",
        "true {1} {2} ifelse",
        "{n} {{n 1 +}} :inc defmacro 5 inc",
    ],
    ids=["block", "function", "map", "ifelse", "macro"],
)
def test_a_limit_the_host_puts_back_stays_while_the_interpreter_runs(
    host_digit_limit, code
):
    stacker = Stacker()
    sys.set_int_max_str_digits(HOST_DEFAULT_LIMIT)
    stacker.eval(code)
    assert sys.get_int_max_str_digits() == HOST_DEFAULT_LIMIT


def test_a_limit_the_host_puts_back_stays_while_an_included_file_runs(
    host_digit_limit, tmp_path
):
    script = tmp_path / "one.stk"
    script.write_text("1 drop\n")
    stacker = Stacker()
    sys.set_int_max_str_digits(HOST_DEFAULT_LIMIT)
    stacker.eval(f'"{script}" include')
    assert sys.get_int_max_str_digits() == HOST_DEFAULT_LIMIT
