from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


class PersistentMemoryStore:
    def __init__(self, project_root: str | Path, memory_dir_name: str = ".epistemic") -> None:
        self.project_root = Path(project_root)
        self.memory_dir = self.project_root / memory_dir_name
        self.memory_file = self.memory_dir / "memory.json"

    def hydrate_graph(self, graph) -> dict[str, Any]:
        state = self.load_state()
        for claim in state.get("known_claims", []):
            graph.register_claim(claim)
        for question in state.get("known_questions", []):
            graph.register_question(question)
        return state

    def persist_run(self, objective: str, report, nodes) -> Path:
        state = self.load_state()
        run_id = self._make_run_id()

        sorted_nodes = sorted(nodes, key=lambda n: n.claim_priority, reverse=True)
        branch_history = []
        for node in sorted_nodes:
            branch_history.append(
                {
                    "branch_path": node.branch_path,
                    "claim": node.claim,
                    "claim_type": node.claim_type.value,
                    "claim_priority": round(node.claim_priority, 4),
                    "confidence": round(node.confidence, 4),
                    "risk": round(node.risk, 4),
                    "status": node.status.value,
                    "stop_reason": node.stop_reason.value if node.stop_reason else None,
                    "source_question": node.source_question,
                }
            )

        state["schema_version"] = 1
        state["project_root"] = str(self.project_root)
        state["known_claims"] = self._dedupe([*state.get("known_claims", []), *report.confidence_map.keys()])
        state["known_questions"] = self._dedupe([*state.get("known_questions", []), *report.unresolved_questions])
        state["last_report"] = report.model_dump()

        runs = state.get("runs", [])
        runs.append(
            {
                "run_id": run_id,
                "timestamp": self._utc_now(),
                "objective": objective,
                "main_findings": report.main_findings[:10],
                "recommended_actions": report.recommended_actions[:10],
                "branch_count": len(report.branch_map),
                "memory_file": str(self.memory_file),
            }
        )
        state["runs"] = runs[-25:]
        state["branch_history"] = branch_history[:250]

        self.memory_dir.mkdir(parents=True, exist_ok=True)
        self.memory_file.write_text(json.dumps(state, indent=2, ensure_ascii=False), encoding="utf-8")
        return self.memory_file

    def load_state(self) -> dict[str, Any]:
        if not self.memory_file.exists():
            return {
                "schema_version": 1,
                "project_root": str(self.project_root),
                "known_claims": [],
                "known_questions": [],
                "runs": [],
                "branch_history": [],
                "last_report": {},
            }
        try:
            raw = json.loads(self.memory_file.read_text(encoding="utf-8"))
            if isinstance(raw, dict):
                return raw
        except Exception:
            pass
        return {
            "schema_version": 1,
            "project_root": str(self.project_root),
            "known_claims": [],
            "known_questions": [],
            "runs": [],
            "branch_history": [],
            "last_report": {},
        }

    def _make_run_id(self) -> str:
        return datetime.now(timezone.utc).strftime("run-%Y%m%dT%H%M%SZ")

    def _utc_now(self) -> str:
        return datetime.now(timezone.utc).isoformat()

    def _dedupe(self, values: list[str]) -> list[str]:
        cleaned: list[str] = []
        seen: set[str] = set()
        for value in values:
            lowered = value.strip().lower()
            if not lowered or lowered in seen:
                continue
            seen.add(lowered)
            cleaned.append(value)
        return cleaned
