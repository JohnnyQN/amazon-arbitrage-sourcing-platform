# Decision 001: Keep Profit Calculator Retailer-Agnostic

Date: 2026-06-30

## Decision

The profit calculator should only perform pure financial math using fully resolved input numbers.

It should not contain retailer-specific logic for coupons, promotions, rewards, or deal parsing.

## Reason

Retailers have different and messy discount systems. Putting that logic inside the profit calculator would make it harder to test, harder to maintain, and harder to reuse.

## Architecture

Future structure:

- `app/calculations/profit_calculator.py`
  - Pure math
  - Profit
  - ROI
  - Margin
  - Fees
  - Cost breakdown

- `app/retailers/deal_resolver.py`
  - Future module
  - Resolves retailer-specific pricing, discounts, coupons, rewards, and promotions into clean numbers

## Status

`deal_resolver` is intentionally deferred until the first real retailer module is built.


## Decision: Evaluate exact variants, present grouped product families

For apparel, footwear, and other variation-heavy products, profitability and demand must be evaluated at the exact child-variant level whenever possible.

Variant dimensions may include:
- color
- size
- width
- gender
- pack quantity
- retailer SKU
- UPC
- child ASIN

The application should group variants under a product-family summary for presentation. BUY variants should be shown by default, while WATCH and PASS variants should be collapsed or summarized to reduce review noise.

Parent-level Amazon data must not be treated as equivalent to exact child-variant data. Recommendations should include a data-quality or confidence indicator when only parent-level history is available.

# Decision 002: Exception Hierarchy - Flat Until Justified
Date: 2026-07-13
## Decision
Custom exceptions inherit directly from Exception rather than a shared SourcingException base.
## Reason
No concrete use case yet requires catching all sourcing errors together.
A base class adds indirection without current value.
Revisit if the API layer or a bulk pipeline needs to handle all sourcing errors uniformly.
## Status
Intentionally deferred.

---

# Decision 003: Apparel and Footwear Variant Grouping
Date: 2026-07-13
## Decision
For apparel and footwear, child variants (size, color, etc.) must eventually be
evaluated separately but presented grouped under a product-family summary.
## Reason
A single shoe listing on Amazon has many ASINs - one per size/color combination.
Each variant has its own BSR, price, and seller count.
Flooding the user with one row per variant is unusable.
The correct UX is: evaluate each variant, surface the best opportunity per family,
let the user drill down into variants if needed.
## Impact
Affects future retailer scraper design, ASIN matching logic, and dashboard layout.
Single-product /evaluate endpoint is not affected.
## Status
Intentionally deferred until retailer scraper work begins.