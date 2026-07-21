from fastapi import APIRouter, Depends, HTTPException

from app.amazon.amazon_client import MockAmazonClient
from app.api.dependencies import get_evaluation_repository
from app.mappers.evaluation_mapper import build_evaluation_record
from app.models.product import Product
from app.repositories.evaluation_repository import EvaluationRepository
from app.schemas.evaluation import (
    AmazonProductOutput,
    EvaluateRequest,
    EvaluateResponse,
    ProfitResultOutput,
    RecommendationOutput,
)
from app.services.exceptions import (
    AmazonProductNotFoundError,
    MissingAsinError,
    MissingRetailerPriceError,
)
from app.services.recommendation_engine import RecommendationConfig
from app.services.sourcing_service import CostAssumptions, SourcingService

router = APIRouter()


@router.post("/evaluate", response_model=EvaluateResponse)
def evaluate_product(
    request: EvaluateRequest,
    repo: EvaluationRepository = Depends(get_evaluation_repository),
):
    """
    Evaluate a retail product as an Amazon arbitrage opportunity.
    Returns profit analysis and Buy/Watch/Pass recommendation.
    Persists successful evaluations and returns the generated evaluation_id.

    Raises:
        422 if the product is missing an ASIN or retailer price.
        404 if the ASIN does not match a known Amazon listing.
    """
    product = Product(
        name=request.product.name,
        brand=request.product.brand,
        upc=request.product.upc,
        category=request.product.category,
        retailer_name=request.product.retailer_name,
        retailer_price=request.product.retailer_price,
        retailer_url=request.product.retailer_url,
        date_found=request.product.date_found,
        asin=request.product.asin,
        amazon_price=request.product.amazon_price,
        amazon_bsr=request.product.amazon_bsr,
        amazon_category=request.product.amazon_category,
    )

    assumptions = CostAssumptions(
        amazon_referral_fee_percent=request.assumptions.amazon_referral_fee_percent,
        fba_fee=request.assumptions.fba_fee,
        shipping_to_you=request.assumptions.shipping_to_you,
        shipping_to_amazon=request.assumptions.shipping_to_amazon,
        prep_cost=request.assumptions.prep_cost,
        cashback_percent=request.assumptions.cashback_percent,
        sales_tax_percent=request.assumptions.sales_tax_percent,
        coupon_discount=request.assumptions.coupon_discount,
        storage_cost=request.assumptions.storage_cost,
        return_risk_percent=request.assumptions.return_risk_percent,
        misc_buffer=request.assumptions.misc_buffer,
    )

    service = SourcingService(
        amazon_client=MockAmazonClient(),
        recommendation_config=RecommendationConfig(),
    )

    # Domain failures raise exceptions — nothing is persisted
    try:
        result = service.evaluate_product(product, assumptions)
    except MissingAsinError as e:
        raise HTTPException(status_code=422, detail=str(e))
    except AmazonProductNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except MissingRetailerPriceError as e:
        raise HTTPException(status_code=422, detail=str(e))

    # Only successful evaluations are persisted
    record = build_evaluation_record(result, assumptions)
    saved = repo.save(record)

    # Defensive guard — save() should always return a record with an ID.
    # If it does not, something is wrong at the repository level and we
    # should fail loudly rather than return a response with a null ID.
    if saved.id is None:
        raise RuntimeError(
            "Evaluation repository returned a saved record without an ID. "
            "This indicates a bug in the repository layer."
        )

    return EvaluateResponse(
        evaluation_id=saved.id,
        product_name=product.name,
        amazon_product=AmazonProductOutput(
            asin=result.amazon_product.asin,
            title=result.amazon_product.title,
            brand=result.amazon_product.brand,
            category=result.amazon_product.category,
            current_price=result.amazon_product.current_price,
            bsr=result.amazon_product.bsr,
            seller_count=result.amazon_product.seller_count,
            review_rating=result.amazon_product.review_rating,
        ),
        profit_result=ProfitResultOutput(
            net_profit=result.profit_result.net_profit,
            roi_percent=result.profit_result.roi_percent,
            margin_percent=result.profit_result.margin_percent,
            total_cost=result.profit_result.total_cost,
            total_fees=result.profit_result.total_fees,
            cashback_amount=result.profit_result.cashback_amount,
            sales_tax_amount=result.profit_result.sales_tax_amount,
            return_risk_cost=result.profit_result.return_risk_cost,
        ),
        recommendation=RecommendationOutput(
            recommendation=result.recommendation.recommendation.value,
            reasons=result.recommendation.reasons,
        ),
    )