class PaymentGateway:
    def __init__(self, settings: dict) -> None:
        self.provider = settings["payment_provider"]
        self.api_key = settings["payment_api_key"]

    def charge(self, amount: float, token: str, currency: str) -> dict:
        return {
            "charge_id": f"{self.provider}-charge-001",
            "amount": amount,
            "currency": currency,
            "token": token,
        }
