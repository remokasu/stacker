from stacker.stacker import Stacker


def string_concat(s1: str, s2: str) -> str:
    if not isinstance(s1, str) or not isinstance(s2, str):
        raise ValueError("Both inputs must be of type 'str'.")
    return s1 + s2


def setup(stacker_core: Stacker):
    stacker_core.register_plugin("strcat", string_concat, description_en="Concatenate two strings.")

# Usage example: