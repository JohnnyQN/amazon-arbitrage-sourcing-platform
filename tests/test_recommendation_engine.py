from app.amazon.amazon_client import AmazonProduct
from app.calculations.profit_calculator import ProfitResult
from app.services.recommendation_engine import (
    Recommendation,
    RecommendationConfig,
    evaluate_opportunity,
)


def make_profit_result(
    net_profit=20.0,
    roi_percent=35.0,
    margin_percent=20.0,
    total_cost=60.0,
    total_fees=15.0,
    cashback_amount=3.0,
    sales_tax_amount=4.0,
    return_risk_cost=1.5,
):
    return ProfitResult(
        net_profit=net_profit,
        roi_percent=roi_percent,
        margin_percent=margin_percent,
        total_cost=total_cost,
        total_fees=total_fees,
        cashback_amount=cashback_amount,
        sales_tax_amount=sales_tax_amount,
        return_risk_cost=return_risk_cost,
    )


def make_amazon_product(seller_count=5, bsr=1500):
    return AmazonProduct(
        asin="B000EXAMPLE",
        title="Nike Air Max 90",
        seller_count=seller_count,
        bsr=bsr,
    )


def test_strong_deal_returns_buy():
    result = evaluate_opportunity(
        profit_result=make_profit_result(roi_percent=35.0, margin_percent=20.0),
        amazon_product=make_amazon_product(seller_count=5, bsr=1500),
    )
    assert result.recommendation == Recommendation.BUY
    assert result.reasons == ["Meets all thresholds."]


def test_marginal_roi_returns_watch():
    result = evaluate_opportunity(
        profit_result=make_profit_result(roi_percent=20.0, margin_percent=20.0),
        amazon_product=make_amazon_product(),
    )
    assert result.recommendation == Recommendation.WATCH


def test_negative_profit_returns_pass():
    result = evaluate_opportunity(
        profit_result=make_profit_result(net_profit=-5.0, roi_percent=0.0),
    )
    assert result.recommendation == Recommendation.PASS
    assert "negative" in result.reasons[0]


def test_roi_below_watch_threshold_returns_pass():
    result = evaluate_opportunity(
        profit_result=make_profit_result(roi_percent=10.0),
    )
    assert result.recommendation == Recommendation.PASS


def test_high_seller_count_downgrades_to_watch():
    result = evaluate_opportunity(
        profit_result=make_profit_result(roi_percent=35.0, margin_percent=20.0),
        amazon_product=make_amazon_product(seller_count=25, bsr=1500),
    )
    assert result.recommendation == Recommendation.WATCH
    assert any("seller" in r.lower() for r in result.reasons)


def test_high_bsr_downgrades_to_watch():
    result = evaluate_opportunity(
        profit_result=make_profit_result(roi_percent=35.0, margin_percent=20.0),
        amazon_product=make_amazon_product(seller_count=5, bsr=200_000),
    )
    assert result.recommendation == Recommendation.WATCH
    assert any("BSR" in r for r in result.reasons)


def test_custom_config_overrides_defaults():
    config = RecommendationConfig(
        min_roi_for_buy=20.0,
        min_roi_for_watch=10.0,
        min_margin_for_buy=10.0,
        max_seller_count=30,
        max_bsr=200_000,
    )
    result = evaluate_opportunity(
        profit_result=make_profit_result(roi_percent=22.0, margin_percent=12.0),
        amazon_product=make_amazon_product(seller_count=5, bsr=1500),
        config=config,
    )
    assert result.recommendation == Recommendation.BUY