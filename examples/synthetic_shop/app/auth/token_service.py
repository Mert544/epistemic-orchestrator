import hashlib


class TokenService:
    def __init__(self, settings: dict) -> None:
        self.secret = settings["jwt_secret"]

    def issue_checkout_token(self, user_id: str) -> str:
        raw = f"{user_id}:{self.secret}".encode("utf-8")
        return hashlib.sha256(raw).hexdigest()
