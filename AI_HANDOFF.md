# AI Handoff Document

## Current Status
14 tests passing across 4 modules.

## Completed Modules
- `app/models/product.py` — Product dataclass
- `app/calculations/profit_calculator.py` — Pure profit/ROI/margin math
- `app/amazon/amazon_client.py` — AmazonClient interface + MockAmazonClient
- `app/services/sourcing_service.py` — Pipeline orchestrator

## Architecture Pattern
Product (facts) + CostAssumptions (variables) → SourcingService → ProfitResult
Next layer: RecommendationEngine takes ProfitResult + AmazonProduct → Buy/Watch/Pass

## Next Task
Build `app/services/recommendation_engine.py`
- RecommendationConfig dataclass with hardcoded defaults + user overrides
- Thresholds: ROI, margin, BSR, seller count, return risk
- Output: BUY / WATCH / PASS + reasons list

## Key Decisions
- See DECISIONS.md Decision 001
- deal_resolver deferred until first real retailer module
- product_to_profit_input converter deferred (low complexity, build when needed)
- Thresholds: hardcoded defaults with override via RecommendationConfig