"""What the machine needs to know of the control words it runs itself.

``ORIGINALS`` holds each control word's built-in function: a word
re-registered under the name holds another, and the machine then leaves
the word to its handler. ``COUNTS`` are the types a count of `times` is
run on by the machine; the word itself looks at any other.
"""

from stacker.engine.primitives import if_else, loop

#: The types a count of `times` is run on here; the word itself looks at any other
COUNTS = frozenset({int, float, bool})
#: The function each control word's entry holds when it is the built-in: a word re-registered under the name
#: holds another, and is not inlined
ORIGINALS = {
    "do": loop.loop_operators["do"]["func"],
    "dolist": loop.loop_operators["dolist"]["func"],
    "loop": loop.loop_operators["loop"]["func"],
    "while": loop.loop_operators["while"]["func"],
    "times": loop.loop_operators["times"]["func"],
    "if": if_else.condition_operators["if"]["func"],
    "ifelse": if_else.condition_operators["ifelse"]["func"],
}
