from pathlib import Path

from app.memory.graph_store import GraphStore
from app.memory.persistent_memory import PersistentMemoryStore
from app.models.enums import ClaimType, NodeStatus
from app.models.node import ResearchNode
from app.models.report import FinalReport


def test_persistent_memory_hydrates_and_persists_runs(tmp_path: Path):
    store = PersistentMemoryStore(project_root=tmp_path)
    graph = GraphStore()

    initial_state = store.hydrate_graph(graph)
    assert initial_state["known_claims"] == []
    assert initial_state["known_questions"] == []

    report = FinalReport(
        objective="demo",
        confidence_map={"Dependency hub claim": 0.8},
        unresolved_questions=["What evidence would directly contradict this claim: Dependency hub claim?"],
        main_findings=["Dependency hub claim"],
        recommended_actions=["Inspect and reduce coupling in central dependency hubs: app/services/order_service.py."],
        branch_map={"x.a": "Dependency hub claim"},
    )
    nodes = [
        ResearchNode(
            id="n1",
            claim="Dependency hub claim",
            branch_path="x.a",
            claim_type=ClaimType.ARCHITECTURE,
            claim_priority=0.9,
            confidence=0.8,
            risk=0.4,
            status=NodeStatus.EXPANDED,
        )
    ]

    summary = store.persist_run("demo", report, nodes)
    assert str(Path(summary["memory_file"])).endswith("memory.json")
    assert summary["known_claim_count"] == 1
    assert summary["previous_run_count"] == 0

    graph2 = GraphStore()
    state2 = store.hydrate_graph(graph2)
    assert graph2.has_memory_claim("Dependency hub claim") is True
    assert graph2.has_memory_question("What evidence would directly contradict this claim: Dependency hub claim?") is True
    assert graph2.has_similar_claim("Dependency hub claim") is False
    assert len(state2["runs"]) == 1
