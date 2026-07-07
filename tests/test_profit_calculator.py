from app.calculations.profit_calculator import ProfitInput, calculate_profit


def test_calculate_profit_with_cashback():
    test_item = ProfitInput(
        buy_cost=50.00,
        amazon_sell_price=89.99,
        amazon_referral_fee_percent=15.0,
        fba_fee=7.50,
        shipping_to_you=0.00,
        shipping_to_amazon=2.00,
        prep_cost=0.75,
        cashback_percent=6.0,
    )

    result = calculate_profit(test_item)

    assert result.net_profit == 19.24
    assert result.roi_percent == 38.48
    assert result.margin_percent == 21.38
    assert result.total_cost == 70.75
    assert result.total_fees == 21.00
    assert result.cashback_amount == 3.00

def test_calculate_profit_with_all_new_fields():
    test_item = ProfitInput(
        buy_cost=50.00,
        amazon_sell_price=89.99,
        amazon_referral_fee_percent=15.0,
        fba_fee=7.50,
        shipping_to_you=2.00,
        shipping_to_amazon=2.00,
        prep_cost=0.75,
        cashback_percent=6.0,
        sales_tax_percent=8.0,
        coupon_discount=5.00,
        storage_cost=0.50,
        return_risk_percent=2.0,
        misc_buffer=1.00,
    )

    result = calculate_profit(test_item)

    # Let's verify the math by hand together rather than me asserting blind numbers —
    # run this test with -s and print(result) first, then we'll lock in the asserts.
def test_calculate_profit_with_all_new_fields():
    test_item = ProfitInput(
        buy_cost=50.00,
        amazon_sell_price=89.99,
        amazon_referral_fee_percent=15.0,
        fba_fee=7.50,
        shipping_to_you=2.00,
        shipping_to_amazon=2.00,
        prep_cost=0.75,
        cashback_percent=6.0,
        sales_tax_percent=8.0,
        coupon_discount=5.00,
        storage_cost=0.50,
        return_risk_percent=2.0,
        misc_buffer=1.00,
    )

    result = calculate_profit(test_item)

    assert result.net_profit == 14.94
    assert result.roi_percent == 29.88
    assert result.margin_percent == 16.6
    assert result.total_cost == 75.05
    assert result.total_fees == 21.00
    assert result.cashback_amount == 3.00
    assert result.sales_tax_amount == 4.00
    assert result.return_risk_cost == 1.80