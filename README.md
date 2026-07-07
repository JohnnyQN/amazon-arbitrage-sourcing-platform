# Amazon Arbitrage Sourcing App

A Python backend that evaluates retail products as Amazon arbitrage opportunities —
calculating true profitability, analyzing risk signals, and returning a
**BUY / WATCH / PASS** recommendation through a clean REST API.

Built as a real business tool and a software engineering portfolio project.

---

## Motivation

Most Amazon arbitrage tools are black boxes. They give you a number but not the reasoning,
and they don't account for your actual costs — cashback portals, prep centers, return risk,
storage overhead.

This app is different. Every calculation is explicit, every threshold is configurable,
and every layer is independently testable. The goal is a sourcing platform I actually
trust because I built it and understand every decision inside it.

This project demonstrates:

- **Clean architecture** — separation of concerns across models, services, and API layers
- **Test-driven development** — 27 passing tests across all modules
- **FastAPI** — typed request/response models, auto-generated Swagger docs
- **Modular design** — swap mock data for real APIs without touching business logic
- **Real business logic** — not a tutorial clone, solves an actual sourcing problem

---

## How It Works

Submit a retail product with cost assumptions. The pipeline:

1. Matches the product to an Amazon listing via ASIN
2. Calculates true profitability after all real costs
3. Analyzes risk signals — BSR, seller count, return risk
4. Returns a **BUY / WATCH / PASS** recommendation with reasons

---

## Architecture

```
Retailer Product + Cost Assumptions
          │
          ▼
   SourcingService          ← orchestrates the pipeline
          │
          ▼
   AmazonClient             ← fetches Amazon product data
          │                   (mock now → Keepa → SP-API later)
          ▼
   ProfitCalculator         ← pure financial math, retailer-agnostic
          │
          ▼
   RecommendationEngine     ← applies thresholds, returns Buy/Watch/Pass
          │
          ▼
   FastAPI /evaluate        ← typed HTTP interface with Swagger UI
```

---

## Module Map

| Module | Location | Purpose |
|--------|----------|---------|
| Product | `app/models/product.py` | Retailer sourcing opportunity data |
| ProfitCalculator | `app/calculations/profit_calculator.py` | True cost and ROI math |
| AmazonClient | `app/amazon/amazon_client.py` | Amazon data interface + mock |
| SourcingService | `app/services/sourcing_service.py` | Pipeline orchestrator |
| RecommendationEngine | `app/services/recommendation_engine.py` | Buy/Watch/Pass logic |
| API Routes | `app/api/routes.py` | FastAPI HTTP endpoints |

---

## Key Design Decisions

- **Profit calculator is retailer-agnostic** — pure math only, no retailer-specific logic
- **Product and ProfitResult are separate** — product facts vs. derived calculations
- **AmazonClient is an interface** — MockAmazonClient used now, real API swapped in later without touching business logic
- **RecommendationConfig is injectable** — sensible defaults, fully overridable per use case
- **deal_resolver deferred** — retailer discount parsing added when first real scraper is built

---

## Project Structure

```
amazon-arbitrage-app/
├── app/
│   ├── main.py                        # FastAPI app entry point
│   ├── api/
│   │   └── routes.py                  # HTTP endpoints + Pydantic models
│   ├── amazon/
│   │   └── amazon_client.py           # AmazonClient interface + MockAmazonClient
│   ├── calculations/
│   │   └── profit_calculator.py       # Profit / ROI / margin math
│   ├── models/
│   │   └── product.py                 # Product dataclass
│   └── services/
│       ├── sourcing_service.py        # Pipeline orchestrator
│       └── recommendation_engine.py   # Buy/Watch/Pass logic
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
```

---

## Tech Stack

- **Python 3.13**
- **FastAPI** — REST API with auto-generated Swagger docs
- **Pydantic** — typed request and response validation
- **pytest** — 27 tests across all modules
- **Keepa API** *(planned)*
- **Amazon SP-API** *(planned)*

---

## Setup

```bash
git clone <repo-url>
cd amazon-arbitrage-app
python -m venv venv
```

**Windows:**

```cmd
venv\Scripts\activate
```

**Mac / Linux:**

```bash
source venv/bin/activate
```

**Install dependencies:**

```bash
pip install -r requirements.txt
```

---

## Running Tests

```bash
pytest -v
```

Expected: **27 tests passing** across 6 test files.

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
|-------|-------------|---------|
| `amazon_referral_fee_percent` | Amazon referral fee % | 15.0 |
| `fba_fee` | FBA fulfillment fee ($) | 0.0 |
| `shipping_to_you` | Retailer shipping cost ($) | 0.0 |
| `shipping_to_amazon` | Cost to ship into Amazon ($) | 0.0 |
| `prep_cost` | Labels, poly bags, labor ($) | 0.0 |
| `cashback_percent` | Portal cashback % on buy cost | 0.0 |
| `sales_tax_percent` | Tax % on purchase | 0.0 |
| `coupon_discount` | Flat dollar coupon or discount ($) | 0.0 |
| `storage_cost` | Estimated storage overhead ($) | 0.0 |
| `return_risk_percent` | Return cost as % of sell price | 0.0 |
| `misc_buffer` | Catch-all cost buffer ($) | 0.0 |

---

## Recommendation Thresholds

Defaults reflect a solid arbitrage standard. All thresholds are configurable
via `RecommendationConfig`.

| Signal | BUY | WATCH | PASS |
|--------|-----|-------|------|
| ROI | ≥ 30% | ≥ 15% | < 15% |
| Margin | ≥ 15% | any | — |
| Seller count | ≤ 20 | > 20 flags | — |
| BSR | ≤ 150,000 | > 150k flags | — |

---

## Current Status

| Module | Tests | Status |
|--------|-------|--------|
| Product model | 2 | ✅ Passing |
| Profit calculator | 2 | ✅ Passing |
| Amazon client + mock | 6 | ✅ Passing |
| Sourcing service | 6 | ✅ Passing |
| Recommendation engine | 7 | ✅ Passing |
| FastAPI /evaluate | 4 | ✅ Passing |
| **Total** | **27** | ✅ **All passing** |

---

## Roadmap

- [x] Profit calculator — true cost math with all real fees
- [x] Product model — clean sourcing opportunity data structure
- [x] Amazon client interface + MockAmazonClient
- [x] Sourcing service pipeline — end-to-end orchestration
- [x] Recommendation engine — Buy/Watch/Pass with configurable thresholds
- [x] FastAPI `/evaluate` endpoint with Swagger UI
- [ ] Keepa API integration — real price history, BSR, seller count
- [ ] First retailer scraper — Kohl's
- [ ] Additional retailers — Walmart, Target
- [ ] deal_resolver — retailer-specific discount and coupon parsing
- [ ] React dashboard — visual sourcing interface
- [ ] Alerts and deal monitoring
- [ ] Return risk scoring from review sentiment analysis