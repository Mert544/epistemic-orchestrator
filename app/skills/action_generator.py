from __future__ import annotations

import re
from pathlib import Path

from app.models.enums import ClaimType


class ActionGenerator:
    META_PREFIXES = (
        "Missing-information claim:",
        "Contradiction claim:",
        "Deepening claim:",
        "Risk claim:",
        "Investigation claim:",
    )

    PATH_PATTERN = re.compile(r"[A-Za-z0-9_./-]+\.(?:py|yml|yaml|toml|json|ini|cfg|md|txt)")

    def generate(self, nodes, profile=None) -> list[str]:
        actions: list[str] = []
        seen: set[str] = set()

        for action in self._profile_actions(profile):
            if action not in seen:
                seen.add(action)
                actions.append(action)

        sorted_nodes = sorted(nodes, key=lambda n: n.claim_priority, reverse=True)
        for node in sorted_nodes:
            action = self._action_for_node(node)
            if action and action not in seen:
                seen.add(action)
                actions.append(action)
            if len(actions) >= 10:
                break

        return actions

    def _profile_actions(self, profile) -> list[str]:
        if profile is None:
            return []

        actions: list[str] = []
        if getattr(profile, "critical_untested_modules", None):
            modules = ", ".join(profile.critical_untested_modules[:5])
            actions.append(f"Add or expand tests for critical untested modules: {modules}.")
        if getattr(profile, "sensitive_paths", None):
            paths = ", ".join(profile.sensitive_paths[:5])
            actions.append(f"Run a focused security review on sensitive paths: {paths}.")
        if getattr(profile, "dependency_hubs", None):
            hubs = ", ".join(profile.dependency_hubs[:5])
            actions.append(f"Inspect and reduce coupling in central dependency hubs: {hubs}.")
        if getattr(profile, "config_files", None):
            configs = ", ".join(profile.config_files[:5])
            actions.append(f"Audit configuration surfaces for unsafe defaults and environment coupling: {configs}.")
        if getattr(profile, "ci_files", None):
            ci_files = ", ".join(profile.ci_files[:3])
            actions.append(f"Review CI workflow coverage and strengthen automated gates in: {ci_files}.")
        return actions

    def _action_for_node(self, node) -> str | None:
        claim = node.claim.strip()
        if claim.startswith(self.META_PREFIXES):
            return None

        paths = self._extract_paths(claim)
        claim_type = node.claim_type
        lowered = claim.lower()

        if "untested module claim" in lowered and paths:
            return f"Prioritize test coverage for the referenced modules: {', '.join(paths[:5])}."
        if "dependency hub claim" in lowered and paths:
            return f"Review central modules and reduce architectural coupling around: {', '.join(paths[:5])}."
        if "sensitive surface claim" in lowered and paths:
            return f"Perform a security-focused review for the referenced sensitive paths: {', '.join(paths[:5])}."
        if "configuration claim" in lowered and paths:
            return f"Audit configuration handling and default safety for: {', '.join(paths[:5])}."
        if "automation claim" in lowered and paths:
            return f"Tighten CI or workflow enforcement around: {', '.join(paths[:5])}."

        if claim_type == ClaimType.SECURITY and paths:
            return f"Review secrets, auth, and payment handling in: {', '.join(paths[:5])}."
        if claim_type == ClaimType.VALIDATION and paths:
            return f"Strengthen or add tests for: {', '.join(paths[:5])}."
        if claim_type == ClaimType.AUTOMATION and paths:
            return f"Expand automated checks for: {', '.join(paths[:5])}."
        if claim_type == ClaimType.CONFIGURATION and paths:
            return f"Harden configuration boundaries around: {', '.join(paths[:5])}."
        if claim_type == ClaimType.ARCHITECTURE and paths:
            return f"Refactor or split high-centrality modules such as: {', '.join(paths[:5])}."
        if claim_type == ClaimType.OPERATIONS and paths:
            return f"Improve observability and failure handling around: {', '.join(paths[:5])}."

        if claim_type == ClaimType.VALIDATION:
            return f"Add or strengthen tests for validation-critical behavior implied by: {claim}"
        if claim_type == ClaimType.SECURITY:
            return f"Review security-sensitive behavior and harden controls for: {claim}"
        if claim_type == ClaimType.AUTOMATION:
            return f"Tighten CI validation gates related to: {claim}"
        if claim_type == ClaimType.CONFIGURATION:
            return f"Audit configuration defaults and environment coupling for: {claim}"
        if claim_type == ClaimType.ARCHITECTURE:
            return f"Inspect architectural coupling and consider refactoring around: {claim}"
        if claim_type == ClaimType.FEATURE_GAP:
            return f"Turn this gap into an engineering task with explicit acceptance criteria: {claim}"
        if claim_type == ClaimType.OPERATIONS:
            return f"Evaluate runtime observability and operational safeguards for: {claim}"
        return None

    def _extract_paths(self, text: str) -> list[str]:
        paths = [m.group(0) for m in self.PATH_PATTERN.finditer(text)]
        cleaned: list[str] = []
        for path in paths:
            normalized = str(Path(path))
            if normalized not in cleaned:
                cleaned.append(normalized)
        return cleaned
