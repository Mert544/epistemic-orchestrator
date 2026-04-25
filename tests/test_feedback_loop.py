from __future__ import annotations

from pathlib import Path

import pytest

from app.engine.feedback_loop import FeedbackLoop


class TestFeedbackLoop:
    def test_update_confidence(self, tmp_path: Path):
        loop = FeedbackLoop(alpha=0.3, log_dir=str(tmp_path))
        new_conf = loop.update("eval:auth.py:5", old_confidence=0.9, feedback_score=1.0)
        # 0.9 * 0.7 + 1.0 * 0.3 = 0.93
        assert abs(new_conf - 0.93) < 0.001

    def test_negative_feedback_lowers_confidence(self, tmp_path: Path):
        loop = FeedbackLoop(alpha=0.3, log_dir=str(tmp_path))
        new_conf = loop.update("eval:auth.py:5", old_confidence=0.9, feedback_score=-0.5)
        # 0.9 * 0.7 + (-0.5) * 0.3 = 0.63 - 0.15 = 0.48
        assert abs(new_conf - 0.48) < 0.001

    def test_clamping(self, tmp_path: Path):
        loop = FeedbackLoop(alpha=0.3, log_dir=str(tmp_path))
        new_conf = loop.update("x", old_confidence=0.1, feedback_score=-1.0)
        assert new_conf >= 0.0
        new_conf = loop.update("y", old_confidence=0.9, feedback_score=2.0)
        assert new_conf <= 1.0

    def test_history(self, tmp_path: Path):
        loop = FeedbackLoop(alpha=0.3, log_dir=str(tmp_path))
        loop.update("eval:auth.py:5", old_confidence=0.9, feedback_score=1.0)
        loop.update("eval:auth.py:5", old_confidence=0.93, feedback_score=-0.5)
        history = loop.get_history("eval:auth.py:5")
        assert len(history) == 2

    def test_should_skip(self, tmp_path: Path):
        loop = FeedbackLoop(alpha=0.3, log_dir=str(tmp_path))
        loop.update("bad", old_confidence=0.9, feedback_score=-0.5)
        loop.update("bad", old_confidence=0.63, feedback_score=-0.5)
        assert loop.should_skip("bad", threshold=-0.2) is True
        assert loop.should_skip("good", threshold=-0.2) is False

    def test_persistence(self, tmp_path: Path):
        loop = FeedbackLoop(alpha=0.3, log_dir=str(tmp_path))
        loop.update("x", old_confidence=0.5, feedback_score=1.0)
        loop2 = FeedbackLoop(alpha=0.3, log_dir=str(tmp_path))
        assert len(loop2.entries) == 1
