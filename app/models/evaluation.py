from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Optional


@dataclass(frozen=True, kw_only=True)
class EvaluationRecord:
    """
    Immutable snapshot of a single completed product evaluation.
    Each instance corresponds to one row in the evaluations table.

    frozen=True: fields cannot be mutated after construction.
    kw_only=True: all fields must be passed by keyword, preventing
                  positional argument errors when fields are added or reordered.

    `id` is None before the record is saved to the database.
    After save(), a new record is returned via dataclasses.replace()
    with id populated — the original record is never mutated.

    `evaluated_at` must be timezone-aware. Naive datetimes are rejected
    by the repository to prevent silent UTC/local time ambiguity.
    """

    # Set by the database on insert — None before first save
    id: Optional[int]

    # Evaluation metadata
    evaluated_at: datetime

    # Product / retailer
    product_name: str                       # required
    product_brand: Optional[str]
    product_upc: Optional[str]
    product_category: Optional[str]
    retailer_name: Optional[str]
    retailer_price: float                   # required
    retailer_url: Optional[str]

    # Amazon listing snapshot
    asin: str                               # required
    amazon_price: float                     # required
    amazon_bsr: Optional[int]
    amazon_category: Optional[str]
    amazon_title: str                       # required
    amazon_brand: Optional[str]
    amazon_seller_count: Optional[int]
    amazon_review_rating: Optional[float]

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