from dataclasses import dataclass
from datetime import date
from typing import Optional


@dataclass
class Product:
    # Identity
    name: str
    brand: Optional[str] = None
    upc: Optional[str] = None
    category: Optional[str] = None

    # Retailer side
    retailer_name: Optional[str] = None
    retailer_price: Optional[float] = None
    retailer_url: Optional[str] = None
    date_found: Optional[date] = None

    # Amazon side
    asin: Optional[str] = None
    amazon_price: Optional[float] = None
    amazon_bsr: Optional[int] = None
    amazon_category: Optional[str] = None