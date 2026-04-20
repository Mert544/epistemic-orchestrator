class Emailer:
    def __init__(self, settings: dict) -> None:
        self.sender = settings["email_sender"]

    def send_receipt(self, user_id: str, items: list[str]) -> dict:
        return {
            "sent": True,
            "to": user_id,
            "items": items,
            "from": self.sender,
        }
