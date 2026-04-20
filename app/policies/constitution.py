from app.models.enums import QuestionType


MANDATORY_QUESTION_TYPES = {
    QuestionType.MISSING,
    QuestionType.CONTRADICTION,
    QuestionType.RISK,
    QuestionType.DEEPENING,
}


def enforce_four_question_types(questions) -> None:
    present = {q.qtype for q in questions}
    missing = MANDATORY_QUESTION_TYPES - present
    if missing:
        raise ValueError(f"Mandatory question classes missing: {missing}")


def downgrade_if_unsupported(node):
    if not node.evidence_for:
        node.confidence = min(node.confidence, 0.30)
    return node


def must_search_counter_evidence(node):
    if not node.evidence_against:
        node.evidence_against = ["No counter-evidence found yet; search incomplete."]
    return node
