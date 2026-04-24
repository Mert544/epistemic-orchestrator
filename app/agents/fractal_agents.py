from __future__ import annotations

from typing import Any

from app.agents.base import Agent, AgentMessage
from app.agents.recursive import RecursiveAgent
from app.engine.fractal_5whys import Fractal5WhysEngine


class FractalSecurityAgent(RecursiveAgent):
    """Security agent with fractal deep-analysis capability.

    When a finding is detected, spawns a FractalAnalyzer sub-agent
    that performs 5-level 'Why?' analysis on the finding.

    Usage:
        agent = FractalSecurityAgent(bus=agent_bus)
        result = agent.run(project_root=".", max_depth=5)
    """

    def __init__(self, name: str = "fractal-security", bus=None, context=None) -> None:
        super().__init__(name=name, role="fractal_security_auditor", bus=bus, context=context)
        self.fractal_engine = Fractal5WhysEngine(max_depth=5)
        self.max_fractal_budget = 10  # Max findings to fractally analyze per run

    def _execute(self, project_root: str = ".", max_depth: int = 5, **kwargs: Any) -> dict[str, Any]:
        from app.agents.skills import SecurityAgent

        # Phase 1: Standard security scan
        scanner = SecurityAgent()
        scan_result = scanner.run(project_root=project_root)
        findings = scan_result.get("findings", [])

        # Phase 2: Fractal deep-analysis for top findings
        fractal_trees = []
        budget = min(len(findings), self.max_fractal_budget)

        for finding in findings[:budget]:
            # Spawn sub-agent for fractal analysis
            sub = self.spawn_fractal_analyzer(finding, max_depth)
            if sub:
                fractal_trees.append(sub.to_dict())

        return {
            "agent": self.name,
            "role": self.role,
            "scanned_files": scan_result.get("scanned_files", 0),
            "findings_count": len(findings),
            "fractal_analyzed": len(fractal_trees),
            "findings": findings,
            "fractal_trees": fractal_trees,
        }

    def spawn_fractal_analyzer(self, finding: dict[str, Any], max_depth: int) -> Any:
        """Spawn a sub-agent that performs fractal 5-whys analysis."""
        engine = Fractal5WhysEngine(max_depth=max_depth)
        tree = engine.analyze(finding)

        # Broadcast fractal analysis complete
        if self.bus:
            self.bus.broadcast(
                sender=self.name,
                topic="fractal.analysis.complete",
                payload={
                    "finding": finding,
                    "tree_depth": max_depth,
                    "root_question": tree.question,
                },
            )

        return tree


class FractalAnalyzerAgent(Agent):
    """Dedicated sub-agent for fractal analysis of a single finding."""

    def __init__(self, name: str, finding: dict[str, Any], max_depth: int = 5, **kwargs: Any) -> None:
        super().__init__(name=name, role="fractal_analyzer", **kwargs)
        self.finding = finding
        self.max_depth = max_depth
        self.engine = Fractal5WhysEngine(max_depth=max_depth)

    def _execute(self, **kwargs: Any) -> dict[str, Any]:
        tree = self.engine.analyze(self.finding)
        return {
            "agent": self.name,
            "finding": self.finding,
            "fractal_tree": tree.to_dict(),
            "depth": self.max_depth,
        }
