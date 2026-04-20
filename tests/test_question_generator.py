from app.models.enums import QuestionType
from app.skills.question_generator import QuestionGenerator


def test_question_generator_emits_all_four_types():
    qgen = QuestionGenerator()
    questions = qgen.generate("A claim", ["An assumption"])
    emitted = {q.qtype for q in questions}
    assert emitted == {
        QuestionType.MISSING,
        QuestionType.CONTRADICTION,
        QuestionType.RISK,
        QuestionType.DEEPENING,
    }
