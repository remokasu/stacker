"""The display module's former name: ``stacker.util.disp`` is ``stacker.engine.display``.

The module object is the same one, so its state (what is being shown,
the color map) is shared, and ``import stacker.util.disp`` keeps working.
Its ``__name__`` and ``__file__`` are those of ``stacker.engine.display``.
"""

from __future__ import annotations

import sys

from stacker.engine import display as _display

sys.modules[__name__] = _display
