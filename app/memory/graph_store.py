from app.models.node import ResearchNode


class GraphStore:
    def __init__(self) -> None:
        self.nodes: dict[str, ResearchNode] = {}
        self.question_texts: set[str] = set()
        self.claim_texts: set[str] = set()

    def add_node(self, node: ResearchNode) -> None:
        self.nodes[node.id] = node
        self.register_claim(node.claim)

    def has_similar_question(self, qtext: str) -> bool:
        return qtext.strip().lower() in self.question_texts

    def register_question(self, qtext: str) -> None:
        self.question_texts.add(qtext.strip().lower())

    def has_similar_claim(self, claim: str) -> bool:
        return claim.strip().lower() in self.claim_texts

    def register_claim(self, claim: str) -> None:
        self.claim_texts.add(claim.strip().lower())

    def get_all_nodes(self) -> list[ResearchNode]:
        return list(self.nodes.values())
