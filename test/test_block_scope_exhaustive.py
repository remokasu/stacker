"""Equivalence classes and error paths for block scope.

A block runs in the scope it was written in. Written where it runs it is
plain code; carried to another function it is a closure. These tests push
carried blocks through every runner, through nesting, `set` / `global`,
`break`, macros, `include` and the recursion guard.
"""

import subprocess
import sys
from pathlib import Path

import pytest

from stacker import Stacker
from stacker.error import UndefinedSymbolError

REPO_ROOT = Path(__file__).resolve().parent.parent


def run(*lines: str) -> list[object]:
    stacker = Stacker()
    for line in lines:
        stacker.process_expression(line)
    return list(stacker.stack)


class TestConditionAndResultBlocksCarriedElsewhere:
    def test_a_while_body_carried_from_the_caller_sees_the_callers_variable(self):
        program = "{c b} {c b while} :w defun {} {0 :k set {k 3 <} {k 1 + :k set} w k} :f defun f"
        assert run(program) == [3]

    def test_a_while_condition_written_in_the_runner_reads_the_runners_variable(self):
        # the condition `{n 3 <}` is written in `w`; the carried body only breaks
        program = "{b} {7 :n set {n 3 <} b while n} :w defun {} {{break} w} :f defun f"
        assert run(program) == [7]

    def test_a_while_body_carried_from_the_caller_cannot_see_the_runners_variable(self):
        program = "{b} {0 :n set {n 3 <} b while} :w defun {} {{n 1 + :n set} w} :c defun c"
        with pytest.raises(UndefinedSymbolError, match="n"):
            run(program)

    def test_a_while_condition_carried_from_the_caller_sees_the_callers_variable(self):
        program = (
            "{c b} {c b while} :w defun "
            "{} {0 :k set {k 3 <} {k 1 + :k set} w k} :f defun f"
        )
        assert run(program) == [3]

    def test_a_while_with_both_blocks_carried_runs_until_the_condition_fails(self):
        program = "{c b} {c b while} :w defun {} {0 :k set 0 :s set {k 4 <} {k 1 + :k set s k + :s set} w s} :f defun f"
        assert run(program) == [10]

    def test_a_cond_with_carried_condition_and_result_blocks(self):
        program = "{cs rs} {cs rs 1 cond} :cc defun {} {7 :v set {v 7 ==} {v 100 +} cc} :f defun f"
        assert run(program) == [107]

    def test_a_cond_picks_the_second_pair_when_carried(self):
        program = (
            "{c1 r1 c2 r2} {c1 r1 c2 r2 2 cond} :cc defun "
            "{} {7 :v set {v 8 ==} {1} {v 7 ==} {v 100 +} cc} :f defun f"
        )
        assert run(program) == [107]

    def test_a_cond_result_block_carried_cannot_see_the_runners_variable(self):
        program = "{r} {5 :hidden set {true} r 1 cond} :cc defun {} {{hidden} cc} :f defun f"
        with pytest.raises(UndefinedSymbolError, match="hidden"):
            run(program)

    def test_an_if_with_a_carried_branch_sees_the_callers_variable(self):
        assert run("{b} {true b if} :g defun {} {4 :v set {v 1 +} g} :f defun f") == [5]

    def test_an_ifelse_with_two_carried_branches(self):
        program = "{t e} {false t e ifelse} :g defun {} {4 :v set {v} {v 1 +} g} :f defun f"
        assert run(program) == [5]


