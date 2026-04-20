def make_child_id(parent_id: str, question_index: int, child_index: int) -> str:
    return f"{parent_id}-{question_index}-{child_index}"
