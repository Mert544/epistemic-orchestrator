from __future__ import annotations

from dataclasses import dataclass


@dataclass
class PatchScopeResult:
    ok: bool
    changed_file_count: int
    max_allowed_files: int
    touched_sensitive_paths: list[str]
    reasons: list[str]


class CheckPatchScopeSkill:
    DEFAULT_SENSITIVE_HINTS = (
        "auth",
        "payment",
        "secret",
        "token",
        "credential",
        "billing",
        ".github/workflows",
    )

    def run(
        self,
        changed_files: list[str],
        max_allowed_files: int = 5,
        sensitive_hints: tuple[str, ...] | None = None,
    ) -> PatchScopeResult:
        hints = sensitive_hints or self.DEFAULT_SENSITIVE_HINTS
        touched_sensitive = [
            path for path in changed_files if any(hint in path.lower() for hint in hints)
        ]

        reasons: list[str] = []
        if len(changed_files) > max_allowed_files:
            reasons.append(
                f"Patch scope too large: {len(changed_files)} files changed, max allowed is {max_allowed_files}."
            )
        if touched_sensitive:
            reasons.append(
                "Patch touches sensitive paths and should require extra review."
            )

        return PatchScopeResult(
            ok=not reasons,
            changed_file_count=len(changed_files),
            max_allowed_files=max_allowed_files,
            touched_sensitive_paths=touched_sensitive,
            reasons=reasons,
        )