class TestNestedCarriedBlocks:
    def test_a_block_returned_by_a_function_that_returns_a_block(self):
        assert run("{x} {{{x 1 +}}} :mk defun 5 mk eval eval") == [6]

    def test_three_levels_of_closures(self):
        assert run("{x} {{{{x 2 *}}}} :mk defun 5 mk eval eval eval") == [10]

    def test_an_inner_block_sees_the_outer_functions_local_through_a_variable(self):
        program = "{x} {{x} :inner set {inner}} :mk defun {y} {y mk} :mk2 defun 5 mk2 eval eval"
        assert run(program) == [5]

    def test_two_calls_of_the_maker_do_not_share_their_argument(self):
        program = "{x} {{x}} :mk defun 1 mk 2 mk :b2 set :b1 set b1 eval b2 eval"
        assert run(program) == [1, 2]

    def test_a_block_carried_across_two_function_boundaries(self):
        program = "{b} {b eval} :r1 defun {b} {b r1} :r2 defun {} {4 :q set {q 1 +} r2} :f defun f"
        assert run(program) == [5]

    def test_a_block_carried_across_three_function_boundaries(self):
        program = (
            "{b} {b eval} :r1 defun {b} {b r1} :r2 defun {b} {b r2} :r3 defun "
            "{} {4 :q set {q 1 +} r3} :f defun f"
        )
        assert run(program) == [5]

    def test_a_carried_block_does_not_see_any_runner_in_the_chain(self):
        program = "{b} {1 :seen set b eval} :r1 defun {b} {2 :seen2 set b r1} :r2 defun {} {{seen seen2 +} r2} :f defun f"
        with pytest.raises(UndefinedSymbolError):
            run(program)


class TestSetAndGlobalFromACarriedBlock:
    def test_set_of_an_existing_variable_updates_the_blocks_own_scope(self):
        program = "{b} {99 :v set b eval v} :run defun {} {10 :v set {v 5 + :v set v} run} :f defun f"
        assert run(program) == [15, 99]

    def test_the_callers_variable_is_updated_after_the_run(self):
        program = "{b} {99 :v set b eval} :run defun {} {10 :v set {v 5 + :v set} run v} :f defun f"
        assert run(program) == [15]

    def test_set_of_a_new_name_lands_in_the_blocks_scope_not_the_runners(self):
        program = "{b} {b eval new} :run defun {} {{1 :new set} run} :f defun f"
        with pytest.raises(UndefinedSymbolError, match="new"):
            run(program)

    def test_set_of_a_new_name_is_visible_to_the_blocks_own_function_afterwards(self):
        program = "{b} {b eval} :run defun {} {{1 :new set} run new} :f defun f"
        assert run(program) == [1]

    def test_global_from_a_carried_block_reaches_the_top_level(self):
        assert run("{b} {b eval} :run defun {} {{5 :gg global} run} :f defun f gg") == [5]

    def test_global_from_a_carried_block_wins_over_a_local_of_the_same_name(self):
        program = "{b} {b eval} :run defun {} {1 :gg set {5 :gg global} run} :f defun f gg"
        assert run(program) == [5]

    def test_a_runner_with_a_shadowing_variable_keeps_it(self):
        program = "{b} {99 :v set b eval v} :run defun {} {10 :v set {v 5 + :v set} run} :f defun f"
        assert run(program) == [99]


class TestBreakInACarriedBlock:
    @pytest.mark.parametrize(
        "runner",
        [
            "{b} {b 5 times} :r defun",
            "{b} {b loop} :r defun",
            "{b} {1 5 :i b do} :r defun",
            "{b} {[1 2 3 4 5] :i b dolist} :r defun",
        ],
    )
    def test_a_dynamic_break_exits_the_runners_loop(self, runner):
        program = runner + " {} {0 :c set {c 1 + :c set c 3 == {break} {} ifelse} r c} :f defun f"
        assert run(program) == [3]

    def test_a_while_loop_is_left_by_a_break_in_a_carried_body(self):
        program = (
            "{b} {{true} b while} :r defun "
            "{} {0 :c set {c 1 + :c set c 2 == {break} {} ifelse} r c} :f defun f"
        )
        assert run(program) == [2]

    def test_code_after_the_runners_loop_still_runs(self):
        program = "{b} {b loop 77} :r defun {} {{break} r} :f defun f"
        assert run(program) == [77]


