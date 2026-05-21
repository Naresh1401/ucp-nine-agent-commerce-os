from uuid import uuid4
from typing import Optional

from ucp_nine.agents import (
    CatalogAgent,
    FulfillmentSupportAgent,
    IntentAgent,
    InventoryAgent,
    MerchantCapabilityAgent,
    OfferAgent,
    PaymentAgent,
    PricingAgent,
    TrustMandateAgent,
)
from ucp_nine.models import ShopperRequest, UcpJourneyResult
from ucp_nine.partners import PartnerRegistry


class UcpJourneyOrchestrator:
    def __init__(self, registry: Optional[PartnerRegistry] = None) -> None:
        self.registry = registry or PartnerRegistry()

    def run(self, request: ShopperRequest) -> UcpJourneyResult:
        trace = []

        intent, event = IntentAgent().run(request)
        trace.append(event)

        product, event = CatalogAgent().run(intent)
        trace.append(event)

        merchant, event = MerchantCapabilityAgent(self.registry).run(product, intent)
        trace.append(event)

        offer, event = OfferAgent(self.registry).run(product, merchant)
        trace.append(event)

        inventory, event = InventoryAgent().run(offer)
        trace.append(event)

        quote, event = PricingAgent().run(offer, inventory, request)
        trace.append(event)

        mandate, event = TrustMandateAgent().run(request, quote)
        trace.append(event)

        payment, event = PaymentAgent().run(quote, mandate)
        trace.append(event)

        fulfillment, event = FulfillmentSupportAgent().run(request, inventory, payment)
        trace.append(event)

        return UcpJourneyResult(
            journey_id=f"journey_{uuid4().hex[:12]}",
            intent=intent,
            selected_product=product,
            merchant=merchant,
            offer=offer,
            inventory=inventory,
            quote=quote,
            mandate=mandate,
            payment=payment,
            fulfillment=fulfillment,
            trace=trace,
        )
