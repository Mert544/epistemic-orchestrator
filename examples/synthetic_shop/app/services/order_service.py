from app.auth.token_service import TokenService
from app.notifications.emailer import Emailer
from app.payments.gateway import PaymentGateway


class OrderService:
    def __init__(self, settings: dict) -> None:
        self.settings = settings
        self.gateway = PaymentGateway(settings)
        self.tokens = TokenService(settings)
        self.emailer = Emailer(settings)

    def checkout(self, payload: dict) -> dict:
        token = self.tokens.issue_checkout_token(payload["user_id"])
        charge = self.gateway.charge(
            amount=payload["cart_total"],
            token=token,
            currency=self.settings["currency"],
        )
        self.emailer.send_receipt(payload["user_id"], payload["items"])
        return {
            "ok": True,
            "charge_id": charge["charge_id"],
            "currency": self.settings["currency"],
        }
