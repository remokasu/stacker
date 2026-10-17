"""`include` runs a file here, in the including interpreter; `require` runs it once."""

from pathlib import Path

import pytest

from stacker import Stacker
from stacker.error import (
    IncludeError,
    NoValueProducedError,
    StackerRuntimeError,
    StackerSyntaxError,
    StackerTypeError,
    UndefinedSymbolError,
)


def run(stacker: Stacker, *lines: str) -> list[object]:
    for line in lines:
        stacker.process_expression(line)
    return list(stacker.stack)


def write(tmp_path: Path, name: str, text: str) -> Path:
    path = tmp_path / name
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")
    return path


@pytest.fixture
def counter(tmp_path: Path) -> Path:
    return write(
        tmp_path,
        "counter.stk",
        "0 :counter set\n{} {counter 1 + :counter set counter} :tick defun\n{} {counter} :peek defun\n",
    )


class TestIncludeRunsInPlace:
    def test_the_file_and_the_includer_share_one_variable(self, counter: Path):
        stacker = Stacker()
        assert run(stacker, f'"{counter}" include', "tick drop tick drop tick drop", "peek counter") == [3, 3]
        assert run(stacker, "clear 100 :counter set peek") == [100]

    def test_including_again_runs_the_file_again(self, counter: Path):
        stacker = Stacker()
        run(stacker, f'"{counter}" include', "tick drop")
        assert run(stacker, f'"{counter}" include', "peek") == [0]

    def test_a_diamond_shares_one_state(self, tmp_path: Path):
        write(tmp_path, "libB.stk", "0 :bstate set\n{} {bstate 1 + :bstate set bstate} :g defun\n")
        write(tmp_path, "libA.stk", '"libB.stk" require\n{} {g 10 *} :f defun\n')
        main = write(tmp_path, "main.stk", '"libA.stk" require\n"libB.stk" require\n')
        stacker = Stacker()
        assert run(stacker, f'"{main}" include') == []
        assert run(stacker, "f f g") == [10, 20, 3]

    def test_the_files_functions_can_call_the_includers_functions(self, tmp_path: Path):
        lib = write(tmp_path, "lib.stk", "{} {g 10 *} :f defun\n")
        stacker = Stacker()
        assert run(stacker, "{} {4} :g defun", f'"{lib}" include', "f") == [40]

    def test_the_file_sees_the_includers_variables_and_plugins(self, tmp_path: Path):
        lib = write(tmp_path, "lib.stk", "base 1 + :base set base twice :t set\n")
        stacker = Stacker()
        stacker.register_plugin("twice", lambda x: x * 2, 1)
        assert run(stacker, "5 :base set", f'"{lib}" include', "base t") == [6, 12]

    def test_names_are_shared_with_the_includer(self, tmp_path: Path):
        lib = write(tmp_path, "lib.stk", "{} {5 :tmp set} :f defun\n0 :i set\n")
        stacker = Stacker()
        assert run(stacker, "1 :tmp set 9 :i set", f'"{lib}" include', "f tmp i") == [5, 0]

    def test_the_file_starts_with_an_empty_stack_and_leaves_nothing(self, tmp_path: Path):
        lib = write(tmp_path, "lib.stk", "42\n")
        plus = write(tmp_path, "plus.stk", "+\n")
        stacker = Stacker()
        assert run(stacker, "1 2", f'"{lib}" include', "depth") == [1, 2, 2]
        with pytest.raises(Exception, match="requires"):
            run(Stacker(), "1 2", f'"{plus}" include')

    def test_inside_a_function_variables_are_local_and_functions_global(self, counter: Path):
        stacker = Stacker()
        assert run(stacker, f'{{}} {{"{counter}" include counter}} :c defun c c') == [0, 0]
        with pytest.raises(UndefinedSymbolError):
            run(stacker, "counter")
        assert run(stacker, "clear peek") == [0]

    def test_inside_a_loop_a_variable_the_file_first_sets_stays(self, tmp_path: Path):
        lib = write(tmp_path, "lib.stk", "7 :fromfile set\n")
        stacker = Stacker()
        assert run(stacker, f'1 2 :i {{"{lib}" include}} do fromfile') == [7]

    def test_a_break_in_the_file_leaves_the_loop_running_the_include(self, tmp_path: Path):
        lib = write(tmp_path, "lib.stk", "break\n")
        stacker = Stacker()
        assert run(stacker, f'1 5 :i {{i "{lib}" include}} do') == [1]

    def test_a_break_outside_a_loop_is_an_error(self, tmp_path: Path):
        lib = write(tmp_path, "lib.stk", "break\n")
        with pytest.raises(StackerSyntaxError, match="break"):
            run(Stacker(), f'"{lib}" include')
        with pytest.raises(StackerSyntaxError, match="break"):
            Stacker().include(str(lib))

    def test_definitions_before_an_error_stay(self, tmp_path: Path):
        lib = write(tmp_path, "lib.stk", "1 :a set\n2 :b set\n1 0 /\n")
        stacker = Stacker()
        assert run(stacker, f'{{"{lib}" include}} {{"failed"}} iferror', "a b") == ["failed", 1, 2]

    def test_a_redefined_prelude_word_is_used_by_the_file(self, tmp_path: Path):
        lib = write(tmp_path, "lib.stk", "[2 4] mean :r set\n")
        stacker = Stacker()
        assert run(stacker, "{xs} {0} :mean defun", f'"{lib}" include', "r") == [0]

    def test_ans_cannot_be_used_inside_the_file_and_is_not_changed(self, tmp_path: Path):
        lib = write(tmp_path, "lib.stk", "ans\n")
        stacker = Stacker()
        stacker.eval("7")
        with pytest.raises(StackerRuntimeError, match="cannot be used in a file"):
            stacker.eval(f'"{lib}" include')
        assert list(stacker.eval("ans")) == [7]

    def test_a_trailing_row_separator_means_the_same_as_in_a_script(self, tmp_path: Path):
        lib = write(tmp_path, "lib.stk", "[1 2 3;]\n:m set\n")
        stacker = Stacker()
        assert run(stacker, f'"{lib}" include', "m") == [[1, 2, 3]]

    def test_two_interpreters_do_not_share_the_include_stack(self, tmp_path: Path):
        lib = write(tmp_path, "lib.stk", "1 :x set\n")
        first, second = Stacker(), Stacker()
        assert run(first, f'"{lib}" include', "x") == [1]
        assert run(second, f'"{lib}" include', "x") == [1]


