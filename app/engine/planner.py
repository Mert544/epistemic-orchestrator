from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass
class Plan:
    """A plan with fallback strategies."""

    primary: str
    fallbacks: list[str] = field(default_factory=list)
    max_retries: int = 2
    current_attempt: int = 0

    def next_strategy(self) -> str | None:
        """Get next strategy when primary fails."""
        if self.current_attempt == 0:
            self.current_attempt += 1
            return self.primary
        idx = self.current_attempt - 1
        if idx < len(self.fallbacks):
            self.current_attempt += 1
            return self.fallbacks[idx]
        return None

    def reset(self) -> None:
        self.current_attempt = 0


class Planner:
    """Adaptive planner: chooses strategy based on finding type and past performance.

    The Planner:
    1. Receives a finding
    2. Looks up past success/failure in FeedbackLoop
    3. Chooses primary strategy + fallbacks
    4. If action fails, retries with fallback

    Usage:
        planner = Planner()
        plan = planner.plan(finding)
        strategy = plan.next_strategy()  # primary
        # if fails:
        strategy = plan.next_strategy()  # fallback 1
    """

    def __init__(self, feedback=None) -> None:
        from app.engine.feedback_loop import FeedbackLoop
        self.feedback = feedback or FeedbackLoop()

    def plan(self, finding: dict[str, Any]) -> Plan:
        """Create a plan for handling a finding."""
        issue = finding.get("issue", "").lower()
        node_key = f"{finding.get('issue','')}:{finding.get('file','')}:{finding.get('line',0)}"

        # Check if this pattern has bad history
        if self.feedback.should_skip(node_key):
            return Plan(
                primary="escalate",
                fallbacks=[],
                max_retries=0,
            )

        # Choose strategies based on issue type
        if "eval" in issue:
            return Plan(
                primary="replace_with_literal_eval",
                fallbacks=["add_input_validation", "escalate"],
                max_retries=2,
            )
        elif "os.system" in issue:
            return Plan(
                primary="replace_with_subprocess_run",
                fallbacks=["add_command_whitelist", "escalate"],
                max_retries=2,
            )
        elif "bare except" in issue:
            return Plan(
                primary="add_exception_type",
                fallbacks=["escalate"],
                max_retries=1,
            )
        elif "missing_docstring" in issue:
            return Plan(
                primary="add_docstring",
                fallbacks=["escalate"],
                max_retries=1,
            )
        else:
            return Plan(
                primary="review",
                fallbacks=["escalate"],
                max_retries=1,
            )
