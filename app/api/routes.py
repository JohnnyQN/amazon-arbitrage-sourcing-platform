from fastapi import APIRouter, Depends, HTTPException, Query

from app.amazon.amazon_client import MockAmazonClient
from app.api.dependencies import get_evaluation_repository
from app.mappers.evaluation_mapper import build_evaluation_record
from app.models.product import Product
from app.repositories.evaluation_repository import EvaluationRepository
from app.schemas.evaluation import (
    AmazonProductOutput,
    EvaluateRequest,
    EvaluateResponse,
    EvaluationRecordResponse,
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

router = APIRouter(tags=["Evaluations"])


# ---------------------------------------------------------------------------
# Evaluation history — read-only
#
# Route definition order matters. FastAPI matches routes in the order they
# are registered. /evaluations/asin/{asin} must appear before
# /evaluations/{evaluation_id} so the literal path segment "asin" is never
# misinterpreted as an integer evaluation_id, which would cause a 422 before
# the ASIN route is ever considered.
# ---------------------------------------------------------------------------

@router.get(
    "/evaluations",
    response_model=list[EvaluationRecordResponse],
    summary="List evaluation history",
    description=(
        "Return all saved evaluations, newest first. "
        "Results are capped by the `limit` parameter (default 50, max 200). "
        "Returns an empty list when the database contains no evaluations."
    ),
    responses={
        422: {"description": "limit is below 1 or above 200"},
    },
)
def list_evaluations(
    limit: int = Query(
        default=50,
        ge=1,
        le=200,
        description="Maximum number of records to return (1–200).",
    ),
    repo: EvaluationRepository = Depends(get_evaluation_repository),
):
    records = repo.list_all(limit=limit)
    return [EvaluationRecordResponse.model_validate(r) for r in records]


@router.get(
    "/evaluations/asin/{asin}",
    response_model=list[EvaluationRecordResponse],
    summary="List evaluations by ASIN",
    description=(
        "Return evaluation history for a specific Amazon ASIN, newest first. "
        "Returns an empty list when no records exist for the ASIN — not 404. "
        "Results are capped by the `limit` parameter (default 50, max 200)."
    ),
    responses={
        422: {"description": "limit is below 1 or above 200"},
    },
)
def list_evaluations_by_asin(
    asin: str,
    limit: int = Query(
        default=50,
        ge=1,
        le=200,
        description="Maximum number of records to return (1–200).",
    ),
    repo: EvaluationRepository = Depends(get_evaluation_repository),
):
    records = repo.list_by_asin(asin, limit=limit)
    return [EvaluationRecordResponse.model_validate(r) for r in records]


@router.get(
    "/evaluations/{evaluation_id}",
    response_model=EvaluationRecordResponse,
    summary="Get evaluation by ID",
    description=(
        "Return a single complete evaluation snapshot by its database ID. "
        "Includes all input assumptions, calculated profit fields, "
        "Amazon listing snapshot, and recommendation."
    ),
    responses={
        404: {"description": "No evaluation found with the given ID"},
    },
)
def get_evaluation(
    evaluation_id: int,
    repo: EvaluationRepository = Depends(get_evaluation_repository),
):
    record = repo.get_by_id(evaluation_id)
    if record is None:
        raise HTTPException(
            status_code=404,
            detail=f"No evaluation found with id {evaluation_id}.",
        )
    return EvaluationRecordResponse.model_validate(record)


# ---------------------------------------------------------------------------
# Sourcing evaluation
# ---------------------------------------------------------------------------

@router.post(
    "/evaluate",
    response_model=EvaluateResponse,
    summary="Evaluate a product",
    description=(
        "Evaluate a retail product as an Amazon arbitrage opportunity. "
        "Calculates true profitability after all cost assumptions and returns "
        "a BUY / WATCH / PASS recommendation with explanation. "
        "Successful evaluations are persisted and retrievable by `evaluation_id`. "
        "Failed evaluations are not persisted.\n\n"
        "**Note:** Amazon data currently comes from a mock provider. "
        "Recognized ASINs are `B000EXAMPLE` and `B000TOASTER`."
    ),
    responses={
        404: {"description": "ASIN not found in Amazon data"},
        422: {
            "description": (
                "Missing ASIN, missing retailer price, "
                "or invalid input values (negative fees, "
                "cashback above 100%, sales tax above 30%, etc.)"
            )
        },
    },
)
def evaluate_product(
    request: EvaluateRequest,
    repo: EvaluationRepository = Depends(get_evaluation_repository),
):
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

    # Defensive guard — save() must always return a record with an ID.
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