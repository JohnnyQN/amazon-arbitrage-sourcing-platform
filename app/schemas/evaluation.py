from datetime import date, datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict, Field


# ---------------------------------------------------------------------------
# Request models
# ---------------------------------------------------------------------------

class ProductInput(BaseModel):
    name: str
    brand: Optional[str] = None
    upc: Optional[str] = None
    category: Optional[str] = None

    retailer_name: Optional[str] = None
    retailer_price: Optional[float] = Field(default=None, ge=0)
    retailer_url: Optional[str] = None
    date_found: Optional[date] = None

    asin: Optional[str] = None
    amazon_price: Optional[float] = Field(default=None, ge=0)
    amazon_bsr: Optional[int] = Field(default=None, gt=0)
    amazon_category: Optional[str] = None


class CostAssumptionsInput(BaseModel):
    amazon_referral_fee_percent: float = Field(default=15.0, ge=0, le=100)
    fba_fee: float = Field(default=0.0, ge=0)
    shipping_to_you: float = Field(default=0.0, ge=0)
    shipping_to_amazon: float = Field(default=0.0, ge=0)
    prep_cost: float = Field(default=0.0, ge=0)
    cashback_percent: float = Field(default=0.0, ge=0, le=100)
    sales_tax_percent: float = Field(default=0.0, ge=0, le=30)
    coupon_discount: float = Field(default=0.0, ge=0)
    storage_cost: float = Field(default=0.0, ge=0)
    return_risk_percent: float = Field(default=0.0, ge=0, le=100)
    misc_buffer: float = Field(default=0.0, ge=0)


class EvaluateRequest(BaseModel):
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "product": {
                    "name": "Nike Air Max 90",
                    "asin": "B000EXAMPLE",
                    "retailer_name": "Kohl's",
                    "retailer_price": 45.00,
                    "brand": "Nike",
                    "category": "Shoes",
                },
                "assumptions": {
                    "fba_fee": 7.50,
                    "shipping_to_amazon": 2.00,
                    "prep_cost": 0.75,
                    "cashback_percent": 6.0,
                    "amazon_referral_fee_percent": 15.0,
                },
            }
        }
    )

    product: ProductInput
    assumptions: CostAssumptionsInput = Field(
        default_factory=CostAssumptionsInput
    )


# ---------------------------------------------------------------------------
# Response models — POST /evaluate
# ---------------------------------------------------------------------------

class AmazonProductOutput(BaseModel):
    asin: str
    title: str
    brand: Optional[str] = None
    category: Optional[str] = None
    current_price: Optional[float] = None
    bsr: Optional[int] = None
    seller_count: Optional[int] = Field(default=None, ge=0)
    review_rating: Optional[float] = Field(default=None, ge=0, le=5)


class ProfitResultOutput(BaseModel):
    net_profit: float
    roi_percent: float
    margin_percent: float
    total_cost: float
    total_fees: float
    cashback_amount: float
    sales_tax_amount: float
    return_risk_cost: float


class RecommendationOutput(BaseModel):
    recommendation: str
    reasons: list[str]


class EvaluateResponse(BaseModel):
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
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
                    "review_rating": 4.5,
                },
                "profit_result": {
                    "net_profit": 23.94,
                    "roi_percent": 53.2,
                    "margin_percent": 26.6,
                    "total_cost": 66.05,
                    "total_fees": 21.00,
                    "cashback_amount": 2.70,
                    "sales_tax_amount": 0.0,
                    "return_risk_cost": 0.0,
                },
                "recommendation": {
                    "recommendation": "BUY",
                    "reasons": ["Meets all thresholds."],
                },
            }
        }
    )

    evaluation_id: int
    product_name: str
    amazon_product: AmazonProductOutput
    profit_result: ProfitResultOutput
    recommendation: RecommendationOutput


# ---------------------------------------------------------------------------
# Response model — GET /evaluations history endpoints
# ---------------------------------------------------------------------------

class EvaluationRecordResponse(BaseModel):
    """
    Complete persisted snapshot of one evaluation.

    from_attributes=True allows model_validate(record) to read fields
    directly from the frozen EvaluationRecord dataclass without manual
    field-by-field construction in route handlers.

    evaluated_at is serialized as a timezone-aware ISO 8601 string.
    """
    model_config = ConfigDict(
        from_attributes=True,
        json_schema_extra={
            "example": {
                "id": 1,
                "evaluated_at": "2026-07-13T12:00:00.000000+00:00",
                "product_name": "Nike Air Max 90",
                "product_brand": "Nike",
                "product_upc": None,
                "product_category": "Shoes",
                "retailer_name": "Kohl's",
                "retailer_price": 45.00,
                "retailer_url": None,
                "asin": "B000EXAMPLE",
                "amazon_price": 89.99,
                "amazon_bsr": 1500,
                "amazon_category": "Shoes",
                "amazon_title": "Nike Air Max 90",
                "amazon_brand": "Nike",
                "amazon_seller_count": 8,
                "amazon_review_rating": 4.5,
                "amazon_referral_fee_percent": 15.0,
                "fba_fee": 7.50,
                "shipping_to_you": 0.0,
                "shipping_to_amazon": 2.00,
                "prep_cost": 0.75,
                "cashback_percent": 6.0,
                "sales_tax_percent": 0.0,
                "coupon_discount": 0.0,
                "storage_cost": 0.0,
                "return_risk_percent": 0.0,
                "misc_buffer": 0.0,
                "net_profit": 23.94,
                "roi_percent": 53.2,
                "margin_percent": 26.6,
                "total_cost": 66.05,
                "total_fees": 21.00,
                "cashback_amount": 2.70,
                "sales_tax_amount": 0.0,
                "return_risk_cost": 0.0,
                "recommendation": "BUY",
                "recommendation_reasons": ["Meets all thresholds."],
            }
        },
    )

    # Identity
    id: int
    evaluated_at: datetime

    # Product / retailer
    product_name: str
    product_brand: Optional[str] = None
    product_upc: Optional[str] = None
    product_category: Optional[str] = None
    retailer_name: Optional[str] = None
    retailer_price: float
    retailer_url: Optional[str] = None

    # Amazon listing snapshot
    asin: str
    amazon_price: float
    amazon_bsr: Optional[int] = None
    amazon_category: Optional[str] = None
    amazon_title: str
    amazon_brand: Optional[str] = None
    amazon_seller_count: Optional[int] = None
    amazon_review_rating: Optional[float] = None

    # Cost assumptions
    amazon_referral_fee_percent: float
    fba_fee: float
    shipping_to_you: float
    shipping_to_amazon: float
    prep_cost: float
    cashback_percent: float
    sales_tax_percent: float
    coupon_discount: float
    storage_cost: float
    return_risk_percent: float
    misc_buffer: float

    # Profit result
    net_profit: float
    roi_percent: float
    margin_percent: float
    total_cost: float
    total_fees: float
    cashback_amount: float
    sales_tax_amount: float
    return_risk_cost: float

    # Recommendation
    recommendation: str
    recommendation_reasons: list[str]