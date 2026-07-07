# Amazon Arbitrage Sourcing App

A Python-based sourcing intelligence platform that evaluates retail products
as Amazon arbitrage opportunities.

Built as both a real business tool and a software engineering portfolio project.

---

## What It Does

Given a product found at a retailer (Kohl's, Walmart, Target, etc.), the app:

1. Matches it to an Amazon listing via ASIN
2. Calculates true profitability after all real costs
3. Analyzes risk signals (BSR, seller count, return risk)
4. Returns a **BUY / WATCH / PASS** recommendation with reasons

---

## Architecture

Retailer Product + Cost Assumptions
↓
SourcingService          ← orchestrates the pipeline
↓
AmazonClient             ← fetches Amazon product data (mock → Keepa → SP-API)
↓
ProfitCalculator         ← pure financial math
↓
RecommendationEngine     ← applies thresholds, returns Buy/Watch/Pass
↓
FastAPI /evaluate        ← HTTP interface

### Module Map

| Module | Location | Purpose |
|---|---|---|
| Product | `app/models/product.py` | Retailer sourcing opportunity data |
| ProfitCalculator | `app/calculations/profit_calculator.py` | True cost and ROI math |
| AmazonClient | `app/amazon/amazon_client.py` | Amazon data interface + mock |
| SourcingService | `app/services/sourcing_service.py` | Pipeline orchestrator |
| RecommendationEngine | `app/services/recommendation_engine.py` | Buy/Watch/Pass logic |
| API Routes | `app/api/routes.py` | FastAPI HTTP endpoints |

---

## Key Design Decisions

- **Profit calculator is retailer-agnostic** — only pure math, no retailer logic
- **Product and ProfitResult are separate** — product facts vs. derived calculations
- **AmazonClient is an interface** — MockAmazonClient used now, real API swapped in later
- **RecommendationConfig is injectable** — default thresholds work out of the box,
  overridable per use case
- **deal_resolver deferred** — retailer-specific discount parsing added when first
  real scraper is built

---

## Tech Stack

- Python 3.13
- FastAPI
- pytest
- Pydantic (via FastAPI)
- Keepa API *(planned)*
- Amazon SP-API *(planned)*

---

## Project Structure

amazon-arbitrage-app/
├── app/
│   ├── main.py                   # FastAPI app entry point
│   ├── api/
│   │   └── routes.py             # HTTP endpoints
│   ├── amazon/
│   │   └── amazon_client.py      # AmazonClient interface + MockAmazonClient
│   ├── calculations/
│   │   └── profit_calculator.py  # Profit / ROI / margin math
│   ├── models/
│   │   └── product.py            # Product dataclass
│   └── services/
│       ├── sourcing_service.py       # Pipeline orchestrator
│       └── recommendation_engine.py  # Buy/Watch/Pass logic
├── tests/
│   ├── test_amazon_client.py
│   ├── test_product.py
│   ├── test_profit_calculator.py
│   ├── test_recommendation_engine.py
│   ├── test_sourcing_service.py
│   └── test_api.py
├── requirements.txt
├── pytest.ini
└── README.md

---

## Setup

```bash
git clone <repo-url>
cd amazon-arbitrage-app
python -m venv venv

# Windows
venv\Scripts\activate

# Mac/Linux
source venv/bin/activate

pip install -r requirements.txt
```

---

## Running Tests

```bash
pytest -v
```

Expected output: **27 tests passing**

---

## Running the API

```bash
uvicorn app.main:app --reload
```

Visit `http://127.0.0.1:8000/docs` for interactive Swagger UI.

---

## Example: POST /evaluate

**Request**

```json
{
  "product": {
    "name": "Nike Air Max 90",
    "asin": "B000EXAMPLE",
    "retailer_name": "Kohl's",
    "retailer_price": 45.00
  },
  "assumptions": {
    "fba_fee": 7.50,
    "shipping_to_amazon": 2.00,
    "prep_cost": 0.75,
    "cashback_percent": 6.0
  }
}
```

**Response**

```json
{
  "product_name": "Nike Air Max 90",
  "amazon_product": {
    "asin": "B000EXAMPLE",
    "title": "Nike Air Max 90",
    "brand": "Nike",
    "category": "Shoes",
    "current_price": 89.99,
    "bsr": 1500,
    "seller_count": 8,
    "review_rating": 4.5
  },
  "profit_result": {
    "net_profit": 23.94,
    "roi_percent": 53.2,
    "margin_percent": 26.6,
    "total_cost": 66.05,
    "total_fees": 21.00,
    "cashback_amount": 2.70,
    "sales_tax_amount": 0.00,
    "return_risk_cost": 0.00
  },
  "recommendation": {
    "recommendation": "BUY",
    "reasons": ["Meets all thresholds."]
  },
  "error": null
}
```

---

## Cost Assumptions Reference

| Field | Description | Default |
|---|---|---|
| `amazon_referral_fee_percent` | Amazon referral fee % | 15.0 |
| `fba_fee` | FBA fulfillment fee | 0.0 |
| `shipping_to_you` | Retailer shipping cost | 0.0 |
| `shipping_to_amazon` | Cost to ship into Amazon | 0.0 |
| `prep_cost` | Labels, poly bags, labor | 0.0 |
| `cashback_percent` | Portal cashback % on buy cost | 0.0 |
| `sales_tax_percent` | Tax % on purchase | 0.0 |
| `coupon_discount` | Flat dollar coupon/discount | 0.0 |
| `storage_cost` | Estimated storage overhead | 0.0 |
| `return_risk_percent` | Return cost as % of sell price | 0.0 |
| `misc_buffer` | Catch-all cost buffer | 0.0 |

---

## Recommendation Thresholds (Defaults)

| Signal | BUY | WATCH | PASS |
|---|---|---|---|
| ROI | ≥ 30% | ≥ 15% | < 15% |
| Margin | ≥ 15% | any | — |
| Seller count | ≤ 20 | > 20 flags | — |
| BSR | ≤ 150,000 | > 150k flags | — |

Thresholds are fully configurable via `RecommendationConfig`.

---

## Roadmap

- [x] Profit calculator
- [x] Product model
- [x] Amazon client interface + mock
- [x] Sourcing service pipeline
- [x] Recommendation engine
- [x] FastAPI /evaluate endpoint
- [ ] Keepa API integration
- [ ] First retailer scraper (Kohl's)
- [ ] Additional retailers (Walmart, Target)
- [ ] React dashboard
- [ ] Alerts and deal monitoring
- [ ] Return risk scoring from review sentiment
