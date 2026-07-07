from dataclasses import dataclass
from typing import Optional


@dataclass
class AmazonProduct:
    asin: str
    title: str
    brand: Optional[str] = None
    category: Optional[str] = None
    current_price: Optional[float] = None
    bsr: Optional[int] = None
    bsr_category: Optional[str] = None
    review_count: Optional[int] = None
    review_rating: Optional[float] = None
    seller_count: Optional[int] = None
    is_fba_eligible: bool = True


@dataclass
class FeeEstimate:
    asin: str
    referral_fee: float
    fba_fee: float
    total_fees: float


class AmazonClient:
    """
    Interface for Amazon product data.
    Currently returns mocked data.
    Will later be backed by Keepa API and/or Amazon SP-API.
    """

    def get_product_by_asin(self, asin: str) -> Optional[AmazonProduct]:
        """
        Fetch product data for a given ASIN.
        Returns AmazonProduct or None if not found.
        """
        raise NotImplementedError

    def search_products(self, query: str) -> list[AmazonProduct]:
        """
        Search Amazon products by keyword.
        Returns a list of matching AmazonProducts.
        """
        raise NotImplementedError

    def estimate_fees(
        self, asin: str, price: float
    ) -> Optional[FeeEstimate]:
        """
        Estimate Amazon fees for a given ASIN at a given sell price.
        Returns FeeEstimate or None if fees cannot be determined.
        """
        raise NotImplementedError


class MockAmazonClient(AmazonClient):
    """
    Mock implementation of AmazonClient for testing.
    Returns predictable hardcoded data without hitting any real API.
    """

    def get_product_by_asin(self, asin: str) -> Optional[AmazonProduct]:
        mock_catalog = {
            "B000EXAMPLE": AmazonProduct(
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
            "B000TOASTER": AmazonProduct(
                asin="B000TOASTER",
                title="2-Slice Toaster",
                brand="Hamilton Beach",
                category="Kitchen",
                current_price=34.99,
                bsr=4200,
                bsr_category="Kitchen & Dining",
                review_count=850,
                review_rating=3.9,
                seller_count=15,
                is_fba_eligible=True,
            ),
        }
        return mock_catalog.get(asin)

    def search_products(self, query: str) -> list[AmazonProduct]:
        all_products = [
            self.get_product_by_asin("B000EXAMPLE"),
            self.get_product_by_asin("B000TOASTER"),
        ]
        return [p for p in all_products if p and query.lower() in p.title.lower()]

    def estimate_fees(
        self, asin: str, price: float
    ) -> Optional[FeeEstimate]:
        product = self.get_product_by_asin(asin)
        if not product:
            return None

        referral_fee = round(price * 0.15, 2)
        fba_fee = 3.22 if price < 10 else 5.40 if price < 20 else 7.50

        return FeeEstimate(
            asin=asin,
            referral_fee=referral_fee,
            fba_fee=fba_fee,
            total_fees=round(referral_fee + fba_fee, 2),
        )