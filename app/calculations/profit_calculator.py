from dataclasses import dataclass


@dataclass
class ProfitInput:
    buy_cost: float
    amazon_sell_price: float
    amazon_referral_fee_percent: float = 15.0
    fba_fee: float = 0.0
    shipping_to_you: float = 0.0
    shipping_to_amazon: float = 0.0
    prep_cost: float = 0.0
    cashback_percent: float = 0.0

    # New fields
    sales_tax_percent: float = 0.0
    coupon_discount: float = 0.0
    storage_cost: float = 0.0
    return_risk_percent: float = 0.0
    misc_buffer: float = 0.0


@dataclass
class ProfitResult:
    net_profit: float
    roi_percent: float
    margin_percent: float
    total_cost: float
    total_fees: float
    cashback_amount: float
    sales_tax_amount: float
    return_risk_cost: float


def calculate_profit(data: ProfitInput) -> ProfitResult:
    # Sales tax is based on buy cost, applied before discount logic
    sales_tax_amount = data.buy_cost * (data.sales_tax_percent / 100)

    # Cashback is calculated on the original buy cost (common real-world behavior:
    # most cashback portals calculate off pre-tax purchase price)
    cashback_amount = data.buy_cost * (data.cashback_percent / 100)

    referral_fee = data.amazon_sell_price * (
        data.amazon_referral_fee_percent / 100
    )

    total_fees = referral_fee + data.fba_fee

    # Return risk cost: expected cost of returns/refunds as a percent of sell price
    return_risk_cost = data.amazon_sell_price * (data.return_risk_percent / 100)

    total_cost = (
        data.buy_cost
        + sales_tax_amount
        - data.coupon_discount
        + data.shipping_to_you
        + data.shipping_to_amazon
        + data.prep_cost
        + data.storage_cost
        + data.misc_buffer
        + total_fees
        + return_risk_cost
        - cashback_amount
    )

    net_profit = data.amazon_sell_price - total_cost

    roi_percent = (
        (net_profit / data.buy_cost) * 100
        if data.buy_cost > 0
        else 0
    )

    margin_percent = (
        (net_profit / data.amazon_sell_price) * 100
        if data.amazon_sell_price > 0
        else 0
    )

    return ProfitResult(
        net_profit=round(net_profit, 2),
        roi_percent=round(roi_percent, 2),
        margin_percent=round(margin_percent, 2),
        total_cost=round(total_cost, 2),
        total_fees=round(total_fees, 2),
        cashback_amount=round(cashback_amount, 2),
        sales_tax_amount=round(sales_tax_amount, 2),
        return_risk_cost=round(return_risk_cost, 2),
    )

