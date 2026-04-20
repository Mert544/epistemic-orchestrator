from app.models.enums import ClaimType
from app.skills.claim_analyzer import ClaimAnalyzer


def test_claim_analyzer_classifies_security_claims_high():
    analyzer = ClaimAnalyzer()
    analysis = analyzer.analyze("Sensitive surface claim: auth token secret payment paths should be inspected early.")

    assert analysis.claim_type == ClaimType.SECURITY
    assert analysis.priority > 0.8
    assert any(signal in {"auth", "token", "secret", "payment"} for signal in analysis.signals)


def test_claim_analyzer_classifies_validation_claims():
    analyzer = ClaimAnalyzer()
    analysis = analyzer.analyze("Validation surface claim: test coverage and assertions should be expanded.")

    assert analysis.claim_type == ClaimType.VALIDATION
    assert analysis.priority > 0.7
