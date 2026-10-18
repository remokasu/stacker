"""`throw` raises the program's own error; `try` hands the error to its handler as a dictionary."""

import pytest

from stacker import Stacker
from stacker.error import StackerSyntaxError, StackerTypeError, UserError, error_kind
from stacker.error_formatter import ErrorFormatter
from stacker.runtime.exec_modes.execution_mode import ExecutionMode


def run(program: str) -> list[object]:
    stacker = Stacker()
    stacker.process_expression(program)
    return list(stacker.stack)


class TestThrow:
    @pytest.mark.parametrize("program", ['"E" "boom" throw', ':E "boom" throw', '"E" "" throw'])
    def test_it_raises_a_user_error_with_the_kind_and_the_message(self, program):
        with pytest.raises(UserError) as info:
            run(program)
        assert info.value.kind == "E"
        assert str(info.value) == info.value.message

    def test_the_display_shows_the_kind_where_a_class_name_goes(self):
        with pytest.raises(UserError) as info:
            run('"IllegalArgumentException" "row 5 is outside 0..4" throw')
        text = ErrorFormatter.format_error(None, None, None, error_kind(info.value), str(info.value))
        assert "row 5 is outside 0..4" in text and "[IllegalArgumentException]" in text
        assert ExecutionMode(Stacker())._get_error_hint(info.value) is None

    @pytest.mark.parametrize("program", ['1 "boom" throw', '"E" 1 throw', '"" "boom" throw', '"E" :m throw'])
    def test_a_kind_or_message_of_the_wrong_type_is_refused(self, program):
        with pytest.raises(StackerTypeError, match="`throw` expects a kind"):
            run(program)


class TestTry:
    @pytest.mark.parametrize(
        "program, expected",
        [
            ('{"E" "boom" throw} {"kind" get} try', ["E"]),
            ('{"E" "boom" throw} {"message" get} try', ["boom"]),
            ('{1 0 /} {"kind" get} try', ["ZeroDivisionError"]),
            ('{zzz} {"message" get} try', ["`zzz` is not defined."]),
            ("{1 2} {drop} try", [1, 2]),
            ('1 2 {3 0 /} {"kind" get} try', [1, 2, "ZeroDivisionError"]),
            ('{{"E" "x" throw} {"kind" get} try "inner" } {"outer"} try', ["E", "inner"]),
            ('{{"E" "boom" throw} {:e set e "kind" get e "message" get throw} try} {"kind" get} try', ["E"]),
        ],
    )
    def test_the_handler_runs_with_the_error_on_the_stack(self, program, expected):
        assert run(program) == expected

    def test_an_error_thrown_again_keeps_its_kind_and_message(self):
        with pytest.raises(UserError) as info:
            run('{"E" "boom" throw} {:e set e "kind" get e "message" get throw} try')
        assert info.value.kind == "E" and info.value.message == "boom"

    def test_the_handler_gets_a_fresh_dictionary_each_time(self):
        assert run('{"E" "a" throw} {} try {"E" "b" throw} {} try same?') == [False]

    def test_the_handler_gets_string_keys(self):
        assert run('{"E" "boom" throw} {dup "kind" has? swap :kind has?} try') == [True, False]

    def test_break_is_not_caught(self):
        with pytest.raises(StackerSyntaxError, match="break"):
            run("{break} {} try")
        assert run("0 {1 + {break} {} try} loop") == [1]

    def test_an_exit_is_not_caught(self):
        with pytest.raises(SystemExit) as info:
            run("{3 exit-code} {} try")
        assert info.value.code == 3

    def test_an_error_in_the_handler_goes_up(self):
        with pytest.raises(UserError) as info:
            run('{1 0 /} {drop "F" "again" throw} try')
        assert info.value.kind == "F"
