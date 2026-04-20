from app.skills.validator import Validator


def test_validator_returns_expected_shape():
    validator = Validator()
    result = validator.validate("A claim")
    assert "evidence_for" in result
    assert "evidence_against" in result
    assert "assumptions" in result
