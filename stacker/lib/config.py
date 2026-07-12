from __future__ import annotations

from pathlib import Path

history_file = ".stacker_history"
history_file_path = Path.home() / history_file
plugins_dir_path = "plugins"

stacker_dotfile = ".stackerrc"
stacker_dotfile_path = Path.home() / stacker_dotfile

script_extension_name = ".stk"

# --- Recursion guard --------------------------------------------
# Measured on CPython 3.13: the engine's true recursion ceiling is the
# interpreter's C-recursion protection (independent of
# sys.setrecursionlimit), which stops this engine's call chain at 2000
# Stacker levels with a plain RecursionError. The limits below stay under
# that ceiling so the guard's named StackerRecursionError always fires
# first.
#
# Default maximum Stacker-level recursion depth for user-defined
# functions and lambdas; overridable per run with --recursion-limit
DEFAULT_RECURSION_LIMIT = 1500
# Hard cap for --recursion-limit; larger values are rejected (kept 10%
# below the measured C-recursion ceiling of 2000)
MAX_RECURSION_LIMIT = 1800
# Upper bound of measured Python frames per Stacker recursion level;
# sizes the sys.setrecursionlimit backstop for non-function recursion
RECURSION_FRAMES_PER_LEVEL = 20
# Headroom on top of the backstop for engine base frames and operators
RECURSION_BACKSTOP_MARGIN = 10_000
