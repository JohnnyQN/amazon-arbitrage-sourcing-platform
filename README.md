# Amazon Arbitrage Sourcing Platform

[![CI](https://github.com/JohnnyQN/amazon-arbitrage-sourcing-platform/actions/workflows/ci.yml/badge.svg)](https://github.com/JohnnyQN/amazon-arbitrage-sourcing-platform/actions/workflows/ci.yml)

A backend API for evaluating retail products as Amazon arbitrage opportunities.

Given a product found at a retailer and a set of cost assumptions, the platform calculates true profitability, analyzes competitive signals, and returns an explainable **BUY / WATCH / PASS** recommendation. All successful evaluations are persisted as immutable snapshots and retrievable by ID or ASIN.

> **Note on data sources:** Amazon product data currently comes from a mock provider.
> Real provider integrations (Keepa, Amazon SP-API) and retailer scrapers are
> planned future work and are not yet implemented.

---

## Problem Statement

Headline profit on an arbitrage deal is almost always misleading. A product that looks like a $20 gain after buying and selling often disappears once you account for:

- Amazon referral fees and FBA fulfillment fees
- Shipping to a prep center and into Amazon
- Prep labor, poly bags, and labels
- Sales tax on the purchase
- Cashback portal adjustments
- Storage fees and return overhead

Beyond cost accuracy, buy decisions also depend on whether a product actually sells. A listing with 40 competing sellers and a BSR of 300,000 is not the same opportunity as one with 5 sellers and a BSR of 1,500 — even at identical margins.

Good sourcing decisions need to be **explainable**: not just a number, but a reason why an item is worth buying or avoiding.

Finally, revisiting past evaluations matters. Prices change. A product that was marginal last month may be a strong buy today — or the opposite. Immutable historical snapshots make that comparison possible.

---

## Current Capabilities

| Capability | Status |
|---|---|
| Product evaluation via `POST /evaluate` | ✅ |
| Configurable cost assumptions (fees, shipping, prep, tax, cashback, return risk) | ✅ |
| True profitability calculation (net profit, ROI, margin, cost breakdown) | ✅ |
| BUY / WATCH / PASS recommendation with configurable thresholds | ✅ |
| Human-readable recommendation reasons | ✅ |
| Immutable evaluation snapshot persistence (SQLite) | ✅ |
| Evaluation history retrieval by ID and ASIN | ✅ |
| Newest-first history with configurable limit | ✅ |
| Environment-variable-based configuration | ✅ |
| Health endpoint for deployment readiness probes | ✅ |
| GitHub Actions CI on pushes and pull requests to `main` | ✅ |
| 127 automated tests across all layers | ✅ |
| Real retailer scraping | 🔲 Planned |
| Live Amazon data (Keepa / SP-API) | 🔲 Planned |
| Frontend dashboard | 🔲 Planned |

---

## Architecture

```mermaid
flowchart TD
    A[HTTP Request] --> B[FastAPI Route]
    B --> C[Pydantic Validation]
    C --> D[SourcingService]
    D --> E[AmazonClient\nMock today · Real API later]
    D --> F[ProfitCalculator]
    D --> G[RecommendationEngine]
    D --> H{Success?}
    H -- Yes --> I[EvaluationMapper]
    H -- No --> J[Domain Exception\n→ HTTP 422 / 404]
    I --> K[EvaluationRepository]
    K --> L[(SQLite)]
    B --> M[HTTP Response\nwith evaluation_id]

    subgraph History Read Path
        N[GET /evaluations] --> O[EvaluationRepository]
        P[GET /evaluations/{evaluation_id}] --> O
        Q[GET /evaluations/asin/{asin}] --> O
        O --> L
    end
```

### Layer Descriptions

| Layer | Location | Purpose |
|---|---|---|
| API routes | `app/api/routes.py`, `app/api/health.py` | Receives HTTP requests, calls domain services, translates domain exceptions to HTTP status codes |
| Pydantic schemas | `app/schemas/` | Validates and documents request/response shapes; separate from domain models |
| Domain models | `app/models/` | Pure Python dataclasses representing product and evaluation facts, with no HTTP knowledge |
| SourcingService | `app/services/sourcing_service.py` | Orchestrates the pipeline: lookup → calculate → recommend |
| ProfitCalculator | `app/calculations/profit_calculator.py` | Pure math: takes fully resolved cost numbers, returns profit/ROI/margin |
| RecommendationEngine | `app/services/recommendation_engine.py` | Applies configurable thresholds to profit and competitive signals; returns BUY/WATCH/PASS with reasons |
| AmazonClient | `app/amazon/amazon_client.py` | Interface abstraction; `MockAmazonClient` returns hardcoded data today; real implementations slot in without changing any other layer |
| EvaluationMapper | `app/mappers/evaluation_mapper.py` | Converts a `SourcingResult` into an `EvaluationRecord` ready for persistence |
| EvaluationRepository | `app/repositories/evaluation_repository.py` | All SQL lives here; parameterized queries only; no ORM |
| SQLite connection | `app/database/connection.py` | Custom context manager that commits on success, rolls back on exception, and always closes |
| Settings | `app/core/settings.py` | Cached frozen dataclass; reads `ARBITRAGE_*` environment variables |
| Health endpoint | `app/api/health.py` | Lightweight liveness probe; reads from settings; no database query |

---

## Design Decisions and Tradeoffs

**Domain exceptions instead of error fields**
Failed evaluations raise named Python exceptions (`MissingAsinError`, `AmazonProductNotFoundError`, `MissingRetailerPriceError`). The API layer catches them and maps each to the correct HTTP status code. This keeps business logic out of HTTP concerns and lets both layers be tested independently.

**Separate Pydantic schemas and dataclasses**
The domain uses plain frozen dataclasses. Pydantic models live only in the API layer. This means the sourcing pipeline, profit calculator, and repository have no dependency on FastAPI or Pydantic — they can be called from a CLI, a background job, or a test without dragging HTTP libraries along.

**Repository pattern**
All SQL is isolated inside `EvaluationRepository`; route handlers and business services do not issue database queries directly. Migrating to PostgreSQL would still require new connection infrastructure, configuration, migrations, and repository implementation changes, but the API and business-service contracts could largely remain unchanged.

**Dependency injection**
`get_evaluation_repository` is a FastAPI dependency. Tests override it with a `tmp_path`-backed repository. No test writes to `data/arbitrage.db`.

**Immutable evaluation snapshots**
`EvaluationRecord` is `@dataclass(frozen=True)`. Every saved evaluation is a complete snapshot of all inputs and outputs at the moment of evaluation. Records are never updated. This makes history reliable — a past evaluation always reflects what was known at that time.

**UTC timestamps with microsecond precision**
All timestamps are normalized to UTC before storage and deserialized as timezone-aware `datetime` objects. Naive datetimes are rejected at the repository boundary.

**File-backed SQLite in tests instead of `:memory:`**

Each test gets its own database file under pytest's `tmp_path`. A standard SQLite `:memory:` database belongs to a single connection, while the repository intentionally opens a fresh connection for each operation. Using a temporary file allows those separate connections to access the same isolated test database while still exercising realistic connection, transaction, and locking behavior.

**Standard-library settings instead of `pydantic-settings`**
`os.getenv` with a frozen dataclass and `lru_cache` covers all current needs without adding a dependency. `pydantic-settings` would be justified if validation of env-var types or `.env` file loading were required.

**Mock Amazon provider**
`AmazonClient` is an abstract interface. `MockAmazonClient` implements it with two hardcoded products. This allows the full pipeline — including persistence and recommendation — to be built and tested before any real API credentials exist. Keepa or SP-API integration replaces only this layer.

**SQLite instead of PostgreSQL**
SQLite requires no server, no credentials, and no setup. It is appropriate for a local development tool at this stage. The repository boundary reduces how far a future PostgreSQL migration would spread. Database connection code, configuration, migrations, and repository queries would change, while the sourcing service and API contracts could remain mostly stable.

---

## Project Structure

```
amazon-arbitrage-sourcing-platform/
├── app/
│   ├── amazon/
│   │   └── amazon_client.py          # AmazonClient interface + MockAmazonClient
│   ├── api/
│   │   ├── dependencies.py           # FastAPI dependency providers
│   │   ├── health.py                 # GET /health
│   │   └── routes.py                 # Evaluation endpoints
│   ├── calculations/
│   │   └── profit_calculator.py      # Pure profit/ROI/margin math
│   ├── core/
│   │   └── settings.py               # Centralized configuration
│   ├── database/
│   │   └── connection.py             # SQLite connection context manager
│   ├── mappers/
│   │   └── evaluation_mapper.py      # SourcingResult → EvaluationRecord
│   ├── models/
│   │   ├── evaluation.py             # EvaluationRecord frozen dataclass
│   │   └── product.py                # Product dataclass
│   ├── repositories/
│   │   └── evaluation_repository.py  # All SQLite persistence logic
│   ├── schemas/
│   │   ├── evaluation.py             # Pydantic request/response models
│   │   └── health.py                 # Health response model
│   └── services/
│       ├── exceptions.py             # Domain exception classes
│       ├── recommendation_engine.py  # BUY/WATCH/PASS logic
│       └── sourcing_service.py       # Pipeline orchestrator
├── tests/
│   ├── test_amazon_client.py
│   ├── test_api.py
│   ├── test_api_history.py
│   ├── test_evaluation_mapper.py
│   ├── test_evaluation_repository.py
│   ├── test_health.py
│   ├── test_openapi.py
│   ├── test_product.py
│   ├── test_profit_calculator.py
│   ├── test_recommendation_engine.py
│   ├── test_settings.py
│   └── test_sourcing_service.py
├── data/                             # SQLite database (git-ignored)
├── .github/
│   └── workflows/
│       └── ci.yml
├── pytest.ini
├── requirements.txt
└── README.md
```

---

## Local Setup

```powershell
git clone https://github.com/JohnnyQN/amazon-arbitrage-sourcing-platform.git
cd amazon-arbitrage-sourcing-platform
python -m venv venv
Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass
.\venv\Scripts\Activate.ps1
pip install -r requirements.txt
pytest -q
uvicorn app.main:app --reload
```

Once running:

- **Swagger UI:** http://127.0.0.1:8000/docs
- **Health check:** http://127.0.0.1:8000/health
- **OpenAPI schema:** http://127.0.0.1:8000/openapi.json

---

## Deployment

The API can be deployed to Render using the native Python runtime and the repository's `render.yaml` Blueprint.

### SQLite persistence limitation

Render free web services use an ephemeral filesystem. The SQLite database stored at `/tmp/arbitrage.db` is therefore temporary.

Local files are lost whenever the free service:

- redeploys
- restarts
- spins down

This means:

- `POST /evaluate` works normally
- The returned `evaluation_id` can be retrieved while the same instance remains active
- History endpoints work during the current instance session
- Evaluation history is erased after the service redeploys, restarts, or spins down

This limitation is acceptable for a portfolio demonstration. Durable production history would require a persistent disk on a paid service or migration to a hosted database such as PostgreSQL.

### Deploy with Render

1. Push the deployment branch and merge it into `main`.
2. Sign in to Render.
3. Choose **New → Blueprint**.
4. Connect the GitHub repository:
   `JohnnyQN/amazon-arbitrage-sourcing-platform`
5. Render will read `render.yaml` from the repository root.
6. Review the proposed free web service.
7. Click **Deploy Blueprint**.
8. Wait for the service health check to pass.

The Blueprint configures:

| Setting | Value |
|---|---|
| Runtime | Python |
| Plan | Free |
| Python version | `3.13.14` |
| Build command | `pip install -r requirements.txt` |
| Start command | `uvicorn app.main:app --host 0.0.0.0 --port $PORT` |
| Health-check path | `/health` |
| Environment | `production` |
| SQLite path | `/tmp/arbitrage.db` |

Render supplies the `PORT` environment variable automatically.

### Verify the public deployment

Replace `<service-name>` with the Render service subdomain:

```text
https://<service-name>.onrender.com/health
https://<service-name>.onrender.com/docs
https://<service-name>.onrender.com/openapi.json


## Configuration

The application reads configuration from environment variables. No `.env` file is automatically loaded — variables must be set in the shell session before starting the server.

| Variable | Default | Description |
|---|---|---|
| `ARBITRAGE_APP_NAME` | `Amazon Arbitrage Sourcing Platform` | Application display name |
| `ARBITRAGE_APP_VERSION` | `0.1.0` | API version string |
| `ARBITRAGE_APP_DESCRIPTION` | *(see settings.py)* | OpenAPI description |
| `ARBITRAGE_ENVIRONMENT` | `development` | Environment label (development / production) |
| `ARBITRAGE_DATABASE_PATH` | `data/arbitrage.db` | Path to SQLite database file |

**PowerShell example — use a custom database path:**

```powershell
$env:ARBITRAGE_DATABASE_PATH = "data\my_custom.db"
uvicorn app.main:app --reload
```

---

## API Documentation

### `GET /health`

Liveness probe. Does not query the database.

**Response `200`:**
```json
{
  "status": "ok",
  "application": "Amazon Arbitrage Sourcing Platform",
  "version": "0.1.0",
  "environment": "production"
}
```

---

### `POST /evaluate`

Evaluate a retail product as an Amazon arbitrage opportunity.

> The current mock provider recognizes ASINs `B000EXAMPLE` (Nike Air Max 90, $89.99) and `B000TOASTER` (2-Slice Toaster, $34.99). Other ASINs return 404.

**Request body:**
```json
{
  "product": {
    "name": "Nike Air Max 90",
    "asin": "B000EXAMPLE",
    "retailer_name": "Kohl's",
    "retailer_price": 45.00,
    "brand": "Nike",
    "category": "Shoes"
  },
  "assumptions": {
    "fba_fee": 7.50,
    "shipping_to_amazon": 2.00,
    "prep_cost": 0.75,
    "cashback_percent": 6.0,
    "amazon_referral_fee_percent": 15.0
  }
}
```

**Response `200`:**
```json
{
  "evaluation_id": 1,
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
    "sales_tax_amount": 0.0,
    "return_risk_cost": 0.0
  },
  "recommendation": {
    "recommendation": "BUY",
    "reasons": ["Meets all thresholds."]
  }
}
```

---

### `GET /evaluations`

Return all evaluation history, newest first.

| Parameter | Type | Default | Min | Max | Description |
|---|---|---|---|---|---|
| `limit` | integer | 50 | 1 | 200 | Maximum records to return |

**Response `200`:** Array of evaluation snapshots (same shape as `GET /evaluations/{id}`).

---

### `GET /evaluations/{evaluation_id}`

Return a single saved evaluation by ID.

**Response `200`:** Complete evaluation snapshot including all input assumptions, calculated profit fields, and recommendation.

**Response `404`:** `{"detail": "No evaluation found with id 99999."}`

---

### `GET /evaluations/asin/{asin}`

Return evaluation history for a specific ASIN, newest first.

| Parameter | Type | Default | Min | Max | Description |
|---|---|---|---|---|---|
| `limit` | integer | 50 | 1 | 200 | Maximum records to return |

Returns an empty list `[]` when no records exist for the ASIN — not 404.

---

## Error Behavior

| Scenario | Status | Detail |
|---|---|---|
| Product submitted with no ASIN | 422 | Includes product name |
| ASIN not found in Amazon data | 404 | Includes the ASIN |
| Product submitted with no retailer price | 422 | Includes product name |
| Negative retailer price or fee | 422 | Pydantic field validation |
| Cashback above 100% | 422 | Pydantic field validation |
| Sales tax above 30% | 422 | Pydantic field validation |
| Return risk above 100% | 422 | Pydantic field validation |
| BSR of 0 | 422 | Pydantic field validation |
| Unknown evaluation ID | 404 | Includes requested ID |
| Unknown ASIN in history | 200 | Empty list `[]` |

---

## Testing

```powershell
pytest -q
```

**Current result: 127 tests passing**

Test coverage spans every layer:

| Layer | Test File |
|---|---|
| Amazon client + mock | `test_amazon_client.py` |
| Product model | `test_product.py` |
| Profit calculator | `test_profit_calculator.py` |
| Recommendation engine | `test_recommendation_engine.py` |
| Sourcing service + domain exceptions | `test_sourcing_service.py` |
| Evaluation mapper | `test_evaluation_mapper.py` |
| SQLite repository | `test_evaluation_repository.py` |
| POST /evaluate API | `test_api.py` |
| History API endpoints | `test_api_history.py` |
| Settings and env overrides | `test_settings.py` |
| Health endpoint | `test_health.py` |
| OpenAPI schema | `test_openapi.py` |

All API tests inject a `tmp_path`-backed repository through FastAPI dependency overrides. No test writes to `data/arbitrage.db`.

---

## Demo Workflow

1. **Start the API**
```powershell
   uvicorn app.main:app --reload
```

2. **Open Swagger UI**
   Navigate to http://127.0.0.1:8000/docs

3. **Verify the health endpoint**
   Call `GET /health` — expect `{"status": "ok", ...}`

4. **Submit an evaluation**
   Call `POST /evaluate` with the example request above.
   Note the returned `evaluation_id`.

5. **Retrieve the evaluation by ID**
   Call `GET /evaluations/{evaluation_id}` using the ID from step 4.
   Confirm all input assumptions and calculated profit fields are present.

6. **Retrieve history by ASIN**
   Call `GET /evaluations/asin/B000EXAMPLE`.
   Each call to step 4 adds another record here.

7. **List recent evaluations**
   Call `GET /evaluations?limit=10`.
   Results appear newest first.

---

## Roadmap

### Current
- Mock Amazon product provider
- Manual product entry via API
- SQLite persistence
- Full profit and recommendation engine
- Evaluation history

### Planned
- Real Amazon data provider (Keepa API, Amazon SP-API)
- Retailer adapters (Kohl's, Walmart, Target)
- UPC and title-based ASIN matching
- Automated cashback percentage sources
- Scheduled bulk retailer scans with structured match statuses
- Deal alerts
- PostgreSQL for production persistence
- Authentication
- React dashboard
- Price forecasting models
- Apparel and footwear variant grouping (size/color)