"""`defmacro` defines a Lisp-style macro: `{args} {body} name defmacro`.

The body runs at expansion time on its own stack and must leave exactly one
value; a code block is then evaluated on the caller's stack, anything else is
pushed as-is.
"""

import pytest

from stacker.engine import recursion
from stacker.engine.data_type import String
from stacker.engine.slambda import StackerLambda
from stacker.error import (
    MacroExpansionError,
    NoValueProducedError,
    StackerRecursionError,
    StackerSyntaxError,
    StackUnderflowError,
    UndefinedSymbolError,
)
from stacker.stacker import Stacker


def run(*expressions: str) -> list[object]:
    stacker = Stacker()
    result = None
    for expression in expressions:
        result = stacker.eval(expression, stack=stacker.stack)
    return list(result)


class TestExpansionResult:
    def test_block_result_is_evaluated_on_caller_stack(self):
        assert run("{} {{2 *}} double defmacro", "5 double") == [10]

    def test_non_block_result_is_pushed(self):
        assert run("{} {42} answer defmacro", "answer") == [42]

    def test_zero_values_is_an_error(self):
        with pytest.raises(NoValueProducedError, match="m"):
            run("{} {} m defmacro", "m")

    def test_two_values_is_an_error(self):
        with pytest.raises(MacroExpansionError, match="2"):
            run("{} {1 2} m defmacro", "m")

    def test_expansion_happens_on_every_call(self):
        assert run("{} {{2 *}} double defmacro", "3 double 4 double") == [6, 8]


class TestArguments:
    def test_arguments_are_received_unevaluated(self):
        # The argument block is never evaluated at expansion time.
        assert run("{c} {{c eval c eval +}} twice defmacro", "{1 2 +} twice") == [6]

    def test_arguments_bound_in_expansion_scope_are_readable_in_body(self):
        # `e len` runs at expansion time on the argument block itself.
        assert run("{e} { e len k = {k} } m defmacro", "{a b c} m") == [3]

    def test_missing_arguments_underflow_names_the_macro(self):
        with pytest.raises(StackUnderflowError, match="m"):
            run("{a b} {{a b}} m defmacro", "1 m")

    def test_kernel_word_argument_names_are_allowed(self):
        assert [str(b) for b in run("{dup} { {dup dup} } m defmacro", "{7} m")] == [
            "{7}",
            "{7}",
        ]

    def test_regular_operator_argument_name_is_interpolated(self):
        assert [str(b) for b in run("{+} { {+ +} } m defmacro", "{7} m")] == [
            "{7}",
            "{7}",
        ]

    def test_undefined_bare_name_argument_is_an_error(self):
        # `foo` is referenced before the macro sees it; pass the name as `$foo` or `{foo}`.
        with pytest.raises(UndefinedSymbolError):
            run("{v} {{v}} m defmacro", "foo m")
        assert [str(b) for b in run("{v} {{v}} m defmacro", "{foo} m")] == ["{foo}"]


class TestDefinitionValidation:
    def test_two_term_form_is_rejected_with_migration_hint(self):
        with pytest.raises(StackerSyntaxError, match="alias"):
            run("{2 *} double defmacro")

    def test_non_block_body_is_a_syntax_error(self):
        with pytest.raises(StackerSyntaxError):
            run("{} 5 five defmacro")

    def test_non_block_args_is_a_syntax_error(self):
        with pytest.raises(StackerSyntaxError):
            run("5 {1} m defmacro")

    def test_duplicate_argument_names_are_rejected(self):
        with pytest.raises(StackerSyntaxError):
            run("{x x} {{x}} m defmacro")

    def test_symbol_argument_name_is_rejected(self):
        with pytest.raises(StackerSyntaxError):
            run("{$x} {{x}} m defmacro")


class TestRedefinition:
    def test_bare_name_redefinition(self):
        assert run("{} {{1}} m defmacro", "{} {{2}} m defmacro", "m") == [2]

    def test_quoted_name_forms(self):
        assert run("{} {{1}} $m defmacro", "{} {{2}} {m} defmacro", "m") == [2]

    def test_redefinition_inside_loop_takes_effect_next_call(self):
        expression = "0 s = 1 3 i {s m + s = {} {{2}} m defmacro} do s"
        assert run("{} {{1}} m defmacro", expression) == [5]


@pytest.fixture
def small_recursion_limit():
    # The test process has no sys.setrecursionlimit backstop (that is set up
    # in __main__), so keep the Stacker-level limit well below Python's.
    original = recursion.get_limit()
    recursion.set_limit(5)
    yield
    recursion.set_limit(original)


@pytest.mark.usefixtures("small_recursion_limit")
class TestRecursionGuard:
    def test_self_recursive_macro_hits_the_guard(self):
        with pytest.raises(StackerRecursionError) as info:
            run("{} {{r}} r defmacro", "r")
        assert info.value.name == "r"
        assert "macro" in str(info.value)

    def test_mutual_recursion_between_function_and_macro(self):
        with pytest.raises(StackerRecursionError):
            run("{} {{f}} m defmacro", "{} {m} f defun", "f")


