from app.models.product import Product


def test_product_minimal_creation():
    product = Product(name="Test Widget")

    assert product.name == "Test Widget"
    assert product.brand is None
    assert product.retailer_price is None
    assert product.asin is None


def test_product_full_creation():
    from datetime import date

    product = Product(
        name="Nike Air Max 90",
        brand="Nike",
        upc="123456789012",
        category="Shoes",
        retailer_name="Kohl's",
        retailer_price=45.00,
        retailer_url="https://kohls.com/example",
        date_found=date(2026, 6, 30),
        asin="B000EXAMPLE",
        amazon_price=89.99,
        amazon_bsr=1500,
        amazon_category="Shoes",
    )

    assert product.name == "Nike Air Max 90"
    assert product.retailer_price == 45.00
    assert product.asin == "B000EXAMPLE"