from __future__ import annotations

import pytest

from app.engine.planner import Planner
from app.engine.feedback_loop import FeedbackLoop


class TestPlanner:
    def test_plan_eval(self):
        planner = Planner()
        finding = {"issue": "eval() usage", "file": "auth.py", "line": 5}
        plan = planner.plan(finding)
        assert plan.primary == "replace_with_literal_eval"
        assert "add_input_validation" in plan.fallbacks

    def test_plan_bare_except(self):
        planner = Planner()
        finding = {"issue": "bare except clause", "file": "main.py", "line": 10}
        plan = planner.plan(finding)
        assert plan.primary == "add_exception_type"

    def test_next_strategy(self):
        planner = Planner()
        finding = {"issue": "eval() usage", "file": "auth.py", "line": 5}
        plan = planner.plan(finding)
        assert plan.next_strategy() == "replace_with_literal_eval"
        assert plan.next_strategy() == "add_input_validation"
        assert plan.next_strategy() == "escalate"
        assert plan.next_strategy() is None

    def test_skip_bad_history(self, tmp_path: Path):
        feedback = FeedbackLoop(log_dir=str(tmp_path))
        # Node key must match Planner's format: "issue:file:line"
        feedback.update("eval() usage:auth.py:5", old_confidence=0.9, feedback_score=-0.5)
        feedback.update("eval() usage:auth.py:5", old_confidence=0.63, feedback_score=-0.5)
        feedback.update("eval() usage:auth.py:5", old_confidence=0.44, feedback_score=-0.5)
        planner = Planner(feedback)
        finding = {"issue": "eval() usage", "file": "auth.py", "line": 5}
        plan = planner.plan(finding)
        assert plan.primary == "escalate"
        assert plan.max_retries == 0
