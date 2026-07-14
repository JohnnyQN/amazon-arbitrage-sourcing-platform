# Amazon Arbitrage Sourcing Platform

A Python backend that evaluates retail products as Amazon arbitrage opportunities by calculating true profitability, analyzing marketplace risk, and returning a **BUY / WATCH /PASS** recommendation through a clean REST API.

Built as both a real business tool and a software engineering portfolio project.

---

# Motivation

While sourcing products for Amazon FBA, I found that most arbitrage tools act as black boxes—they provide a recommendation without clearly explaining how it was reached or allowing easy customization of the underlying assumptions.

I built this project to solve a real workflow that I personally use. Rather than recreating a tutorial application, I focused on designing software that is modular, testable, and easy to extend while accurately modeling the financial decisions involved in sourcing products.

The long-term goal is to evolve this into a production sourcing platform capable of integrating multiple retailers, Keepa, Amazon SP-API, and automated deal monitoring.

---

# Engineering Highlights

- Layered architecture with clear separation of concerns
- Dependency injection for configurable services
- Fully modular service-oriented design
- Mock-driven development before external API integration
- REST API built with FastAPI
- Typed request/response models using Pydantic
- 27 automated tests covering business logic and API endpoints
- Configurable recommendation engine
- Business logic completely separated from the HTTP layer

---

# What It Does

Given a retail product and user-defined cost assumptions, the application:

1. Matches the product to an Amazon listing (currently via mock data)
2. Calculates true profitability after all sourcing costs
3. Evaluates marketplace risk signals
4. Returns a **BUY**, **WATCH**, or **PASS** recommendation with supporting reasons

---

# Architecture

```
Retailer Product + Cost Assumptions
                │
                ▼
        SourcingService
                │
                ▼
        AmazonClient
 (Mock → Keepa → SP-API)
                │
                ▼
      ProfitCalculator
                │
                ▼
   RecommendationEngine
                │
                ▼
      FastAPI REST API
```

The architecture intentionally separates:

- Product data
- Amazon data
- Financial calculations
- Recommendation logic
- HTTP API

Each layer has a single responsibility and can be tested independently.

---

# Module Overview

| Module | Purpose |
|---------|---------|
| Product | Represents retailer product information |
| ProfitCalculator | Calculates true profit, ROI, and margin |
| AmazonClient | Abstract interface for Amazon data |
| MockAmazonClient | Mock implementation used during development |
| RecommendationEngine | Evaluates sourcing opportunities |
| SourcingService | Coordinates the complete evaluation pipeline |
| FastAPI | HTTP interface for external clients |

---

# Design Decisions

Several architectural decisions were intentionally made to maximize maintainability.

### Profit calculator is retailer-agnostic

The calculator performs only financial calculations.

Retailer-specific coupon parsing and pricing logic intentionally live elsewhere so the calculator remains reusable and easy to test.

---

### Product is separate from ProfitResult

A Product represents facts.

A ProfitResult represents calculations.

Separating these prevents calculated values from becoming stale if assumptions change.

---

### AmazonClient is an abstraction

Business logic depends on an interface rather than a concrete implementation.

Current implementation:

- MockAmazonClient

Future implementations:

- KeepaClient
- Amazon SP-API Client

No business logic needs to change when swapping implementations.

---

### Dependency Injection

Services receive dependencies through constructors rather than creating them internally.

This allows:

- Mock implementations during testing
- Production implementations later
- Easier unit testing
- Greater flexibility

---

### Recommendation thresholds are configurable

Different sellers have different sourcing strategies.

Thresholds are defined through a RecommendationConfig object rather than hardcoded throughout the application.

---

# Current Features

- ✅ Product model
- ✅ Profit calculator
- ✅ Recommendation engine
- ✅ Amazon client abstraction
- ✅ Mock Amazon implementation
- ✅ End-to-end sourcing pipeline
- ✅ FastAPI REST API
- ✅ Swagger documentation
- ✅ Comprehensive automated tests

---

# Tech Stack

- Python 3.13
- FastAPI
- Pydantic
- pytest
- Uvicorn

Planned:

- Keepa API
- Amazon SP-API
- PostgreSQL
- React

---

# Project Structure

```
amazon-arbitrage-app/

app/
│
├── amazon/
├── api/
├── calculations/
├── models/
├── services/
│
├── main.py

tests/
│
├── test_api.py
├── test_amazon_client.py
├── test_product.py
├── test_profit_calculator.py
├── test_recommendation_engine.py
└── test_sourcing_service.py
```

---

# Running the Project

## Install

```bash
python -m venv venv

# Windows
venv\Scripts\activate

pip install -r requirements.txt
```

---

## Run Tests

```bash
pytest -v
```

Current status:

**27 passing tests**

---

## Start API

```bash
uvicorn app.main:app --reload
```

Swagger documentation:

```
http://127.0.0.1:8000/docs
```

---

# Example Request

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
    "cashback_percent": 6.00
  }
}
```

---

# Example Response

```json
{
  "product_name": "Nike Air Max 90",
  "recommendation": {
    "recommendation": "BUY",
    "reasons": [
      "Meets all thresholds."
    ]
  },
  "profit_result": {
    "net_profit": 23.94,
    "roi_percent": 53.2,
    "margin_percent": 26.6
  }
}
```

---

# Automated Testing

The project currently includes automated tests for:

- Profit calculations
- Product models
- Amazon client
- Recommendation engine
- Sourcing service
- FastAPI endpoints

Current coverage:

- **27 passing tests**

---

# Roadmap

## Completed

- ✅ Modular architecture
- ✅ Profit calculation engine
- ✅ Recommendation engine
- ✅ Mock Amazon client
- ✅ REST API
- ✅ Automated testing

## Planned

- Keepa integration
- Amazon SP-API integration
- Retailer integrations
    - Kohl's
    - Walmart
    - Target
- Retailer deal resolver
- Database persistence
- User authentication
- React frontend
- Automated deal monitoring
- Historical sourcing analytics
- Review sentiment analysis

---

# Why This Project?

This project serves two purposes.

First, it is intended to become a real sourcing tool that supports my Amazon FBA workflow.

Second, it demonstrates software engineering skills beyond basic CRUD applications by emphasizing architecture, testing, modularity, dependency injection, and clean separation of responsibilities.