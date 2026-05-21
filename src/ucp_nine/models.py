from decimal import Decimal
from enum import Enum
from typing import Any, Literal

from pydantic import BaseModel, Field, field_validator


class Capability(str, Enum):
    catalog = "catalog"
    offers = "offers"
    checkout = "checkout"
    orders = "orders"
    fulfillment = "fulfillment"
    support = "support"
    loyalty = "loyalty"
    direct_offers = "direct_offers"


class AgentName(str, Enum):
    intent = "IntentAgent"
    catalog = "CatalogAgent"
    merchant_capability = "MerchantCapabilityAgent"
    offer = "OfferAgent"
    inventory = "InventoryAgent"
    pricing = "PricingAgent"
    trust_mandate = "TrustMandateAgent"
    payment = "PaymentAgent"
    fulfillment_support = "FulfillmentSupportAgent"


class ShopperRequest(BaseModel):
    shopper_id: str
    prompt: str = Field(min_length=8, max_length=500)
    destination_zip: str = Field(min_length=5, max_length=10)
    max_budget: Decimal = Decimal("100.00")
    human_approved_checkout: bool = False

    @field_validator("destination_zip")
    @classmethod
    def zip_prefix_must_be_numeric(cls, value: str) -> str:
        if not value[:5].isdigit():
            raise ValueError("destination_zip must start with five digits")
        return value


class UcpIntent(BaseModel):
    shopper_id: str
    query: str
    category: str
    constraints: dict[str, Any]
    requested_capabilities: list[Capability]


class Product(BaseModel):
    sku: str
    title: str
    category: str
    tags: list[str]


class MerchantProfile(BaseModel):
    merchant_id: str
    name: str
    capabilities: list[Capability]
    extensions: list[str]


class NormalizedOffer(BaseModel):
    merchant_id: str
    sku: str
    title: str
    price: Decimal
    currency: str = "USD"
    availability: Literal["in_stock", "limited", "out_of_stock"]
    source_ref: str
    attributes: dict[str, Any] = Field(default_factory=dict)


class InventoryDecision(BaseModel):
    sku: str
    merchant_id: str
    reservable: bool
    available_units: int
    fulfillment_modes: list[str]


class Quote(BaseModel):
    quote_id: str
    merchant_id: str
    sku: str
    quantity: int
    subtotal: Decimal
    discount: Decimal
    tax: Decimal
    shipping: Decimal
    total: Decimal
    currency: str = "USD"
    warnings: list[str] = []


class CheckoutMandate(BaseModel):
    mandate_id: str
    shopper_id: str
    merchant_id: str
    checkout_hash: str
    max_total: Decimal
    currency: str = "USD"
    human_present: bool
    signed_by_trusted_surface: bool
    constraints: dict[str, Any]


class PaymentAuthorization(BaseModel):
    authorization_id: str
    status: Literal["authorized", "rejected"]
    reasons: list[str] = []


class FulfillmentPlan(BaseModel):
    fulfillment_id: str
    mode: str
    destination_zip: str
    status: Literal["reserved", "not_started"]
    support_case_id: str


class AgentTrace(BaseModel):
    agent: AgentName
    summary: str
    input_keys: list[str]
    output_keys: list[str]
    risk_flags: list[str] = []


class UcpJourneyResult(BaseModel):
    journey_id: str
    intent: UcpIntent
    selected_product: Product
    merchant: MerchantProfile
    offer: NormalizedOffer
    inventory: InventoryDecision
    quote: Quote
    mandate: CheckoutMandate
    payment: PaymentAuthorization
    fulfillment: FulfillmentPlan
    trace: list[AgentTrace]


class ToolInvocation(BaseModel):
    name: Literal["ucp.discover", "ucp.quote", "ucp.checkout"]
    arguments: dict[str, Any] = Field(default_factory=dict)
    approved_by_human: bool = False


class AgenticEvalResult(BaseModel):
    accepted: bool
    reasons: list[str] = []