class TestCircular:
    def test_a_script_that_includes_itself_fails_at_once(self, tmp_path: Path):
        main = write(tmp_path, "main.stk", f'"x" echo\n"{tmp_path / "main.stk"}" include\n')
        import contextlib
        import io

        from stacker.runtime.exec_modes import ScriptMode
        out = io.StringIO()
        with contextlib.redirect_stdout(out), pytest.raises(SystemExit):
            ScriptMode(Stacker()).run(str(main))
        assert out.getvalue() == "x\n"

    def test_mutual_require_is_circular(self, tmp_path: Path):
        write(tmp_path, "a.stk", '"b.stk" require\n')
        write(tmp_path, "b.stk", '"a.stk" require\n')
        with pytest.raises(IncludeError, match="Circular"):
            run(Stacker(), f'"{tmp_path / "a.stk"}" require')


class TestRequire:
    def test_a_second_require_does_nothing(self, counter: Path):
        stacker = Stacker()
        assert run(stacker, f'"{counter}" require', "tick drop", f'"{counter}" require', "peek") == [1]

    def test_the_same_file_written_differently_is_read_once(self, tmp_path: Path, monkeypatch):
        write(tmp_path, "lib.stk", "n 1 + :n set\n")
        monkeypatch.chdir(tmp_path)
        stacker = Stacker()
        run(stacker, "0 :n set", '"lib.stk" require', '"./lib.stk" require', f'"{tmp_path / "lib.stk"}" require')
        link = tmp_path / "link.stk"
        link.symlink_to(tmp_path / "lib.stk")
        assert run(stacker, '"link.stk" require', "n") == [1]

    def test_another_interpreter_reads_it_again(self, counter: Path):
        assert run(Stacker(), f'"{counter}" require', "peek") == [0]
        assert run(Stacker(), f'"{counter}" require', "peek") == [0]

    def test_include_then_require_does_nothing_and_require_then_include_runs(self, counter: Path):
        stacker = Stacker()
        assert run(stacker, f'"{counter}" include', "tick drop", f'"{counter}" require', "peek") == [1]
        assert run(stacker, "clear", f'"{counter}" include', "peek") == [0]

    def test_a_file_that_failed_is_not_recorded(self, tmp_path: Path):
        lib = write(tmp_path, "lib.stk", "1 :a set\n1 0 /\n")
        stacker = Stacker()
        run(stacker, f'{{"{lib}" require}} {{"failed"}} iferror drop')
        lib.write_text("2 :a set\n", encoding="utf-8")
        assert run(stacker, f'"{lib}" require', "a") == [2]

    def test_require_binds_in_the_root_scope_wherever_it_is_written(self, counter: Path):
        stacker = Stacker()
        assert run(stacker, f'{{}} {{"{counter}" require counter}} :c defun c c') == [0, 0]
        assert run(stacker, "clear counter") == [0]

    def test_a_deleted_file_already_read_is_not_an_error(self, counter: Path):
        stacker = Stacker()
        run(stacker, f'"{counter}" require')
        counter.unlink()
        assert run(stacker, f'"{counter}" require', "peek") == [0]

    @pytest.mark.parametrize("program", ["5 require", ":lib require"])
    def test_the_argument_must_be_a_string(self, program):
        with pytest.raises(StackerTypeError, match="`require`"):
            run(Stacker(), program)

    def test_a_missing_file_is_an_error(self, tmp_path: Path):
        with pytest.raises(IncludeError, match="not found"):
            run(Stacker(), f'"{tmp_path / "nope.stk"}" require')

    def test_the_python_api(self, counter: Path):
        stacker = Stacker()
        stacker.require(str(counter))
        stacker.process_expression("tick drop")
        stacker.require(str(counter))
        assert run(stacker, "peek") == [1]
        stacker.include(str(counter))
        assert run(stacker, "clear peek") == [0]