class TestErrorContext:
    def test_error_while_expanding_names_the_macro(self):
        with pytest.raises(StackUnderflowError, match="while expanding macro 'm'"):
            run("{} {1 + {1}} m defmacro", "m")

    def test_error_in_generated_code_names_the_macro(self):
        with pytest.raises(StackUnderflowError, match="in code generated by macro 'm'"):
            run("{} {{1 +}} m defmacro", "m")

    def test_innermost_macro_wins(self):
        with pytest.raises(StackUnderflowError) as info:
            run("{} {{1 +}} inner defmacro", "{} {{inner}} outer defmacro", "outer")
        assert str(info.value).count("macro") == 1
        assert "inner" in str(info.value)


class TestAcceptance:
    WHILE = "{c b} {{{c eval not {break} if b eval} loop}} {while} defmacro"

    def test_while_written_as_a_macro_matches_the_builtin(self):
        macro = run(self.WHILE, "0 i = {i 1000 <} {i 1 + i =} while i")
        builtin = run("0 i = {i 1000 <} {i 1 + i =} while i")
        assert macro == builtin == [1000]

    def test_while_macro_survives_100k_iterations(self):
        assert run(self.WHILE, "0 i = {i 100000 <} {i 1 + i =} while i") == [100000]

    def test_double_bang_with_gensym(self):
        define = "{x} { gensym t = { x eval t set  t t + } } {double!} defmacro"
        assert run(define, "{3 4 +} double!") == [14]

    def test_alias_can_be_written_as_a_macro(self):
        alias = "{body name} { {{} {body} name defmacro} } {alias} defmacro"
        assert run(alias, "{2 *} {double} alias", "5 double") == [10]


class TestNonBlockExpansionResults:
    def test_string_result_is_pushed_as_string(self):
        (value,) = run('{} {"hi"} m defmacro', "m")
        assert isinstance(value, String)
        assert value == "hi"

    def test_list_result_is_pushed(self):
        assert run("{} {[1 2]} m defmacro", "m") == [[1, 2]]

    def test_lambda_result_is_pushed_not_called(self):
        (value,) = run("{} {{x} {x 1 +} lambda} m defmacro", "m")
        assert isinstance(value, StackerLambda)


class TestMacroexpandErrors:
    def test_missing_arguments_underflow_names_the_macro(self):
        with pytest.raises(StackUnderflowError, match="m"):
            run("{a b} {{a b}} m defmacro", "1 {m} macroexpand")


class TestArgumentBlockKinds:
    def test_empty_block_argument_is_inserted_as_empty_block(self):
        (block,) = run("{c} {{c}} m defmacro", "{} {m} macroexpand")
        assert [type(t).__name__ for t in block.tokens] == ["Stacker"]
        assert list(block.tokens[0].tokens) == []

    def test_empty_block_argument_evaluates_to_empty_block(self):
        (block,) = run("{c} {{c}} m defmacro", "{} m")
        assert list(block.tokens) == []

    def test_round_bracket_block_argument_keeps_its_bracket_type(self):
        (block,) = run("{c} {{c}} m defmacro", "(1 2) m")
        assert block.bracket_type == "("

    def test_macro_call_inside_argument_block_runs_when_the_block_is_evaluated(self):
        assert run("{c} {{c eval}} id defmacro", "{{5} id} id") == [5]

    def test_caller_variable_in_argument_block_resolves_in_caller_scope(self):
        assert run("{c} {{c}} m defmacro", "3 y =", "{y} m dup +") == [6]

    def test_macroexpand_result_can_be_passed_as_a_macro_argument(self):
        define = ("{x} {{x}} ident defmacro", "{c} {{c eval eval}} twice defmacro")
        # `{3} {ident} macroexpand` leaves `{{3}}`; `twice` unwraps both layers.
        assert run(*define, "{3} {ident} macroexpand twice") == [3]


class TestNestedMacroCalls:
    def test_macro_may_call_itself_in_generated_code_a_finite_number_of_times(self):
        define = "{} {{ 1 cnt + cnt = lvl 1 - lvl = lvl 0 > {m} if }} m defmacro"
        assert run(define, "3 lvl = 0 cnt = m cnt") == [3]

    def test_nested_macro_expansion_scopes_are_independent(self):
        # If the inner `t =` leaked into the outer scope the result would be 4.
        assert run(
            "{} { 2 t = {t} } inner defmacro",
            "{} { 1 t = inner t + } outer defmacro",
            "outer",
        ) == [3]


class TestDefinitionValidationOfArguments:
    @pytest.mark.parametrize(
        "args",
        ["{x 1}", "{x {y}}", "{x 1.5}"],
        ids=["number", "nested-block", "float"],
    )
    def test_non_name_argument_tokens_are_rejected(self, args):
        with pytest.raises(StackerSyntaxError):
            run(f"{args} {{{{x}}}} m defmacro")

    def test_string_literal_argument_token_is_rejected(self):
        with pytest.raises(StackerSyntaxError):
            run('{x "s"} {{x}} m defmacro')

    def test_two_token_block_as_macro_name_is_rejected(self):
        with pytest.raises(StackerSyntaxError):
            run("{x} {{x}} {a b} defmacro")

    @pytest.mark.parametrize("name", ["$m", "{m}", "m"], ids=["dollar", "block", "bare"])
    def test_every_name_form_defines_the_same_macro(self, name):
        assert [str(b) for b in run(f"{{x}} {{{{x x}}}} {name} defmacro", "{7} {m} macroexpand")] == [
            "{{7} {7}}"
        ]
