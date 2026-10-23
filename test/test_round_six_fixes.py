"""Strings holding syntax characters are text; sequence words and deep nesting name themselves."""

import pytest

from stacker import Stacker
from stacker.engine.data_type import Symbol
from stacker.error import StackerRecursionError, StackerTypeError, StackUnderflowError


def run(program: str) -> list[object]:
    stacker = Stacker()
    stacker.process_expression(program)
    return list(stacker.stack)


class TestASemicolonStringInAListLiteral:
    @pytest.mark.parametrize(
        "program, expected",
        [
            ('[";"]', [[";"]]),
            ('["x" ";" "y"]', [["x", ";", "y"]]),
            ('[[";" :A] ["q" :B]]', [[[";", Symbol("A")], ["q", Symbol("B")]]]),
            ('{[";" 1]} eval', [[";", 1]]),
            ("[1 2; 3 4]", [[[1, 2], [3, 4]]]),
            ('[1 ";"; 3]', [[[1, ";"], [3]]]),
        ],
    )
    def test_it_stays_a_string_and_a_bare_semicolon_still_splits_rows(self, program, expected):
        assert run(program) == expected


class TestABracketInsideAStringInsideABlock:
    @pytest.mark.parametrize(
        "program, expected",
        [
            ('{} {"{" } :f defun f', ["{"]),
            ('{"json: {" } eval', ["json: {"]),
            ('{"a{b"} eval type', [Symbol("str")]),
            ('{"a{b" "c"} eval', ["a{b", "c"]),
            ('("(" 1) eval', ["(", 1]),
            ('{"}"} eval', ["}"]),
            ('{"\\"{"} eval', ['"{']),
            ("{'''{'''} eval", ["{"]),
            ('{"{" "}"} eval', ["{", "}"]),
        ],
    )
    def test_the_block_is_a_block(self, program, expected):
        assert run(program) == expected

    def test_a_host_only_literal_is_never_a_value(self):
        from stacker.syntax.token_rules import cached_literal_eval

        assert cached_literal_eval("{1, 2}") == "{1, 2}"
        assert cached_literal_eval("(1, 2)") == "(1, 2)"
        assert cached_literal_eval("b'x'") == "b'x'"
        assert cached_literal_eval("42") == 42


class TestSequenceWordsRefuseAScalarByName:
    @pytest.mark.parametrize(
        "program, word",
        [
            ("5 :x {x echo} dolist", "dolist"),
            ("5 {x} {x} lambda map", "map"),
            ("5 {true} filter", "filter"),
            ("5 sum", "sum"),
            ("5 len", "len"),
            ("5 reversed", "reversed"),
            ("5 enumerate", "enumerate"),
            ("5 any", "any"),
            ("null all", "all"),
            ("5 list", "list"),
            ("5 [1] zip", "zip"),
            ("5 car", "car"),
            ("5 cdr", "cdr"),
            ("5 1 contains", "contains"),
            ('5 " " split', "split"),
            ('"a" 5 split', "split"),
            ("[1] 5 concat", "concat"),
            ("5 [1] concat", "concat"),
            ("1.5 0 :a :x {a x +} reduce", "reduce"),
        ],
    )
    def test_the_word_names_itself(self, program, word):
        with pytest.raises(StackerTypeError) as info:
            run(program)
        text = str(info.value)
        assert f"`{word}`" in text and "object" not in text

    def test_the_words_still_work(self):
        assert run('[1 2] :x {x} dolist [1 2] sum "ab" len [1 2] reversed [1 2] car "a,b" "," split "a" "b" concat [1] [2] concat "abc" "b" contains') == [1, 2, 3, 2, [2, 1], 1, ["a", "b"], "ab", [1, 2], True]


class TestDeepRecursionThroughNestedBlocks:
    def test_the_hosts_limit_is_reported_as_the_functions_by_name(self):
        nested = "{n} {true {true {true {true {true {true {true {true {true {true {n 0 == {0} {n 1 - f 1 +} ifelse} {0} ifelse} {0} ifelse} {0} ifelse} {0} ifelse} {0} ifelse} {0} ifelse} {0} ifelse} {0} ifelse} {0} ifelse} {0} ifelse} :f defun "
        with pytest.raises(StackerRecursionError) as info:
            run(nested + "100000 f")
        assert "`f`" in str(info.value) and info.value.depth is not None and info.value.depth < 1500
        # the counter is back in order afterwards
        assert run(nested + "{100000 f} {drop} try 10 f") == [10]

    def test_try_sees_the_usual_kind(self):
        nested = "{n} {true {true {true {true {true {true {true {true {true {true {n 0 == {0} {n 1 - f 1 +} ifelse} {0} ifelse} {0} ifelse} {0} ifelse} {0} ifelse} {0} ifelse} {0} ifelse} {0} ifelse} {0} ifelse} {0} ifelse} {0} ifelse} :f defun "
        assert run(nested + '{100000 f} {"kind" get} try') == ["StackerRecursionError"]


class TestAFunctionShortOfArguments:
    def test_is_called_a_function(self):
        with pytest.raises(StackUnderflowError, match="Function `g` requires 2 arguments."):
            run("{a b} {a b +} :g defun 1 g")

    def test_one_argument_is_singular(self):
        with pytest.raises(StackUnderflowError, match="Operator `sqrt` requires 1 argument."):
            run("sqrt")
