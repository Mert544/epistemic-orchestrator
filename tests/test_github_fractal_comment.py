from __future__ import annotations

from unittest.mock import patch, MagicMock

import pytest

from app.integrations.github_fractal_comment import GitHubFractalCommenter


class TestGitHubFractalCommenter:
    def test_post_fractal_summary(self):
        commenter = GitHubFractalCommenter(token="fake-token", repo="owner/repo")
        results = [
            {
                "agent": "fractal-security",
                "findings": [
                    {"issue": "eval() usage", "severity": "critical", "file": "auth.py"},
                ],
                "fractal_trees": [{"level": 1, "question": "Q?", "answer": "A.", "confidence": 1.0}],
                "meta_analyses": [
                    {"recommended_action": "patch", "rationale": "High confidence critical finding"},
                ],
            },
        ]

        with patch("urllib.request.urlopen") as mock_urlopen:
            mock_resp = MagicMock()
            mock_resp.read.return_value = b'{"id": 123}'
            mock_urlopen.return_value.__enter__.return_value = mock_resp
            resp = commenter.post_fractal_summary(pr_number=42, results=results)

        assert resp["id"] == 123
        mock_urlopen.assert_called_once()
        req = mock_urlopen.call_args[0][0]
        assert req.full_url == "https://api.github.com/repos/owner/repo/issues/42/comments"
        assert req.method == "POST"
        body = req.data.decode()
        assert "eval() usage" in body
        assert "PATCH" in body.upper()

    def test_post_comment(self):
        commenter = GitHubFractalCommenter(token="fake-token", repo="owner/repo")
        with patch("urllib.request.urlopen") as mock_urlopen:
            mock_resp = MagicMock()
            mock_resp.read.return_value = b'{"id": 456}'
            mock_urlopen.return_value.__enter__.return_value = mock_resp
            resp = commenter.post_comment(pr_number=1, body="Hello PR")
        assert resp["id"] == 456
