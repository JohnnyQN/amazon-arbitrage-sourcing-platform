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