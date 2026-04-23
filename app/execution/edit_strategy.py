from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any


@dataclass
class EditStrategyResult:
    strategy: str
    confidence: float
    reasons: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


class EditStrategy:
    """Choose a conservative semantic edit strategy from task + patch signals."""

    def choose(
        self,
        title: str,
        patch_plan: dict[str, Any],
        related_tests: list[str] | None = None,
        repair_context: dict[str, Any] | None = None,
    ) -> EditStrategyResult:
        title_lower = (title or "").lower()
        strategy_text = " ".join(patch_plan.get("change_strategy", [])).lower()
        combined = f"{title_lower} {strategy_text}"
        related_tests = related_tests or []
        repair_context = repair_context or {}
        reasons: list[str] = []

        failure_type = str(repair_context.get("failure_type", ""))
        if failure_type == "test_failure":
            reasons.append("Repair context indicates a test failure.")
            return EditStrategyResult(strategy="repair_test_assertion", confidence=0.8, reasons=reasons)
        if failure_type == "patch_scope_failure":
            reasons.append("Repair context indicates scope reduction is needed.")
            return EditStrategyResult(strategy="add_docstring", confidence=0.6, reasons=reasons)

        if patch_plan.get("rename"):
            reasons.append("Patch plan includes explicit rename configuration.")
            return EditStrategyResult(strategy="rename_variable", confidence=0.9, reasons=reasons)
        if patch_plan.get("extract"):
            reasons.append("Patch plan includes explicit extract-method configuration.")
            return EditStrategyResult(strategy="extract_method", confidence=0.9, reasons=reasons)
        if patch_plan.get("inline"):
            reasons.append("Patch plan includes explicit inline-variable configuration.")
            return EditStrategyResult(strategy="inline_variable", confidence=0.85, reasons=reasons)
        if patch_plan.get("move"):
            reasons.append("Patch plan includes explicit move-class configuration.")
            return EditStrategyResult(strategy="move_class", confidence=0.85, reasons=reasons)
        if patch_plan.get("extract_class"):
            reasons.append("Patch plan includes explicit extract-class configuration.")
            return EditStrategyResult(strategy="extract_class", confidence=0.85, reasons=reasons)

        if any(token in combined for token in ("import", "unused import", "cleanup import", "organize import")):
            reasons.append("Task text suggests import cleanup.")
            return EditStrategyResult(strategy="organize_imports", confidence=0.7, reasons=reasons)
        if any(token in combined for token in ("guard", "validate", "input", "security")):
            reasons.append("Task text suggests validation or guard behavior.")
            return EditStrategyResult(strategy="add_guard_clause", confidence=0.75, reasons=reasons)
        if any(token in combined for token in ("type", "typing", "annotation")):
            reasons.append("Task text suggests typing improvements.")
            return EditStrategyResult(strategy="add_type_annotations", confidence=0.7, reasons=reasons)
        if any(token in combined for token in ("docstring", "document", "documentation")):
            reasons.append("Task text suggests documentation improvements.")
            return EditStrategyResult(strategy="add_docstring", confidence=0.7, reasons=reasons)
        if any(token in combined for token in ("test", "coverage")) and related_tests:
            reasons.append("Task text suggests testing and related tests were found.")
            return EditStrategyResult(strategy="repair_test_assertion", confidence=0.65, reasons=reasons)

        reasons.append("No explicit semantic strategy matched; using conservative default.")
        return EditStrategyResult(strategy="add_docstring", confidence=0.5, reasons=reasons)
