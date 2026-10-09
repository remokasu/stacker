"""The prelude: Stacker code loaded into every new interpreter.

Files are evaluated in the order listed in ``PRELUDE_FILES`` (a later file
may use words defined by an earlier one). A ``.stk`` file in this directory
that is not listed is ignored with a warning, so the load order never depends
on the filesystem.
"""

from __future__ import annotations

import logging
from functools import cache
from pathlib import Path
from typing import TYPE_CHECKING

from stacker.error import PreludeLoadError

if TYPE_CHECKING:
    from stacker.stacker import Stacker

_LOGGER = logging.getLogger("stacker")

PRELUDE_DIR = Path(__file__).resolve().parent
PRELUDE_FILES: tuple[str, ...] = ("macro.stk", "sfunction.stk")


@cache
def _read_source(path: str) -> str:
    """Reads a prelude file once per process.

    Args:
        path: Absolute path of the ``.stk`` file.

    Returns:
        The file contents.
    """
    return Path(path).read_text(encoding="utf-8")


def _defined_names(stacker: Stacker) -> set[str]:
    """Returns every variable, macro and function name ``stacker`` defines."""
    return set(stacker.variables.keys()) | set(stacker.macros) | set(stacker.sfunctions)


def _lookup(stacker: Stacker, name: str) -> object:
    """Returns the object bound to ``name`` (macro, function entry or variable)."""
    if name in stacker.macros:
        return stacker.macros[name]
    if name in stacker.sfunctions:
        return stacker.sfunctions[name]
    return stacker.variables[name]


def load_prelude(
    stacker: Stacker,
    directory: Path = PRELUDE_DIR,
    files: tuple[str, ...] = PRELUDE_FILES,
) -> None:
    """Evaluates the prelude files into ``stacker`` and records what they defined.

    Args:
        stacker: Root interpreter to load the prelude into.
        directory: Directory holding the prelude files.
        files: File names to load, in order.

    Raises:
        PreludeLoadError: If a prelude file fails to evaluate. The failing
            file and the underlying error are also logged at ERROR level.
    """
    prelude = stacker._prelude
    before = _defined_names(stacker)
    prelude["loading"] = True
    try:
        for filename in files:
            path = directory / filename
            stacker.current_file = str(path)
            try:
                stacker.process_expression(_read_source(str(path)))
            except Exception as error:  # noqa: BLE001 - any failure aborts the load
                _LOGGER.error("prelude file '%s' failed to load: %s", filename, error)
                raise PreludeLoadError(filename, error) from error
    finally:
        prelude["loading"] = False
        stacker.current_file = None

    for path in sorted(directory.glob("*.stk")):
        if path.name not in files:
            _LOGGER.warning(
                "prelude file '%s' is not listed in PRELUDE_FILES and was not loaded", path.name
            )

    new_names = _defined_names(stacker) - before
    prelude["names"] |= new_names
    prelude["objects"].update({name: _lookup(stacker, name) for name in new_names})
