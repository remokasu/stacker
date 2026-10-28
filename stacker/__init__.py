from __future__ import annotations

import os

from stacker import constant, error, stacker
from stacker.engine.console import Console, StreamConsole
from stacker.engine.data_type import Array, Symbol
from stacker.stacker import Stacker
from stacker.version import __version__

__all__ = [
    "Array",
    "Console",
    "Stacker",
    "StreamConsole",
    "Symbol",
    "__version__",
    "constant",
    "error",
    "include",
    "stacker",
]

# リソースフォルダへのパスを取得する
resource_path = os.path.join(os.path.dirname(__file__), "data")

plugins_path = os.path.join(os.path.dirname(__file__), "plugins")

# モジュールにパスを追加する
__path__.append(resource_path)
__path__.append(plugins_path)
