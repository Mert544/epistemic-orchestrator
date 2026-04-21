from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Any

from app.skills.repair.analyze_failure_log import AnalyzeFailureLogSkill
from app.skills.repair.repair_failed_test import RepairFailedTestSkill


@dataclass
class RepairLoopResult:
    failure_analysis: dict[str, Any]
    repair_suggestion: dict[str, Any]

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


class RepairLoop:
    def __init__(self) -> None:
        self.failure_analyzer = AnalyzeFailureLogSkill()
        self.repair_planner = RepairFailedTestSkill()

    def run(self, verification: dict[str, Any], patch_plan: dict[str, Any] | None = None) -> RepairLoopResult:
        analysis = self.failure_analyzer.run(verification).to_dict()
        suggestion = self.repair_planner.run(analysis, patch_plan).to_dict()
        return RepairLoopResult(
            failure_analysis=analysis,
            repair_suggestion=suggestion,
        )
