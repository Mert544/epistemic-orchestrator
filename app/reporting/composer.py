from __future__ import annotations

import json
import time
from pathlib import Path
from typing import Any


class ReportComposer:
    """Compose human-readable reports from Apex agent results.

    Supports Markdown and HTML output.

    Usage:
        composer = ReportComposer(results)
        composer.to_markdown("report.md")
        composer.to_html("report.html")
    """

    def __init__(self, results: list[dict[str, Any]]) -> None:
        self.results = results
        self.timestamp = time.strftime("%Y-%m-%d %H:%M:%S")

    def to_markdown(self, path: str | Path | None = None) -> str:
        lines = [
            "# Apex Orchestrator Report",
            f"**Generated:** {self.timestamp}",
            f"**Results:** {len(self.results)} agent(s)",
            "",
        ]
        for result in self.results:
            agent_name = result.get("agent", "unknown")
            findings = result.get("findings", [])
            lines.append(f"## {agent_name}")
            lines.append(f"- **Findings:** {len(findings)}")
            for f in findings:
                sev = f.get("severity", "info")
                icon = "🔴" if sev == "critical" else "🟠" if sev == "high" else "🟡"
                lines.append(f"{icon} **{f.get('issue', 'Unknown')}** — `{f.get('file', '?')}`")
                if "suggestion" in f:
                    lines.append(f"   💡 {f['suggestion']}")
            lines.append("")

        md = "\n".join(lines)
        if path:
            Path(path).write_text(md, encoding="utf-8")
        return md

    def to_html(self, path: str | Path | None = None) -> str:
        findings_html = []
        for result in self.results:
            agent_name = result.get("agent", "unknown")
            findings = result.get("findings", [])
            for f in findings:
                sev = f.get("severity", "info")
                color = "#dc2626" if sev == "critical" else "#ea580c" if sev == "high" else "#ca8a04"
                findings_html.append(f"""
                <div style="margin:0.5rem 0;padding:0.75rem;border-left:4px solid {color};background:#f9fafb;">
                    <div style="font-weight:600;color:{color};">{f.get('issue', 'Unknown')}</div>
                    <div style="color:#666;font-size:0.9rem;">{f.get('file', '?')}</div>
                    <div style="color:#059669;font-size:0.85rem;margin-top:0.25rem;">{f.get('suggestion', '')}</div>
                </div>
                """)

        html = f"""<!doctype html>
<html><head><meta charset="utf-8"><title>Apex Report</title></head>
<body style="font-family:system-ui,sans-serif;max-width:800px;margin:2rem auto;padding:0 1rem;">
<h1>Apex Orchestrator Report</h1>
<p style="color:#666;">Generated: {self.timestamp} | Agents: {len(self.results)}</p>
{''.join(findings_html) if findings_html else '<p style="color:#666;">No findings.</p>'}
</body></html>"""

        if path:
            Path(path).write_text(html, encoding="utf-8")
        return html

    def to_sarif(self, path: str | Path | None = None) -> dict[str, Any]:
        """Export as SARIF for GitHub Code Scanning integration."""
        rules = []
        results_sarif = []
        rule_index = {}

        for result in self.results:
            for f in result.get("findings", []):
                rule_id = f.get("issue", "unknown").replace(" ", "_").lower()[:40]
                if rule_id not in rule_index:
                    rule_index[rule_id] = len(rules)
                    rules.append({
                        "id": rule_id,
                        "name": f.get("issue", "Unknown"),
                        "shortDescription": {"text": f.get("issue", "Unknown")},
                    })
                results_sarif.append({
                    "ruleId": rule_id,
                    "level": "error" if f.get("severity") in ("critical", "high") else "warning",
                    "message": {"text": f.get("suggestion", f.get("issue", ""))},
                    "locations": [{
                        "physicalLocation": {
                            "artifactLocation": {"uri": f.get("file", "unknown")},
                        }
                    }],
                })

        sarif = {
            "$schema": "https://raw.githubusercontent.com/oasis-tcs/sarif-spec/master/Schemata/sarif-schema-2.1.0.json",
            "version": "2.1.0",
            "runs": [{
                "tool": {"driver": {"name": "Apex Orchestrator"}},
                "results": results_sarif,
                "rules": rules,
            }],
        }
        if path:
            Path(path).write_text(json.dumps(sarif, indent=2), encoding="utf-8")
        return sarif
