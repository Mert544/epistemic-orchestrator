from app.skills.spam_guard import SpamGuard


def test_spam_guard_filters_nested_meta_claims():
    guard = SpamGuard()
    claims = [
        "Missing-information claim: the project still lacks critical evidence needed to validate Missing-information claim: dependency hub claim around app/services/order_service.py.",
        "Dependency hub claim: the files app/services/order_service.py appear central in the import graph and should be expanded first for dependency risk and architectural coupling.",
    ]

    # Parent claim must differ from the child claims so the duplicate filter does not remove both.
    parent_claim="Dependency hub claim: the files app/services/order_service.py, app/payments/gateway.py appear central in the import graph and should be expanded first for dependency risk and architectural coupling."
    filtered = guard.filter_claims(claims, parent_claim=parent_claim)

    assert len(filtered) == 1
    assert filtered[0].startswith("Dependency hub claim:")


def test_spam_guard_rejects_low_value_questions():
    guard = SpamGuard()
    parent = "Dependency hub claim: the files app/services/order_service.py appear central in the import graph and should be expanded first for dependency risk and architectural coupling."

    assert guard.is_low_value_question(parent, parent) is True
    assert guard.is_low_value_question("What are the consequences if this claim is wrong?", parent) is True
    assert guard.is_low_value_question("What are the consequences if this claim is wrong: Dependency hub claim around app/services/order_service.py?", parent) is False
