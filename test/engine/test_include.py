"""The rule of `include` / `require`, written once in start_include, and the file it prepares."""

from __future__ import annotations

import logging

import pytest

from stacker import Stacker
from stacker.data_type import stack_data
from stacker.engine.include import INCLUDE, Started, start_include
from stacker.error import IncludeError, include_location_of


@pytest.fixture
def lib(tmp_path):
    path = tmp_path / "lib.stk"
    path.write_text("1 2 +\n3\n", encoding="utf-8")
    return path


def test_a_started_file_is_not_running_until_begun_and_not_remembered_until_ended(lib, caplog):
    stacker = Stacker()
    started = start_include(stacker, str(lib), once=False)
    assert isinstance(started, Started)
    assert started.resolved == lib.resolve()
    assert started.runner.parent is stacker and started.runner.current_file == str(lib.resolve())
    assert stacker._includes.stack == [] and stacker._includes.loaded == set()
    started.begin()
    assert [(frame.path, frame.kind) for frame in stacker._includes.stack] == [(lib.resolve(), INCLUDE)]
    assert list(started.expressions) == ["1 2 +", "3"]
    assert (started.running.line, started.runner.current_line) == (2, 2)
    started.stop()
    assert stacker._includes.stack == []
    with caplog.at_level(logging.WARNING):
        started.end(stack_data([3, 3]))
    assert stacker._includes.loaded == {lib.resolve()}
    assert [record.getMessage() for record in caplog.records] == ["2 values left on the stack at the end of lib.stk: 3, 3"]


def test_require_of_a_file_already_run_has_nothing_to_start(lib):
    stacker = Stacker()
    stacker.require(str(lib))
    assert start_include(stacker, str(lib), once=True) is None
    assert start_include(stacker, str(lib), once=False) is not None


def test_a_file_that_is_running_is_circular(lib):
    stacker = Stacker()
    started = start_include(stacker, str(lib), once=False)
    started.begin()
    with pytest.raises(IncludeError, match="Circular include detected"):
        start_include(started.runner, str(lib), once=False)


def test_tag_records_the_files_position_on_the_error(lib):
    stacker = Stacker()
    started = start_include(stacker, str(lib), once=False)
    started.begin()
    next(started.expressions)
    error = ValueError("stopped")
    started.tag(error)
    assert include_location_of(error) == ((str(lib.resolve()), 1, "1 2 +"), [])


def test_require_runs_the_file_in_the_root_scope_and_include_where_the_word_is(lib):
    stacker = Stacker()
    stacker.process_expression("{} {} :f defun")  # (a child scope to start from)
    child = type(stacker)(parent=stacker)
    child.variables = stacker.variables.create_child_scope({})
    assert start_include(child, str(lib), once=True).runner.variables is stacker.variables
    assert start_include(child, str(lib), once=False).runner.variables is child.variables
