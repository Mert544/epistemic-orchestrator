from __future__ import annotations

from pathlib import Path

import pytest

from app.reporting.composer import ReportComposer


class TestReportComposer:
    def test_to_markdown(self, tmp_path: Path):
        results = [
            {"agent": "security", "findings": [
                {"issue": "eval() usage", "severity": "critical", "file": "app/auth.py", "suggestion": "Use ast.literal_eval"},
            ]},
        ]
        composer = ReportComposer(results)
        md = composer.to_markdown(tmp_path / "report.md")
        assert "eval() usage" in md
        assert "app/auth.py" in md
        assert (tmp_path / "report.md").exists()

    def test_to_html(self, tmp_path: Path):
        results = [
            {"agent": "security", "findings": [
                {"issue": "eval() usage", "severity": "critical", "file": "app/auth.py"},
            ]},
        ]
        composer = ReportComposer(results)
        html = composer.to_html(tmp_path / "report.html")
        assert "eval() usage" in html
        assert "#dc2626" in html  # critical color
        assert (tmp_path / "report.html").exists()

    def test_to_sarif(self, tmp_path: Path):
        results = [
            {"agent": "security", "findings": [
                {"issue": "eval() usage", "severity": "critical", "file": "app/auth.py", "suggestion": "fix it"},
            ]},
        ]
        composer = ReportComposer(results)
        sarif = composer.to_sarif(tmp_path / "report.sarif")
        assert sarif["version"] == "2.1.0"
        assert len(sarif["runs"][0]["results"]) == 1
        assert (tmp_path / "report.sarif").exists()

    def test_empty_results(self):
        composer = ReportComposer([])
        md = composer.to_markdown()
        assert "No findings" not in md  # Just empty sections
        html = composer.to_html()
        assert "No findings" in html
