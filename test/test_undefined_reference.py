"""A reference to an undefined bare name is an error where it is written.

Until 1.16.0 an undefined name was pushed as a value and only failed later.
The name itself is written `:name` or `{name}`.
"""

import pytest

from stacker import Stacker
from stacker.engine.core import StackerCore
from stacker.engine.data_type import Symbol
from stacker.error import UndefinedSymbolError
from stacker.runtime.exec_modes.repl_mode import ReplMode
from stacker.runtime.exec_modes.script_mode import ScriptMode


def run(*lines: str) -> list[object]:
    stacker = Stacker()
    for line in lines:
        stacker.process_expression(line)
    return list(stacker.stack)


class TestReferences:
    def test_bare_name(self):
        with pytest.raises(UndefinedSymbolError) as info:
            run("foo")
        assert "`foo` is not defined" in str(info.value)

    def test_error_at_the_reference_not_the_consumer(self, capsys):
        with pytest.raises(UndefinedSymbolError):
            run("1 echo foo +")
        assert capsys.readouterr().out.strip() == "1"

    def test_stack_keeps_what_came_before(self):
        stacker = Stacker()
        with pytest.raises(UndefinedSymbolError):
            stacker.process_expression("3 foo +")
        assert list(stacker.stack) == [3]

    def test_inside_a_block_when_evaluated(self):
        (block,) = run("{foo}")
        assert isinstance(block, StackerCore)
        with pytest.raises(UndefinedSymbolError):
            run("{foo} eval")

    @pytest.mark.parametrize("program", [":foo eval", '"foo" read-from-string eval', "{foo} 0 nth eval"])
    def test_evaluating_an_undefined_name(self, program):
        with pytest.raises(UndefinedSymbolError):
            run(program)

    def test_list_literal_and_macro_argument(self):
        with pytest.raises(UndefinedSymbolError):
            run("[a b]")
        with pytest.raises(UndefinedSymbolError):
            run("{v} {{v}} m defmacro", "foo m")

    def test_alias_needs_a_quoted_name(self):
        with pytest.raises(UndefinedSymbolError):
            run("{2 *} double alias")
        assert run("{2 *} {double} alias", "4 double") == [8]
        assert run("{2 *} :double alias", "4 double") == [8]


class TestNamesThemselves:
    def test_symbol_and_quoted_name_are_fine(self):
        assert run(":foo") == [Symbol("foo")]
        assert str(run("{foo}")[0]) == "{foo}"

    def test_name_positions_are_not_references(self):
        assert run("5 foo set foo") == [5]
        assert run("0 1 3 i {i +} do") == [6]
        assert run("{a} {a} f defun") == []


class TestHints:
    @pytest.mark.parametrize("mode_class", [ReplMode, ScriptMode])
    def test_undefined_name_hint_shows_how_to_write_the_name(self, mode_class):
        hint = mode_class._get_error_hint(None, UndefinedSymbolError("foo"))
        assert hint == "To use the name itself, write `:foo` or `{foo}`"
