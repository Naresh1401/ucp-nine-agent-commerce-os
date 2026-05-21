# UCP Nine-Agent Commerce OS

Personal flagship project by Naresh Sampangi: an end-to-end, UCP-inspired agentic commerce platform powered by nine specialized AI agents.

This project is designed as a portfolio-grade learning system for agentic commerce roles. It models the full shopping journey from user intent to discovery, merchant capability negotiation, offers, inventory, quote, AP2-style mandate validation, payment authorization, fulfillment, and post-purchase support.

> This is a UCP-inspired implementation for learning and portfolio purposes. It uses public UCP/AP2/MCP concepts and local deterministic agents so the repo runs without API keys.

## Why This Project Exists

Universal Commerce Protocol (UCP) is about giving agents, merchants, and payment providers a common way to operate across the shopping journey. This project turns that idea into a runnable reference architecture:

- REST APIs for agentic commerce.
- Nine specialized agents with explicit responsibilities.
- Partner adapter layer for Shopify-like, marketplace-like, and UCP-like merchants.
- MCP-style tool manifest and invocation endpoint.
- AP2-inspired checkout mandate and payment authorization checks.
- Event trace for every agent decision.
- Agentic evals for prompt injection, missing tool arguments, and risky side effects.
- Production readiness artifacts: Dockerfile, CI, docs, tests, runbook.

## The Nine Agents

1. `IntentAgent` - converts shopper language into structured UCP intent.
2. `CatalogAgent` - discovers candidate products.
3. `MerchantCapabilityAgent` - negotiates merchant capabilities and extensions.
4. `OfferAgent` - normalizes offers from partner ecosystems.
5. `InventoryAgent` - checks stock and fulfillment availability.
6. `PricingAgent` - calculates subtotal, promotions, tax, shipping, and total.
7. `TrustMandateAgent` - creates and validates AP2-inspired checkout mandates.
8. `PaymentAgent` - authorizes payment only when mandate constraints pass.
9. `FulfillmentSupportAgent` - creates fulfillment plan and post-purchase support state.

## Quick Start

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"
pytest
uvicorn ucp_nine.main:app --reload --app-dir src
```

Open:

- API docs: http://127.0.0.1:8000/docs
- Agent registry: http://127.0.0.1:8000/v1/agents
- MCP tools: http://127.0.0.1:8000/mcp/tools

## Demo Request

```bash
curl -s -X POST http://127.0.0.1:8000/v1/ucp/journeys \
  -H "Authorization: Bearer demo-agent-token" \
  -H "Idempotency-Key: demo-journey-1" \
  -H "Content-Type: application/json" \
  -d '{
    "shopper_id": "shopper_naresh",
    "prompt": "Find me coffee under 40 dollars and ship it to Cincinnati",
    "destination_zip": "45202",
    "max_budget": "40.00",
    "human_approved_checkout": true
  }'
```

## Project Map

```text
src/ucp_nine/
  agents.py        nine-agent orchestration units
  auth.py          scoped bearer-token demo auth
  evals.py         agentic safety/eval rules
  main.py          FastAPI app
  mcp.py           MCP-style tool registry and invocation
  models.py        API-first Pydantic contracts
  orchestrator.py  end-to-end UCP journey engine
  partners.py      partner adapters and capability negotiation
  security.py      mandate hashing and webhook signatures
  store.py         in-memory journey/event/idempotency storage
docs/
  ARCHITECTURE.md
  NINE_AGENTS.md
  UCP_AP2_MCP_NOTES.md
  API_GUIDE.md
  RUNBOOK.md
examples/
  demo_journey.py
tests/
```

## Demo Tokens

- `Bearer demo-agent-token`: `journey:run tools:invoke agents:read`
- `Bearer demo-analyst-token`: `agents:read`

## What Makes It Advanced

- A complete multi-agent workflow with typed handoffs.
- UCP-style capability negotiation and offer normalization.
- AP2-style mandate validation before payment authorization.
- MCP-style tools that agents can discover and call.
- Idempotent journey execution.
- Webhook signature verification for partner events.
- Agentic eval endpoint for risky tool calls and prompt injection.
- CI-ready test suite covering end-to-end behavior and security boundaries.

