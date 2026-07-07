# Amazon Arbitrage App - Project Context

## Purpose

This app is an Amazon arbitrage sourcing intelligence platform.

The goal is to help evaluate whether a product is worth buying for resale on Amazon by combining:

- retailer purchase data
- Amazon selling data
- true cost calculations
- Keepa historical pricing data
- return-risk estimates
- buy/pass recommendations

The app is being built both as a real business tool and as a software engineering portfolio project.

## Current Development Goal

Build a resume-ready MVP first, not the entire full-scale arbitrage platform.

The first major milestone is an end-to-end workflow:

1. Input or scan a retailer product
2. Match it to an Amazon listing
3. Calculate true profitability
4. Use historical/risk data where available
5. Return a buy/pass/watch recommendation

## Current Tech Stack

- Python 3.13.14
- FastAPI planned
- pytest for testing
- python-dotenv for environment variables
- requests / BeautifulSoup for early data fetching
- pandas for data handling
- Keepa API planned

## Current Environment

- Windows CMD
- Project path: C:\Users\johnn\amazon-arbitrage-app
- Virtual environment: venv
- pytest configured with pytest.ini

## Current Project Structure

```text
amazon-arbitrage-app/
├── app/
│   ├── __init__.py
│   ├── main.py
│   ├── amazon/
│   ├── api/
│   ├── calculations/
│   │   ├── __init__.py
│   │   └── profit_calculator.py
│   ├── core/
│   ├── keepa/
│   ├── models/
│   ├── retailers/
│   └── utils/
├── tests/
│   └── test_profit_calculator.py
├── config/
├── data/
├── .env
├── README.md
├── requirements.txt
├── pytest.ini
├── PROJECT_CONTEXT.md
├── AI_HANDOFF.md
├── TODO.md
├── DECISIONS.md
└── ROADMAP.md


Current Working Feature

The first working module is the profit calculator.

Current supported inputs:

buy_cost
amazon_sell_price
amazon_referral_fee_percent
fba_fee
shipping_to_you
shipping_to_amazon
prep_cost
cashback_percent

Current tested result:

ProfitResult(
    net_profit=19.24,
    roi_percent=38.48,
    margin_percent=21.38,
    total_cost=70.75,
    total_fees=21.0,
    cashback_amount=3.0
)
Profit Calculator Direction

The calculator should eventually account for:

retailer purchase price
sales tax
coupons / discounts
cashback
retailer shipping
shipping to prep center
shipping into Amazon
prep materials
Amazon referral fee
Amazon FBA fee
storage cost
return-risk adjustment
miscellaneous cost buffer
Architecture Principles

Do not build this as loose scripts.

Use:

clean modules
dataclasses or Pydantic models
automated tests
small incremental changes
readable business logic
clear separation of concerns
AI Collaboration Workflow

ChatGPT is acting as technical lead / architect.

Claude is being used as implementation support.

All major decisions should be captured in:

DECISIONS.md
PROJECT_CONTEXT.md
AI_HANDOFF.md
TODO.md
ROADMAP.md

The codebase and Markdown files are the shared memory between AI tools.

Near-Term MVP Priority

Resume-ready MVP in 6-8 weeks.

Must demonstrate:

clean architecture
tests
modular design
Amazon/Keepa integration
one retailer integration
end-to-end profitability workflow
strong README/demo

Full daily-driver arbitrage platform can continue after that.