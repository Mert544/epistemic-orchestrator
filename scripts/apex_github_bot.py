#!/usr/bin/env python3
"""GitHub Actions bot for Apex Orchestrator.

Runs Apex on the PR codebase and posts findings as a comment.
Usage:
    python scripts/apex_github_bot.py --mode=report
"""
from __future__ import annotations

import argparse
import json
import os
import subprocess
import urllib.request


def run_apex(mode: str) -> dict:
    cmd = ["python", "-m", "app.cli", "run", "--goal=security audit", f"--mode={mode}"]
    result = subprocess.run(cmd, capture_output=True, text=True, timeout=300)
    # Parse JSON output if present
    for line in result.stdout.splitlines():
        if line.strip().startswith("{"):
            try:
                return json.loads(line)
            except json.JSONDecodeError:
                continue
    return {"stdout": result.stdout, "stderr": result.stderr, "returncode": result.returncode}


def post_pr_comment(body: str) -> bool:
    token = os.getenv("GITHUB_TOKEN")
    repo = os.getenv("GITHUB_REPOSITORY")
    pr_number = os.getenv("GITHUB_EVENT_NUMBER") or _extract_pr_number()
    if not all([token, repo, pr_number]):
        print("Missing GITHUB_TOKEN, GITHUB_REPOSITORY, or PR number")
        return False

    url = f"https://api.github.com/repos/{repo}/issues/{pr_number}/comments"
    req = urllib.request.Request(
        url,
        data=json.dumps({"body": body}).encode("utf-8"),
        headers={
            "Authorization": f"token {token}",
            "Content-Type": "application/json",
            "Accept": "application/vnd.github.v3+json",
        },
        method="POST",
    )
    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            return resp.status == 201
    except Exception as exc:
        print(f"Failed to post comment: {exc}")
        return False


def _extract_pr_number() -> str | None:
    # GITHUB_REF format: refs/pull/123/merge
    ref = os.getenv("GITHUB_REF", "")
    if ref.startswith("refs/pull/"):
        return ref.split("/")[2]
    return None


def build_comment(result: dict, mode: str) -> str:
    lines = ["## 🔍 Apex Orchestrator Review", ""]
    risks = result.get("risks", [])
    if risks:
        lines.append(f"**{len(risks)} risk(s) detected:**")
        for r in risks:
            severity = r.get("severity", "info")
            icon = "🔴" if severity == "critical" else "🟠" if severity == "high" else "🟡"
            lines.append(f"{icon} **{r.get('issue', 'Unknown')}** in `{r.get('file', '?')}`")
            if "line" in r:
                lines.append(f"   Line {r['line']}: `{r.get('snippet', '')}`")
    else:
        lines.append("✅ No critical risks detected.")

    lines.append("")
    lines.append(f"*Mode: `{mode}` | Powered by Apex Orchestrator*")
    return "\n".join(lines)


def main() -> int:
    parser = argparse.ArgumentParser(description="Apex GitHub Bot")
    parser.add_argument("--mode", default="report", choices=["report", "supervised"])
    args = parser.parse_args()

    print("[apex-bot] Running security audit...")
    result = run_apex(args.mode)

    comment = build_comment(result, args.mode)
    print("[apex-bot] Posting PR comment...")
    if post_pr_comment(comment):
        print("[apex-bot] Comment posted successfully.")
    else:
        print(comment)  # Fallback: print to CI log

    # Fail CI if critical risks found
    critical = sum(1 for r in result.get("risks", []) if r.get("severity") == "critical")
    if critical > 0:
        print(f"[apex-bot] {critical} critical risk(s) found — failing build.")
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
