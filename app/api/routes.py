from datetime import date
from typing import Optional

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from app.amazon.amazon_client import MockAmazonClient
from app.models.product import Product
from app.services.exceptions import (
    AmazonProductNotFoundError,
    MissingAsinError,
    MissingRetailerPriceError,
)
from app.services.recommendation_engine import RecommendationConfig
from app.services.sourcing_service import CostAssumptions, SourcingService

router = APIRouter()


# --- Request Models ---

class ProductInput(BaseModel):
    name: str
    brand: Optional[str] = None
    upc: Optional[str] = None
    category: Optional[str] = None
    retailer_name: Optional[str] = None
    retailer_price: Optional[float] = None
    retailer_url: Optional[str] = None
    date_found: Optional[date] = None
    asin: Optional[str] = None
    amazon_price: Optional[float] = None
    amazon_bsr: Optional[int] = None
    amazon_category: Optional[str] = None


class CostAssumptionsInput(BaseModel):
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


class EvaluateRequest(BaseModel):
    product: ProductInput
    assumptions: CostAssumptionsInput = CostAssumptionsInput()


# --- Response Models ---

class AmazonProductOutput(BaseModel):
    asin: str
    title: str
    brand: Optional[str] = None
    category: Optional[str] = None
    current_price: Optional[float] = None
    bsr: Optional[int] = None
    seller_count: Optional[int] = None
    review_rating: Optional[float] = None


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


# --- Endpoint ---

@router.post("/evaluate", response_model=EvaluateResponse)
def evaluate_product(request: EvaluateRequest):
    """
    Evaluate a retail product as an Amazon arbitrage opportunity.
    Returns profit analysis and Buy/Watch/Pass recommendation.

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

    try:
        result = service.evaluate_product(product, assumptions)

    except MissingAsinError as e:
        raise HTTPException(status_code=422, detail=str(e))

    except AmazonProductNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))

    except MissingRetailerPriceError as e:
        raise HTTPException(status_code=422, detail=str(e))

    return EvaluateResponse(
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