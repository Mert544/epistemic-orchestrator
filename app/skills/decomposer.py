class Decomposer:
    def decompose(self, text: str) -> list[str]:
        cleaned = text.strip()
        return [cleaned] if cleaned else []
