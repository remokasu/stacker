"""The language's values and their surroundings: how a value is written, a scope,
the boundary between tokens and values, a word's arguments, the console, a macro,
the recursion limit, and the protocols by which the words see the engine. The
layer imports only from itself, the syntax and the foundation (the value types,
the errors); it never runs code and knows nothing of terminals.
"""
