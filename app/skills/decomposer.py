from __future__ import annotations

from pathlib import Path

from app.skills.claim_normalizer import ClaimNormalizer
from app.tools.project_profile import ProjectProfiler


class Decomposer:
    def __init__(self, project_root: str | Path | None = None) -> None:
        self.project_root = Path(project_root) if project_root is not None else None
        self.normalizer = ClaimNormalizer()

    def decompose(self, text: str) -> list[str]:
        cleaned = text.strip()
        if not cleaned:
            return []

        if self._should_seed_from_project(cleaned):
            seeded = self._seed_claims_from_project(cleaned)
            if seeded:
                return seeded

        normalized = self.normalizer.normalize(cleaned)
        if self.normalizer._looks_like_question(cleaned):
            return [normalized] if self.normalizer.is_viable(normalized) else []

        parts = self.normalizer.split_sentences(cleaned)
        if parts:
            return parts

        if self.normalizer.is_viable(normalized):
            return [normalized]

        fallback = self.normalizer.normalize(f"Objective claim: {cleaned} should be investigated further.")
        return [fallback] if self.normalizer.is_viable(fallback) else []

    def _should_seed_from_project(self, text: str) -> bool:
        lowered = text.lower()
        markers = {
            "scan the target project",
            "scan the project",
            "repository",
            "codebase",
            "target project",
            "implementation claims",
        }
        return any(marker in lowered for marker in markers) and self.project_root is not None

    def _seed_claims_from_project(self, objective: str) -> list[str]:
        profiler = ProjectProfiler(self.project_root)
        profile = profiler.profile()
        claims: list[str] = []

        claims.append(
            f"Project profile claim: the target repository contains {profile.total_files} files and should be decomposed into structural subclaims before deeper validation."
        )

        top_ext = next(iter(profile.extension_counts.keys()), None)
        if top_ext:
            claims.append(
                f"Language surface claim: the dominant file extension is {top_ext}, so core architectural and maintenance questions should start from that implementation surface."
            )

        if profile.top_directories:
            claims.append(
                "Module boundary claim: the top project directories are "
                + ", ".join(profile.top_directories)
                + ", and each may deserve separate fractal expansion as its own subsystem."
            )

        if profile.entrypoints:
            claims.append(
                "Entrypoint claim: the project exposes probable execution entrypoints at "
                + ", ".join(profile.entrypoints[:5])
                + ", which should be examined for orchestration, control flow, and dependency assumptions."
            )

        if profile.dependency_hubs:
            claims.append(
                "Dependency hub claim: the files "
                + ", ".join(profile.dependency_hubs[:5])
                + ", appear central in the import graph and should be expanded first for dependency risk and architectural coupling."
            )

        if profile.symbol_hubs:
            claims.append(
                "Symbol density claim: the files "
                + ", ".join(profile.symbol_hubs[:5])
                + ", define unusually rich symbol surfaces and may hide high-leverage abstractions or overgrown responsibilities."
            )

        if profile.test_files:
            claims.append(
                f"Validation surface claim: the repository contains {len(profile.test_files)} test-related files, so evidence should compare implementation paths against available test coverage."
            )
        else:
            claims.append(
                "Testing gap claim: the repository does not visibly expose test files, so missing validation coverage may be a first-order project risk."
            )

        if profile.untested_modules:
            claims.append(
                "Untested module claim: the files "
                + ", ".join(profile.untested_modules[:5])
                + ", do not appear to have obvious matching tests, so validation-oriented branching should inspect them early."
            )

        if profile.ci_files:
            claims.append(
                "Automation claim: CI workflow files are present at "
                + ", ".join(profile.ci_files[:3])
                + ", so the system should inspect what is already enforced automatically versus what remains unchecked."
            )
        else:
            claims.append(
                "Automation gap claim: no CI workflow files were detected, so build, test, and validation gates may be under-specified."
            )

        if profile.config_files:
            claims.append(
                "Configuration claim: the repository includes configuration surfaces at "
                + ", ".join(profile.config_files[:5])
                + ", which may contain hidden assumptions, environment coupling, or missing safeguards."
            )

        if profile.sensitive_paths:
            claims.append(
                "Sensitive surface claim: the repository includes potentially sensitive paths such as "
                + ", ".join(profile.sensitive_paths[:5])
                + ", so risk-oriented branching should inspect those areas early."
            )

        claims.append(
            f"Objective alignment claim: the system should continue from this project profile and recursively expand only the highest-value claims implied by the objective '{objective}'."
        )

        return claims
