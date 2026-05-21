import hashlib
import hmac
import json
from decimal import Decimal
from typing import Any


def stable_json_hash(payload: dict[str, Any]) -> str:
    def normalize(value: Any) -> Any:
        if isinstance(value, Decimal):
            return str(value)
        if isinstance(value, dict):
            return {key: normalize(item) for key, item in sorted(value.items())}
        if isinstance(value, list):
            return [normalize(item) for item in value]
        return value

    encoded = json.dumps(normalize(payload), separators=(",", ":"), sort_keys=True).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


def sign_webhook(secret: str, body: bytes) -> str:
    return hmac.new(secret.encode("utf-8"), body, hashlib.sha256).hexdigest()


def verify_webhook(secret: str, body: bytes, signature: str) -> bool:
    return hmac.compare_digest(sign_webhook(secret, body), signature)

