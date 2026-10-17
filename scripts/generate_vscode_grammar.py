"""Writes syntaxes/stacker.tmLanguage.json from the words the interpreter knows.

The lexical rules (comments, strings, numbers, symbols, blocks) are written
here by hand; every list of words comes from the operator dictionaries, the
prelude and the constants, so the grammar cannot drift from the language.
Run it from the repository root after adding, renaming or removing a word:

    python scripts/generate_vscode_grammar.py

test/test_vscode_grammar.py fails when the file on disk is out of date.
"""

from __future__ import annotations

import json
import re
from pathlib import Path

from stacker.constant import constants
from stacker.operators import (
    algebra,
    arith,
    base,
    bitwise,
    comparison,
    exit,
    file,
    hof,
    if_else,
    io,
    logic,
    loop,
    math,
    os,
    random,
    setting,
    stack,
    string,
    system,
    time,
    transform,
    types,
)
from stacker.operators import (
    list as list_ops,
)
from stacker.operators.manager import aggregate_operators
from stacker.stacker import Stacker
from stacker.syntax.token_rules import KEYWORD_LITERALS

GRAMMAR = Path(__file__).resolve().parent.parent / ".vscode-extension" / "syntaxes" / "stacker.tmLanguage.json"

#: A word made of letters is matched where no name character (letter, digit,
#: `_`, `?`, `!`, `-`) touches it, so `list` does not light up inside
#: `my-list`; a word made of symbols (`+`, `==`, `<<`) is matched between
#: whitespace, brackets or the ends of the line.
WORD = re.compile(r"[A-Za-z_][\w?!-]*")
NAME_CHAR = r"[\w?!-]"

#: The words of the language, grouped as the highlighter shows them. Each
#: group is (scope name, words). A word may appear in one group only.
GROUPS: list[tuple[str, set[str]]] = [
    ("keyword.control.stacker", set(loop.loop_operators) | set(if_else.condition_operators) | {"break"}),
    ("keyword.control.definition.stacker", {"defun", "defmacro", "lambda", "alias"}),
    ("keyword.operator.assignment.stacker", {"set", "=", "global"}),
    ("keyword.operator.code.stacker", {"eval", "apply", "expand", "sub", "subn", "parse", "concat-block", "gensym", "macroexpand", "symbol", "include", "require"}),
    ("keyword.operator.arithmetic.stacker", set(arith.arith_operators) | set(algebra.alge_operators)),
    ("keyword.operator.comparison.stacker", set(comparison.compare_operators)),
    ("keyword.operator.logical.stacker", set(logic.logic_operators)),
    ("keyword.operator.bitwise.stacker", set(bitwise.bitwise_operators) | set(base.base_operators)),
    ("keyword.operator.math.stacker", set(math.math_operators) | set(random.random_operators)),
    ("keyword.operator.stack.stacker", set(stack.stack_operators) | {"ans"}),
    ("keyword.operator.list.stacker", set(hof.hof_operators) | set(transform.transform_operators) | set(aggregate_operators) | set(list_ops.list_operators) | {"nth", "listn"}),
    ("keyword.operator.string.stacker", set(string.string_operators) | {"split"}),
    ("keyword.operator.type.stacker", set(types.type_operators)),
    ("keyword.operator.io.stacker", set(io.io_operators) | set(file.file_operators) | set(os.os_operators) | set(time.time_operators) | {"read"}),
    ("keyword.operator.system.stacker", set(system.system_operators) | set(setting.settings_operators) | set(exit.exit_operators)),
    ("support.function.prelude.stacker", set(Stacker()._prelude["names"]) - {"alias"}),
    ("constant.language.stacker", set(constants) | {word for word in KEYWORD_LITERALS if word.islower()}),
]


def language_words() -> set[str]:
    """Returns every word a fresh interpreter knows without user definitions."""
    stacker = Stacker()
    return (
        set(stacker.operator_manager.built_in_operators)
        | set(stacker._prelude["names"])
        | set(constants)
        | {word for word in KEYWORD_LITERALS if word.islower()}
    )


class GrammarError(ValueError):
    """The word groups and the interpreter's words disagree."""


def _check_groups() -> None:
    grouped: dict[str, str] = {}
    for scope, words in GROUPS:
        for word in words:
            if word in grouped:
                raise GrammarError(f"{word!r} is in {grouped[word]} and {scope}")
            grouped[word] = scope
    missing = language_words() - set(grouped)
    extra = set(grouped) - language_words()
    if missing:
        raise GrammarError(f"words without a group: {sorted(missing)}")
    if extra:
        raise GrammarError(f"grouped words the interpreter does not know: {sorted(extra)}")


def _alternation(words: set[str]) -> str:
    return "|".join(re.escape(word) for word in sorted(words, key=lambda w: (-len(w), w)))


