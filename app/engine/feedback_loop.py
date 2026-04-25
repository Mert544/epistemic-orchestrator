from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any


@dataclass
class FeedbackEntry:
    """A single feedback event."""

    node_key: str  # "issue:file:line" format
    old_confidence: float
    feedback_score: float  # +1.0 success, -0.5 failure
    new_confidence: float
    timestamp: str
    action_type: str

    def to_dict(self) -> dict[str, Any]:
        return {
            "node_key": self.node_key,
            "old_confidence": self.old_confidence,
            "feedback_score": self.feedback_score,
            "new_confidence": self.new_confidence,
            "timestamp": self.timestamp,
            "action_type": self.action_type,
        }


class FeedbackLoop:
    """Closed-loop feedback: action results update fractal node confidence.

    Uses Exponential Moving Average (EMA) with configurable alpha.

    Usage:
        loop = FeedbackLoop()
        new_conf = loop.update("eval:auth.py:5", old_conf=0.9, score=1.0)
        # new_conf = 0.9 * 0.7 + 1.0 * 0.3 = 0.93
    """

    def __init__(self, alpha: float = 0.3, log_dir: str = ".apex") -> None:
        self.alpha = alpha
        self.log_path = Path(log_dir) / "feedback_log.json"
        self.log_path.parent.mkdir(parents=True, exist_ok=True)
        self.entries: list[FeedbackEntry] = []
        self._load()

    def _load(self) -> None:
        if self.log_path.exists():
            try:
                data = json.loads(self.log_path.read_text(encoding="utf-8"))
                self.entries = [FeedbackEntry(**e) for e in data.get("entries", [])]
            except Exception:
                self.entries = []

    def _save(self) -> None:
        self.log_path.write_text(
            json.dumps({"entries": [e.to_dict() for e in self.entries]}, indent=2),
            encoding="utf-8",
        )

    def update(self, node_key: str, old_confidence: float, feedback_score: float, action_type: str = "") -> float:
        """Update confidence with EMA. Returns new confidence."""
        import time
        new_confidence = old_confidence * (1 - self.alpha) + feedback_score * self.alpha
        # Clamp to [0, 1]
        new_confidence = max(0.0, min(1.0, new_confidence))

        entry = FeedbackEntry(
            node_key=node_key,
            old_confidence=old_confidence,
            feedback_score=feedback_score,
            new_confidence=new_confidence,
            timestamp=time.strftime("%Y-%m-%d %H:%M:%S"),
            action_type=action_type,
        )
        self.entries.append(entry)
        self._save()
        return new_confidence

    def get_history(self, node_key: str) -> list[FeedbackEntry]:
        """Get feedback history for a specific node."""
        return [e for e in self.entries if e.node_key == node_key]

    def get_average_feedback(self, node_key: str) -> float:
        """Get average feedback score for a node."""
        history = self.get_history(node_key)
        if not history:
            return 0.0
        return sum(e.feedback_score for e in history) / len(history)

    def should_skip(self, node_key: str, threshold: float = -0.2) -> bool:
        """Return True if this node consistently gets negative feedback."""
        avg = self.get_average_feedback(node_key)
        return avg < threshold