class TestHandlersAndCombinators:
    def test_an_iferror_handler_carried_from_the_caller(self):
        program = "{h} {{1 0 /} h iferror} :ie defun {} {5 :v set {v} ie} :f defun f"
        assert run(program) == [5]

    def test_a_try_handler_carried_from_the_caller(self):
        program = "{h} {{1 0 /} h try} :ie defun {} {5 :v set {drop v 2 +} ie} :f defun f"
        assert run(program) == [7]

    def test_an_iferror_handler_carried_cannot_see_the_runners_variable(self):
        program = "{h} {5 :hidden set {1 0 /} h iferror} :ie defun {} {{hidden} ie} :f defun f"
        with pytest.raises(UndefinedSymbolError, match="hidden"):
            run(program)

    def test_a_reduce_body_carried_from_the_caller(self):
        program = "{b} {[1 2 3] 0 :acc :x b reduce} :rd defun {} {10 :k set {acc x + k +} rd} :f defun f"
        assert run(program) == [36]

    def test_a_reduce_body_that_sets_a_new_name_leaves_it_in_the_bodys_scope(self):
        program = (
            "{b} {[1 2 3] 0 :acc :x b reduce} :rd defun "
            "{} {10 :k set {1 :fresh set acc x + k +} rd fresh} :f defun f"
        )
        assert run(program) == [36, 1]

    def test_a_reduce_body_new_name_is_not_in_the_runners_scope(self):
        program = (
            "{b} {[1 2 3] 0 :acc :x b reduce fresh} :rd defun "
            "{} {{1 :fresh set acc x +} rd} :f defun f"
        )
        with pytest.raises(UndefinedSymbolError, match="fresh"):
            run(program)

    def test_a_do_whose_body_is_a_variable_holding_a_block(self):
        assert run("{i} :b set 1 3 :i b do") == [1, 2, 3]

    def test_a_do_body_variable_can_use_the_loop_variable_in_arithmetic(self):
        assert run("{i 2 *} :b set 1 3 :i b do") == [2, 4, 6]

    def test_a_dolist_whose_body_is_a_variable_holding_a_block(self):
        assert run("{x} :b set [4 5] :x b dolist") == [4, 5]

    def test_a_dolist_body_variable_inside_a_function(self):
        assert run("{} {{x 1 +} :b set [4 5] :x b dolist} :f defun f") == [5, 6]

    def test_a_collect_of_a_carried_block(self):
        program = "{b} {b collect} :cl defun {} {3 :v set {v v 1 +} cl} :f defun f"
        assert run(program) == [[3, 4]]

    def test_an_apply_of_a_carried_block_with_an_argument_list(self):
        program = "{b} {[10] b apply} :ap defun {} {3 :v set {v +} ap} :f defun f"
        assert run(program) == [13]

    def test_an_apply_with_an_empty_argument_list(self):
        program = "{b} {[] b apply} :ap defun {} {3 :v set {v} ap} :f defun f"
        assert run(program) == [3]

    def test_a_map_body_carried_from_the_caller(self):
        program = "{b} {[1 2] b map} :mp defun {} {10 :k set {k +} mp} :f defun f"
        assert run(program) == [[11, 12]]


class TestLambdaMadeInACarriedBlock:
    def test_a_lambda_made_by_times_captures_the_blocks_scope(self):
        program = (
            "{b} {b 3 times} :t defun "
            "{} {0 :z set {{} {z 1 + :z set z} lambda} t :l3 set l3 eval l3 eval l3 eval z} :f defun f"
        )
        # two lambdas stay under the one bound to `l3`; all three share the caller's `z`
        assert run(program)[-4:] == [1, 2, 3, 3]

    def test_the_lambda_still_works_after_the_runner_returned(self):
        program = "{b} {b eval} :t defun {} {5 :z set {{} {z 10 +} lambda} t} :f defun f eval"
        assert run(program) == [15]


class TestRecursionThroughACarriedBlock:
    def test_a_function_that_passes_the_same_block_down(self):
        program = (
            "{n b} {n 0 > {b eval n 1 - b rr} {} ifelse} :rr defun "
            "{} {0 :cnt set {cnt 1 + :cnt set} 5 swap rr cnt} :f defun f"
        )
        assert run(program) == [5]

    def test_plain_recursion_with_a_block_argument(self):
        program = (
            "{n b} {n 0 <= {0} {b eval n 1 - b rr +} ifelse} :rr defun "
            "{} {2 :step set {step} 4 swap rr} :f defun f"
        )
        assert run(program) == [8]

    def test_eval_recursion_returns_the_depth(self):
        program = "{n} {n 0 <= {0} {{n 1 - rec 1 +} eval} ifelse} :rec defun 20 rec"
        assert run(program) == [20]

    def test_plain_recursion_returns_the_depth(self):
        program = "{n} {n 0 <= {0} {n 1 - rec 1 +} ifelse} :rec defun 20 rec"
        assert run(program) == [20]


