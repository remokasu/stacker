"""What the whole test session checks and how it is run.

- Every shallow copy of a core is checked against the dictionary update it stands for
- The compile tier runs in the state ``STACKER_TEST_COMPILE`` names: ``default`` (blocks
  are compiled once they have run often), ``off`` (never) or ``eager`` (on their first
  run, every unit made whether or not it would gain anything, every name re-resolved
  before its step). Tests that start another process always
  run it in the default state; the golden snapshot covers those in every state
- The kept macro expansions run in the state ``STACKER_TEST_MEMO`` names: ``default``
  (kept and used), ``off`` (never kept) or ``shadow`` (kept, and every use checked
  against a fresh expansion, which is the one run: only ``default`` runs the kept code)
"""

import os

import pytest

from stacker.engine import compiler, copier, machine

COMPILE_STATES = ("off", "default", "eager")
MEMO_STATES = ("off", "default", "shadow")


def pytest_configure(config):
    """Puts the compile tier in the state ``STACKER_TEST_COMPILE`` names, before any test imports run."""
    state = os.environ.get("STACKER_TEST_COMPILE", "default")
    if state not in COMPILE_STATES:
        raise pytest.UsageError(f"STACKER_TEST_COMPILE must be one of {', '.join(COMPILE_STATES)}, not {state!r}")
    if state == "off":
        compiler.THRESHOLD = None
    elif state == "eager":
        compiler.THRESHOLD = 1
        compiler.VERIFY = True
        compiler.ONLY_WORTHWHILE = False
    config.stacker_compile_state = state
    memo = os.environ.get("STACKER_TEST_MEMO", "default")
    if memo not in MEMO_STATES:
        raise pytest.UsageError(f"STACKER_TEST_MEMO must be one of {', '.join(MEMO_STATES)}, not {memo!r}")
    if memo == "off":
        machine.MEMO_ENABLED = False
    elif memo == "shadow":
        machine.MEMO_SHADOW = True
    config.stacker_memo_state = memo


def pytest_report_header(config):
    """Names the compile tier's and the kept expansions' states at the top of the run, so a log says which they were."""
    return (
        f"stacker compile tier: {config.stacker_compile_state} (STACKER_TEST_COMPILE), "
        f"kept expansions: {config.stacker_memo_state} (STACKER_TEST_MEMO)"
    )


def check_shallow_copy(core, new):
    """Fails when ``new`` is not what ``object.__new__`` and ``__dict__.update`` would have made of ``core``."""
    if new is core:
        pytest.fail("a shallow copy is the original itself")
    if type(new) is not type(core):
        pytest.fail(f"a shallow copy is a {type(new).__name__}, the original a {type(core).__name__}")
    missing = sorted(core.__dict__.keys() - new.__dict__.keys(), key=repr)
    extra = sorted(new.__dict__.keys() - core.__dict__.keys(), key=repr)
    if missing or extra:
        pytest.fail(f"a shallow copy lacks {missing} and has {extra} beyond the original")
    for name, value in core.__dict__.items():
        if new.__dict__[name] is not value:
            pytest.fail(f"a shallow copy's `{name}` is not the original's object")


@pytest.fixture(autouse=True, scope="session")
def checked_shallow_copies():
    """Routes every shallow copy made during the session through the check."""
    original = copier.shallow_copy

    def checked(core):
        new = original(core)
        check_shallow_copy(core, new)
        return new

    copier.shallow_copy = checked
    yield
    copier.shallow_copy = original


@pytest.fixture
def shallow_copy_check():
    """The check itself, for the tests of the check."""
    return check_shallow_copy
