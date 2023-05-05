from collections.abc import Iterable

import numpy as np

"""
> 10:
[[0, 1, 2, 3, 4, 5, 6, 7, 8, 9]]

> (3 10):
[[3, 4, 5, 6, 7, 8, 9]]

> (0 1 0.2):
[[0.0, 0.2, 0.4, 0.6000000000000001, 0.8]]

"""


def custom_range(args):
    if not isinstance(args, Iterable):
        if isinstance(args, int):
            stop = args
            return list(np.arange(stop))
        else:
            raise ValueError(f"Invalid arguments: {args}")
    if len(args) == 1:
        stop = args[0]
        return list(np.arange(stop))
    elif len(args) == 2:
        start, stop = args
        return list(np.arange(start, stop))
    elif len(args) == 3:
        start, stop, step = args
        return list(np.arange(start, stop, step))
    else:
        raise ValueError("Invalid number of arguments for range ':' function.")


def setup(stacker_core):
    stacker_core.register_plugin(":", custom_range)
