"""The package is in layers, and a module imports only from its own layer and the ones below.

Every ``import`` in ``stacker/`` is read from the source (functions and
``TYPE_CHECKING`` blocks included) and checked against the matrix below. The
crossings that still exist are listed in ``KNOWN_CROSSINGS``, each with the
step that removes it; the list only ever shrinks.
"""

from __future__ import annotations

import ast
import tomllib
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parent.parent
PACKAGE = REPO_ROOT / "stacker"

#: Module prefix -> layer. The longest matching prefix wins; ``stacker`` alone
#: is the face (the package's ``__init__``, ``stacker.stacker`` and the prelude).
LAYERS = {
    "stacker.error": "foundation",
    "stacker.constant": "foundation",
    "stacker.version": "foundation",
    "stacker.data_type": "foundation",
    "stacker.syntax": "syntax",
    "stacker.lang": "lang",
    "stacker.engine": "engine",
    "stacker.operators": "operators",
    "stacker": "face",
    "stacker.stacker": "face",
    "stacker.slib": "face",
    "stacker.runtime": "runtime",
    "stacker.__main__": "runtime",
    "stacker.plugins": "plugins",
}

#: Layer -> the layers it may import from (its own included).
ALLOWED = {
    "foundation": {"foundation"},
    "syntax": {"foundation", "syntax"},
    "lang": {"foundation", "syntax", "lang"},
    "engine": {"foundation", "syntax", "lang", "engine"},
    "operators": {"foundation", "lang", "operators"},
    "face": {"foundation", "syntax", "lang", "engine", "operators", "face"},
    "runtime": {"foundation", "syntax", "lang", "face", "runtime"},
    "plugins": {"foundation", "lang", "face"},
}

#: (file, layer imported, the step that removes it): the crossings that still exist. Empty since 1.33.0; a new
#: one is a defect to fix, not to list.
KNOWN_CROSSINGS: set[tuple[str, str, str]] = set()


def _module_name(path: Path) -> str:
    parts = path.relative_to(REPO_ROOT).with_suffix("").parts
    if parts[-1] == "__init__":
        parts = parts[:-1]
    return ".".join(parts)


def _layer_of(module: str) -> str:
    candidates = [prefix for prefix in LAYERS if module == prefix or module.startswith(prefix + ".")]
    if not candidates:
        raise AssertionError(f"{module} belongs to no layer; add it to LAYERS")
    return LAYERS[max(candidates, key=len)]


def _is_submodule(module: str) -> bool:
    relative = Path(*module.split(".")[1:])
    return (PACKAGE / relative).is_dir() or (PACKAGE / relative).with_suffix(".py").is_file()


def _imported_modules(tree: ast.AST) -> list[tuple[int, str]]:
    """Every module a file imports, as (line, dotted name), ``stacker`` ones only.

    ``from stacker.lang import console`` is the module ``stacker.lang.console``;
    ``from stacker import Stacker`` is the face (``stacker``).
    """
    found = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            found.extend((node.lineno, alias.name) for alias in node.names if alias.name.split(".")[0] == "stacker")
        elif isinstance(node, ast.ImportFrom) and node.module and node.module.split(".")[0] == "stacker":
            assert node.level == 0, f"relative import at line {node.lineno}"
            for alias in node.names:
                full = f"{node.module}.{alias.name}"
                found.append((node.lineno, full if _is_submodule(full) else node.module))
    return found


def _crossings() -> dict[tuple[str, str], list[str]]:
    """Every import against the matrix: (file, layer imported) -> where it happens."""
    found: dict[tuple[str, str], list[str]] = {}
    for path in sorted(PACKAGE.rglob("*.py")):
        if "__pycache__" in path.parts:
            continue
        own = _layer_of(_module_name(path))
        tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
        for line, module in _imported_modules(tree):
            target = _layer_of(module)
            if target not in ALLOWED[own]:
                where = f"{path.relative_to(REPO_ROOT)}:{line} imports {module} ({own} -> {target})"
                found.setdefault((str(path.relative_to(REPO_ROOT)), target), []).append(where)
    return found


def test_every_module_is_in_a_layer():
    for path in PACKAGE.rglob("*.py"):
        if "__pycache__" not in path.parts:
            _layer_of(_module_name(path))


def test_no_import_crosses_the_layers_except_the_known_ones():
    found = _crossings()
    known = {(file, layer) for file, layer, _step in KNOWN_CROSSINGS}
    unknown = [where for key, places in found.items() if key not in known for where in places]
    assert unknown == [], "imports against the layer matrix:\n" + "\n".join(unknown)


def test_the_known_crossings_still_exist():
    found = set(_crossings())
    stale = sorted((file, layer, step) for file, layer, step in KNOWN_CROSSINGS if (file, layer) not in found)
    assert stale == [], f"crossings no longer in the tree, remove them from KNOWN_CROSSINGS: {stale}"


def test_the_subpackages_are_the_ones_the_wheel_ships():
    config = tomllib.loads((REPO_ROOT / "pyproject.toml").read_text(encoding="utf-8"))
    shipped = set(config["tool"]["setuptools"]["packages"])
    in_tree = {_module_name(init) for init in PACKAGE.rglob("__init__.py") if "__pycache__" not in init.parts}
    assert in_tree == shipped, f"missing from pyproject: {sorted(in_tree - shipped)}, not in the tree: {sorted(shipped - in_tree)}"


@pytest.mark.parametrize(
    "module, layer",
    [
        ("stacker.data_type", "foundation"),
        ("stacker.lang.console", "lang"),
        ("stacker.engine.primitives.loop", "engine"),
        ("stacker.operators.arith", "operators"),
        ("stacker", "face"),
        ("stacker.stacker", "face"),
        ("stacker.slib", "face"),
        ("stacker.runtime.exec_modes.repl_mode", "runtime"),
        ("stacker.__main__", "runtime"),
        ("stacker.plugins.matrix", "plugins"),
    ],
)
def test_the_longest_prefix_decides_the_layer(module, layer):
    assert _layer_of(module) == layer
