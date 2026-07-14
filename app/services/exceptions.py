class MissingAsinError(Exception):
    """
    Raised when a product is submitted for evaluation
    but has no ASIN to match against Amazon.

    An ASIN is required to look up Amazon pricing, BSR,
    seller count, and other data the pipeline depends on.

    HTTP mapping: 422 Unprocessable Entity
    The request was valid JSON but the data cannot be evaluated.
    """
    pass


class AmazonProductNotFoundError(Exception):
    """
    Raised when a product has an ASIN but no matching
    Amazon listing can be found.

    This means the ASIN itself is unrecognized — either invalid,
    delisted, or not present in the current data source.

    HTTP mapping: 404 Not Found
    A specific resource was requested by identifier and does not exist.
    """
    pass


class MissingRetailerPriceError(Exception):
    """
    Raised when a product has no retailer price.

    Without a buy cost, profit and ROI cannot be calculated.
    The pipeline cannot proceed.

    HTTP mapping: 422 Unprocessable Entity
    The request was valid JSON but the data cannot be evaluated.
    """
    pass