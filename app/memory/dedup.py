class ExactQuestionDeduplicator:
    def normalize(self, text: str) -> str:
        return text.strip().lower()
