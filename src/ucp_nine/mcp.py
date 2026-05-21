from typing import Any

from ucp_nine.evals import evaluate_tool_call
from ucp_nine.models import ShopperRequest, ToolInvocation
from ucp_nine.orchestrator import UcpJourneyOrchestrator


class UcpMcpToolRegistry:
    def tool_manifest(self) -> list[dict[str, Any]]:
        request_schema = ShopperRequest.model_json_schema()
        return [
            {
                "name": "ucp.discover",
                "title": "UCP Discovery",
                "description": "Run the discovery and offer stages for a shopper request.",
                "inputSchema": request_schema,
                "annotations": {"side_effects": "none", "human_approval_required": False},
            },
            {
                "name": "ucp.quote",
                "title": "UCP Quote",
                "description": "Create a quote using the nine-agent UCP pipeline.",
                "inputSchema": request_schema,
                "annotations": {"side_effects": "none", "human_approval_required": False},
            },
            {
                "name": "ucp.checkout",
                "title": "UCP Checkout",
                "description": "Run checkout. Requires human approval and trusted mandate generation.",
                "inputSchema": request_schema,
                "annotations": {"side_effects": "external_payment", "human_approval_required": True},
            },
        ]

    def invoke(self, invocation: ToolInvocation) -> dict[str, Any]:
        eval_result = evaluate_tool_call("mcp tool invocation", invocation)
        if not eval_result.accepted:
            return {"isError": True, "structuredContent": eval_result.model_dump()}
        request = ShopperRequest.model_validate(invocation.arguments)
        if invocation.name == "ucp.checkout" and not request.human_approved_checkout:
            return {
                "isError": True,
                "structuredContent": {
                    "accepted": False,
                    "reasons": ["human_approved_checkout must be true for checkout"],
                },
            }
        result = UcpJourneyOrchestrator().run(request)
        return {"isError": False, "structuredContent": result.model_dump(mode="json")}

