from __future__ import annotations

from pathlib import Path

import pytest

from app.engine.fractal_cross_run import FractalCrossRunBridge


class TestFractalCrossRunBridge:
    def test_record_and_recall(self, tmp_path: Path):
        bridge = FractalCrossRunBridge(tmp_path)
        findings = [
            {"issue": "eval() usage", "file": "auth.py", "severity": "critical"},
            {"issue": "missing_docstring", "file": "utils.py", "severity": "low"},
        ]
        bridge.record_findings(run_id="run-1", findings=findings)
        prompt = bridge.build_recall_prompt()
        assert "eval() usage" in prompt
        assert "auth.py" in prompt

    def test_persistent_findings(self, tmp_path: Path):
        bridge = FractalCrossRunBridge(tmp_path)
        findings = [
            {"issue": "eval() usage", "file": "auth.py", "severity": "critical"},
        ]
        bridge.record_findings(run_id="run-1", findings=findings)
        bridge.record_findings(run_id="run-2", findings=findings)
        persistent = bridge.get_persistent_findings()
        assert len(persistent) >= 1
        assert persistent[0]["run_count"] >= 2

    def test_mark_resolved(self, tmp_path: Path):
        bridge = FractalCrossRunBridge(tmp_path)
        findings = [
            {"issue": "eval() usage", "file": "auth.py", "severity": "critical"},
        ]
        bridge.record_findings(run_id="run-1", findings=findings)
        bridge.mark_resolved("eval() usage in auth.py")
        persistent = bridge.get_persistent_findings()
        assert all(p["status"] != "resolved" for p in persistent)
