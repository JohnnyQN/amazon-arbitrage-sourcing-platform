from datetime import datetime, timezone

from app.models.evaluation import EvaluationRecord
from app.services.sourcing_service import CostAssumptions, SourcingResult


def build_evaluation_record(
    result: SourcingResult,
    assumptions: CostAssumptions,
) -> EvaluationRecord:
    """
    Convert a completed sourcing pipeline result into an EvaluationRecord
    ready for persistence.

    Accepts SourcingResult directly rather than a separate Product argument.
    result.product is the authoritative source of product data — this prevents
    a caller from passing a mismatched Product and SourcingResult.

    Only called after SourcingService.evaluate_product() returns successfully.
    All fields on SourcingResult are guaranteed non-None at this point.

    Sets:
        id=None       — the database assigns the real ID on insert
        evaluated_at  — UTC timestamp at the moment of mapping
    """
    product = result.product

    return EvaluationRecord(
        id=None,
        evaluated_at=datetime.now(timezone.utc),

        # Product / retailer
        product_name=product.name,
        product_brand=product.brand,
        product_upc=product.upc,
        product_category=product.category,
        retailer_name=product.retailer_name,
        retailer_price=product.retailer_price,
        retailer_url=product.retailer_url,

        # Amazon listing snapshot
        asin=result.amazon_product.asin,
        amazon_price=result.amazon_product.current_price,
        amazon_bsr=result.amazon_product.bsr,
        amazon_category=result.amazon_product.category,
        amazon_title=result.amazon_product.title,
        amazon_brand=result.amazon_product.brand,
        amazon_seller_count=result.amazon_product.seller_count,
        amazon_review_rating=result.amazon_product.review_rating,

        # Cost assumptions
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

        # Profit result
        net_profit=result.profit_result.net_profit,
        roi_percent=result.profit_result.roi_percent,
        margin_percent=result.profit_result.margin_percent,
        total_cost=result.profit_result.total_cost,
        total_fees=result.profit_result.total_fees,
        cashback_amount=result.profit_result.cashback_amount,
        sales_tax_amount=result.profit_result.sales_tax_amount,
        return_risk_cost=result.profit_result.return_risk_cost,

        # Recommendation — .value converts enum to string for storage
        recommendation=result.recommendation.recommendation.value,
        recommendation_reasons=result.recommendation.reasons,
    )