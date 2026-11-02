"""Tests for the compiler of blocks that run often: when it compiles, what it keeps, and when it lets go."""

import logging

import pytest

from stacker import Stacker
from stacker.engine import compiler, core
from stacker.engine.core import StackerCore
from stacker.engine.data_type import Symbol
from stacker.engine.scope import ScopedVariables
from stacker.error import StackUnderflowError, UndefinedSymbolError


@pytest.fixture
def at_once(monkeypatch):
    """Compiles every block on its first run, worthwhile or not (without the checking the session's eager state adds)."""
    monkeypatch.setattr(compiler, "THRESHOLD", 1)
    monkeypatch.setattr(compiler, "VERIFY", False)
    monkeypatch.setattr(compiler, "ONLY_WORTHWHILE", False)


@pytest.fixture
def verifying(monkeypatch):
    """Compiles on the first run and re-resolves every name before its step."""
    monkeypatch.setattr(compiler, "THRESHOLD", 1)
    monkeypatch.setattr(compiler, "VERIFY", True)
    monkeypatch.setattr(compiler, "ONLY_WORTHWHILE", False)


def block_of(stacker, source):
    """The block value `source` denotes, with its shared token list."""
    return next(iter(stacker.eval(source)))


def run_block(stacker, block, program="blk eval"):
    stacker.register_parameter("blk", block)
    return list(stacker.eval(program))


# --- when a block is compiled ---


def test_a_block_is_compiled_on_the_threshold_run_and_not_before(monkeypatch):
    monkeypatch.setattr(compiler, "THRESHOLD", 3)
    stacker = Stacker()
    block = block_of(stacker, "{1 +}")
    for run in (1, 2):
        assert run_block(stacker, block, "10 blk eval") == [11]
        assert block.tokens._runs == run
        assert block.tokens._unit is None
    assert run_block(stacker, block, "10 blk eval") == [11]
    assert isinstance(block.tokens._unit, compiler.Unit)


def test_an_interpreter_told_not_to_compile_neither_counts_nor_compiles(at_once):
    stacker = Stacker(compile=False)
    block = block_of(stacker, "{1 +}")
    for _ in range(3):
        assert run_block(stacker, block, "10 blk eval") == [11]
    assert (block.tokens._runs, block.tokens._unit) == (0, None)


def test_no_threshold_means_no_compiling(monkeypatch):
    monkeypatch.setattr(compiler, "THRESHOLD", None)
    stacker = Stacker()
    block = block_of(stacker, "{1 +}")
    for _ in range(3):
        run_block(stacker, block, "10 blk eval")
    assert (block.tokens._runs, block.tokens._unit) == (0, None)


def test_a_copy_of_the_interpreter_starts_cold(at_once):
    stacker = Stacker()
    block = block_of(stacker, "{1 +}")
    run_block(stacker, block, "10 blk eval")
    assert isinstance(block.tokens._unit, compiler.Unit)
    copied = next(iter(stacker.copy().eval("blk")))
    assert (copied.tokens._runs, copied.tokens._unit) == (0, None)


def test_a_macro_body_being_expanded_is_not_compiled(at_once):
    stacker = Stacker()
    stacker.process_expression("{a} {{a a +}} :twice defmacro")
    body = stacker.macros["twice"].body
    for _ in range(3):
        stacker.eval("3 twice")
    assert (body.tokens._runs, body.tokens._unit) == (0, None)


def test_the_instructions_are_data(at_once):
    stacker = Stacker()
    stacker.process_expression("{x} {x} :f defun 5 :v set")
    block = block_of(stacker, '{v 1 + f dup "s" :sym [1 2] {9} nosuch}')
    with pytest.raises(UndefinedSymbolError):
        run_block(stacker, block)
    kinds = [i.kind for i in block.tokens._unit.instructions]
    assert kinds == [
        compiler.VAR,
        compiler.CONST,
        compiler.FAST2,  # `+`: a regular word of two arguments
        compiler.CALL,  # a function written in Stacker
        compiler.WORD,  # `dup`: a stack word
        compiler.CONST,
        compiler.CONST,
        compiler.LIST,
        compiler.BLOCK,
        compiler.UNDEF,
    ]
    for instruction in block.tokens._unit.instructions:
        assert not callable(instruction.value) and not isinstance(instruction.value, StackerCore)
        assert instruction.name is None or isinstance(instruction.name, str)


