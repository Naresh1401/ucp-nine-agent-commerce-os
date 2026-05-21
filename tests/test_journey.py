from fastapi.testclient import TestClient

from ucp_nine.main import app
from ucp_nine.models import AgentName, ShopperRequest
from ucp_nine.orchestrator import UcpJourneyOrchestrator

client = TestClient(app)


def auth(token: str = "demo-agent-token") -> dict[str, str]:
    return {"Authorization": f"Bearer {token}"}


def test_orchestrator_runs_exactly_nine_agents_for_approved_checkout() -> None:
    request = ShopperRequest(
        shopper_id="shopper_naresh",
        prompt="Find me coffee under 40 dollars and ship it to Cincinnati",
        destination_zip="45202",
        max_budget="40.00",
        human_approved_checkout=True,
    )
    result = UcpJourneyOrchestrator().run(request)

    assert len(result.trace) == 9
    assert [event.agent for event in result.trace] == list(AgentName)
    assert result.payment.status == "authorized"
    assert result.fulfillment.status == "reserved"
    assert result.offer.attributes["protocol"] == "ucp_like"


def test_unapproved_checkout_is_rejected_by_payment_agent() -> None:
    request = ShopperRequest(
        shopper_id="shopper_naresh",
        prompt="Find me coffee under 40 dollars",
        destination_zip="45202",
        max_budget="40.00",
        human_approved_checkout=False,
    )
    result = UcpJourneyOrchestrator().run(request)

    assert result.payment.status == "rejected"
    assert "mandate is not signed by trusted surface" in result.payment.reasons
    assert result.fulfillment.status == "not_started"


def test_api_journey_is_idempotent() -> None:
    payload = {
        "shopper_id": "shopper_naresh",
        "prompt": "Find me coffee under 40 dollars and ship it to Cincinnati",
        "destination_zip": "45202",
        "max_budget": "40.00",
        "human_approved_checkout": True,
    }
    headers = {**auth(), "Idempotency-Key": "same-journey-key"}
    first = client.post("/v1/ucp/journeys", headers=headers, json=payload)
    second = client.post("/v1/ucp/journeys", headers=headers, json=payload)

    assert first.status_code == 200
    assert second.status_code == 200
    assert first.json()["journey_id"] == second.json()["journey_id"]
    assert len(first.json()["trace"]) == 9


def test_analyst_token_can_read_agents_but_not_run_journey() -> None:
    agents = client.get("/v1/agents", headers=auth("demo-analyst-token"))
    journey = client.post(
        "/v1/ucp/journeys",
        headers={**auth("demo-analyst-token"), "Idempotency-Key": "analyst-denied"},
        json={
            "shopper_id": "shopper_naresh",
            "prompt": "Find me coffee under 40 dollars",
            "destination_zip": "45202",
            "max_budget": "40.00",
            "human_approved_checkout": True,
        },
    )

    assert agents.status_code == 200
    assert journey.status_code == 403

