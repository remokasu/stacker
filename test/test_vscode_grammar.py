"""The VSCode grammar highlights every word of the language, and only those.

The grammar file is generated from the interpreter's own word lists by
.vscode-extension/generate_grammar.py; this keeps the file on disk and the
generator in step, so a word added, renamed or removed shows up here.
"""

from __future__ import annotations

import importlib.util
import json
import re
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent
GENERATOR = ROOT / "scripts" / "generate_vscode_grammar.py"
GRAMMAR = ROOT / ".vscode-extension" / "syntaxes" / "stacker.tmLanguage.json"


def _generator():
    spec = importlib.util.spec_from_file_location("generate_vscode_grammar", GENERATOR)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_grammar_on_disk_is_what_the_generator_writes():
    assert GRAMMAR.read_text(encoding="utf-8") == _generator().render(), (
        "run `python scripts/generate_vscode_grammar.py` from the repository root"
    )


def test_grammar_lists_every_word_of_the_language_once():
    generator = _generator()
    highlighted = [word for _, words in generator.GROUPS for word in words]
    assert sorted(highlighted) == sorted(set(highlighted)), "a word is in two groups"
    assert set(highlighted) == generator.language_words()


@pytest.mark.parametrize(
    ("source", "scope", "text"),
    [
        ("3 4 +", "keyword.operator.arithmetic.stacker", "+"),
        ("3 :x set", "constant.other.symbol.stacker", ":x"),
        ("3 :x set", "keyword.operator.assignment.stacker", "set"),
        ('"3 4 +" parse eval', "keyword.operator.code.stacker", "parse"),
        ("1 10 :i {i echo} do", "keyword.control.stacker", "do"),
        ("[1 2] 0 :acc :x {acc x +} reduce", "keyword.operator.list.stacker", "reduce"),
        ("null true", "constant.language.stacker", "null"),
        ("3 int?", "keyword.operator.type.stacker", "int?"),
        ("1 2 ==", "keyword.operator.comparison.stacker", "=="),
        ("x 2 <<", "keyword.operator.bitwise.stacker", "<<"),
        ("0x1a 1_000 1.5e3 2+3j", "constant.numeric.hex.stacker", "0x1a"),
        ("3 -5 +", "constant.numeric.integer.stacker", "-5"),
        ("-1.5 2 *", "constant.numeric.float.stacker", "-1.5"),
        ("3 4 -", "keyword.operator.arithmetic.stacker", "-"),
        ("#| a comment |# 1", "comment.block.stacker", "#| a comment |#"),
    ],
)
def test_a_pattern_matches_the_word_in_context(source, scope, text):
    grammar = json.loads(GRAMMAR.read_text(encoding="utf-8"))
    patterns = [p for rep in grammar["repository"].values() for p in rep["patterns"] if p.get("name") == scope]
    found = []
    for pattern in patterns:
        if "match" in pattern:
            found += [m.group(0) for m in re.finditer(pattern["match"], source)]
        else:
            found += [m.group(0) for m in re.finditer(pattern["begin"] + r".*?" + pattern["end"], source)]
    assert text in found, f"{scope} matched {found!r} in {source!r}"


@pytest.mark.parametrize(
    "name",
    ["my-list", "foo-do", "is-empty?", "x-1", "list-2", "read-from-file", "a++b", "mapped", "dolist-helper", "include", "x1", "set!"],
)
def test_nothing_lights_up_inside_a_longer_name(name):
    # A user's `my-list` must not show `list` highlighted, nor `x-1` the `1`:
    # every word and number pattern matches the whole name or nothing
    grammar = json.loads(GRAMMAR.read_text(encoding="utf-8"))
    for rep in grammar["repository"].values():
        for pattern in rep["patterns"]:
            if "match" not in pattern or pattern["name"].startswith(("comment.", "string.")):
                continue
            hits = [m.group(0) for m in re.finditer(pattern["match"], name)]
            assert hits in ([], [name]), f"{pattern['name']} highlights {hits} inside {name!r}"
