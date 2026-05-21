from decimal import Decimal
from uuid import uuid4

from ucp_nine.models import (
    AgentName,
    AgentTrace,
    Capability,
    CheckoutMandate,
    FulfillmentPlan,
    InventoryDecision,
    MerchantProfile,
    NormalizedOffer,
    PaymentAuthorization,
    Product,
    Quote,
    ShopperRequest,
    UcpIntent,
)
from ucp_nine.partners import PartnerRegistry
from ucp_nine.security import stable_json_hash


CATALOG = [
    Product(
        sku="coffee-001",
        title="Cincinnati Blend Coffee",
        category="coffee",
        tags=["coffee", "gift", "cincinnati", "pantry"],
    ),
    Product(
        sku="mug-002",
        title="Agentic Commerce Mug",
        category="drinkware",
        tags=["mug", "gift", "coffee"],
    ),
    Product(
        sku="rug-003",
        title="Washable Dining Room Rug",
        category="home",
        tags=["rug", "home", "washable", "dining"],
    ),
]

UCP_OFFER_PAYLOADS = {
    "coffee-001": {
        "commerceObjectId": "ucp_offer_coffee_001",
        "merchantSku": "coffee-001",
        "displayName": "Cincinnati Blend Coffee",
        "agentSurface": "naresh-portfolio-agent",
        "journeyStage": "checkout",
        "offers": [{"price": {"amount": "12.99", "currency": "USD"}, "availability": "in_stock"}],
    },
    "rug-003": {
        "commerceObjectId": "ucp_offer_rug_003",
        "merchantSku": "rug-003",
        "displayName": "Washable Dining Room Rug",
        "agentSurface": "naresh-portfolio-agent",
        "journeyStage": "checkout",
        "offers": [{"price": {"amount": "89.00", "currency": "USD"}, "availability": "limited"}],
    },
}

SHOPIFY_OFFER_PAYLOADS = {
    "mug-002": {
        "id": "shopify_product_mug_002",
        "title": "Agentic Commerce Mug",
        "vendor": "Naresh Demo Store",
        "variants": [{"sku": "mug-002", "price": "9.50", "inventory_quantity": 3}],
    }
}

INVENTORY = {
    ("merchant_google_ucp", "coffee-001"): 28,
    ("merchant_google_ucp", "rug-003"): 2,
    ("merchant_shopify_like", "mug-002"): 3,
}


class IntentAgent:
    name = AgentName.intent

    def run(self, request: ShopperRequest) -> tuple[UcpIntent, AgentTrace]:
        prompt = request.prompt.lower()
        category = "coffee"
        if "rug" in prompt:
            category = "home"
        elif "mug" in prompt:
            category = "drinkware"

        intent = UcpIntent(
            shopper_id=request.shopper_id,
            query=request.prompt,
            category=category,
            constraints={
                "max_budget": str(request.max_budget),
                "destination_zip": request.destination_zip,
                "human_approved_checkout": request.human_approved_checkout,
            },
            requested_capabilities=[
                Capability.catalog,
                Capability.offers,
                Capability.checkout,
                Capability.fulfillment,
                Capability.support,
            ],
        )
        return intent, AgentTrace(
            agent=self.name,
            summary=f"Converted shopper prompt into structured {category} intent.",
            input_keys=["shopper_id", "prompt", "destination_zip", "max_budget"],
            output_keys=["intent"],
        )


class CatalogAgent:
    name = AgentName.catalog

    def run(self, intent: UcpIntent) -> tuple[Product, AgentTrace]:
        candidates = [
            product
            for product in CATALOG
            if product.category == intent.category or intent.category in product.tags
        ]
        product = candidates[0] if candidates else CATALOG[0]
        return product, AgentTrace(
            agent=self.name,
            summary=f"Selected product {product.sku} from catalog candidates.",
            input_keys=["intent.category"],
            output_keys=["selected_product"],
        )


class MerchantCapabilityAgent:
    name = AgentName.merchant_capability

    def __init__(self, registry: PartnerRegistry) -> None:
        self.registry = registry

    def run(self, product: Product, intent: UcpIntent) -> tuple[MerchantProfile, AgentTrace]:
        selected = None
        for merchant in self.registry.all_merchants():
            if all(capability in merchant.capabilities for capability in intent.requested_capabilities):
                selected = merchant
                break
        if selected is None:
            selected = self.registry.merchant("merchant_google_ucp")
        if product.sku == "mug-002":
            selected = self.registry.merchant("merchant_shopify_like")
        return selected, AgentTrace(
            agent=self.name,
            summary=f"Negotiated merchant capabilities with {selected.merchant_id}.",
            input_keys=["selected_product", "requested_capabilities"],
            output_keys=["merchant_profile"],
        )


class OfferAgent:
    name = AgentName.offer

    def __init__(self, registry: PartnerRegistry) -> None:
        self.registry = registry

    def run(self, product: Product, merchant: MerchantProfile) -> tuple[NormalizedOffer, AgentTrace]:
        adapter = self.registry.adapter_for(merchant.merchant_id)
        if merchant.merchant_id == "merchant_shopify_like":
            payload = SHOPIFY_OFFER_PAYLOADS[product.sku]
        else:
            payload = UCP_OFFER_PAYLOADS[product.sku]
        offer = adapter.normalize_offer(payload)
        return offer, AgentTrace(
            agent=self.name,
            summary=f"Normalized partner offer {offer.source_ref} into UCP-like offer contract.",
            input_keys=["partner_payload", "merchant_profile"],
            output_keys=["normalized_offer"],
        )


