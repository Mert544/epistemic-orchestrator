from __future__ import annotations

from pathlib import Path

from app.orchestrator import FractalResearchOrchestrator
from app.skills.decomposer import Decomposer
from app.skills.synthesizer import Synthesizer
from app.skills.validator import Validator
from app.utils.json_utils import pretty_json
from app.utils.logging import get_logger
from app.utils.yaml_utils import load_yaml

logger = get_logger(__name__)


def main() -> None:
    project_root = Path(__file__).resolve().parents[1]
    config = load_yaml(project_root / "config" / "default.yaml")

    orchestrator = FractalResearchOrchestrator(
        config=config,
        decomposer=Decomposer(),
        validator=Validator(),
        synthesizer=Synthesizer(),
    )

    objective = "Research current market structure and derive actionable claims."
    report = orchestrator.run(objective)
    logger.info("Run complete.")
    print(pretty_json(report.model_dump()))


if __name__ == "__main__":
    main()
