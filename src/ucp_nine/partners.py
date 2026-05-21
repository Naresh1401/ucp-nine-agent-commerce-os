from decimal import Decimal
from typing import Any

from ucp_nine.models import Capability, MerchantProfile, NormalizedOffer


MERCHANTS = {
    "merchant_google_ucp": MerchantProfile(
        merchant_id="merchant_google_ucp",
        name="UCP Demo Merchant",
        capabilities=[
            Capability.catalog,
            Capability.offers,
            Capability.checkout,
            Capability.orders,
            Capability.fulfillment,
            Capability.support,
            Capability.direct_offers,
        ],
        extensions=[
            "dev.ucp.shopping.fulfillment",
            "dev.ucp.shopping.direct_offers",
            "naresh.ucp.agentic_support",
        ],
    ),
    "merchant_shopify_like": MerchantProfile(
        merchant_id="merchant_shopify_like",
        name="Shopify-Like Coffee Store",
        capabilities=[
            Capability.catalog,
            Capability.offers,
            Capability.checkout,
            Capability.orders,
            Capability.fulfillment,
        ],
        extensions=["dev.ucp.shopping.fulfillment"],
    ),
}


class PartnerAdapter:
    merchant_id = "base"

    def normalize_offer(self, payload: dict[str, Any]) -> NormalizedOffer:
        raise NotImplementedError


class UcpLikeMerchantAdapter(PartnerAdapter):
    merchant_id = "merchant_google_ucp"

    def normalize_offer(self, payload: dict[str, Any]) -> NormalizedOffer:
        offer = payload["offers"][0]
        return NormalizedOffer(
            merchant_id=self.merchant_id,
            sku=payload["merchantSku"],
            title=payload["displayName"],
            price=Decimal(str(offer["price"]["amount"])),
            currency=offer["price"].get("currency", "USD"),
            availability=offer.get("availability", "in_stock"),
            source_ref=payload["commerceObjectId"],
            attributes={
                "protocol": "ucp_like",
                "agent_surface": payload.get("agentSurface", "portfolio_agent"),
                "journey_stage": payload.get("journeyStage", "discovery"),
            },
        )


class ShopifyLikeMerchantAdapter(PartnerAdapter):
    merchant_id = "merchant_shopify_like"

    def normalize_offer(self, payload: dict[str, Any]) -> NormalizedOffer:
        variant = payload["variants"][0]
        inventory = int(variant.get("inventory_quantity", 0))
        availability = "out_of_stock" if inventory == 0 else "limited" if inventory < 5 else "in_stock"
        return NormalizedOffer(
            merchant_id=self.merchant_id,
            sku=variant["sku"],
            title=payload["title"],
            price=Decimal(str(variant["price"])),
            availability=availability,
            source_ref=str(payload["id"]),
            attributes={"protocol": "shopify_like", "vendor": payload.get("vendor")},
        )


class PartnerRegistry:
    def __init__(self) -> None:
        self.adapters: dict[str, PartnerAdapter] = {
            "merchant_google_ucp": UcpLikeMerchantAdapter(),
            "merchant_shopify_like": ShopifyLikeMerchantAdapter(),
        }

    def merchant(self, merchant_id: str) -> MerchantProfile:
        return MERCHANTS[merchant_id]

    def all_merchants(self) -> list[MerchantProfile]:
        return list(MERCHANTS.values())

    def adapter_for(self, merchant_id: str) -> PartnerAdapter:
        return self.adapters[merchant_id]

