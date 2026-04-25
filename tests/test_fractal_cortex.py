from __future__ import annotations

from pathlib import Path

import pytest

from app.engine.fractal_cortex import FractalCortex, CortexDecision


class TestFractalCortex:
    def test_decide_eval_finding(self):
        cortex = FractalCortex(max_depth=3)
        finding = {"issue": "eval() usage", "file": "auth.py", "severity": "critical"}
        decision = cortex.decide(finding)
        assert decision.action_type == "patch"
        assert len(decision.patches) >= 1
        assert decision.fractal_tree["level"] == 1

    def test_decide_missing_docstring(self):
        cortex = FractalCortex(max_depth=3)
        finding = {"issue": "missing_docstring", "file": "utils.py", "severity": "low"}
        decision = cortex.decide(finding)
        assert decision.action_type in ("patch", "review", "escalate")
        assert decision.fractal_tree["level"] == 1

    def test_batch_decide(self):
        cortex = FractalCortex(max_depth=3)
        findings = [
            {"issue": "eval() usage", "file": "a.py", "severity": "critical"},
            {"issue": "missing_docstring", "file": "b.py", "severity": "low"},
        ]
        decisions = cortex.batch_decide(findings)
        assert len(decisions) == 2
        assert all(isinstance(d, CortexDecision) for d in decisions)

    def test_cortex_no_side_effects(self, tmp_path: Path):
        """Cortex should never modify files."""
        cortex = FractalCortex(max_depth=3)
        test_file = tmp_path / "test.py"
        test_file.write_text("x = eval(y)\n")
        finding = {"issue": "eval() usage", "file": str(test_file), "severity": "critical"}
        decision = cortex.decide(finding)
        # File should be unchanged
        assert test_file.read_text() == "x = eval(y)\n"
