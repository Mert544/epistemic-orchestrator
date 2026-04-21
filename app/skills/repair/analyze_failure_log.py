from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any


@dataclass
class FailureAnalysis:
    primary_failure_type: str
    failing_commands: list[list[str]] = field(default_factory=list)
    summary: list[str] = field(default_factory=list)
    recommended_next_step: str = ""

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


class AnalyzeFailureLogSkill:
    def run(self, verification: dict[str, Any]) -> FailureAnalysis:
        test_summary = verification.get("test_summary", {}) or {}
        patch_scope = verification.get("patch_scope", {}) or {}
        sensitive_edit = verification.get("sensitive_edit", {}) or {}

        failing_commands: list[list[str]] = []
        for result in test_summary.get("results", []) or []:
            if not result.get("ok", False):
                failing_commands.append(list(result.get("command", [])))

        if not test_summary.get("ok", True):
            summary = [
                "Detected failing verification commands.",
                *[
                    f"Command failed: {' '.join(cmd)}"
                    for cmd in failing_commands
                ],
            ]
            return FailureAnalysis(
                primary_failure_type="test_failure",
                failing_commands=failing_commands,
                summary=summary,
                recommended_next_step="Inspect test output and generate a minimal repair patch or targeted regression test.",
            )

        if not patch_scope.get("ok", True):
            return FailureAnalysis(
                primary_failure_type="patch_scope_failure",
                failing_commands=[],
                summary=list(patch_scope.get("reasons", []) or ["Patch scope failed policy checks."]),
                recommended_next_step="Reduce the changed file set or split the task into smaller, auditable edits.",
            )

        if not sensitive_edit.get("ok", True):
            touched = sensitive_edit.get("touched_sensitive_paths", []) or []
            return FailureAnalysis(
                primary_failure_type="sensitive_edit",
                failing_commands=[],
                summary=[
                    "Sensitive paths were touched during planning or verification.",
                    *[f"Sensitive path: {path}" for path in touched],
                ],
                recommended_next_step="Require extra review, tighten scope, or avoid sensitive paths in the first patch.",
            )

        return FailureAnalysis(
            primary_failure_type="no_failure_detected",
            failing_commands=[],
            summary=["No failure detected in verification output."],
            recommended_next_step="Continue with supervised patch application or manual review.",
        )
