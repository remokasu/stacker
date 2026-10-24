"""The package ships every file the interpreter reads at run time."""

import tomllib
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent


def test_the_prelude_and_the_data_files_are_package_data():
    config = tomllib.loads((ROOT / "pyproject.toml").read_text(encoding="utf-8"))
    package_data = config["tool"]["setuptools"]["package-data"]
    assert "*.stk" in package_data["stacker.slib"], "the prelude (stacker/slib/*.stk) must ship, or `stacker` cannot start"
    assert "data/*" in package_data["stacker"]


def test_every_runtime_file_in_the_tree_is_covered():
    package = ROOT / "stacker"
    stray = [
        str(f.relative_to(package))
        for f in package.rglob("*")
        if f.is_file() and f.suffix not in (".py", ".pyc") and "__pycache__" not in f.parts
        and not (f.parent == package / "slib" and f.suffix == ".stk")
        and f.parent != package / "data"
    ]
    assert stray == [], f"files the package would not ship: {stray}"
