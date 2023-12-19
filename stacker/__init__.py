from __future__ import annotations

import os

from stacker import constant, error, stacker
from stacker.stacker import Stacker

__all__ = ["stacker", "error", "constant", "include", "Stacker"]

# リソースフォルダへのパスを取得する
resource_path = os.path.join(os.path.dirname(__file__), "data")

plugins_path = os.path.join(os.path.dirname(__file__), "plugins")

# モジュールにパスを追加する
__path__.append(resource_path)
__path__.append(plugins_path)
