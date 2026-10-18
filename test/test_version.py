"""`stacker --version` and the word `version` tell which Stacker this is."""

import re
import subprocess
import sys
from pathlib import Path

from stacker import Stacker, __version__


def test_the_word_version_pushes_the_version_string():
    stacker = Stacker()
    stacker.process_expression("version")
    (value,) = stacker.stack
    assert value == __version__
    assert re.fullmatch(r"1\.\d+\.\d+", value)


def test_the_version_matches_pyproject_and_docs():
    root = Path(__file__).resolve().parents[1]
    assert f'version = "{__version__}"' in (root / "pyproject.toml").read_text()
    assert (root / "docs" / "VERSION").read_text().strip() == __version__


def test_the_command_line_flag_prints_it_and_exits_0():
    result = subprocess.run([sys.executable, "-m", "stacker", "--version"], capture_output=True, text=True, check=False)
    assert result.returncode == 0
    assert result.stdout.strip() == f"Stacker {__version__}"
