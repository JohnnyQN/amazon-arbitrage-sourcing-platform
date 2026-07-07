from dataclasses import dataclass, field
from enum import Enum
from typing import Optional

from app.amazon.amazon_client import AmazonProduct
from app.calculations.profit_calculator import ProfitResult


class Recommendation(Enum):
    BUY = "BUY"
    WATCH = "WATCH"
    PASS = "PASS"


@dataclass
class RecommendationConfig:
    """
    Thresholds used to evaluate a sourcing opportunity.
    Defaults reflect a solid arbitrage standard.
    Override any field to match your personal sourcing strategy.
    """
    # Profit thresholds
    min_roi_for_buy: float = 30.0       # ROI % to qualify as BUY
    min_roi_for_watch: float = 15.0     # ROI % to qualify as WATCH (below = PASS)
    min_margin_for_buy: float = 15.0    # Margin % required for BUY

    # Amazon listing health
    max_seller_count: int = 20          # Too many sellers = too competitive
    max_bsr: int = 150_000             # BSR above this = slow mover

    # Risk
    max_return_risk_percent: float = 5.0  # Return risk above this triggers flag


@dataclass
class RecommendationResult:
    """
    Output of the recommendation engine for a single sourcing opportunity.
    """
    recommendation: Recommendation
    reasons: list[str] = field(default_factory=list)


def evaluate_opportunity(
    profit_result: ProfitResult,
    amazon_product: Optional[AmazonProduct] = None,
    config: Optional[RecommendationConfig] = None,
) -> RecommendationResult:
    """
    Evaluate a sourcing opportunity and return a Buy/Watch/Pass recommendation.

    Logic:
    - PASS immediately if profit is negative or ROI below watch threshold
    - Collect risk flags across ROI, margin, BSR, seller count, return risk
    - BUY if ROI meets buy threshold and no critical flags
    - WATCH if ROI meets watch threshold but has flags
    - PASS otherwise
    """
    if config is None:
        config = RecommendationConfig()

    reasons = []

    # Hard PASS: negative profit
    if profit_result.net_profit <= 0:
        return RecommendationResult(
            recommendation=Recommendation.PASS,
            reasons=["Net profit is negative."],
        )

    # Hard PASS: ROI below minimum watch threshold
    if profit_result.roi_percent < config.min_roi_for_watch:
        return RecommendationResult(
            recommendation=Recommendation.PASS,
            reasons=[
                f"ROI of {profit_result.roi_percent}% is below "
                f"minimum threshold of {config.min_roi_for_watch}%."
            ],
        )

    # Collect risk flags
    roi_qualifies_for_buy = profit_result.roi_percent >= config.min_roi_for_buy
    if not roi_qualifies_for_buy:
        reasons.append(
            f"ROI of {profit_result.roi_percent}% is below "
            f"BUY threshold of {config.min_roi_for_buy}%."
        )

    margin_qualifies = profit_result.margin_percent >= config.min_margin_for_buy
    if not margin_qualifies:
        reasons.append(
            f"Margin of {profit_result.margin_percent}% is below "
            f"minimum of {config.min_margin_for_buy}%."
        )

    if amazon_product:
        if (
            amazon_product.seller_count is not None
            and amazon_product.seller_count > config.max_seller_count
        ):
            reasons.append(
                f"High seller count: {amazon_product.seller_count} "
                f"sellers (max {config.max_seller_count})."
            )

        if (
            amazon_product.bsr is not None
            and amazon_product.bsr > config.max_bsr
        ):
            reasons.append(
                f"BSR of {amazon_product.bsr} exceeds "
                f"max acceptable BSR of {config.max_bsr}."
            )

    # Determine final recommendation
    if roi_qualifies_for_buy and margin_qualifies and not reasons:
        return RecommendationResult(
            recommendation=Recommendation.BUY,
            reasons=["Meets all thresholds."],
        )

    if profit_result.roi_percent >= config.min_roi_for_watch:
        return RecommendationResult(
            recommendation=Recommendation.WATCH,
            reasons=reasons,
        )

    return RecommendationResult(
        recommendation=Recommendation.PASS,
        reasons=reasons,
    )