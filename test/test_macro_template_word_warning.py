"""A macro whose template replaces a built-in or prelude word with a bound variable is logged once."""

import logging

from stacker import Stacker
from stacker.engine.data_type import Symbol


def run(programs: list[str], caplog) -> tuple[list[object], list[str]]:
    stacker = Stacker()
    with caplog.at_level(logging.WARNING, logger="stacker"):
        for program in programs:
            stacker.process_expression(program)
    return list(stacker.stack), [r.getMessage() for r in caplog.records]


M5 = "{x} {x :len set {[1 2 3] len}} :m5 defmacro"
LEN_WARNING = "macro 'm5' replaces the built-in word 'len' in the code it generates (its body binds a variable 'len')"


class TestABoundNameThatIsAWord:
    def test_a_variable_the_body_sets_is_reported_with_the_macro_and_the_word(self, caplog):
        values, logged = run([M5, "9 m5"], caplog)
        assert values == [[1, 2, 3], 9]  # the generated code is `{[1 2 3] 9}`, as before
        assert logged == [LEN_WARNING]

    def test_once_however_often_the_macro_is_called(self, caplog):
        _, logged = run([M5, "9 m5", "8 m5", "{m5} macroexpand"], caplog)
        assert logged == [LEN_WARNING]

    def test_a_prelude_word_is_called_so(self, caplog):
        values, logged = run(["{x} {x :mean set {mean}} :m defmacro", "4 m"], caplog)
        assert values == [4]
        assert logged == ["macro 'm' replaces the prelude word 'mean' in the code it generates (its body binds a variable 'mean')"]

    def test_each_macro_is_reported_on_its_own(self, caplog):
        _, logged = run([M5, "{x} {x :len set {len}} :m defmacro", "9 m5", "3 m", "9 m5"], caplog)
        assert logged == [
            LEN_WARNING,
            "macro 'm' replaces the built-in word 'len' in the code it generates (its body binds a variable 'len')",
        ]

    def test_at_any_depth_of_the_template(self, caplog):
        _, logged = run([M5.replace("{[1 2 3] len}", "{{[1 2 3] len} eval}"), "9 m5"], caplog)
        assert logged == [LEN_WARNING]


class TestNothingIsLogged:
    def test_for_a_parameter_whatever_its_name(self, caplog):
        # Replacing a parameter is what a template is for: `unless` takes `cond`, `inc` takes `sum`
        values, logged = run([
            "{cond body} { {cond eval not {body eval} if} } :unless defmacro",
            "{sum} {{sum 1 +}} :inc defmacro",
            '-3 {0 >} {"neg" echo} unless',
            "2 inc",
        ], caplog)
        assert values == [3]
        assert logged == []

    def test_for_a_word_of_the_programs_own(self, caplog):
        values, logged = run(["{a} {a 1 +} :g defun", "{f} {{3 f}} :call defmacro", ":g call"], caplog)
        assert values == [4]
        assert logged == []

    def test_for_a_word_the_body_does_not_bind(self, caplog):
        values, logged = run(["{x} {{[1 2 3] len x +}} :m defmacro", "1 m"], caplog)
        assert values == [4]
        assert logged == []

    def test_for_the_symbol_form(self, caplog):
        values, logged = run(["{x} {x :len set {:len}} :m defmacro", ":k m"], caplog)
        assert values == [Symbol("k")]
        assert logged == []

    def test_for_a_name_inside_a_string_literal(self, caplog):
        values, logged = run(['{x} {x :len set {"len"}} :m defmacro', "9 m"], caplog)
        assert values == ["len"]
        assert logged == []

    def test_for_the_prelude_itself(self, caplog):
        _, logged = run(["{2 *} {double} alias", "3 double"], caplog)
        assert logged == []
