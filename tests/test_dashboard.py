from app.agents.dashboard import ConsensusDashboard
from app.agents.consensus import ConsensusEngine, ConsensusResult, Verdict, Vote


def _make_vote(agent: str, verdict: str, confidence: float) -> Vote:
    return Vote(
        agent_name=agent,
        agent_role="test",
        verdict=Verdict[verdict],
        confidence=confidence,
        reasoning="test",
        weight=1.0,
    )


def test_dashboard_update():
    dashboard = ConsensusDashboard(host="127.0.0.1", port=0)  # Port 0 = don't bind

    engine = ConsensusEngine(strategy="majority", quorum=1)
    votes = [_make_vote("a1", "APPROVE", 0.9)]
    result = engine.evaluate("test claim", votes)

    dashboard.update([result])

    # Data should be in handler class variable
    from app.agents.dashboard import DashboardHandler
    assert len(DashboardHandler.consensus_data) == 1
    assert DashboardHandler.consensus_data[0]["claim"] == "test claim"


def test_dashboard_url():
    dashboard = ConsensusDashboard(host="127.0.0.1", port=8766)
    assert dashboard.url == "http://127.0.0.1:8766"


def test_dashboard_html_loaded():
    from app.agents.dashboard import DashboardHandler
    assert "Consensus Dashboard" in DashboardHandler.dashboard_html
    assert "Apex Orchestrator" in DashboardHandler.dashboard_html
