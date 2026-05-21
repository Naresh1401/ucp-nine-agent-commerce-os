# The Nine Agents

## 1. IntentAgent

Turns natural language into `UcpIntent`. It extracts category, budget, destination, approval state, and requested commerce capabilities.

## 2. CatalogAgent

Selects candidate products from catalog data. In production this could query a catalog API, vector index, or merchant feed.

## 3. MerchantCapabilityAgent

Chooses a merchant whose UCP-like capabilities match the requested journey. This models capability negotiation.

## 4. OfferAgent

Normalizes partner payloads into one internal `NormalizedOffer` contract. This avoids brittle point-to-point integrations.

## 5. InventoryAgent

Checks whether the offer is reservable and what fulfillment modes are available.

## 6. PricingAgent

Computes quote, discount, tax, shipping, total, and warnings.

## 7. TrustMandateAgent

Creates an AP2-inspired mandate bound to checkout hash and shopper constraints.

## 8. PaymentAgent

Authorizes payment only when mandate constraints pass.

## 9. FulfillmentSupportAgent

Creates a fulfillment reservation and support case state after payment authorization.

