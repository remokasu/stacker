from __future__ import annotations

from pathlib import Path

from stacker.engine.include import SCRIPT_EXTENSION as script_extension_name  # noqa: F401

# The recursion limits live with the guard that enforces them, and the
# script extension with the include words; both stay importable from here
from stacker.lang.recursion import DEFAULT_RECURSION_LIMIT, HOST_RECURSION_LIMIT  # noqa: F401

history_file = ".stacker_history"
history_file_path = Path.home() / history_file
plugins_dir_path = "plugins"

stacker_dotfile = ".stackerrc"
stacker_dotfile_path = Path.home() / stacker_dotfile
