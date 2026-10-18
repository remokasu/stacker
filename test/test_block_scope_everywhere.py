"""A block reads its names in the scope it is bound to, whichever word runs it.

`eval`, `if`, `times`, `do`, `collect`, `apply`, `iferror`, `try`, `while`,
`loop`, `reduce` and `map` all agree: a block written where it runs sees
what it always saw, and a block carried somewhere else is a closure.
"""

import pytest

from stacker import Stacker
from stacker.error import UndefinedSymbolError


def run(*lines: str) -> list[object]:
    stacker = Stacker()
    for line in lines:
        stacker.process_expression(line)
    return list(stacker.stack)


# a function that takes a block and runs it with each word; `local` is the caller's variable
RUNNERS = {
    "eval": "{b} {b eval} :g defun",
    "if": "{b} {true b if} :g defun",
    "ifelse": "{b} {false {0} b ifelse} :g defun",
    "cond": "{b} {{true} b 1 cond} :g defun",
    "times": "{b} {b 1 times} :g defun",
    "collect": "{b} {b collect 0 at} :g defun",
    "apply": "{b} {[] b apply} :g defun",
    "iferror": "{b} {{1 0 /} b iferror} :g defun",
    "try": "{b} {{1 0 /} {drop b eval} try} :g defun",
    "while": "{b} {true :go set {go} {b eval false :go set} while} :g defun",
    "loop": "{b} {{b eval break} loop} :g defun",
    "do": "{b} {1 1 :i b do} :g defun",
    "dolist": "{b} {[1] :i b dolist} :g defun",
    "map": "{b} {[0] {drop b eval} map 0 at} :g defun",
    "filter-count": "{b} {[0] {drop b eval 10 >} filter len} :g defun",
}


class TestABlockCarriedIntoAFunctionKeepsItsScope:
    @pytest.mark.parametrize("word", list(RUNNERS))
    def test_the_callers_local_variable_is_visible(self, word):
        program = RUNNERS[word] + " {} {10 :local set {local 1 +} g} :c defun c"
        expected = [1] if word == "filter-count" else [11]
        assert run(program) == expected

    @pytest.mark.parametrize("word", ["eval", "if", "times", "do", "collect"])
    def test_a_block_does_not_see_the_runners_variables(self, word):
        runner = RUNNERS[word].replace("{b} {", "{b} {99 :hidden set ")
        with pytest.raises(UndefinedSymbolError, match="hidden"):
            run(runner + " {hidden} g")


class TestABlockReturnedFromAFunctionIsAClosure:
    @pytest.mark.parametrize(
        "program, expected",
        [
            ("{x} {{x 100 +}} :mk defun 5 mk eval", [105]),
            ("{x} {{drop x 100 +}} :mk defun [0] 5 mk map", [[105]]),
            ("{x} {{x 100 +}} :mk defun {} 5 mk lambda eval", [105]),
            ("{x} {{x 100 +}} :mk defun true 5 mk if", [105]),
            ("{x} {{x 100 +}} :mk defun 5 mk 2 times", [105, 105]),
            ("{x} {{x 100 +}} :mk defun 5 mk collect", [[105]]),
            ("{x} {{x 100 +}} :mk defun [] 5 mk apply", [105]),
        ],
    )
    def test_it_sees_the_calls_argument(self, program, expected):
        assert run(program) == expected


class TestABlockKeptFromALoopIterationSeesThatIteration:
    @pytest.mark.parametrize(
        "program, expected",
        [
            ("1 3 :i {{i 0 +}} do 3 listn {eval} map", [[1, 2, 3]]),
            ("1 3 :i {{drop i}} do 3 listn {b} {[0] b map} lambda map", [[[1], [2], [3]]]),
            ("1 3 :i {{} {i} lambda} do 3 listn {eval} map", [[1, 2, 3]]),
            ("[10 20] :x {{x}} dolist 2 listn {eval} map", [[10, 20]]),
            ("[1 2] 0 :acc :x {{x} :f set acc x +} reduce f eval", [3, 2]),
        ],
    )
    def test_it(self, program, expected):
        assert run(program) == expected


class TestABlockWrittenWhereItRunsIsUnchanged:
    @pytest.mark.parametrize(
        "program, expected",
        [
            ("{} {0 :q set true {5 :q set} if q} :f defun f", [5]),
            ("{} {1 2 :i {i :last set} do last} :f defun f", [2]),
            ("1 3 :i {i} do", [1, 2, 3]),
            ("0 :s set 1 3 :i {s i + :s set} do s", [6]),
            ("3 :x set {x 1 +} :y set 10 :x set y eval", [11]),
            ("[1 2 3] 0 :acc :x {acc x + :seen set acc x +} reduce drop seen", [6]),
            ("1 2 {3 0 /} {\"caught\"} iferror", [1, 2, "caught"]),
            ("0 :n set {n 3 <} {n 1 + :n set} while n", [3]),
            ("{} {5 :m set {m} 2 times} :f defun f", [5, 5]),
        ],
    )
    def test_it(self, program, expected):
        assert run(program) == expected

    def test_a_variable_first_set_in_a_loop_body_inside_a_function_stays_in_the_function(self):
        with pytest.raises(UndefinedSymbolError):
            run("{} {1 3 :i {i :tmp set} do} :f defun f tmp")


class TestWhatChanged:
    def test_a_block_made_at_the_top_level_does_not_see_a_functions_variables(self):
        with pytest.raises(UndefinedSymbolError, match="x"):
            run("{x 1 +} :b set {x} {b eval} :f defun 5 f")

    def test_a_block_made_at_the_top_level_does_not_see_a_loop_variable_from_inside_the_loop(self):
        with pytest.raises(UndefinedSymbolError, match="i"):
            run("{i} :b set 1 3 :i {b eval} do")

    def test_but_a_block_handed_to_do_as_its_body_gets_the_loop_variable(self):
        assert run("{i} :b set 1 3 :i b do") == [1, 2, 3]

    def test_a_name_first_set_in_a_carried_block_lands_in_the_blocks_own_scope(self):
        # `b` is bound to the top level, so `w` is a top-level variable, not the function's
        assert run("{7 :w set} :b set {} {b eval} :f defun f w") == [7]


class TestMacrosStillExpandInPlace:
    def test_a_block_run_during_expansion_writes_behind_the_barrier(self):
        assert run("1 :t =", "{} { 1 2 :i { i :t = } do {t} } :m defmacro", "m t") == [2, 1]
        assert run("1 :t =", "{} { { 5 :t = } eval {t} } :m defmacro", "m t") == [5, 1]

    def test_the_expansion_runs_in_the_callers_scope(self):
        assert run("{v n} {{v :n =}} :setq defmacro 5 :x setq x") == [5]
        assert run("0 :c set {} {{c 1 + :c set c}} :count defmacro count count") == [1, 2]

    def test_a_lambda_made_by_a_macro_closes_over_the_caller(self):
        assert run("0 :k set {} {{} {k 1 + :k set k} lambda} :mk defmacro mk :f set f eval f eval k") == [1, 2, 2]
