from __future__ import annotations


def index_to_branch_token(index: int) -> str:
    if index < 0:
        raise ValueError("index must be non-negative")

    alphabet = "abcdefghijklmnopqrstuvwxyz"
    value = index
    token = ""
    while True:
        value, remainder = divmod(value, 26)
        token = alphabet[remainder] + token
        if value == 0:
            break
        value -= 1
    return token


def make_branch_path(parent_branch: str, child_index: int) -> str:
    token = index_to_branch_token(child_index)
    return f"{parent_branch}.{token}" if parent_branch else f"x.{token}"
