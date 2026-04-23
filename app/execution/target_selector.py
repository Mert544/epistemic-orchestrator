from __future__ import annotations

from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any


@dataclass
class RankedTarget:
    path: str
    score: float
    reasons: list[str] = field(default_factory=list)


@dataclass
class TargetSelectionResult:
    targets: list[RankedTarget] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {"targets": [asdict(target) for target in self.targets]}


class TargetSelector:
    """Choose the safest high-value file targets for semantic patching."""

    def select(
        self,
        project_root: str | Path,
        patch_plan: dict[str, Any],
        task: dict[str, Any] | None = None,
        project_profile: dict[str, Any] | None = None,
    ) -> TargetSelectionResult:
        root = Path(project_root).resolve()
        task = task or {}
        project_profile = project_profile or {}
        title = str(task.get("title") or patch_plan.get("title") or "").lower()
        suggested = list(dict.fromkeys(patch_plan.get("target_files", []) or task.get("suggested_files", []) or []))
        ranked: list[RankedTarget] = []

        for rel_path in suggested:
            target = root / rel_path
            lowered = rel_path.lower()
            score = 0.45
            reasons = ["Suggested by patch or task plan."]
            if target.exists():
                score += 0.2
                reasons.append("File exists in workspace.")
            else:
                score -= 0.1
                reasons.append("File does not exist yet.")
            suffix = target.suffix.lower()
            if suffix == ".py":
                score += 0.2
                reasons.append("Python file matches current semantic transforms.")
            elif suffix in {".md", ".txt"}:
                score += 0.05
                reasons.append("Text file is suitable for low-risk draft fallback.")
            else:
                score -= 0.05
                reasons.append("File type has limited semantic transform support.")
            if any(token in lowered for token in ("test", "spec")):
                score += 0.1
                reasons.append("Test-like target is lower risk for automated edits.")
            if any(token in title for token in ("test", "coverage")) and any(token in lowered for token in ("test", "spec")):
                score += 0.1
                reasons.append("Task title and file target both indicate test-related work.")
            if rel_path in project_profile.get("critical_untested_modules", []):
                score += 0.1
                reasons.append("File appears in critical untested modules.")
            if rel_path in project_profile.get("sensitive_paths", []):
                score -= 0.35
                reasons.append("Sensitive path detected; lower confidence for auto-edit.")
            ranked.append(RankedTarget(path=rel_path, score=round(max(score, 0.0), 4), reasons=reasons))

        if not ranked:
            for fallback in project_profile.get("critical_untested_modules", [])[:2]:
                ranked.append(RankedTarget(path=fallback, score=0.3, reasons=["Fallback target from project profile."]))

        ranked.sort(key=lambda item: item.score, reverse=True)
        return TargetSelectionResult(targets=ranked[:3])
