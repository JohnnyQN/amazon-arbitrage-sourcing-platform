from datetime import timezone

from app.amazon.amazon_client import AmazonProduct
from app.calculations.profit_calculator import ProfitInput, ProfitResult
from app.mappers.evaluation_mapper import build_evaluation_record
from app.models.product import Product
from app.services.recommendation_engine import Recommendation, RecommendationResult
from app.services.sourcing_service import CostAssumptions, SourcingResult


def make_product() -> Product:
    return Product(
        name="Nike Air Max 90",
        brand="Nike",
        upc="123456789012",
        category="Shoes",
        retailer_name="Kohl's",
        retailer_price=45.00,
        retailer_url="https://kohls.com/example",
        asin="B000EXAMPLE",
    )


def make_assumptions() -> CostAssumptions:
    return CostAssumptions(
        amazon_referral_fee_percent=15.0,
        fba_fee=7.50,
        shipping_to_you=1.00,
        shipping_to_amazon=2.00,
        prep_cost=0.75,
        cashback_percent=6.0,
        sales_tax_percent=8.0,
        coupon_discount=5.00,
        storage_cost=0.50,
        return_risk_percent=2.0,
        misc_buffer=1.00,
    )


def make_profit_input() -> ProfitInput:
    return ProfitInput(
        buy_cost=45.00,
        amazon_sell_price=89.99,
        amazon_referral_fee_percent=15.0,
        fba_fee=7.50,
        shipping_to_you=1.00,
        shipping_to_amazon=2.00,
        prep_cost=0.75,
        cashback_percent=6.0,
        sales_tax_percent=8.0,
        coupon_discount=5.00,
        storage_cost=0.50,
        return_risk_percent=2.0,
        misc_buffer=1.00,
    )


def make_profit_result() -> ProfitResult:
    return ProfitResult(
        net_profit=14.94,
        roi_percent=29.88,
        margin_percent=16.60,
        total_cost=75.05,
        total_fees=21.00,
        cashback_amount=3.00,
        sales_tax_amount=4.00,
        return_risk_cost=1.80,
    )


def make_sourcing_result() -> SourcingResult:
    product = make_product()
    return SourcingResult(
        product=product,
        amazon_product=AmazonProduct(
            asin="B000EXAMPLE",
            title="Nike Air Max 90",
            brand="Nike",
            category="Shoes",
            current_price=89.99,
            bsr=1500,
            bsr_category="Shoes",
            review_count=1200,
            review_rating=4.5,
            seller_count=8,
            is_fba_eligible=True,
        ),
        profit_input=make_profit_input(),
        profit_result=make_profit_result(),
        recommendation=RecommendationResult(
            recommendation=Recommendation.WATCH,
            reasons=["ROI of 29.88% is below BUY threshold of 30.0%."],
        ),
    )


# --- Product and retailer fields ---

def test_mapper_product_and_retailer_fields():
    record = build_evaluation_record(make_sourcing_result(), make_assumptions())

    assert record.product_name == "Nike Air Max 90"
    assert record.product_brand == "Nike"
    assert record.product_upc == "123456789012"
    assert record.product_category == "Shoes"
    assert record.retailer_name == "Kohl's"
    assert record.retailer_price == 45.00
    assert record.retailer_url == "https://kohls.com/example"


# --- Amazon listing snapshot ---

def test_mapper_amazon_snapshot_fields():
    record = build_evaluation_record(make_sourcing_result(), make_assumptions())

    assert record.amazon_category == "Shoes"
    assert record.asin == "B000EXAMPLE"
    assert record.amazon_price == 89.99
    assert record.amazon_title == "Nike Air Max 90"
    assert record.amazon_brand == "Nike"
    assert record.amazon_bsr == 1500
    assert record.amazon_seller_count == 8
    assert record.amazon_review_rating == 4.5


# --- Cost assumptions ---

def test_mapper_all_cost_assumptions():
    record = build_evaluation_record(make_sourcing_result(), make_assumptions())

    assert record.amazon_referral_fee_percent == 15.0
    assert record.fba_fee == 7.50
    assert record.shipping_to_you == 1.00
    assert record.shipping_to_amazon == 2.00
    assert record.prep_cost == 0.75
    assert record.cashback_percent == 6.0
    assert record.sales_tax_percent == 8.0
    assert record.coupon_discount == 5.00
    assert record.storage_cost == 0.50
    assert record.return_risk_percent == 2.0
    assert record.misc_buffer == 1.00


# --- Profit result fields ---

def test_mapper_all_profit_result_fields():
    record = build_evaluation_record(make_sourcing_result(), make_assumptions())

    assert record.net_profit == 14.94
    assert record.roi_percent == 29.88
    assert record.margin_percent == 16.60
    assert record.total_cost == 75.05
    assert record.total_fees == 21.00
    assert record.cashback_amount == 3.00
    assert record.sales_tax_amount == 4.00
    assert record.return_risk_cost == 1.80


# --- Recommendation and metadata ---

def test_mapper_recommendation_and_metadata():
    record = build_evaluation_record(make_sourcing_result(), make_assumptions())

    # Enum is converted to string value for storage
    assert record.recommendation == "WATCH"
    assert record.recommendation_reasons == [
        "ROI of 29.88% is below BUY threshold of 30.0%."
    ]

    # id is None before persistence
    assert record.id is None

    # evaluated_at is timezone-aware UTC
    assert record.evaluated_at.tzinfo is not None
    assert record.evaluated_at.tzinfo == timezone.utc