class InventoryAgent:
    name = AgentName.inventory

    def run(self, offer: NormalizedOffer) -> tuple[InventoryDecision, AgentTrace]:
        units = INVENTORY.get((offer.merchant_id, offer.sku), 0)
        decision = InventoryDecision(
            sku=offer.sku,
            merchant_id=offer.merchant_id,
            reservable=units > 0 and offer.availability != "out_of_stock",
            available_units=units,
            fulfillment_modes=["ship", "pickup"] if units > 5 else ["ship"],
        )
        risk_flags = [] if decision.reservable else ["inventory_unavailable"]
        return decision, AgentTrace(
            agent=self.name,
            summary=f"Checked inventory: {units} available unit(s).",
            input_keys=["normalized_offer"],
            output_keys=["inventory_decision"],
            risk_flags=risk_flags,
        )


class PricingAgent:
    name = AgentName.pricing

    def run(
        self,
        offer: NormalizedOffer,
        inventory: InventoryDecision,
        request: ShopperRequest,
    ) -> tuple[Quote, AgentTrace]:
        quantity = 1
        subtotal = offer.price * quantity
        discount = Decimal("2.00") if subtotal >= Decimal("20.00") else Decimal("0.00")
        tax = ((subtotal - discount) * Decimal("0.075")).quantize(Decimal("0.01"))
        shipping = Decimal("0.00") if subtotal >= Decimal("50.00") else Decimal("4.99")
        total = subtotal - discount + tax + shipping
        warnings: list[str] = []
        if total > request.max_budget:
            warnings.append("quote exceeds shopper max_budget")
        if not inventory.reservable:
            warnings.append("inventory is not reservable")
        quote = Quote(
            quote_id=f"quote_{uuid4().hex[:10]}",
            merchant_id=offer.merchant_id,
            sku=offer.sku,
            quantity=quantity,
            subtotal=subtotal,
            discount=discount,
            tax=tax,
            shipping=shipping,
            total=total,
            warnings=warnings,
        )
        return quote, AgentTrace(
            agent=self.name,
            summary=f"Calculated quote total {quote.total} {quote.currency}.",
            input_keys=["offer", "inventory_decision", "shopper_constraints"],
            output_keys=["quote"],
            risk_flags=warnings,
        )


class TrustMandateAgent:
    name = AgentName.trust_mandate

    def run(self, request: ShopperRequest, quote: Quote) -> tuple[CheckoutMandate, AgentTrace]:
        checkout_hash = stable_json_hash(
            {
                "shopper_id": request.shopper_id,
                "merchant_id": quote.merchant_id,
                "sku": quote.sku,
                "quantity": quote.quantity,
                "total": quote.total,
                "currency": quote.currency,
            }
        )
        mandate = CheckoutMandate(
            mandate_id=f"mandate_{uuid4().hex[:10]}",
            shopper_id=request.shopper_id,
            merchant_id=quote.merchant_id,
            checkout_hash=checkout_hash,
            max_total=request.max_budget,
            currency=quote.currency,
            human_present=request.human_approved_checkout,
            signed_by_trusted_surface=request.human_approved_checkout,
            constraints={
                "max_total": str(request.max_budget),
                "sku": quote.sku,
                "merchant_id": quote.merchant_id,
            },
        )
        risk_flags = [] if mandate.signed_by_trusted_surface else ["checkout_not_human_approved"]
        return mandate, AgentTrace(
            agent=self.name,
            summary="Created AP2-inspired checkout mandate bound to checkout hash.",
            input_keys=["shopper_request", "quote"],
            output_keys=["checkout_mandate"],
            risk_flags=risk_flags,
        )


class PaymentAgent:
    name = AgentName.payment

    def run(self, quote: Quote, mandate: CheckoutMandate) -> tuple[PaymentAuthorization, AgentTrace]:
        reasons: list[str] = []
        if not mandate.signed_by_trusted_surface:
            reasons.append("mandate is not signed by trusted surface")
        if quote.total > mandate.max_total:
            reasons.append("quote total exceeds mandate max_total")
        if quote.merchant_id != mandate.merchant_id:
            reasons.append("merchant mismatch")
        authorization = PaymentAuthorization(
            authorization_id=f"auth_{uuid4().hex[:10]}",
            status="rejected" if reasons else "authorized",
            reasons=reasons,
        )
        return authorization, AgentTrace(
            agent=self.name,
            summary=f"Payment authorization {authorization.status}.",
            input_keys=["quote", "checkout_mandate"],
            output_keys=["payment_authorization"],
            risk_flags=reasons,
        )


class FulfillmentSupportAgent:
    name = AgentName.fulfillment_support

    def run(
        self,
        request: ShopperRequest,
        inventory: InventoryDecision,
        payment: PaymentAuthorization,
    ) -> tuple[FulfillmentPlan, AgentTrace]:
        reserved = payment.status == "authorized" and inventory.reservable
        plan = FulfillmentPlan(
            fulfillment_id=f"fulfill_{uuid4().hex[:10]}",
            mode=inventory.fulfillment_modes[0],
            destination_zip=request.destination_zip,
            status="reserved" if reserved else "not_started",
            support_case_id=f"support_{uuid4().hex[:8]}",
        )
        risk_flags = [] if reserved else ["fulfillment_not_reserved"]
        return plan, AgentTrace(
            agent=self.name,
            summary=f"Created fulfillment status {plan.status} and support case.",
            input_keys=["shopper_request", "inventory_decision", "payment_authorization"],
            output_keys=["fulfillment_plan", "support_case"],
            risk_flags=risk_flags,
        )

