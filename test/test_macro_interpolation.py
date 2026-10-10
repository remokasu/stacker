"""Parameter interpolation: names bound in the expansion scope are substituted
into the body's block literals at the moment each literal is pushed."""

import pytest

from stacker.error import UndefinedSymbolError
from stacker.stacker import Stacker


def run(*expressions: str) -> list[object]:
    stacker = Stacker()
    result = None
    for expression in expressions:
        result = stacker.eval(expression, stack=stacker.stack)
    return list(result)


def shape(value: object) -> object:
    """Token structure of a block (nested blocks become nested lists)."""
    if hasattr(value, "tokens") and hasattr(value, "bracket_type"):
        return [shape(token) for token in value.tokens]
    return value


def expansion(*expressions: str) -> object:
    """Return the token structure of the last expression's single result."""
    (block,) = run(*expressions)
    return shape(block)


@pytest.mark.parametrize(
    ("definition", "call", "expected"),
    [
        ("{c} { {c c} } m defmacro", "{1 2 +} {m} macroexpand", [[1, 2, "+"], [1, 2, "+"]]),
        ("{c} { {{{c}}} } m defmacro", "{9} {m} macroexpand", [[[[9]]]]),
        # Values already substituted are not walked again.
        ("{a b} { {a b} } m defmacro", "{b} {9} {m} macroexpand", [["b"], [9]]),
        # `$name`, string literals and list literals are left alone.
        ("{c} { {$c \"c\" [c]} } m defmacro", "5 {m} macroexpand", ["$c", "c", "[c]"]),
        # A variable bound during expansion is interpolated too.
        ("{} { 5 k = {k k +} } m defmacro", "{m} macroexpand", [5, 5, "+"]),
        # Only names bound at push time are substituted.
        ("{} { {k} 5 k = } m defmacro", "{m} macroexpand", ["k"]),
        # `$x` stays as the symbol while the bare `x` next to it is replaced.
        ("{x} { {$x x} } m defmacro", "5 {m} macroexpand", ["$x", 5]),
        # Only the bound name is replaced at every depth; `z` is unbound.
        ("{a} { {{{a z}}} } m defmacro", "9 {m} macroexpand", [[[9, "z"]]]),
        # An empty block argument is inserted as an empty block.
        ("{c} { {c} } m defmacro", "{} {m} macroexpand", [[]]),
    ],
)
def test_interpolation_rules(definition, call, expected):
    assert expansion(definition, call) == expected


def test_caller_scope_names_are_not_interpolated():
    # `y` is bound in the caller, not in the expansion scope.
    assert expansion("7 y =", "{} { {y} } m defmacro", "{m} macroexpand") == ["y"]
    assert run("7 y =", "{} { {y} } m defmacro", "m") == [7]


def test_body_level_names_are_variable_references_not_interpolation():
    # `k` outside a block literal is an ordinary variable read at expansion time.
    assert run("{} { 5 k = k 1 + j = {j} } m defmacro", "m") == [6]


def test_runtime_generated_blocks_are_not_interpolated():
    built = expansion('{c} { "c 1 +" read-from-string } m defmacro', "5 {m} macroexpand")
    assert built == ["c", 1, "+"]


def test_defined_body_is_not_mutated_by_expansion():
    assert run("{c} { {c} } m defmacro", "1 m 2 m") == [1, 2]


class TestValueKinds:
    def test_block_is_inserted_as_block(self):
        assert run("{v} {{v}} m defmacro", "{1 2 +} m dup +") == [6]

    def test_string_is_inserted_as_string_literal(self):
        assert run("{v} {{v}} m defmacro", '"hi" m') == ["hi"]

    def test_symbol_value_is_inserted_as_bare_name(self):
        # The expansion is `{foo}`, so evaluating it references `foo`.
        with pytest.raises(UndefinedSymbolError):
            run("{v} {{v}} m defmacro", "$foo m")
        assert run("{v} {{v 1 +}} m defmacro", "3 foo =", "$foo m") == [4]

    def test_symbol_value_resolves_as_variable_in_generated_code(self):
        assert run("3 foo =", "{v} {{v}} m defmacro", "$foo m") == [3]

    def test_number_and_list_are_inserted_as_values(self):
        assert run("{v} {{v}} m defmacro", "3 m [1 2] m") == [3, [1, 2]]


class TestExpansionScope:
    def test_assignment_in_body_does_not_touch_caller_variable(self):
        assert run("1 t =", "{} { 9 t = {t} } m defmacro", "m t") == [9, 1]

    def test_body_can_read_caller_variables(self):
        assert run("4 t =", "{} { t 1 + k = {k} } m defmacro", "m") == [5]

    def test_global_in_body_still_writes_global(self):
        assert run("{} { 9 t global {t} } m defmacro", "m t") == [9, 9]

    def test_assignment_inside_do_in_body_never_reaches_the_caller(self):
        # The write barrier stops `update_existing` at the expansion scope, so
        # the loop's `t =` binds in the loop scope and the caller's `t` is intact.
        assert run("1 t =", "{} { 1 2 i { i t = } do {t} } m defmacro", "m t") == [1, 1]


def test_name_set_in_body_is_not_visible_to_the_caller_after_expansion():
    assert run("{} { 7 q = {q} } m defmacro", "m") == [7]
    with pytest.raises(UndefinedSymbolError):
        run("{} { 7 q = {q} } m defmacro", "m q")


def test_expansion_scope_is_discarded_so_later_calls_start_fresh():
    # The first call binds `q`; the second sees no leftover binding and
    # interpolates its own value.
    assert run("{v} { v q = {q} } m defmacro", "1 m 2 m") == [1, 2]
