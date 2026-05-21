# UCP, AP2, And MCP Notes

## UCP-Inspired Concepts

UCP is about a shared commerce language between agents, merchants, and payment providers. This repo models:

- Product discovery.
- Merchant capability negotiation.
- Offer normalization.
- Checkout constraints.
- Fulfillment and post-purchase support.

## AP2-Inspired Concepts

Agentic payments require verifiable authorization. This repo models:

- `CheckoutMandate` with shopper, merchant, checkout hash, and max total.
- Payment rejection if mandate is not signed by trusted surface.
- Payment rejection if quote exceeds mandate constraints.

## MCP-Inspired Concepts

Agents need discoverable tools. This repo exposes:

- `GET /mcp/tools`
- `POST /mcp/invoke`

Tool annotations include side-effect level and human approval requirement.

