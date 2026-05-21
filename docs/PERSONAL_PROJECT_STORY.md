# Personal Project Story

I built this project to demonstrate how I think about agentic commerce beyond a basic API. Instead of one monolithic agent, I decomposed the journey into nine agents, each with a clear contract and trace. The system shows how a shopper prompt becomes a UCP-like intent, how merchant capabilities are negotiated, how offers are normalized from partners, how pricing and inventory are composed, and how payment is protected by an AP2-inspired mandate.

The important engineering point is that agents are allowed to help with discovery and workflow, but deterministic services still enforce contracts, auth, side effects, payment constraints, and auditability.

