import pytest
from datetime import date

from app.amazon.amazon_client import MockAmazonClient
from app.models.product import Product
from app.services.exceptions import (
    AmazonProductNotFoundError,
    MissingAsinError,
    MissingRetailerPriceError,
)
from app.services.recommendation_engine import Recommendation, RecommendationConfig
from app.services.sourcing_service import CostAssumptions, SourcingService


def make_nike_product():
    return Product(
        name="Nike Air Max 90",
        brand="Nike",
        asin="B000EXAMPLE",
        retailer_name="Kohl's",
        retailer_price=45.00,
        date_found=date(2026, 6, 30),
    )


def make_service(config=None):
    return SourcingService(
        amazon_client=MockAmazonClient(),
        recommendation_config=config,
    )


# --- Success cases ---

def test_evaluate_product_success():
    service = make_service()
    product = make_nike_product()
    assumptions = CostAssumptions(
        fba_fee=7.50,
        shipping_to_amazon=2.00,
        prep_cost=0.75,
        cashback_percent=6.0,
    )

    result = service.evaluate_product(product, assumptions)

    assert result.amazon_product is not None
    assert result.amazon_product.asin == "B000EXAMPLE"
    assert result.profit_input.buy_cost == 45.00
    assert result.profit_input.amazon_sell_price == 89.99
    assert result.profit_result.net_profit > 0
    assert result.recommendation is not None


def test_evaluate_product_returns_recommendation():
    service = make_service()
    product = make_nike_product()
    assumptions = CostAssumptions(
        fba_fee=7.50,
        shipping_to_amazon=2.00,
        prep_cost=0.75,
        cashback_percent=6.0,
    )

    result = service.evaluate_product(product, assumptions)

    assert result.recommendation.recommendation in [
        Recommendation.BUY,
        Recommendation.WATCH,
        Recommendation.PASS,
    ]
    assert len(result.recommendation.reasons) > 0


def test_evaluate_product_custom_config_affects_recommendation():
    strict_config = RecommendationConfig(
        min_roi_for_buy=80.0,
        min_roi_for_watch=50.0,
    )
    service = make_service(config=strict_config)
    product = make_nike_product()
    assumptions = CostAssumptions(fba_fee=7.50, cashback_percent=6.0)

    result = service.evaluate_product(product, assumptions)

    assert result.recommendation.recommendation == Recommendation.WATCH


# --- Failure cases: domain exceptions ---

def test_evaluate_product_no_asin_raises():
    """
    A product submitted with no ASIN cannot be matched to Amazon.
    SourcingService should raise MissingAsinError immediately
    without attempting any lookup.
    """
    service = make_service()
    product = Product(
        name="Mystery Item",
        retailer_price=20.00,
        # asin intentionally omitted - defaults to None
    )

    with pytest.raises(MissingAsinError):
        service.evaluate_product(product, CostAssumptions())


def test_evaluate_product_asin_not_found_raises():
    """
    A product with an ASIN that returns no Amazon listing
    should raise AmazonProductNotFoundError.
    This is distinct from a missing ASIN - the ASIN was provided
    but the lookup failed to find a match.
    """
    service = make_service()
    product = Product(
        name="Ghost Product",
        asin="DOESNOTEXIST",
        retailer_price=20.00,
    )

    with pytest.raises(AmazonProductNotFoundError):
        service.evaluate_product(product, CostAssumptions())


def test_evaluate_product_no_retailer_price_raises():
    """
    A product with no retailer price cannot have profit calculated.
    SourcingService should raise MissingRetailerPriceError.
    """
    service = make_service()
    product = Product(
        name="Nike Air Max 90",
        asin="B000EXAMPLE",
        # retailer_price intentionally omitted - defaults to None
    )

    with pytest.raises(MissingRetailerPriceError):
        service.evaluate_product(product, CostAssumptions())


def test_missing_asin_error_message_is_informative():
    """
    The exception message should name the product so the caller
    can identify which product failed in a multi-product context.
    """
    service = make_service()
    product = Product(name="Unnamed Product", retailer_price=20.00)

    with pytest.raises(MissingAsinError) as exc_info:
        service.evaluate_product(product, CostAssumptions())

    assert "Unnamed Product" in str(exc_info.value)


def test_amazon_not_found_error_message_includes_asin():
    """
    The exception message should include the ASIN that was not found
    so the caller knows exactly which lookup failed.
    """
    service = make_service()
    product = Product(
        name="Ghost Product",
        asin="DOESNOTEXIST",
        retailer_price=20.00,
    )

    with pytest.raises(AmazonProductNotFoundError) as exc_info:
        service.evaluate_product(product, CostAssumptions())

    assert "DOESNOTEXIST" in str(exc_info.value)