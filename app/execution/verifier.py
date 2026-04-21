from __future__ import annotations

from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any

from app.skills.execution.run_tests import RunTestsSkill
from app.skills.safety.check_patch_scope import CheckPatchScopeSkill
from app.skills.safety.detect_sensitive_edit import DetectSensitiveEditSkill


@dataclass
class VerificationSummary:
    ok: bool
    project_root: str
    test_summary: dict[str, Any] = field(default_factory=dict)
    patch_scope: dict[str, Any] = field(default_factory=dict)
    sensitive_edit: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


class Verifier:
    def __init__(self) -> None:
        self.test_runner = RunTestsSkill()
        self.patch_scope_checker = CheckPatchScopeSkill()
        self.sensitive_detector = DetectSensitiveEditSkill()

    def verify(self, project_root: str | Path, changed_files: list[str] | None = None) -> VerificationSummary:
        changed = changed_files or []
        test_summary = self.test_runner.run(project_root)
        patch_scope = self.patch_scope_checker.run(changed_files=changed)
        sensitive = self.sensitive_detector.run(changed_files=changed)

        return VerificationSummary(
            ok=test_summary.ok and patch_scope.ok and sensitive.ok,
            project_root=str(Path(project_root).resolve()),
            test_summary={
                "project_root": test_summary.project_root,
                "commands": test_summary.commands,
                "results": test_summary.results,
                "ok": test_summary.ok,
            },
            patch_scope={
                "ok": patch_scope.ok,
                "changed_file_count": patch_scope.changed_file_count,
                "max_allowed_files": patch_scope.max_allowed_files,
                "touched_sensitive_paths": patch_scope.touched_sensitive_paths,
                "reasons": patch_scope.reasons,
            },
            sensitive_edit={
                "ok": sensitive.ok,
                "touched_sensitive_paths": sensitive.touched_sensitive_paths,
                "detected_hints": sensitive.detected_hints,
            },
        )
