from __future__ import annotations

import math


constants: dict[str, int | float | bool | None] = {
    "e": math.e,
    "pi": math.pi,
    "phi": (1 + math.sqrt(5)) / 2,
    "tau": math.tau,
    "nan": math.nan,
    "inf": float("inf"),
    "true": True,
    "false": False,
    "null": None,
}
