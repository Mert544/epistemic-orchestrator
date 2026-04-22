from __future__ import annotations

from typing import Any


class CompressedModeEngine:
    """Adjust fractal expansion parameters for token-efficient operation.

    When mode is 'compressed', the engine reduces depth, breadth, and detail
    to stay within tight token budgets while still producing actionable output.
    """

    COMPRESSED_OVERRIDES: dict[str, Any] = {
        "max_depth": 2,
        "max_total_nodes": 10,
        "top_k_questions": 1,
        "max_retries": 0,
        "claim_detail": "summary",
        "include_evidence": False,
        "include_assumptions": False,
    }

    def __init__(self, config: dict[str, Any]) -> None:
        self.mode = str(config.get("mode", "balanced")).lower()
        self._original_config = dict(config)
        self._active_config = dict(config)
        if self.mode == "compressed":
            self._apply_compression()

    def _apply_compression(self) -> None:
        for key, value in self.COMPRESSED_OVERRIDES.items():
            self._active_config[key] = value

    @property
    def config(self) -> dict[str, Any]:
        return dict(self._active_config)

    def compress_report(self, report: dict[str, Any]) -> dict[str, Any]:
        """Reduce report verbosity for compressed mode."""
        if self.mode != "compressed":
            return report
        compressed: dict[str, Any] = {
            "objective": report.get("objective", ""),
            "main_findings": report.get("main_findings", [])[:5],
            "branch_map": self._trim_branch_map(report.get("branch_map", {})),
            "recommended_actions": report.get("recommended_actions", [])[:5],
            "focus_branch": report.get("focus_branch"),
        }
        if report.get("key_risks"):
            compressed["key_risks"] = report["key_risks"][:3]
        return compressed

    @staticmethod
    def _trim_branch_map(branch_map: dict[str, str]) -> dict[str, str]:
        # Keep only top-level branches and one level deep
        trimmed: dict[str, str] = {}
        for branch, claim in branch_map.items():
            parts = branch.split(".")
            if len(parts) <= 3:  # e.g., x.a or x.a.b
                trimmed[branch] = claim
            if len(trimmed) >= 8:
                break
        return trimmed
