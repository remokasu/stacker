"""`code-text`, `code=` and `code?` take a block as it is, without running it."""

import pytest

from stacker import Stacker
from stacker.engine.data_type import Symbol
from stacker.error import StackerTypeError, StackUnderflowError


def run(*programs: str) -> list[object]:
    stacker = Stacker()
    for program in programs:
        stacker.process_expression(program)
    return list(stacker.stack)


UNLESS = "{cond body} { {cond eval not {body eval} if} } :unless defmacro"
EXPANSION = '{{0 >} eval not {{"neg" echo} eval} if}'


class TestCodeText:
    def test_is_the_text_the_stack_shows(self):
        assert run("{1 2 +} code-text") == ["{1 2 +}"]

    def test_keeps_strings_nested_blocks_and_symbols_as_written(self):
        assert run('{"hi" echo {x 1 +} :x (2)} code-text') == ['{"hi" echo {x 1 +} :x (2)}']

    def test_reads_back_as_the_same_code(self):
        # `parse` wraps the text in a block of its own; `eval` of that pushes the block read
        assert run('{"a" 1 {x} :y +} code-text parse eval {"a" 1 {x} :y +} code=') == [True]
        assert run('{"a" 1 {x} :y +} code-text parse code-text') == ['{{"a" 1 {x} :y +}}']

    def test_does_not_run_the_block(self, capsys):
        assert run('{"hi" echo 1 2} code-text') == ['{"hi" echo 1 2}']
        assert capsys.readouterr().out == ""

    def test_shows_a_macro_expansion(self):
        assert run(UNLESS, '{0 >} {"neg" echo} {unless} macroexpand code-text') == [EXPANSION]

    def test_a_block_held_by_a_variable(self):
        assert run("{1 2 +} :b set b code-text") == ["{1 2 +}"]

    def test_refuses_a_value_that_is_not_a_block(self):
        with pytest.raises(StackerTypeError, match="`code-text` expects a code block, got 5"):
            run("5 code-text")

    def test_a_lambda_is_not_a_block(self):
        with pytest.raises(StackerTypeError, match="`code-text` expects a code block"):
            run("{x} {x} lambda code-text")

    def test_short_of_an_argument_is_an_underflow(self):
        with pytest.raises(StackUnderflowError, match="code-text"):
            run("code-text")


class TestCodeEq:
    @pytest.mark.parametrize(
        "program, expected",
        [
            ("{1 2 +} {1 2 +} code=", True),
            ("{1 2 +} {3} code=", False),
            ("{1 2} (1 2) code=", True),
            ('{"a"} {"a"} code=', True),
            ('{"a"} {a} code=', False),
            ("{x} {:x} code=", False),
            ("{{1} 2} {{1} 2} code=", True),
            ("{{1} 2} {{2} 1} code=", False),
            ("{1} {1.0} code=", False),
            ("{0.0} {-0.0} code=", False),
            ("{0j} {-0j} code=", False),
            ("{1.5} {1.5} code=", True),
            ("{true} {1} code=", False),
            ("{} {} code=", True),
            ("1 {1} code=", False),
            ("{1} 1 code=", False),
            ("1 1 code=", False),
            ('{1} "{1}" code=', False),
            ("{x} {x} lambda {x} code=", False),
        ],
    )
    def test_compares_code_not_results(self, program, expected):
        assert run(program) == [expected]

    def test_runs_neither_block(self, capsys):
        assert run('{"a" echo} {"b" echo} code=') == [False]
        assert capsys.readouterr().out == ""

    def test_compares_a_macro_expansion_with_the_expected_code(self):
        assert run(UNLESS, f'{{0 >}} {{"neg" echo}} {{unless}} macroexpand {EXPANSION} code=') == [True]
        assert run(UNLESS, '{0 >} {"neg" echo} {unless} macroexpand {{0 >} eval {{"neg" echo} eval} if} code=') == [False]

    def test_a_block_held_by_a_variable_is_the_code_it_holds(self):
        assert run("{1 2 +} :b set b {1 2 +} code=") == [True]

    def test_short_of_an_argument_is_an_underflow(self):
        with pytest.raises(StackUnderflowError, match="code="):
            run("{1} code=")


class TestCodeP:
    @pytest.mark.parametrize(
        "program, expected",
        [
            ("{1 2 +} code?", True),
            ("{} code?", True),
            ("(1 2) code?", True),
            ("{1} :b set b code?", True),
            ("[1 2] code?", False),
            ("{x} {x} lambda code?", False),
            (":x code?", False),
            ("5 code?", False),
            ('"{1}" code?', False),
            ("null code?", False),
        ],
    )
    def test_tells_a_block_from_any_other_value(self, program, expected):
        assert run(program) == [expected]

    def test_does_not_run_the_block(self, capsys):
        assert run('{"hi" echo} code?') == [True]
        assert capsys.readouterr().out == ""

    def test_type_still_runs_a_block_first(self):
        assert run("{1} type") == [Symbol("int")]
