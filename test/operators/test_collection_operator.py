"""Arrays and dictionaries: the words that make, read and change them."""

import pytest

from stacker import Array, Stacker
from stacker.engine.data_type import Symbol
from stacker.error import (
    KeyNotFoundError,
    StackerIndexError,
    StackerTypeError,
    ValidationError,
)


def run(*lines: str) -> list[object]:
    stacker = Stacker()
    for line in lines:
        stacker.process_expression(line)
    return list(stacker.stack)


class TestArrayWords:
    def test_array_makes_an_array_from_a_list_string_or_block(self):
        a, = run("[1 2 3] array")
        assert isinstance(a, Array) and a == [1, 2, 3]
        assert run('"abc" array') == [["a", "b", "c"]]
        assert run("{a b} array") == [[Symbol("a"), Symbol("b")]]

    def test_array_converts_one_level_only(self):
        a, = run("[[1 2] [3 4]] array")
        assert isinstance(a, Array) and not isinstance(a[0], Array)

    def test_array_of_an_array_is_a_new_array_sharing_elements(self):
        assert run("[1 2] array :a set a array :b set a b same? a b ==") == [False, True]

    @pytest.mark.parametrize("program", ["5 array", "dict array", "null array", ":x array"])
    def test_array_rejects_other_values(self, program):
        with pytest.raises(StackerTypeError):
            run(program)

    def test_array_of_makes_n_slots(self):
        assert run("3 0 array-of") == [[0, 0, 0]]
        assert run("0 7 array-of") == [[]]
        assert run("3 [0 0] array-of") == [[[0, 0], [0, 0], [0, 0]]]

    @pytest.mark.parametrize("program", ["-1 0 array-of", "2.5 0 array-of", "true 0 array-of"])
    def test_array_of_needs_a_count(self, program):
        with pytest.raises((ValidationError, StackerTypeError)):
            run(program)

    def test_array_of_refuses_to_share_one_array_or_dict(self):
        with pytest.raises(StackerTypeError, match="every slot"):
            run("3 [] array array-of")
        with pytest.raises(StackerTypeError, match="every slot"):
            run("3 dict array-of")

    def test_at_reads_and_takes_the_container_off(self):
        assert run("[10 20 30] 1 at") == [20]
        assert run("[10 20 30] array -1 at") == [30]
        assert run('"abc" 1 at') == ["b"]
        assert run("{a b} 0 at") == [Symbol("a")]

    @pytest.mark.parametrize("program", ["[1 2 3] 3 at", "[] array 0 at", "[1 2] -3 at"])
    def test_at_out_of_range(self, program):
        with pytest.raises(StackerIndexError, match="out of range"):
            run(program)

    @pytest.mark.parametrize("program", ["[1 2] 1.0 at", "[1 2] true at", "[1 2] {0} at", "dict 0 at", "5 0 at"])
    def test_at_type_errors(self, program):
        with pytest.raises(StackerTypeError):
            run(program)

    def test_at_on_a_dictionary_points_to_get(self):
        with pytest.raises(StackerTypeError, match="get"):
            run("dict 0 at")

    def test_at_bang_stores_and_pushes_nothing(self):
        assert run("[1 2 3] array :a set 9 a 0 at! 8 a -1 at! a") == [[9, 2, 8]]

    def test_at_bang_does_not_grow(self):
        with pytest.raises(StackerIndexError):
            run("[1 2 3] array :a set 9 a 3 at!")

    @pytest.mark.parametrize("program", ["9 [1 2 3] 0 at!", '9 "abc" 0 at!', "9 {a} 0 at!", "9 dict 0 at!"])
    def test_changing_words_refuse_lists_strings_blocks_and_dicts(self, program):
        with pytest.raises(StackerTypeError):
            run(program)

    def test_a_list_cannot_be_changed_and_the_message_says_how(self):
        with pytest.raises(StackerTypeError, match="array"):
            run("9 [1 2 3] 0 at!")

    def test_a_block_value_is_stored_without_being_evaluated(self):
        assert run("[0] array :a set {1 2 +} a 0 at! a 0 at eval") == [3]

    def test_append_bang_and_pop_bang(self):
        assert run("[1 2] array :a set 3 a append! a pop! a pop! a") == [3, 2, [1]]

    def test_pop_bang_on_an_empty_array(self):
        with pytest.raises(StackerIndexError, match="empty"):
            run("[] array pop!")

    def test_the_whole_example(self):
        assert run("[1 2 3] array :a set 9 a 0 at! 4 a append! a") == [[9, 2, 3, 4]]
        assert run("[1 2 3] array :a set a dup 7 swap 1 at!") == [[1, 7, 3]]


