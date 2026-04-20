from app.models.enums import QuestionType
from app.models.question import Question


class QuestionGenerator:
    def generate(self, claim: str, assumptions: list[str]) -> list[Question]:
        assumption_hint = assumptions[0] if assumptions else "No explicit assumptions extracted."
        return [
            Question(
                text=f"What critical information is missing to validate this claim: {claim}?",
                qtype=QuestionType.MISSING,
                impact=0.9,
                uncertainty=0.9,
                risk=0.5,
            ),
            Question(
                text=f"What evidence would directly contradict this claim: {claim}?",
                qtype=QuestionType.CONTRADICTION,
                impact=0.8,
                uncertainty=0.7,
                risk=0.6,
            ),
            Question(
                text=f"What are the consequences if this claim is wrong: {claim}?",
                qtype=QuestionType.RISK,
                impact=0.7,
                uncertainty=0.6,
                risk=0.9,
            ),
            Question(
                text=f"What sub-factors or causal components explain this claim: {claim}? Assumption anchor: {assumption_hint}",
                qtype=QuestionType.DEEPENING,
                impact=0.75,
                uncertainty=0.7,
                risk=0.4,
            ),
        ]
