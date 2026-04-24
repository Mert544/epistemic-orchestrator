from __future__ import annotations

import pytest

from scripts.apex_github_bot import build_comment


class TestGitHubBot:
    def test_build_comment_with_risks(self):
        result = {
            "risks": [
                {"severity": "critical", "issue": "eval() usage", "file": "app/auth.py", "line": 42},
                {"severity": "high", "issue": "bare except", "file": "app/main.py"},
            ]
        }
        comment = build_comment(result, "report")
        assert "eval() usage" in comment
        assert "app/auth.py" in comment
        assert "bare except" in comment
        assert "report" in comment

    def test_build_comment_no_risks(self):
        result = {"risks": []}
        comment = build_comment(result, "supervised")
        assert "No critical risks" in comment
        assert "supervised" in comment
