# Runbook

## Local Verification

```bash
pytest
python examples/demo_journey.py
```

## Health Check

```bash
curl http://127.0.0.1:8000/health
```

## Common Failure Modes

- `401 Missing bearer token`: add `Authorization` header.
- `403 Missing scope`: use `demo-agent-token` for journey and tool endpoints.
- Payment rejected: set `human_approved_checkout` to `true` and keep total under `max_budget`.
- Webhook rejected: sign the payload with `WEBHOOK_SECRET`.

## Production Notes

- Use real identity provider for tokens.
- Move webhook secret to a secrets manager.
- Persist state outside process memory.
- Add replay protection to webhooks.
- Add audit log storage for mandates and payment decisions.