def _word_patterns(scope: str, words: set[str]) -> list[dict[str, str]]:
    """One pattern for the letter words, one for the symbol words of a group."""
    letters = {w for w in words if WORD.fullmatch(w)}
    symbols = words - letters
    patterns = []
    if letters:
        patterns.append({"name": scope, "match": rf"(?<!{NAME_CHAR})({_alternation(letters)})(?!{NAME_CHAR})"})
    if symbols:
        patterns.append({"name": scope, "match": rf"(?<![^\s\[\]{{}}()])({_alternation(symbols)})(?![^\s\[\]{{}}()])"})
    return patterns


def grammar() -> dict:
    _check_groups()
    words = {f"words-{i}": {"patterns": _word_patterns(scope, ws)} for i, (scope, ws) in enumerate(GROUPS)}
    return {
        "$schema": "https://raw.githubusercontent.com/martinring/tmlanguage/master/tmlanguage.json",
        "name": "Stacker",
        "scopeName": "source.stacker",
        "patterns": [
            {"include": "#comments"},
            {"include": "#strings"},
            {"include": "#numbers"},
            {"include": "#symbols"},
            *({"include": f"#{key}"} for key in words),
            {"include": "#blocks"},
        ],
        "repository": {
            "comments": {
                "patterns": [
                    {
                        "name": "comment.block.stacker",
                        "begin": r"#\|",
                        "end": r"\|#",
                        "patterns": [{"include": "#comments"}],  # block comments nest
                    },
                    {"name": "comment.line.number-sign.stacker", "match": r"#(?!\|).*$"},
                ]
            },
            "strings": {
                # Escapes are not interpreted: a backslash is an ordinary character
                "patterns": [
                    {"name": "string.quoted.triple.stacker", "begin": '"""', "end": '"""'},
                    {"name": "string.quoted.triple.stacker", "begin": "'''", "end": "'''"},
                    {"name": "string.quoted.double.stacker", "begin": '"', "end": '"'},
                    {"name": "string.quoted.single.stacker", "begin": "'", "end": "'"},
                ]
            },
            "numbers": {
                "patterns": [
                    # Earlier patterns win at the same position, so the longer
                    # forms (complex, float) come before the integer
                    # A leading `-` belongs to the number unless a name character
                    # precedes it: `-5` is a number, `x-1` is a name
                    {"name": "constant.numeric.complex.stacker", "match": r"(?<![\w.?!-])(?:(?<![\w?!-])-)?[0-9]+(?:\.[0-9]+)?(?:[+-][0-9]+(?:\.[0-9]+)?)?[jJ](?![\w.?!-])"},
                    {"name": "constant.numeric.hex.stacker", "match": r"(?<![\w.?!-])(?:(?<![\w?!-])-)?0[xX][0-9a-fA-F_]+(?![\w.?!-])"},
                    {"name": "constant.numeric.octal.stacker", "match": r"(?<![\w.?!-])(?:(?<![\w?!-])-)?0[oO][0-7_]+(?![\w.?!-])"},
                    {"name": "constant.numeric.binary.stacker", "match": r"(?<![\w.?!-])(?:(?<![\w?!-])-)?0[bB][01_]+(?![\w.?!-])"},
                    {"name": "constant.numeric.float.stacker", "match": r"(?<![\w.?!-])(?:(?<![\w?!-])-)?[0-9][0-9_]*(?:\.[0-9_]+)?[eE][+-]?[0-9]+(?![\w.?!-])|(?<![\w.?!-])(?:(?<![\w?!-])-)?[0-9][0-9_]*\.[0-9_]+(?![\w.?!-])"},
                    {"name": "constant.numeric.integer.stacker", "match": r"(?<![\w.?!-])(?:(?<![\w?!-])-)?[0-9][0-9_]*(?![\w.?!-])"},
                ]
            },
            "symbols": {
                "patterns": [
                    # `:name` is the name itself as a value
                    {"name": "constant.other.symbol.stacker", "match": r"(?<![^\s\[\]{}()]):[^\s\[\]{}()\"'#;:$]+"},
                ]
            },
            **words,
            "blocks": {
                "patterns": [
                    {"name": "meta.block.stacker", "begin": r"\{", "end": r"\}", "patterns": [{"include": "$self"}]},
                    {"name": "meta.block.stacker", "begin": r"\(", "end": r"\)", "patterns": [{"include": "$self"}]},
                    {"name": "meta.list.stacker", "begin": r"\[", "end": r"\]", "patterns": [{"include": "$self"}]},
                ]
            },
        },
    }


def render() -> str:
    return json.dumps(grammar(), indent=2, ensure_ascii=False) + "\n"


if __name__ == "__main__":
    GRAMMAR.write_text(render(), encoding="utf-8")
    print(f"wrote {GRAMMAR}")
