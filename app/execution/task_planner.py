from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any


@dataclass
class EngineeringTask:
    id: str
    title: str
    rationale: str
    priority: float
    branch: str | None = None
    suggested_files: list[str] = field(default_factory=list)
    acceptance_criteria: list[str] = field(default_factory=list)


@dataclass
class TaskPlannerResult:
    tasks: list[EngineeringTask] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {"tasks": [asdict(task) for task in self.tasks]}


class TaskPlanner:
    def plan(self, report: dict[str, Any]) -> TaskPlannerResult:
        branch_map = report.get("branch_map", {}) or {}
        claim_types = report.get("claim_types", {}) or {}
        claim_priorities = report.get("claim_priorities", {}) or {}
        recommended_actions = report.get("recommended_actions", []) or []
        key_risks = report.get("key_risks", []) or []

        tasks: list[EngineeringTask] = []
        for idx, (branch, claim) in enumerate(branch_map.items()):
            priority = float(claim_priorities.get(claim, 0.5))
            claim_type = str(claim_types.get(claim, "general"))
            rationale = self._build_rationale(claim, claim_type, key_risks)
            suggested_files = self._infer_files(claim, recommended_actions)
            acceptance = self._acceptance_for_type(claim_type)
            tasks.append(
                EngineeringTask(
                    id=f"task-{idx}",
                    title=self._title_for_claim(claim),
                    rationale=rationale,
                    priority=priority,
                    branch=branch,
                    suggested_files=suggested_files,
                    acceptance_criteria=acceptance,
                )
            )

        tasks.sort(key=lambda task: task.priority, reverse=True)
        return TaskPlannerResult(tasks=tasks[:8])

    def _title_for_claim(self, claim: str) -> str:
        lowered = claim.lower()
        if "dependency hub" in lowered:
            return "Reduce dependency hub pressure"
        if "untested" in lowered or "testing gap" in lowered:
            return "Close critical test gaps"
        if "sensitive" in lowered or "security" in lowered:
            return "Harden sensitive surface"
        if "config" in lowered:
            return "Stabilize configuration surface"
        return f"Investigate and improve: {claim[:80]}"

    def _build_rationale(self, claim: str, claim_type: str, key_risks: list[str]) -> str:
        risk_hint = key_risks[0] if key_risks else "No explicit risk summary was captured yet."
        return f"Claim type: {claim_type}. Prioritize because: {claim}. Risk context: {risk_hint}"

    def _infer_files(self, claim: str, recommended_actions: list[str]) -> list[str]:
        lowered = claim.lower()
        files: list[str] = []
        for action in recommended_actions:
            for token in action.replace(",", " ").split():
                if "/" in token and "." in token:
                    files.append(token.strip(".`'\""))
        if "order_service" in lowered:
            files.append("app/services/order_service.py")
        if "auth" in lowered or "token" in lowered:
            files.append("app/auth/token_service.py")
        if "payment" in lowered:
            files.append("app/payments/gateway.py")
        return list(dict.fromkeys(files))[:5]

    def _acceptance_for_type(self, claim_type: str) -> list[str]:
        defaults = ["Change scope is documented", "Verification command is identified"]
        if claim_type == "validation":
            return [*defaults, "Relevant tests exist or are added", "pytest or equivalent passes"]
        if claim_type == "security":
            return [*defaults, "Sensitive paths are reviewed", "Patch scope passes safety checks"]
        if claim_type == "architecture":
            return [*defaults, "Target coupling point is reduced or documented"]
        return defaults
