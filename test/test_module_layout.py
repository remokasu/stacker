"""Pins where the engine's modules live and what importing them pulls in."""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent


def _run_python(code: str) -> str:
    """Runs ``code`` in a fresh interpreter from the repository root and returns its output."""
    result = subprocess.run([sys.executable, "-c", code], capture_output=True, text=True, cwd=REPO_ROOT, check=False)
    assert result.returncode == 0, result.stderr
    return result.stdout.strip()


def test_the_display_module_keeps_its_former_name():
    import stacker.util.disp as old_name
    from stacker.engine import display
    from stacker.util import disp as attribute
    from stacker.util.disp import plain_text

    assert old_name is display
    assert attribute is display
    assert plain_text is display.plain_text


def test_the_former_name_imported_first_is_still_one_module():
    code = (
        "import stacker.util.disp as a\n"
        "import stacker.engine.display as b\n"
        "from stacker.util import disp as c\n"
        "print(a is b is c)\n"
    )
    assert _run_python(code) == "True"


def test_the_engine_imports_nothing_from_the_runtime():
    code = (
        "import sys\n"
        "import stacker.engine, stacker.stacker\n"
        "prefixes = ('stacker.runtime', 'stacker.lib')\n"
        "print(sorted(m for m in sys.modules if m in prefixes or m.startswith(tuple(p + '.' for p in prefixes))))\n"
    )
    assert _run_python(code) == "[]"


def test_the_limits_and_the_extension_are_still_importable_from_config():
    from stacker.engine.recursion import DEFAULT_RECURSION_LIMIT, MAX_RECURSION_LIMIT
    from stacker.include.include import SCRIPT_EXTENSION
    from stacker.lib import config

    assert (config.DEFAULT_RECURSION_LIMIT, config.MAX_RECURSION_LIMIT) == (DEFAULT_RECURSION_LIMIT, MAX_RECURSION_LIMIT)
    assert config.script_extension_name == SCRIPT_EXTENSION == ".stk"
