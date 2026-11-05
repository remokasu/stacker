"""The value words: each takes values from the stack and gives values back, and none runs code.

``STANDARD`` is the set of tables the interpreter is made with, by category
and in the order the words are listed in (the `operators` word, the help).
The face hands it to the engine (``Stacker.WORD_TABLES``); the engine holds
only its own words, the control words and the higher-order words.
"""

from __future__ import annotations

from collections.abc import Mapping, Sequence

from stacker.operators.aggregate import aggregate_operators
from stacker.operators.algebra import alge_operators
from stacker.operators.arith import arith_operators
from stacker.operators.base import base_operators
from stacker.operators.bitwise import bitwise_operators
from stacker.operators.collection import collection_operators
from stacker.operators.comparison import compare_operators
from stacker.operators.file import file_operators
from stacker.operators.io import io_operators
from stacker.operators.list import list_operators
from stacker.operators.logic import logic_operators
from stacker.operators.math import math_operators
from stacker.operators.os import os_operators
from stacker.operators.random import random_operators
from stacker.operators.setting import settings_operators
from stacker.operators.stack import stack_operators
from stacker.operators.string import string_operators
from stacker.operators.system import system_operators
from stacker.operators.time import time_operators
from stacker.operators.transform import transform_operators
from stacker.operators.types import type_operators

#: Category -> the tables whose words it holds, in listing order. The file words are regular words too
#: (looked up as regular first), so their table is in both categories.
STANDARD: Mapping[str, Sequence[Mapping[str, object]]] = {
    "regular": (
        alge_operators,
        arith_operators,
        base_operators,
        bitwise_operators,
        compare_operators,
        file_operators,
        io_operators,
        logic_operators,
        math_operators,
        random_operators,
        type_operators,
        list_operators,
        string_operators,
        time_operators,
        os_operators,
    ),
    "aggregate": (aggregate_operators,),
    "collection": (collection_operators,),
    "transform": (transform_operators,),
    "stack": (stack_operators,),
    "file": (file_operators,),
    "settings": (settings_operators,),
    "system": (system_operators,),
}