class TestMacrosStayBehindTheBarrier:
    def test_a_times_in_a_macro_body_writes_behind_the_barrier(self):
        program = ("1 :t =", "{} { {9 :t =} 3 times {t} } :m defmacro", "m t")
        assert run(*program) == [9, 1]

    def test_an_eval_in_a_macro_body_writes_behind_the_barrier(self):
        assert run("1 :t =", "{} { {7 :t =} eval {t} } :m defmacro", "m t") == [7, 1]

    def test_a_do_in_a_macro_body_writes_behind_the_barrier(self):
        assert run("1 :t =", "{} { 1 2 :i {i :t =} do {t} } :m defmacro", "m t") == [2, 1]

    def test_a_name_set_in_a_macro_body_block_is_not_left_in_the_caller(self):
        with pytest.raises(UndefinedSymbolError, match="mm"):
            run("{} {{ 8 :mm set} eval {1}} :m defmacro", "m mm")

    def test_a_macro_expansion_that_is_a_lambda_closes_over_the_caller(self):
        program = "0 :k set {} {{} {k 1 + :k set k} lambda} :mk defmacro mk :f set f eval f eval k"
        assert run(program) == [1, 2, 2]

    def test_a_macro_lambda_inside_a_function_closes_over_that_function(self):
        program = "{} {0 :k set {} {{} {k 1 + :k set k} lambda} :mk defmacro mk} :f defun f eval f eval"
        assert run(program) == [1, 1]

    def test_a_nested_block_in_an_expansion_is_evaled_in_the_caller(self):
        assert run("{} {{ {k} }} :mk defmacro 5 :k set mk eval eval") == [5]

    def test_a_nested_block_in_an_expansion_sees_the_callers_function_scope(self):
        program = "{} {{ {k} }} :mk defmacro {} {6 :k set mk} :f defun f eval eval"
        assert run(program) == [6]

    def test_a_macro_argument_is_read_in_the_callers_scope(self):
        program = "{x} {{x 1 +}} :m defmacro {} {3 :x set {x} m} :f defun f"
        assert run(program) == [4]

    def test_macroexpand_result_runs_in_the_caller(self):
        assert run("{} {{ 3 :zz set zz }} :m defmacro {m} macroexpand eval zz") == [3, 3]

    def test_macroexpand_inside_a_function_binds_to_that_function(self):
        program = "{} {{ 3 :zz set zz }} :m defmacro {} {{m} macroexpand eval zz} :f defun f"
        assert run(program) == [3, 3]

    def test_macroexpand_inside_a_function_does_not_leak_its_names_to_the_top_level(self):
        program = "{} {{ 3 :zz set zz }} :m defmacro {} {{m} macroexpand eval zz} :f defun f drop drop zz"
        with pytest.raises(UndefinedSymbolError, match="zz"):
            run(program)

    def test_macroexpand_shows_the_expansion_without_running_it(self):
        (block,) = run("{} {{ 3 :zz set zz }} :m defmacro {m} macroexpand")
        assert str(block) == "{3 :zz set zz}"


