"""A bare name is a reference wherever it stands; a name is written `:name`.

Earlier versions read a bare name right before `set`, `=`, `global`,
`defun`, `defmacro` or `macroexpand`, the loop variable of `do` / `dolist`
and the two names before the block of `reduce` / `fold` as the name being
bound, by looking at the tokens after it. That lookahead is gone: tokens
are read one at a time, left to right, and a bare name always pushes what
it refers to.
"""

import pytest

from stacker.engine.core import K_SYMBOL, _classify_tokens
from stacker.engine.data_type import Symbol
from stacker.error import StackerSyntaxError, UndefinedSymbolError
from stacker.stacker import Stacker


def run(*expressions: str) -> list[object]:
    stacker = Stacker()
    result = None
    for expression in expressions:
        result = stacker.eval(expression, stack=stacker.stack)
    return list(result)


BINDING_WORDS = ["set", "=", "global", "defun", "defmacro", "macroexpand"]


@pytest.mark.parametrize(
    "expression",
    [
        "3 x set",
        "3 x =",
        "3 x global",
        "{a} {a} f defun",
        "{} {{1}} m defmacro",
        "m macroexpand",
        "1 3 i {i} do",
        "[1 2] x {x} dolist",
        "[1 2 3] 0 acc x {acc x +} reduce",
        "[1 2 3] 0 :acc x {acc x +} fold",
    ],
)
def test_an_undefined_bare_name_is_an_error_at_its_own_position(expression):
    with pytest.raises(UndefinedSymbolError):
        run(expression)


def test_the_error_names_the_bare_name():
    # The REPL and scripts add the hint "To use the name itself, write `:x` or `{x}`"
    with pytest.raises(UndefinedSymbolError, match="`x` is not defined"):
        run("3 x set")


def test_what_comes_before_the_bare_name_has_already_run(capsys):
    # Left to right: `1 echo` runs, then `x` fails; nothing waits for `set`.
    with pytest.raises(UndefinedSymbolError):
        run("1 echo 3 x set")
    assert capsys.readouterr().out == "1\n"


@pytest.mark.parametrize("name", [":x", "{x}", "{:x}"], ids=["symbol", "block", "quoted-symbol"])
class TestANameIsWrittenAsASymbol:
    def test_set(self, name):
        assert run(f"3 {name} set x") == [3]

    def test_assign(self, name):
        assert run(f"3 {name} = x") == [3]

    def test_global(self, name):
        assert run(f"3 {name} global x") == [3]

    def test_defun(self, name):
        assert run(f"{{a}} {{a 1 +}} {name} defun 1 x") == [2]

    def test_defmacro_and_macroexpand(self, name):
        (block,) = run(f"{{}} {{{{1}}}} {name} defmacro", f"{name} macroexpand")
        assert list(block.tokens) == [1]

    def test_do(self, name):
        assert run(f"0 1 3 {name} {{x +}} do") == [6]

    def test_dolist(self, name):
        assert run(f"0 [1 2 3] {name} {{x +}} dolist") == [6]

    def test_reduce_and_fold(self, name):
        assert run(f"[1 2 3] 0 :acc {name} {{acc x +}} reduce") == [6]
        assert run(f"[1 2 3] 0 {name} :y {{x y +}} fold") == [6]


def test_a_bound_bare_name_before_a_binding_word_is_its_value():
    # `x` holds 5, so `x` pushes 5 and `set` is handed a number, not a name
    with pytest.raises(StackerSyntaxError, match="`set` expects a name, got 5"):
        run("5 :x set 7 x set")


def test_the_error_for_a_value_explains_how_to_write_a_name():
    with pytest.raises(StackerSyntaxError) as info:
        run("7 5 set")
    assert "A bare name pushes what it refers to" in str(info.value)
    assert "`:name` or `{name}`" in str(info.value)


class TestIndirectBinding:
    """A bare name that holds a name binds that name: `set` sees the symbol."""

    def test_through_a_symbol(self):
        assert run(":y :x set 7 x set y") == [7]

    def test_through_a_quoted_name(self):
        assert run("{y} :x set 7 x set y") == [7]

    def test_the_variable_that_held_the_name_is_untouched(self):
        assert run(":y :x set 7 x set x") == [Symbol("y")]


class TestNoWordIsProtectedAnyMore:
    """A built-in word before a binding word simply runs, as every bare name does."""

    def test_a_built_in_word_runs(self):
        # `dup` runs on 3, then `set` is handed the number
        with pytest.raises(StackerSyntaxError, match="`set` expects a name, got 3"):
            run("3 dup set")

    def test_a_built_in_word_is_bound_through_its_symbol(self):
        assert run("3 :dup set dup") == [3]
        assert run("4 {dup} = dup") == [4]

    def test_a_loop_variable_named_like_a_built_in_word(self):
        assert run("0 1 3 :dup {dup +} do") == [6]

    def test_a_loop_variable_named_like_a_constant(self):
        assert run("0 1 3 :e {e +} do") == [6]

    def test_a_registered_operator_is_not_special_either(self):
        stacker = Stacker()
        stacker.register_operator("abs", lambda a: 42, 1, True, "replaced abs")
        with pytest.raises(StackerSyntaxError, match="got 42"):
            stacker.eval("3 abs set")
        assert list(stacker.eval("3 :abs set abs")) == [3]


class TestOneTokenAtATime:
    """Reading a token never depends on the tokens after it."""

    def test_classification_of_a_token_is_the_same_alone_and_in_a_sequence(self):
        tokens = ["3", "x", "set", "1", "3", "i", "{i}", "do", ":s", "[1 2]", '"s"', "{a}"]
        together = _classify_tokens(tokens)
        alone = [_classify_tokens([token])[0] for token in tokens]
        assert together == alone

    def test_only_the_symbol_form_is_classified_as_a_symbol(self):
        kinds = {token: kind for (kind, token, _) in _classify_tokens(["x", "set", ":x"])}
        assert kinds[":x"] == K_SYMBOL
        assert kinds["x"] != K_SYMBOL

    def test_code_means_the_same_split_or_joined(self):
        # Concatenating two blocks and evaluating them one after the other agree
        joined = run("{4 :x} {set} concat-block eval x")
        split = run("{4 :x} eval {set} eval x")
        assert joined == split == [4]

    def test_a_bare_name_means_the_same_split_or_joined(self):
        # A lookahead used to make `{4 x} {set} concat-block eval` bind x while
        # `{4 x} eval {set} eval` failed: the same code, split, meant something else
        with pytest.raises(UndefinedSymbolError):
            run("{4 x} {set} concat-block eval")
        with pytest.raises(UndefinedSymbolError):
            run("{4 x} eval {set} eval")
        joined = run(":z :x set {4 x} {set} concat-block eval z")
        split = run(":z :x set {4 x} eval {set} eval z")
        assert joined == split == [4]

    @pytest.mark.parametrize("word", BINDING_WORDS + ["do"])
    def test_a_string_reading_like_a_binding_word_is_a_string(self, word):
        assert run("5 :x set", f'{{x "{word}"}} eval') == [5, word]
