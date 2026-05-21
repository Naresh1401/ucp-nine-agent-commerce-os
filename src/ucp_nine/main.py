from typing import Annotated, Any

from fastapi import Depends, FastAPI, Header, HTTPException, Request

from ucp_nine.auth import Principal, require_scope
from ucp_nine.evals import evaluate_tool_call
from ucp_nine.mcp import UcpMcpToolRegistry
from ucp_nine.models import AgentName, AgenticEvalResult, ShopperRequest, ToolInvocation, UcpJourneyResult
from ucp_nine.orchestrator import UcpJourneyOrchestrator
from ucp_nine.security import verify_webhook
from ucp_nine.store import JourneyStore

app = FastAPI(
    title="UCP Nine-Agent Commerce OS",
    version="0.1.0",
    description="UCP-inspired nine-agent agentic commerce platform.",
)

store = JourneyStore()
WEBHOOK_SECRET = "ucp-demo-secret"


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok", "service": "ucp-nine-agent-commerce-os"}


@app.get("/v1/agents")
def agents(_: Principal = Depends(require_scope("agents:read"))) -> dict[str, list[dict[str, str]]]:
    return {
        "agents": [
            {"name": name.value, "role": role}
            for name, role in [
                (AgentName.intent, "Natural language to UCP intent"),
                (AgentName.catalog, "Product discovery"),
                (AgentName.merchant_capability, "Capability negotiation"),
                (AgentName.offer, "Partner offer normalization"),
                (AgentName.inventory, "Inventory and fulfillment availability"),
                (AgentName.pricing, "Quote, tax, shipping, and promotions"),
                (AgentName.trust_mandate, "AP2-inspired checkout mandate"),
                (AgentName.payment, "Payment authorization"),
                (AgentName.fulfillment_support, "Fulfillment and post-purchase support"),
            ]
        ]
    }


@app.post("/v1/ucp/journeys", response_model=UcpJourneyResult)
def create_journey(
    request: ShopperRequest,
    idempotency_key: Annotated[str, Header(alias="Idempotency-Key")],
    _: Principal = Depends(require_scope("journey:run")),
) -> UcpJourneyResult:
    cached = store.get_by_idempotency_key(idempotency_key)
    if cached:
        return cached
    result = UcpJourneyOrchestrator().run(request)
    store.save(idempotency_key, result)
    return result


@app.get("/v1/ucp/journeys/{journey_id}", response_model=UcpJourneyResult)
def get_journey(
    journey_id: str,
    _: Principal = Depends(require_scope("journey:run")),
) -> UcpJourneyResult:
    result = store.get(journey_id)
    if not result:
        raise HTTPException(status_code=404, detail="Journey not found")
    return result


@app.get("/v1/ucp/journeys/{journey_id}/events")
def get_journey_events(
    journey_id: str,
    _: Principal = Depends(require_scope("journey:run")),
) -> dict[str, Any]:
    return {"journey_id": journey_id, "events": [event.model_dump() for event in store.events(journey_id)]}


@app.get("/mcp/tools")
def mcp_tools(_: Principal = Depends(require_scope("tools:invoke"))) -> dict[str, Any]:
    return {"tools": UcpMcpToolRegistry().tool_manifest()}


@app.post("/mcp/invoke")
def mcp_invoke(
    invocation: ToolInvocation,
    _: Principal = Depends(require_scope("tools:invoke")),
) -> dict[str, Any]:
    return UcpMcpToolRegistry().invoke(invocation)


@app.post("/v1/quality/agentic-eval", response_model=AgenticEvalResult)
def agentic_eval(
    prompt: str,
    invocation: ToolInvocation,
    _: Principal = Depends(require_scope("tools:invoke")),
) -> AgenticEvalResult:
    return evaluate_tool_call(prompt, invocation)


@app.post("/v1/partners/{merchant_id}/webhooks")
async def partner_webhook(
    merchant_id: str,
    request: Request,
    x_partner_signature: str = Header(...),
) -> dict[str, str]:
    body = await request.body()
    if not verify_webhook(WEBHOOK_SECRET, body, x_partner_signature):
        raise HTTPException(status_code=401, detail="Invalid webhook signature")
    return {"status": "accepted", "merchant_id": merchant_id}

