from pydantic import BaseModel

from app.models.enums import QuestionType


class Question(BaseModel):
    text: str
    qtype: QuestionType
    impact: float = 0.7
    uncertainty: float = 0.7
    risk: float = 0.5
    novelty: float = 0.0
    priority: float = 0.0