def test_a_function_written_in_stacker_is_a_call_and_a_host_function_registered_as_a_word_is_a_word(at_once):
    stacker = Stacker()
    stacker.process_expression("{x} {x 1 +} :f defun")
    stacker.register_sfunction("hf", lambda a: a + 1, 1, True, "adds one")
    block = block_of(stacker, "{f hf}")
    assert run_block(stacker, block, "1 blk eval") == [3]
    kinds = [(i.kind, i.name) for i in block.tokens._unit.instructions]
    assert kinds == [(compiler.CALL, "f"), (compiler.WORD, "hf")]


def test_a_call_with_too_few_values_fails_as_the_interpreter_does(at_once):
    compiled, plain = Stacker(), Stacker(compile=False)
    for stacker in (compiled, plain):
        stacker.process_expression("{a b} {a b +} :f defun")
    block = block_of(compiled, "{f}")
    errors = []
    for stacker, program in ((compiled, "1 blk eval"), (plain, "1 {f} eval")):
        with pytest.raises(StackUnderflowError) as info:
            if stacker is compiled:
                run_block(stacker, block, program)
            else:
                list(stacker.eval(program))
        errors.append((str(info.value), list(stacker.stack)))
    assert errors[0] == errors[1] == ("Function `f` requires 2 arguments.", [])


@pytest.mark.parametrize("word", ["set", "="])
def test_a_symbol_and_set_compile_to_one_step_that_stands_at_the_words_position(at_once, word):
    stacker = Stacker()
    block = block_of(stacker, "{5 :x " + word + " x}")
    assert run_block(stacker, block) == [5]  # (`x` was undefined when the block was compiled: the unit is dropped)
    assert run_block(stacker, block) == [5]  # (compiled anew, with `x` a variable)
    steps = [(i.kind, i.index, i.name) for i in block.tokens._unit.instructions]
    assert steps == [(compiler.CONST, 0, None), (compiler.SET, 2, word), (compiler.VAR, 3, "x")]


def test_a_symbol_before_a_set_that_a_variable_hides_is_a_value(at_once):
    stacker = Stacker()
    stacker.process_expression("99 :set set")
    block = block_of(stacker, "{5 :x set}")
    assert run_block(stacker, block) == [5, Symbol("x"), 99]
    assert [i.kind for i in block.tokens._unit.instructions] == [compiler.CONST, compiler.CONST, compiler.VAR]


# --- a unit runs as the interpreter does ---


@pytest.mark.parametrize(
    ("program", "result"),
    [
        ("{n} {n 2 < {n} {n 1 - fib n 2 - fib +} ifelse} :fib defun 12 fib", [144]),
        ("0 :acc set 1 100 :i {acc i + :acc set} do acc", [5050]),
        ("[] array :fs set 1 3 :i {{i} fs append!} do fs {eval} map 0 :acc :x {acc x +} reduce", [6]),
        ('"" :s set 1 5 :i {s i str + :s set} do s', ["12345"]),
        ("1 5 :i {i 3 == {break} if i} do", [1, 2]),
    ],
)
def test_a_compiled_block_computes_what_the_interpreter_does(at_once, program, result):
    assert list(Stacker().eval(program)) == result
    assert list(Stacker(compile=False).eval(program)) == result


# --- the guards ---


def test_defining_a_word_sends_the_block_back_to_counting_and_it_is_compiled_again(at_once):
    stacker = Stacker()
    block = block_of(stacker, "{3 4 +}")
    assert run_block(stacker, block) == [7]
    unit = block.tokens._unit
    stacker.process_expression("{a b} {a b *} :+ defun")  # the word table changed
    assert run_block(stacker, block) == [12]  # the function now wins, as it does for the interpreter
    assert (block.tokens._unit, block.tokens._drops) == (None, 0)  # forgotten before it ran: no drop counted
    assert run_block(stacker, block) == [12]
    assert isinstance(block.tokens._unit, compiler.Unit) and block.tokens._unit is not unit
    assert block.tokens._unit.instructions[2].value[0] == "function"  # resolved anew, to the function