class TestIncludeIsUnchanged:
    def test_a_top_level_set_in_an_included_file_goes_to_the_includers_scope(self, tmp_path: Path):
        lib = tmp_path / "lib.stk"
        lib.write_text("5 :top set\n{} {top 1 +} :getop defun\n", encoding="utf-8")
        assert run(f'"{lib}" include', "top getop") == [5, 6]

    def test_an_included_file_inside_a_function_sets_in_that_function(self, tmp_path: Path):
        lib = tmp_path / "lib.stk"
        lib.write_text("5 :inner set\n", encoding="utf-8")
        assert run(f'{{}} {{"{lib}" include inner}} :f defun f') == [5]
        with pytest.raises(UndefinedSymbolError, match="inner"):
            run(f'{{}} {{"{lib}" include}} :f defun f inner')

    def test_a_block_made_by_an_included_file_is_bound_to_the_includers_scope(self, tmp_path: Path):
        lib = tmp_path / "lib.stk"
        lib.write_text("{9 :fromblock set} :blk set\n", encoding="utf-8")
        assert run(f'"{lib}" include', "{} {blk eval} :f defun f fromblock") == [9]

    def test_a_block_made_by_an_included_file_run_by_a_function_is_a_closure(self, tmp_path: Path):
        lib = tmp_path / "lib.stk"
        lib.write_text("100 :base set\n{base +} :addbase set\n", encoding="utf-8")
        program = f'"{lib}" include'
        assert run(program, "{b} {1 b eval} :g defun {} {addbase g} :f defun f") == [101]


def _run_script(tmp_path: Path, text: str, *args: str) -> subprocess.CompletedProcess:
    script = tmp_path / "script.stk"
    script.write_text(text, encoding="utf-8")
    return subprocess.run(
        [sys.executable, "-m", "stacker", *args, str(script)],
        capture_output=True,
        text=True,
        timeout=120,
        check=False,
        cwd=REPO_ROOT,
    )


PLAIN = "{n} {n 0 <= {0} {n 1 - plain 1 +} ifelse} :plain defun\n"
VIA_EVAL = "{n} {n 0 <= {0} {{n 1 - viaeval 1 +} eval} ifelse} :viaeval defun\n"
CARRIED = (
    "{n b} {n 0 <= {0} {b eval n 1 - b carried 1 +} ifelse} :carried defun\n"
    "0 :hits set\n"
)


@pytest.mark.skipif(sys.version_info < (3, 11), reason="the C stack overflows at the default recursion limit on 3.10")
class TestRecursionDepthAtTheDefaultLimit:
    """The default limit is 1500 calls; n=1499 makes exactly 1500 (n=1499 down to 0)."""

    @pytest.mark.parametrize("name, prelude", [("plain", PLAIN), ("viaeval", VIA_EVAL)])
    def test_recursion_to_exactly_the_limit_works(self, tmp_path, name, prelude):
        result = _run_script(tmp_path, prelude + f"1499 {name} echo\n")
        assert (result.returncode, result.stdout.strip()) == (0, "1499"), result.stderr

    @pytest.mark.parametrize("name, prelude", [("plain", PLAIN), ("viaeval", VIA_EVAL)])
    def test_recursion_one_past_the_limit_raises_stacker_recursion_error(self, tmp_path, name, prelude):
        result = _run_script(tmp_path, prelude + f"1500 {name} echo\n")
        combined = result.stdout + result.stderr
        assert "StackerRecursionError" in combined
        assert "(1500)" in combined
        assert f"`{name}`" in combined

    def test_recursion_far_past_the_limit_does_not_crash_the_process(self, tmp_path):
        result = _run_script(tmp_path, PLAIN + "100000 plain echo\n")
        assert result.returncode >= 0
        assert "StackerRecursionError" in result.stdout + result.stderr

    def test_a_carried_block_survives_deep_recursion(self, tmp_path):
        program = CARRIED + "{} {{hits 1 + :hits set} 1000 swap carried drop hits} :f defun f echo\n"
        result = _run_script(tmp_path, program)
        assert (result.returncode, result.stdout.strip()) == (0, "1000"), result.stderr

    def test_a_lowered_limit_applies_to_eval_recursion(self, tmp_path):
        result = _run_script(tmp_path, VIA_EVAL + "20 viaeval echo\n", "--recursion-limit", "10")
        combined = result.stdout + result.stderr
        assert "StackerRecursionError" in combined
        assert "(10)" in combined

    def test_the_guard_is_unwound_after_the_error(self, tmp_path):
        program = PLAIN + "{} {1500 plain} :boom defun\n{boom} {0} iferror drop\n10 plain echo\n"
        result = _run_script(tmp_path, program)
        assert result.stdout.strip().endswith("10"), result.stdout + result.stderr
