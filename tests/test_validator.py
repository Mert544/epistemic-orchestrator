from app.skills.validator import Validator


class EmptyEvidenceMapper:
    def map(self, claim: str) -> dict:
        return {
            "evidence_for": [],
            "evidence_against": [],
            "sources_for": [],
            "sources_against": [],
        }


class FilledEvidenceMapper:
    def map(self, claim: str) -> dict:
        return {
            "evidence_for": [f"support for {claim}"],
            "evidence_against": [f"counter for {claim}"],
            "sources_for": ["source-a"],
            "sources_against": ["source-b"],
        }


def test_validator_returns_expected_shape():
    validator = Validator(evidence_mapper=EmptyEvidenceMapper())
    result = validator.validate("A claim")
    assert "evidence_for" in result
    assert "evidence_against" in result
    assert "assumptions" in result
    assert "raw_sources_for" in result
    assert "raw_sources_against" in result


def test_validator_falls_back_when_local_search_returns_nothing():
    validator = Validator(evidence_mapper=EmptyEvidenceMapper())
    result = validator.validate("A claim")
    assert result["evidence_for"][0].startswith("No local supporting evidence")
    assert result["evidence_against"][0].startswith("No local counter-evidence")


def test_validator_uses_mapper_results_when_available():
    validator = Validator(evidence_mapper=FilledEvidenceMapper())
    result = validator.validate("Market structure claim")
    assert result["evidence_for"][0] == "support for Market structure claim"
    assert result["evidence_against"][0] == "counter for Market structure claim"
    assert result["risk"] >= 0.35
