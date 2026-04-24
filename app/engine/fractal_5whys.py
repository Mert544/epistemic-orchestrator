from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass
class FractalNode:
    """A single node in the fractal analysis tree.

    Each node represents one 'Why?' answer, spawning deeper nodes.
    """

    level: int
    question: str
    answer: str
    confidence: float
    evidence: list[str] = field(default_factory=list)
    children: list["FractalNode"] = field(default_factory=list)
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return {
            "level": self.level,
            "question": self.question,
            "answer": self.answer,
            "confidence": self.confidence,
            "evidence": self.evidence,
            "children": [c.to_dict() for c in self.children],
            "metadata": self.metadata,
        }


class Fractal5WhysEngine:
    """Recursively ask 'Why?' up to 5 levels deep for every finding.

    This is the core of Apex's fractal intelligence:
    - Level 1: What is the risk? (surface)
    - Level 2: Why does it exist? (cause)
    - Level 3: Why was it introduced? (origin)
    - Level 4: Why wasn't it caught? (process gap)
    - Level 5: Why does the system allow it? (architecture gap)

    Usage:
        engine = Fractal5WhysEngine(max_depth=5)
        tree = engine.analyze(finding={"issue": "eval() usage", "file": "auth.py"})
        # tree is a FractalNode with 5 levels of children
    """

    def __init__(self, max_depth: int = 5, min_confidence: float = 0.3) -> None:
        self.max_depth = max_depth
        self.min_confidence = min_confidence

    def analyze(self, finding: dict[str, Any]) -> FractalNode:
        """Build a fractal analysis tree for a single finding."""
        issue = finding.get("issue", "Unknown issue")
        file = finding.get("file", "unknown")
        severity = finding.get("severity", "info")

        root = FractalNode(
            level=1,
            question=f"What is the risk: {issue}?",
            answer=f"{severity.upper()} severity issue in {file}",
            confidence=1.0,
            evidence=[f"Detected in {file}"],
            metadata={"finding": finding},
        )

        self._deepen(root, finding)
        return root

    def _deepen(self, parent: FractalNode, finding: dict[str, Any]) -> None:
        """Recursively spawn deeper 'Why?' nodes."""
        if parent.level >= self.max_depth:
            return

        next_level = parent.level + 1
        generators = [
            self._why_exists,
            self._why_introduced,
            self._why_missed,
            self._why_allowed,
        ]

        if next_level - 2 < len(generators):
            generator = generators[next_level - 2]
            child = generator(next_level, finding, parent)
            if child.confidence >= self.min_confidence:
                parent.children.append(child)
                self._deepen(child, finding)

    def _why_exists(self, level: int, finding: dict[str, Any], parent: FractalNode) -> FractalNode:
        """Level 2: Why does this risk exist?"""
        issue = finding.get("issue", "")
        if "eval" in issue.lower():
            return FractalNode(
                level=level,
                question="Why does eval() exist in this code?",
                answer="Developer used dynamic execution instead of safer alternatives",
                confidence=0.9,
                evidence=["eval() allows arbitrary code execution"],
            )
        elif "os.system" in issue.lower():
            return FractalNode(
                level=level,
                question="Why does os.system() exist in this code?",
                answer="Developer used shell execution for convenience",
                confidence=0.85,
                evidence=["os.system() is easier than subprocess.run()"],
            )
        elif "missing_docstring" in issue.lower():
            return FractalNode(
                level=level,
                question="Why are docstrings missing?",
                answer="No documentation requirement in the team's coding standards",
                confidence=0.8,
                evidence=["No linter rule enforces docstrings"],
            )
        else:
            return FractalNode(
                level=level,
                question=f"Why does {issue} exist?",
                answer="Root cause not yet determined",
                confidence=0.5,
                evidence=["Requires manual investigation"],
            )

    def _why_introduced(self, level: int, finding: dict[str, Any], parent: FractalNode) -> FractalNode:
        """Level 3: Why was this introduced?"""
        issue = finding.get("issue", "")
        if "eval" in issue.lower():
            return FractalNode(
                level=level,
                question="Why was eval() introduced instead of safer parsing?",
                answer="Developer may not have known about ast.literal_eval or json.loads",
                confidence=0.75,
                evidence=["Knowledge gap in secure coding practices"],
            )
        elif "missing_docstring" in issue.lower():
            return FractalNode(
                level=level,
                question="Why were docstring requirements not enforced?",
                answer="Code review process does not check documentation",
                confidence=0.8,
                evidence=["No docstring checks in CI pipeline"],
            )
        else:
            return FractalNode(
                level=level,
                question="Why was this pattern introduced?",
                answer="Lack of secure coding guidelines during development",
                confidence=0.6,
                evidence=["Team may not have security training"],
            )

    def _why_missed(self, level: int, finding: dict[str, Any], parent: FractalNode) -> FractalNode:
        """Level 4: Why wasn't this caught earlier?"""
        return FractalNode(
            level=level,
            question="Why wasn't this caught in code review or testing?",
            answer="Security scanning is not part of the CI pipeline",
            confidence=0.85,
            evidence=["No automated security checks in pre-commit or CI"],
        )

    def _why_allowed(self, level: int, finding: dict[str, Any], parent: FractalNode) -> FractalNode:
        """Level 5: Why does the architecture allow this?"""
        return FractalNode(
            level=level,
            question="Why does the system architecture permit this risk?",
            answer="No input validation layer or sandboxing at the application boundary",
            confidence=0.8,
            evidence=["Architecture lacks defense-in-depth strategy"],
        )

    def analyze_batch(self, findings: list[dict[str, Any]]) -> list[FractalNode]:
        """Analyze multiple findings, returning a forest of fractal trees."""
        return [self.analyze(f) for f in findings]

    def summarize_tree(self, node: FractalNode) -> str:
        """Generate a human-readable summary of the fractal analysis."""
        lines = [f"Level {node.level}: {node.question}", f"  → {node.answer}"]
        for child in node.children:
            lines.append(self.summarize_tree(child))
        return "\n".join(lines)
