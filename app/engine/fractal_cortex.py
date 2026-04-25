from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from app.engine.fractal_5whys import Fractal5WhysEngine, FractalNode, MetaAnalysisResult
from app.engine.fractal_patch_generator import FractalPatchGenerator, FractalPatch


@dataclass
class CortexDecision:
    """A decision produced by the Cortex (brain), executed by Hands."""

    finding: dict[str, Any]
    fractal_tree: dict[str, Any]
    meta_analysis: dict[str, Any]
    action_type: str  # "patch", "review", "ignore", "escalate"
    patches: list[dict[str, Any]] = field(default_factory=list)
    rationale: str = ""

    def to_dict(self) -> dict[str, Any]:
        return {
            "finding": self.finding,
            "fractal_tree": self.fractal_tree,
            "meta_analysis": self.meta_analysis,
            "action_type": self.action_type,
            "patches": self.patches,
            "rationale": self.rationale,
        }


class FractalCortex:
    """Pure reasoning layer — no filesystem access, no side effects.

    The Cortex:
    1. Receives a finding
    2. Builds fractal 5-Whys tree
    3. Runs meta-analysis
    4. Decides action type (patch/review/ignore/escalate)
    5. Generates patch plans (but does NOT apply them)

    Usage:
        cortex = FractalCortex()
        decision = cortex.decide(finding)
        # decision.action_type tells Hands what to do
    """

    def __init__(self, max_depth: int = 5, enable_counter_evidence: bool = True) -> None:
        self.engine = Fractal5WhysEngine(max_depth=max_depth, enable_counter_evidence=enable_counter_evidence)
        self.patch_generator = FractalPatchGenerator()

    def decide(self, finding: dict[str, Any]) -> CortexDecision:
        """Pure reasoning: analyze finding and decide action."""
        # Step 1: Fractal analysis
        tree = self.engine.analyze(finding)

        # Step 2: Meta-analysis
        meta = self.engine.meta_analyze(tree)

        # Step 3: Generate patches if recommended
        patches = []
        if meta.recommended_action == "patch":
            patches = [p.to_dict() for p in self.patch_generator.generate(finding, meta.to_dict())]

        return CortexDecision(
            finding=finding,
            fractal_tree=tree.to_dict(),
            meta_analysis=meta.to_dict(),
            action_type=meta.recommended_action,
            patches=patches,
            rationale=meta.rationale,
        )

    def batch_decide(self, findings: list[dict[str, Any]]) -> list[CortexDecision]:
        """Reason about multiple findings."""
        return [self.decide(f) for f in findings]
