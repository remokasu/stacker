"""When `try` or `iferror` catches an error, the stack is as it was when the word began."""

import pytest

from stacker import Stacker


def run(*lines: str) -> list[object]:
    stacker = Stacker()
    for line in lines:
        stacker.process_expression(line)
    return list(stacker.stack)


class TestTheStackIsPutBack:
    @pytest.mark.parametrize(
        "program, expected",
        [
            ('1 2 {3 0 /} {"caught"} iferror', [1, 2, "caught"]),
            ('5 6 {7 1 0 /} {"caught"} iferror', [5, 6, "caught"]),
            ('5 6 {[1] 9 at} {"caught"} iferror', [5, 6, "caught"]),
            ('5 {null 1 +} {"caught"} iferror', [5, "caught"]),
            ("10 20 {+ 1 0 /} {drop} try", [10, 20]),
            ('{} {1 2 1 0 /} :g defun {g} {"h"} iferror', ["h"]),
            ('{1 2 1 0 /} {"h"} iferror', ["h"]),
            ("{300 1 0 /} {drop 0} try", [0]),
            ('1 2 {3 4} {"never"} iferror', [1, 2, 3, 4]),
        ],
    )
    def test_values_pushed_and_taken_by_the_failing_block_are_undone(self, program, expected):
        assert run(program) == expected

    def test_the_wrong_total_from_the_report_is_right_now(self):
        program = (
            '{d} {{d "price" get int d "qty" get int *} {e} {0} lambda try} :amount defun '
            'dict :a set 100 a "price" put! 2 a "qty" put! '
            'dict :b set 300 b "price" put! "x" b "qty" put! '
            'dict :c set 50 c "price" put! 4 c "qty" put! '
            "0 :total set a b c 3 listn :o {total o amount + :total set} dolist total"
        )
        assert run(program) == [400]

    def test_a_lambda_handler_sees_a_clean_stack_below_the_error(self):
        assert run('1 {2 3 1 0 /} {e} {depth} lambda try') == [1, 0]

    def test_what_a_block_changed_in_place_is_not_undone(self):
        assert run('[1 2] array :a set {9 a append! 1 0 /} {drop} try a') == [[1, 2, 9]]

    def test_a_variable_set_in_the_block_is_not_undone(self):
        assert run('{7 :v set 1 0 /} {drop} try v') == [7]


class TestTheErrorDictionaryCarriesTheStackAtTheFailure:
    def test_the_partial_stack_is_under_the_stack_key(self):
        assert run('1 {2 3 1 0 /} {"stack" get} try') == [1, [1, 2, 3]]

    def test_the_kind_and_message_are_still_there(self):
        assert run('{"E" "boom" throw} {dup "kind" get swap "message" get} try') == ["E", "boom"]

    def test_the_stack_key_is_a_copy(self):
        assert run('{2 1 0 /} {"stack" get 9 swap drop} try') == [9]


class TestNestingAndFailingHandlers:
    def test_an_inner_try_puts_back_its_own_stack_and_an_outer_one_the_rest(self):
        assert run("1 {2 {3 4 1 0 /} {5 1 0 /} try} {drop 9} try") == [1, 9]

    def test_an_error_in_the_handler_leaves_the_restored_stack_plus_the_handlers_work(self):
        stacker = Stacker()
        with pytest.raises(Exception, match="undefined_y"):
            stacker.process_expression("1 {2 0 1 0 /} {drop 1 2 3 undefined_y} try")
        assert list(stacker.stack) == [1, 1, 2, 3]

    def test_a_try_inside_a_map_body_works_on_the_bodys_own_stack(self):
        assert run("[1 2 3] {:x set 10 {x 2 == {1 0 /} if x} {drop 5} try +} map") == [[11, 15, 13]]


class TestWhatStillPassesThrough:
    def test_break_leaves_the_loop_with_the_stack_as_the_body_left_it(self):
        assert run("0 {1 + {5 break} {} iferror} loop") == [1, 5]

    def test_an_exit_is_not_caught(self):
        with pytest.raises(SystemExit):
            run("{3 exit-code} {} try")

    def test_no_error_leaves_everything_the_block_did(self):
        assert run("1 {2 3 +} {drop} try") == [1, 5]