def test_a_variable_made_elsewhere_that_hides_a_word_is_seen_on_the_next_run(at_once):
    stacker = Stacker()
    block = block_of(stacker, "{dup}")
    assert run_block(stacker, block, "1 blk eval") == [1, 1]
    stacker.process_expression("99 :dup set")
    assert run_block(stacker, block, "1 blk eval") == [1, 99]


def test_a_variable_the_block_makes_itself_hides_a_word_from_the_next_step_on(at_once):
    stacker = Stacker()
    block = block_of(stacker, "{99 :dup set dup}")
    assert run_block(stacker, block) == [99]
    assert block.tokens._drops == 1  # `dup` was a word when compiled; the interpreter finished the run


def test_a_variable_that_vanished_lets_its_name_mean_what_it_means_now(at_once):
    stacker = Stacker()
    stacker.process_expression("7 :dup set")
    block = block_of(stacker, "{dup}")
    assert run_block(stacker, block, "1 blk eval") == [1, 7]
    stacker.variables.pop("dup")
    assert run_block(stacker, block, "1 blk eval") == [1, 1]  # the word again


def test_a_block_of_another_interpreter_runs_by_the_interpreter_there(at_once):
    first, second = Stacker(), Stacker()
    second.process_expression("{a b} {a b *} :+ defun")  # the same name means something else there
    block = block_of(first, "{3 4 +}")
    assert run_block(first, block) == [7]
    unit = block.tokens._unit
    assert list(second._evaluate(block.tokens, second.eval(""))) == [12]
    assert block.tokens._unit is unit  # neither dropped nor replaced


def test_a_change_made_by_another_block_between_runs_counts_no_drop(at_once):
    stacker = Stacker()
    block = block_of(stacker, "{1 +}")
    for _ in range(compiler.GIVE_UP + 1):
        assert run_block(stacker, block, "10 blk eval") == [11]
        stacker.operator_manager.words_changed()
    assert block.tokens._drops == 0
    assert run_block(stacker, block, "10 blk eval") == [11]
    assert isinstance(block.tokens._unit, compiler.Unit)


def test_a_failing_compiler_leaves_the_block_to_the_interpreter(at_once, monkeypatch, caplog):
    def broken(*args):
        raise ValueError("no")

    monkeypatch.setattr(compiler, "_instruction", broken)
    stacker = Stacker()
    block = block_of(stacker, "{1 +}")
    with caplog.at_level(logging.DEBUG, logger="stacker"):
        assert run_block(stacker, block, "10 blk eval") == [11]
    assert block.tokens._unit is compiler.UNCOMPILABLE
    assert any("left to the interpreter" in record.message for record in caplog.records)


def test_the_trace_after_an_error_in_the_part_the_interpreter_finished_is_the_blocks_tokens(at_once):
    stacker = Stacker()
    block = block_of(stacker, "{99 :dup set dup nosuch}")
    with pytest.raises(UndefinedSymbolError):
        run_block(stacker, block)
    assert list(stacker.get_trace_copy()) == list(block.tokens)


def test_verifying_catches_a_resolution_the_guards_let_through(verifying):
    stacker = Stacker()
    block = block_of(stacker, "{dup}")
    run_block(stacker, block, "1 blk eval")
    block.tokens._unit.not_variables = frozenset()  # the guard is blinded on purpose
    stacker.process_expression("99 :dup set")
    with pytest.raises(AssertionError, match="compiled `dup` as WORD"):
        run_block(stacker, block, "1 blk eval")


