from app.amazon.amazon_client import MockAmazonClient


def test_get_product_by_asin_found():
    client = MockAmazonClient()
    product = client.get_product_by_asin("B000EXAMPLE")

    assert product is not None
    assert product.asin == "B000EXAMPLE"
    assert product.title == "Nike Air Max 90"
    assert product.current_price == 89.99
    assert product.bsr == 1500


def test_get_product_by_asin_not_found():
    client = MockAmazonClient()
    product = client.get_product_by_asin("DOESNOTEXIST")

    assert product is None


def test_search_products_returns_match():
    client = MockAmazonClient()
    results = client.search_products("Nike")

    assert len(results) == 1
    assert results[0].asin == "B000EXAMPLE"


def test_search_products_no_match():
    client = MockAmazonClient()
    results = client.search_products("Refrigerator")

    assert len(results) == 0


def test_estimate_fees_known_asin():
    client = MockAmazonClient()
    fees = client.estimate_fees("B000EXAMPLE", 89.99)

    assert fees is not None
    assert fees.referral_fee == 13.50
    assert fees.fba_fee == 7.50
    assert fees.total_fees == 21.00


def test_estimate_fees_unknown_asin():
    client = MockAmazonClient()
    fees = client.estimate_fees("DOESNOTEXIST", 89.99)

    assert fees is None