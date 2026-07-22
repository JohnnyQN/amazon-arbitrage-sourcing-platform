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
    Pydantic response model for a persisted EvaluationRecord snapshot.

    from_attributes=True allows model_validate(record) to read fields
    directly from the frozen EvaluationRecord dataclass without manual
    field-by-field construction in route handlers.

    evaluated_at is a timezone-aware datetime. FastAPI serializes it as
    an ISO 8601 string with UTC offset, e.g. 2026-07-13T12:00:00+00:00.
    """
    model_config = ConfigDict(from_attributes=True)

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