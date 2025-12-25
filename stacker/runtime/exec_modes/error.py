from __future__ import annotations

from stacker.util.color import colored


def create_error_message(error_tokens: list[str]):
    last_token = error_tokens[-1]
    expression = " ".join([str(token) for token in error_tokens])
    hilight = " " * (len(expression) - len(last_token)) + "^" * len(last_token)
    return colored(f"{expression}\n{hilight}", "red")


def create_error_message_from_str(code: str):
    return colored(code, "red")
