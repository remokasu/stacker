"""Integers of any size can be shown and written; code= treats an embedded value and its literal as the same code."""

import logging

import pytest

from stacker import Stacker
from stacker.runtime.exec_modes.script_mode import ScriptMode


def run(program: str) -> list[object]:
    stacker = Stacker()
    stacker.process_expression(program)
    return list(stacker.stack)


class TestBigIntegers:
    def test_can_be_turned_into_text_in_every_base(self):
        assert run("2000 ! str len 2000 ! hex len 2000 ! bin len 2000 ! oct len") == [5736, 4766, 19055, 6353]

    def test_can_be_printed_formatted_written_and_shown_as_code(self, capsys, tmp_path):
        run("2 15000 ^ echo")
        assert len(capsys.readouterr().out.strip()) == 4516
        assert run('"{}" 2 15000 ^ format len') == [4516]
        path = tmp_path / "big.txt"
        run(f'2 15000 ^ "{path}" write-to-file')
        assert len(path.read_text()) == 4516
        assert run("2 15000 ^ 1 subn code-text len") == [4518]

    def test_a_long_literal_reads_as_an_integer(self):
        digits = "1" * 5000
        assert run(f"{digits} 10 %") == [1]
        assert run(f'"{digits}" int 10 %') == [1]
        assert run(f"[{digits}] 0 at 10 %") == [1]

    def test_a_big_integer_left_at_the_end_of_a_script_is_only_a_warning(self, tmp_path, caplog):
        path = tmp_path / "big.stk"
        path.write_text("2000 !\n")
        with caplog.at_level(logging.WARNING, logger="stacker"):
            ScriptMode(Stacker()).run(str(path))
        assert any("1 value left on the stack" in r.getMessage() and "..." in r.getMessage() for r in caplog.records)


class TestCodeEqualityOfEmbeddedValues:
    @pytest.mark.parametrize(
        "program",
        [
            "{xs} {{xs len}} :mlen defmacro [1 2 3] {mlen} macroexpand {[1 2 3] len} code=",
            "{n} {{n 1 +}} :inc defmacro [] {inc} macroexpand {[] 1 +} code=",
            "{n} {{n 1 +}} :inc defmacro inf {inc} macroexpand {inf 1 +} code=",
            "[1 2] array 1 subn {[1 2]} code=",
            '[1 "a" [2]] 1 subn {[1 "a" [2]]} code=',
            "nan 1 subn {nan} code=",
            "{1 2 +} code-text parse eval {1 2 +} code=",
            "[1 2] array 1 subn [1 2] 1 subn code=",
            '[1 "a" [2]] 1 subn code-text parse eval [1 "a" [2]] 1 subn code=',
        ],
    )
    def test_an_embedded_value_equals_the_literal_that_reads_as_it(self, program):
        assert run(program) == [True]

    @pytest.mark.parametrize("program", ["[1 2 3] 1 subn {[1 2 4]} code=", "{1 2 3} {[1 2 3]} code=", '{"x"} {x} code=', "{1} {1.0} code=", "5 :x set {[x]} [5] 1 subn code="])
    def test_different_code_is_still_different(self, program):
        assert run(program) == [False]
