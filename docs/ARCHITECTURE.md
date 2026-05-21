# Architecture

```text
Shopper / Agent Client / Partner
             |
             v
FastAPI REST API + MCP Tool Shim
             |
             v
UCP Journey Orchestrator
             |
             +--> 1. IntentAgent
             +--> 2. CatalogAgent
             +--> 3. MerchantCapabilityAgent
             +--> 4. OfferAgent
             +--> 5. InventoryAgent
             +--> 6. PricingAgent
             +--> 7. TrustMandateAgent
             +--> 8. PaymentAgent
             +--> 9. FulfillmentSupportAgent
             |
             v
Journey Result + Agent Trace + Support State
```

## Core Ideas

- REST APIs are deterministic and API-first.
- MCP-style tools allow agents to discover safe commerce capabilities.
- Partner adapters normalize UCP-like and third-party platform payloads.
- Checkout is gated by a mandate that binds shopper, merchant, SKU, quantity, total, and currency.
- Payment authorization fails unless the mandate is signed by a trusted surface.
- Every agent creates an `AgentTrace` so the journey is explainable.

## Production Extensions

- Replace demo bearer tokens with OAuth 2.0/JWT verification.
- Persist journeys and idempotency keys in Postgres or Redis.
- Add OpenTelemetry spans around each agent and partner call.
- Add real payment provider sandbox integration.
- Add webhook replay protection with timestamp and nonce.
- Add streaming events over SSE or WebSocket.
- Add real LLM provider adapters behind each deterministic agent.

