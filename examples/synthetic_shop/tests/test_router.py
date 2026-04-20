from app.api.router import handle_checkout


def test_checkout_returns_success():
    result = handle_checkout({
        "user_id": "user-123",
        "cart_total": 50.0,
        "items": ["notebook"],
    })

    assert result["ok"] is True
    assert result["currency"] == "USD"
