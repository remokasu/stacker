"""The fixtures the tests of the compile tier share: a recorder of the units made, and a pair of interpreters."""

import pytest

from stacker.engine import compiler
from test.engine.compile_helpers import Compilations, Twin


@pytest.fixture
def compilations(monkeypatch):
    """Records the units the compiler makes."""
    return Compilations(monkeypatch)


@pytest.fixture
def twin(monkeypatch, compilations):
    """A pair of interpreters (see ``Twin``); every block of the compiling one is compiled on its first run, worthwhile or not."""
    monkeypatch.setattr(compiler, "THRESHOLD", 1)
    monkeypatch.setattr(compiler, "ONLY_WORTHWHILE", False)
    return Twin(compilations)
