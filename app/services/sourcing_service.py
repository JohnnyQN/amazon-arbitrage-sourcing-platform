from dataclasses import dataclass
from typing import Optional

from app.amazon.amazon_client import AmazonClient, AmazonProduct
from app.calculations.profit_calculator import ProfitInput, ProfitResult, calculate_profit
from app.models.product import Product
from app.services.exceptions import (
    AmazonProductNotFoundError,
    MissingAsinError,
    MissingRetailerPriceError,
)
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
    Only exists when the pipeline completed successfully.
    Failures raise exceptions rather than populating this object.
    """
    product: Product
    amazon_product: AmazonProduct
    profit_input: ProfitInput
    profit_result: ProfitResult
    recommendation: RecommendationResult


class SourcingService:
    """
    Orchestrates the full sourcing pipeline:
    1. Validates product has enough data to evaluate
    2. Looks up matching Amazon data via AmazonClient
    3. Builds ProfitInput from combined data and cost assumptions
    4. Runs profit calculation
    5. Runs recommendation engine
    6. Returns complete SourcingResult

    Raises:
        MissingAsinError: product has no ASIN
        AmazonProductNotFoundError: ASIN provided but not found in Amazon data
        MissingRetailerPriceError: product has no retailer price
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
        # Step 1: require an ASIN before attempting any lookup
        # is None used deliberately - empty string and None are different problems
        if product.asin is None:
            raise MissingAsinError(
                f"Product '{product.name}' has no ASIN. "
                "An ASIN is required to match against Amazon."
            )

        # Step 2: look up the Amazon listing
        amazon_product = self.amazon_client.get_product_by_asin(product.asin)

        # Step 3: ASIN was provided but no listing was found
        if amazon_product is None:
            raise AmazonProductNotFoundError(
                f"No Amazon listing found for ASIN '{product.asin}'. "
                "The ASIN may be invalid or delisted."
            )

        # Step 4: require a retailer price to calculate profit
        # is None used deliberately - a price of 0.0 is valid data, not missing data
        if product.retailer_price is None:
            raise MissingRetailerPriceError(
                f"Product '{product.name}' has no retailer price. "
                "A buy cost is required to calculate profitability."
            )

        # Step 5: require a sell price from the Amazon listing
        if amazon_product.current_price is None:
            raise AmazonProductNotFoundError(
                f"Amazon listing for ASIN '{product.asin}' has no current price. "
                "Cannot calculate profitability without a sell price."
            )

        # Step 6: build ProfitInput from product facts and cost assumptions
        profit_input = ProfitInput(
            buy_cost=product.retailer_price,
            amazon_sell_price=amazon_product.current_price,
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

        # Step 7: run profit calculation
        profit_result = calculate_profit(profit_input)

        # Step 8: run recommendation engine
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