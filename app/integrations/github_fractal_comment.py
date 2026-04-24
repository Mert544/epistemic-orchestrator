from __future__ import annotations

import json
import os
import urllib.request
from typing import Any


class GitHubFractalCommenter:
    """Post fractal analysis results as GitHub PR comments.

    Uses only stdlib (urllib) — no external dependencies.

    Usage:
        commenter = GitHubFractalCommenter()
        commenter.post_fractal_summary(pr_number=42, results=[...])
    """

    def __init__(self, token: str | None = None, repo: str | None = None) -> None:
        self.token = token or os.environ.get("GITHUB_TOKEN", "")
        self.repo = repo or os.environ.get("GITHUB_REPOSITORY", "")
        self.base_url = f"https://api.github.com/repos/{self.repo}"

    def _request(self, method: str, path: str, data: dict[str, Any] | None = None) -> dict[str, Any]:
        url = f"{self.base_url}{path}"
        headers = {
            "Accept": "application/vnd.github+json",
            "Authorization": f"Bearer {self.token}",
            "X-GitHub-Api-Version": "2022-11-28",
        }
        body = json.dumps(data).encode() if data else None
        req = urllib.request.Request(url, data=body, headers=headers, method=method)
        with urllib.request.urlopen(req, timeout=30) as resp:
            return json.loads(resp.read().decode())

    def post_fractal_summary(self, pr_number: int, results: list[dict[str, Any]]) -> dict[str, Any]:
        """Post a markdown summary of fractal analysis to a PR."""
        lines = ["## 🔬 Apex Fractal Analysis", ""]
        for result in results:
            agent = result.get("agent", "unknown")
            findings = result.get("findings", [])
            trees = result.get("fractal_trees", [])
            lines.append(f"### {agent}")
            lines.append(f"- **Findings:** {len(findings)}")
            lines.append(f"- **Fractal trees:** {len(trees)}")
            for f in findings:
                sev = f.get("severity", "info")
                icon = "🔴" if sev == "critical" else "🟠" if sev == "high" else "🟡"
                lines.append(f"{icon} **{f.get('issue', 'Unknown')}** — `{f.get('file', '?')}`")
            for meta in result.get("meta_analyses", []):
                action = meta.get("recommended_action", "unknown")
                icon = "✅" if action == "patch" else "⚠️" if action == "review" else "❌"
                lines.append(f"{icon} Meta-action: **{action.upper()}** — {meta.get('rationale', '')}")
            lines.append("")

        body = "\n".join(lines)
        return self._request("POST", f"/issues/{pr_number}/comments", {"body": body})

    def post_comment(self, pr_number: int, body: str) -> dict[str, Any]:
        """Post a raw comment to a PR."""
        return self._request("POST", f"/issues/{pr_number}/comments", {"body": body})
