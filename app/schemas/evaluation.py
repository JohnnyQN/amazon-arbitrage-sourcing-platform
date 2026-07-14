from datetime import date
from typing import Optional

from pydantic import BaseModel, Field


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
    amazon_referral_fee_percent: float = Field(
        default=15.0,
        ge=0,
        le=100,
    )
    fba_fee: float = Field(default=0.0, ge=0)
    shipping_to_you: float = Field(default=0.0, ge=0)
    shipping_to_amazon: float = Field(default=0.0, ge=0)
    prep_cost: float = Field(default=0.0, ge=0)
    cashback_percent: float = Field(
        default=0.0,
        ge=0,
        le=100,
    )
    sales_tax_percent: float = Field(
        default=0.0,
        ge=0,
        le=30,
    )
    coupon_discount: float = Field(default=0.0, ge=0)
    storage_cost: float = Field(default=0.0, ge=0)
    return_risk_percent: float = Field(
        default=0.0,
        ge=0,
        le=100,
    )
    misc_buffer: float = Field(default=0.0, ge=0)


class EvaluateRequest(BaseModel):
    product: ProductInput
    assumptions: CostAssumptionsInput = Field(
        default_factory=CostAssumptionsInput
    )


class AmazonProductOutput(BaseModel):
    asin: str
    title: str
    brand: Optional[str] = None
    category: Optional[str] = None
    current_price: Optional[float] = None
    bsr: Optional[int] = None
    seller_count: Optional[int] = Field(default=None, ge=0)
    review_rating: Optional[float] = Field(
        default=None,
        ge=0,
        le=5,
    )


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
    product_name: str
    amazon_product: AmazonProductOutput
    profit_result: ProfitResultOutput
    recommendation: RecommendationOutput