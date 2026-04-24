import tempfile

from app.agents.memory import AgentMemory
from app.agents.consensus import Vote, Verdict


def _make_vote(agent: str, role: str, verdict: str, confidence: float) -> Vote:
    return Vote(
        agent_name=agent,
        agent_role=role,
        verdict=Verdict[verdict],
        confidence=confidence,
        reasoning="test",
        weight=1.0,
    )


def test_memory_remembers_and_recalls():
    with tempfile.TemporaryDirectory() as tmpdir:
        mem = AgentMemory(memory_dir=tmpdir)
        votes = [
            _make_vote("a1", "security_auditor", "APPROVE", 0.9),
        ]
        mem.remember("Test claim about security", votes, "APPROVE")

        recalled = mem.recall("Test claim about security")
        assert recalled is not None
        assert len(recalled) == 1
        assert recalled[0].agent_name == "a1"


def test_memory_similar_claim_recall():
    with tempfile.TemporaryDirectory() as tmpdir:
        mem = AgentMemory(memory_dir=tmpdir)
        votes = [_make_vote("a1", "security_auditor", "REJECT", 0.85)]
        mem.remember("Use eval() for dynamic config loading", votes, "REJECT")

        # Very similar claim — shares most of the text
        recalled = mem.recall("Use eval() for dynamic config loading in production")
        assert recalled is not None
        assert recalled[0].verdict == Verdict.REJECT


def test_memory_no_match_for_different_claim():
    with tempfile.TemporaryDirectory() as tmpdir:
        mem = AgentMemory(memory_dir=tmpdir)
        votes = [_make_vote("a1", "security_auditor", "APPROVE", 0.9)]
        mem.remember("Add docstrings to all functions", votes, "APPROVE")

        recalled = mem.recall("Completely different claim about databases")
        assert recalled is None


def test_memory_learns_pattern_confidence():
    with tempfile.TemporaryDirectory() as tmpdir:
        mem = AgentMemory(memory_dir=tmpdir)
        votes = [
            _make_vote("sec", "security_auditor", "REJECT", 0.9),
        ]
        mem.remember("Use eval() for config", votes, "REJECT")

        learned = mem.get_learned_confidence("security_auditor", "eval usage detected")
        assert learned is not None
        assert learned > 0.5


def test_memory_persistence():
    with tempfile.TemporaryDirectory() as tmpdir:
        mem1 = AgentMemory(memory_dir=tmpdir)
        votes = [_make_vote("a1", "test", "APPROVE", 0.8)]
        mem1.remember("Persistent claim", votes, "APPROVE")

        # New instance, same directory
        mem2 = AgentMemory(memory_dir=tmpdir)
        recalled = mem2.recall("Persistent claim")
        assert recalled is not None
        assert recalled[0].confidence == 0.8


def test_memory_stats():
    mem = AgentMemory()
    votes = [_make_vote("a1", "test", "APPROVE", 0.8)]
    mem.remember("Claim 1", votes, "APPROVE")
    mem.remember("Claim 2", votes, "APPROVE")

    stats = mem.stats()
    assert stats["total_entries"] == 2
    assert stats["total_hits"] >= 2
