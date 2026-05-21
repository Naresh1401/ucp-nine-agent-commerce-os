from fastapi.testclient import TestClient

from ucp_nine.main import WEBHOOK_SECRET, app
from ucp_nine.security import sign_webhook, stable_json_hash

client = TestClient(app)


def test_stable_checkout_hash_is_deterministic() -> None:
    left = stable_json_hash({"total": "18.95", "sku": "coffee-001"})
    right = stable_json_hash({"sku": "coffee-001", "total": "18.95"})
    assert left == right


def test_partner_webhook_requires_valid_signature() -> None:
    body = b'{"event":"offer.updated"}'
    signature = sign_webhook(WEBHOOK_SECRET, body)

    ok = client.post(
        "/v1/partners/merchant_google_ucp/webhooks",
        content=body,
        headers={"X-Partner-Signature": signature},
    )
    bad = client.post(
        "/v1/partners/merchant_google_ucp/webhooks",
        content=body,
        headers={"X-Partner-Signature": "bad"},
    )

    assert ok.status_code == 200
    assert bad.status_code == 401