def test_a_list_literal_whose_template_failed_to_build_is_built_when_it_runs(at_once, monkeypatch):
    # the interpreter builds the template again at the token, and pushes the list when it can
    original = core._compile_list_template
    failing = {"on": False}

    def flaky(token):
        if failing["on"]:
            raise RecursionError("too deep for now")
        return original(token)

    monkeypatch.setattr(core, "_compile_list_template", flaky)
    stacker = Stacker()
    block = block_of(stacker, "{[1 2] len}")
    failing["on"] = True
    block.tokens.classification()  # classified while the template cannot be built
    failing["on"] = False
    assert run_block(stacker, block) == [2]
    assert block.tokens._unit.instructions[0].kind == compiler.BAD_LIST


@pytest.mark.parametrize(
    ("source", "before", "change", "after"),
    [
        pytest.param("{10 1 +}", [11], lambda t: t.extend(["2", "*"]), [22], id="extend"),
        pytest.param("{10 1 +}", [11], lambda t: t.__iadd__(["2", "*"]), [22], id="+="),
        pytest.param("{10 1 +}", [11], lambda t: t.__imul__(2), [11, 11], id="*="),
        pytest.param("{10 1 +}", [11], lambda t: t.__setitem__(0, "20"), [21], id="rewritten at the same length"),
        pytest.param("{3 1 2}", [3, 1, 2], lambda t: t.reverse(), [2, 1, 3], id="reverse"),
        pytest.param("{3 1 2}", [3, 1, 2], lambda t: t.sort(), [1, 2, 3], id="sort"),
    ],
)
def test_a_token_list_changed_in_place_is_not_run_by_its_old_unit(at_once, source, before, change, after):
    stacker = Stacker()
    block = block_of(stacker, source)
    assert run_block(stacker, block) == before
    change(block.tokens)
    assert (block.tokens._unit, block.tokens._runs) == (None, 0)  # the change itself forgets the unit
    assert run_block(stacker, block) == after  # as the interpreter reads the list now
    assert block.tokens._drops == 0 and len(block.tokens._unit.steps) == len(block.tokens)  # compiled anew


def test_one_change_during_a_recursion_counts_one_drop(at_once):
    stacker = Stacker()
    stacker.process_expression("{n} {n 0 == {{} {1} :g defun 0} {n 1 - f} ifelse} :f defun")
    body = stacker.sfunctions["f"]["func"].blockstack.tokens
    assert list(stacker.eval("4 f")) == [0]
    assert body._drops == 1  # the change on the way down is one change, whatever the depth


def test_the_same_block_under_two_loop_variables_follows_each(at_once):
    stacker = Stacker()
    block = block_of(stacker, "{dup}")
    assert run_block(stacker, block, "7 1 2 :i blk do") == [7, 7, 7]
    assert run_block(stacker, block, "7 1 2 :dup blk do") == [7, 1, 2]  # the loop variable hides the word
    assert run_block(stacker, block, "7 1 2 :i blk do") == [7, 7, 7]


def test_a_variable_made_in_the_scope_above_between_two_runs_hides_the_word_from_the_next_run(at_once):
    stacker = Stacker()
    block = block_of(stacker, "{dup}")
    assert run_block(stacker, block, "7 1 2 :i blk do") == [7, 7, 7]
    stacker.process_expression("99 :dup set")  # the loop scope is new each time; its parent changed shape
    assert run_block(stacker, block, "7 1 2 :i blk do") == [7, 99, 99]


def test_a_second_run_under_the_same_parent_does_not_walk_the_chain_again(at_once, monkeypatch):
    walks = []
    original = ScopedVariables.hides_any
    monkeypatch.setattr(ScopedVariables, "hides_any", lambda self, names: walks.append(1) or original(self, names))
    stacker = Stacker()
    block = block_of(stacker, "{dup}")
    run_block(stacker, block, "7 1 2 :i blk do")  # the first iteration walks the chain
    assert walks == [1]
    run_block(stacker, block, "7 1 2 :i blk do")  # the same parent, no new name anywhere: the head alone is looked at
    assert walks == [1]
    stacker.process_expression("1 :fresh set")  # a name somewhere: the chain is walked once more
    run_block(stacker, block, "7 1 2 :i blk do")
    assert walks == [1, 1]
