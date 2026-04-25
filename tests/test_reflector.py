from __future__ import annotations

from pathlib import Path

import pytest

from app.engine.reflector import Reflector
from app.engine.feedback_loop import FeedbackLoop


class TestReflector:
    def test_reflect_empty(self, tmp_path: Path):
        feedback = FeedbackLoop(log_dir=str(tmp_path))
        reflector = Reflector(feedback)
        report = reflector.reflect()
        assert report.total_actions == 0
        assert "No feedback history" in report.recommendations[0]

    def test_reflect_success(self, tmp_path: Path):
        feedback = FeedbackLoop(log_dir=str(tmp_path))
        feedback.update("eval:auth.py:5", old_confidence=0.9, feedback_score=1.0)
        feedback.update("eval:auth.py:5", old_confidence=0.93, feedback_score=1.0)
        reflector = Reflector(feedback)
        report = reflector.reflect()
        assert report.total_actions == 2
        assert report.success_rate == 1.0
        assert report.false_positive_rate == 0.0

    def test_reflect_false_positives(self, tmp_path: Path):
        feedback = FeedbackLoop(log_dir=str(tmp_path))
        feedback.update("eval:auth.py:5", old_confidence=0.9, feedback_score=-0.5)
        feedback.update("eval:auth.py:5", old_confidence=0.63, feedback_score=-0.5)
        feedback.update("eval:auth.py:5", old_confidence=0.44, feedback_score=-0.5)
        reflector = Reflector(feedback)
        report = reflector.reflect()
        assert report.false_positive_rate == 1.0
        assert report.success_rate == 0.0
        assert len(report.top_false_positives) >= 1
        assert "skip" in report.top_false_positives[0]["recommendation"].lower()

    def test_reflect_mixed(self, tmp_path: Path):
        feedback = FeedbackLoop(log_dir=str(tmp_path))
        feedback.update("eval:auth.py:5", old_confidence=0.9, feedback_score=1.0)
        feedback.update("eval:auth.py:5", old_confidence=0.93, feedback_score=-0.5)
        reflector = Reflector(feedback)
        report = reflector.reflect()
        assert report.success_rate == 0.5
        assert report.false_positive_rate == 0.5
