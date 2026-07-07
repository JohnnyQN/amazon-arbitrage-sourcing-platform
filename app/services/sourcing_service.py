from dataclasses import dataclass
from typing import Optional

from app.amazon.amazon_client import AmazonClient, AmazonProduct
from app.calculations.profit_calculator import ProfitInput, ProfitResult, calculate_profit
from app.models.product import Product
from app.services.recommendation_engine import (
    RecommendationConfig,
    RecommendationResult,
    evaluate_opportunity,
)


@dataclass
class CostAssumptions:
    """
    User-defined cost assumptions that vary per deal.
    Separate from Product facts because they can change
    without the underlying product changing.
    """
    amazon_referral_fee_percent: float = 15.0
    fba_fee: float = 0.0
    shipping_to_you: float = 0.0
    shipping_to_amazon: float = 0.0
    prep_cost: float = 0.0
    cashback_percent: float = 0.0
    sales_tax_percent: float = 0.0
    coupon_discount: float = 0.0
    storage_cost: float = 0.0
    return_risk_percent: float = 0.0
    misc_buffer: float = 0.0


@dataclass
class SourcingResult:
    """
    Full output of the sourcing pipeline for one product.
    Combines retailer product, matched Amazon data,
    resolved inputs, profit calculation, and recommendation.
    """
    product: Product
    amazon_product: Optional[AmazonProduct]
    profit_input: Optional[ProfitInput]
    profit_result: Optional[ProfitResult]
    recommendation: Optional[RecommendationResult]
    error: Optional[str] = None


class SourcingService:
    """
    Orchestrates the full sourcing pipeline:
    1. Takes a retailer Product and cost assumptions
    2. Looks up matching Amazon data via AmazonClient
    3. Builds ProfitInput from combined data
    4. Runs profit calculation
    5. Runs recommendation engine
    6. Returns complete SourcingResult
    """

    def __init__(
        self,
        amazon_client: AmazonClient,
        recommendation_config: Optional[RecommendationConfig] = None,
    ):
        self.amazon_client = amazon_client
        self.recommendation_config = recommendation_config or RecommendationConfig()

    def evaluate_product(
        self,
        product: Product,
        assumptions: CostAssumptions,
    ) -> SourcingResult:
        """
        Run the full sourcing pipeline for a single product.
        Returns a SourcingResult with all resolved data.
        """

        # Step 1: match product to Amazon listing via ASIN
        amazon_product = None
        if product.asin:
            amazon_product = self.amazon_client.get_product_by_asin(product.asin)

        if not amazon_product:
            return SourcingResult(
                product=product,
                amazon_product=None,
                profit_input=None,
                profit_result=None,
                recommendation=None,
                error="No matching Amazon product found for ASIN.",
            )

        # Step 2: determine sell price
        sell_price = amazon_product.current_price
        if not sell_price:
            return SourcingResult(
                product=product,
                amazon_product=amazon_product,
                profit_input=None,
                profit_result=None,
                recommendation=None,
                error="Amazon product has no current price.",
            )

        # Step 3: determine buy cost
        buy_cost = product.retailer_price
        if not buy_cost:
            return SourcingResult(
                product=product,
                amazon_product=amazon_product,
                profit_input=None,
                profit_result=None,
                recommendation=None,
                error="Product has no retailer price.",
            )

        # Step 4: build ProfitInput
        profit_input = ProfitInput(
            buy_cost=buy_cost,
            amazon_sell_price=sell_price,
            amazon_referral_fee_percent=assumptions.amazon_referral_fee_percent,
            fba_fee=assumptions.fba_fee,
            shipping_to_you=assumptions.shipping_to_you,
            shipping_to_amazon=assumptions.shipping_to_amazon,
            prep_cost=assumptions.prep_cost,
            cashback_percent=assumptions.cashback_percent,
            sales_tax_percent=assumptions.sales_tax_percent,
            coupon_discount=assumptions.coupon_discount,
            storage_cost=assumptions.storage_cost,
            return_risk_percent=assumptions.return_risk_percent,
            misc_buffer=assumptions.misc_buffer,
        )

        # Step 5: run profit calculation
        profit_result = calculate_profit(profit_input)

        # Step 6: run recommendation engine
        recommendation = evaluate_opportunity(
            profit_result=profit_result,
            amazon_product=amazon_product,
            config=self.recommendation_config,
        )

        return SourcingResult(
            product=product,
            amazon_product=amazon_product,
            profit_input=profit_input,
            profit_result=profit_result,
            recommendation=recommendation,
        )