class TestReviewFindings:
    def test_require_picks_the_file_next_to_the_includer_even_when_cwd_has_a_read_one(
        self, tmp_path: Path, monkeypatch
    ):
        write(tmp_path, "x.stk", '"cwd" :which set\n')
        write(tmp_path, "A/x.stk", '"A" :which set\n')
        main = write(tmp_path, "A/main.stk", '"x.stk" require\n')
        monkeypatch.chdir(tmp_path)
        stacker = Stacker()
        assert run(stacker, '"x.stk" require', f'"{main}" include', "which") == ["A"]

    def test_require_inside_a_loop_inside_a_function_binds_at_the_root(self, counter: Path):
        stacker = Stacker()
        run(stacker, f'{{}} {{1 2 :i {{"{counter}" require}} do}} :f defun f')
        assert run(stacker, "counter") == [0]

    def test_ans_inside_a_function_defined_by_a_required_file_sees_the_latest_result(self, tmp_path: Path):
        lib = write(tmp_path, "lib.stk", "{} {ans} :last defun\n")
        stacker = Stacker()
        stacker.eval(f'1 2 :i {{"{lib}" require}} do')
        stacker.eval("7")
        assert list(stacker.eval("last")) == [7]

    def test_an_unterminated_text_given_to_parse_keeps_the_expressions_line(self, tmp_path: Path):
        lib = write(tmp_path, "lib.stk", '1\n2\n"[1 2" parse\n')
        stacker = Stacker()
        with pytest.raises(Exception) as info:
            stacker.eval(f'"{lib}" include')
        assert info.value.include_location[1] == 3

    def test_a_type_error_attributed_to_a_word_keeps_the_position(self, tmp_path: Path):
        lib = write(tmp_path, "lib.stk", '1\n"a" 1 +\n')
        stacker = Stacker()
        with pytest.raises(TypeError) as info:
            stacker.eval(f'"{lib}" include')
        from stacker.error import include_location_of

        assert include_location_of(info.value)[0][1] == 2

    def test_an_error_in_a_catch_block_is_not_placed_in_the_file(self, tmp_path: Path):
        lib = write(tmp_path, "lib.stk", "1 0 /\n")
        stacker = Stacker()
        with pytest.raises(Exception) as info:
            stacker.eval(f'{{"{lib}" include}} {{zzz}} iferror')
        from stacker.error import include_location_of

        assert include_location_of(info.value) is None

    def test_reduce_without_a_value_names_the_block(self):
        with pytest.raises(NoValueProducedError, match="The block passed to `reduce`"):
            run(Stacker(), "[1 2] 0 :a :x {} reduce")
