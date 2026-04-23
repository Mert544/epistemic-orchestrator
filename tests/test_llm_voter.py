from app.agents.llm_voter import LLMVoter
from app.agents.consensus import Verdict


def test_llm_voter_heuristic_security_reject():
    voter = LLMVoter(router=None)  # No LLM, use heuristic
    vote = voter.vote(
        agent_name="sec",
        agent_role="security_auditor",
        claim="Use eval() for configuration",
        weight=1.5,
    )
    assert vote.verdict == Verdict.REJECT
    assert vote.confidence > 0.5
    assert vote.weight == 1.5


def test_llm_voter_heuristic_docstring_approve():
    voter = LLMVoter(router=None)
    vote = voter.vote(
        agent_name="doc",
        agent_role="documentation_enforcer",
        claim="Add docstrings to all functions",
        weight=0.8,
    )
    assert vote.verdict == Verdict.APPROVE
    assert vote.confidence > 0.5


def test_llm_voter_heuristic_test_abstain():
    voter = LLMVoter(router=None)
    vote = voter.vote(
        agent_name="test",
        agent_role="test_coverage_analyst",
        claim="Refactor database layer",
        weight=1.0,
    )
    assert vote.verdict == Verdict.ABSTAIN


def test_llm_voter_architecture_approve():
    voter = LLMVoter(router=None)
    vote = voter.vote(
        agent_name="arch",
        agent_role="architecture_analyst",
        claim="Reduce dependency coupling",
        weight=1.2,
    )
    assert vote.verdict == Verdict.APPROVE


def test_llm_voter_unknown_role_defaults():
    voter = LLMVoter(router=None)
    vote = voter.vote(
        agent_name="unknown",
        agent_role="some_random_role",
        claim="Anything",
    )
    assert vote.verdict == Verdict.ABSTAIN