class TestDictWords:
    def test_put_get_has_del_keys_values(self):
        assert run('dict :d set 1 d "a" put! 2 d :b put! d "a" get d "z" get d :b has? d "z" has?') == [1, None, True, False]
        assert run('dict :d set 1 d "a" put! 2 d :b put! d keys d values') == [["a", Symbol("b")], [1, 2]]
        assert run('dict :d set 1 d "a" put! 2 d "b" put! d "a" del! d keys') == [["b"]]

    def test_put_keeps_the_order_of_an_existing_key(self):
        assert run('dict :d set 1 d "a" put! 2 d "b" put! 3 d "a" put! d keys d values') == [["a", "b"], [3, 2]]

    def test_equal_numbers_are_one_key_and_a_symbol_is_not_a_string(self):
        assert run("dict :d set 1 d 1 put! 2 d 1.0 put! d keys d 1 get") == [[1], 2]
        assert run('dict :d set 1 d :a put! 2 d "a" put! d len') == [2]

    @pytest.mark.parametrize("program", ["dict true get", "dict null get", "dict [1 2] get", "dict [] array get", "dict nan get", "1 dict {x} put!"])
    def test_keys_must_be_strings_numbers_or_symbols(self, program):
        with pytest.raises(StackerTypeError, match="key"):
            run(program)

    def test_null_stored_under_a_key_is_there(self):
        assert run('dict :d set null d "k" put! d "k" get d "k" has?') == [None, True]

    def test_del_of_a_missing_key(self):
        with pytest.raises(KeyNotFoundError, match="no key"):
            run('dict "z" del!')

    @pytest.mark.parametrize("program", ['[1 2] "a" get', '1 [1 2] "a" put!', 'null "a" get', '5 "a" has?'])
    def test_dict_words_need_a_dictionary(self, program):
        with pytest.raises(StackerTypeError, match="dictionary"):
            run(program)

    def test_get_on_an_array_points_to_at(self):
        with pytest.raises(StackerTypeError, match="at"):
            run('[1 2] array "a" get')

    def test_keys_is_a_snapshot(self):
        assert run('dict :d set 1 d "a" put! 2 d "b" put! d keys :k {d k del!} dolist d len') == [0]

    def test_a_block_value_is_stored_without_being_evaluated(self):
        assert run('dict :d set {1 2 +} d "f" put! d "f" get eval') == [3]


class TestPredicates:
    def test_array_and_dict_predicates(self):
        assert run("[1] array array? [1] array? dict array? dict dict? [1] dict?") == [True, False, False, True, False]

    def test_list_null_pair_on_arrays_and_dicts(self):
        assert run("[] array list? [] array null? [1] array pair? dict null? dict list?") == [False, True, True, False, False]

    def test_same_is_identity_for_arrays_and_dicts_and_equality_otherwise(self):
        assert run("[1 2] array dup same?") == [True]
        assert run("[1 2] array [1 2] array same?") == [False]
        assert run("[1 2] array [1 2] array ==") == [True]
        assert run("[1 2] array [1 2] ==") == [True]
        assert run("dict dict == dict dict same?") == [True, False]
        assert run("null null same? 1 1 same? 1 2 same?") == [True, True, False]
