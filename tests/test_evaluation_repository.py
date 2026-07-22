import pytest
from datetime import datetime, timezone, timedelta
from pathlib import Path

from app.models.evaluation import EvaluationRecord
from app.repositories.evaluation_repository import EvaluationRepository


# ---------------------------------------------------------------------------
# Fixture
# ---------------------------------------------------------------------------

@pytest.fixture
def repo(tmp_path: Path) -> EvaluationRepository:
    """
    Each test gets a fresh repository backed by a unique temporary SQLite file.
    pytest's tmp_path fixture guarantees no shared state between tests.
    """
    return EvaluationRepository(db_path=tmp_path / "test_arbitrage.db")


# ---------------------------------------------------------------------------
# Factory
# ---------------------------------------------------------------------------

def make_record(**overrides) -> EvaluationRecord:
    """
    Build an EvaluationRecord from a defaults dictionary.

    All fields are set in defaults first, then overrides are applied.
    This avoids duplicate-key errors that occur when a field appears
    both as an explicit keyword argument and in **kwargs.

    Usage:
        make_record()                          # all defaults
        make_record(retailer_price=99.00)      # override one field
        make_record(asin="B000OTHER")          # override another
    """
    defaults = dict(
        id=None,
        evaluated_at=datetime(2026, 7, 13, 12, 0, 0, tzinfo=timezone.utc),
        product_name="Nike Air Max 90",
        product_brand="Nike",
        product_upc=None,
        product_category="Shoes",
        retailer_name="Kohl's",
        retailer_price=45.00,
        retailer_url=None,
        asin="B000EXAMPLE",
        amazon_price=89.99,
        amazon_bsr=1500,
        amazon_category="Shoes",
        amazon_title="Nike Air Max 90",
        amazon_brand="Nike",
        amazon_seller_count=8,
        amazon_review_rating=4.5,
        amazon_referral_fee_percent=15.0,
        fba_fee=7.50,
        shipping_to_you=0.0,
        shipping_to_amazon=2.00,
        prep_cost=0.75,
        cashback_percent=6.0,
        sales_tax_percent=0.0,
        coupon_discount=0.0,
        storage_cost=0.0,
        return_risk_percent=0.0,
        misc_buffer=0.0,
        net_profit=23.94,
        roi_percent=53.2,
        margin_percent=26.6,
        total_cost=66.05,
        total_fees=21.00,
        cashback_amount=2.70,
        sales_tax_amount=0.0,
        return_risk_cost=0.0,
        recommendation="BUY",
        recommendation_reasons=["Meets all thresholds."],
    )
    defaults.update(overrides)
    return EvaluationRecord(**defaults)


# ---------------------------------------------------------------------------
# Table initialization
# ---------------------------------------------------------------------------

def test_table_is_created_on_init(repo: EvaluationRepository):
    """
    The repository should create the evaluations table automatically.
    Querying immediately after construction should return an empty list,
    not raise an exception.
    """
    assert repo.list_all() == []


# ---------------------------------------------------------------------------
# Save and generated IDs
# ---------------------------------------------------------------------------

def test_save_returns_record_with_id(repo: EvaluationRepository):
    """
    save() must return a new EvaluationRecord with id populated.
    The input record has id=None; the returned record has a real integer ID.
    """
    record = make_record()
    assert record.id is None

    saved = repo.save(record)

    assert saved.id is not None
    assert isinstance(saved.id, int)
    assert saved.id >= 1


def test_save_does_not_mutate_original_record(repo: EvaluationRepository):
    """
    The original record passed to save() must be unchanged afterward.
    EvaluationRecord is frozen — this test confirms save() uses
    dataclasses.replace() rather than attempting mutation.
    """
    record = make_record()
    assert record.id is None

    repo.save(record)

    # Original must still have id=None
    assert record.id is None


def test_save_assigns_incrementing_ids(repo: EvaluationRepository):
    """
    Successive saves should produce incrementing IDs.
    """
    first = repo.save(make_record())
    second = repo.save(make_record())

    assert second.id == first.id + 1


# ---------------------------------------------------------------------------
# Naive datetime rejection
# ---------------------------------------------------------------------------

def test_save_rejects_naive_datetime(repo: EvaluationRepository):
    """
    A naive datetime (no tzinfo) must raise ValueError before any
    database operation is attempted.
    Naive datetimes are ambiguous — they could be local time or UTC.
    """
    record = make_record(
        evaluated_at=datetime(2026, 7, 13, 12, 0, 0)  # no tzinfo
    )

    with pytest.raises(ValueError, match="timezone-aware"):
        repo.save(record)

def test_save_normalizes_timestamp_to_utc(
    repo: EvaluationRepository,
):
    """
    save() should return the canonical UTC timestamp written to
    the database, even when the input uses another timezone.

    The original frozen record must remain unchanged, while the
    saved and retrieved records use the equivalent UTC timestamp.
    """
    pacific_offset = timezone(timedelta(hours=-7))
    local_time = datetime(
        2026,
        7,
        13,
        5,
        0,
        0,
        tzinfo=pacific_offset,
    )

    original = make_record(evaluated_at=local_time)
    saved = repo.save(original)

    assert saved.id is not None

    retrieved = repo.get_by_id(saved.id)

    expected_utc = datetime(
        2026,
        7,
        13,
        12,
        0,
        0,
        tzinfo=timezone.utc,
    )

    assert original.evaluated_at == local_time
    assert saved.evaluated_at == expected_utc
    assert retrieved is not None
    assert retrieved.evaluated_at == expected_utc
# ---------------------------------------------------------------------------
# Retrieval by ID
# ---------------------------------------------------------------------------

def test_get_by_id_returns_saved_record(repo: EvaluationRepository):
    """
    get_by_id() should return the record that was saved with that ID.
    """
    saved = repo.save(make_record())
    retrieved = repo.get_by_id(saved.id)

    assert retrieved is not None
    assert retrieved.id == saved.id
    assert retrieved.product_name == "Nike Air Max 90"
    assert retrieved.asin == "B000EXAMPLE"
    assert retrieved.net_profit == 23.94


def test_get_by_id_unknown_returns_none(repo: EvaluationRepository):
    """
    get_by_id() with a nonexistent ID should return None, not raise.
    """
    assert repo.get_by_id(99999) is None


# ---------------------------------------------------------------------------
# list_all — basic behavior
# ---------------------------------------------------------------------------

def test_list_all_returns_all_records(repo: EvaluationRepository):
    """
    list_all() should return every saved evaluation.
    """
    repo.save(make_record(product_name="Product A"))
    repo.save(make_record(product_name="Product B"))
    repo.save(make_record(product_name="Product C"))

    assert len(repo.list_all()) == 3


def test_list_all_orders_by_evaluated_at_desc(repo: EvaluationRepository):
    """
    list_all() must order by evaluated_at DESC, id DESC.
    Tests use distinct timestamps rather than relying on ID order alone,
    because the sort key is evaluated_at, not insertion order.
    """
    base = datetime(2026, 7, 13, 10, 0, 0, tzinfo=timezone.utc)

    oldest = repo.save(make_record(
        product_name="Oldest",
        evaluated_at=base,
    ))
    middle = repo.save(make_record(
        product_name="Middle",
        evaluated_at=base + timedelta(hours=1),
    ))
    newest = repo.save(make_record(
        product_name="Newest",
        evaluated_at=base + timedelta(hours=2),
    ))

    results = repo.list_all()

    assert results[0].id == newest.id
    assert results[1].id == middle.id
    assert results[2].id == oldest.id


# ---------------------------------------------------------------------------
# list_by_asin — basic behavior
# ---------------------------------------------------------------------------

def test_list_by_asin_filters_correctly(repo: EvaluationRepository):
    """
    list_by_asin() should return only evaluations matching the given ASIN.
    """
    repo.save(make_record(asin="B000EXAMPLE"))
    repo.save(make_record(asin="B000EXAMPLE"))
    repo.save(make_record(asin="B000OTHER"))

    results = repo.list_by_asin("B000EXAMPLE")

    assert len(results) == 2
    assert all(r.asin == "B000EXAMPLE" for r in results)


def test_list_by_asin_unknown_returns_empty(repo: EvaluationRepository):
    """
    list_by_asin() with an unknown ASIN should return an empty list, not raise.
    """
    assert repo.list_by_asin("DOESNOTEXIST") == []


def test_list_by_asin_orders_by_evaluated_at_desc(repo: EvaluationRepository):
    """
    list_by_asin() must order by evaluated_at DESC, id DESC.
    Uses distinct timestamps to test the actual sort key.
    """
    base = datetime(2026, 7, 13, 10, 0, 0, tzinfo=timezone.utc)

    earlier = repo.save(make_record(
        asin="B000EXAMPLE",
        evaluated_at=base,
    ))
    later = repo.save(make_record(
        asin="B000EXAMPLE",
        evaluated_at=base + timedelta(hours=1),
    ))

    results = repo.list_by_asin("B000EXAMPLE")

    assert results[0].id == later.id
    assert results[1].id == earlier.id


# ---------------------------------------------------------------------------
# Round-trip integrity
# ---------------------------------------------------------------------------

def test_recommendation_reasons_round_trip(repo: EvaluationRepository):
    """
    recommendation_reasons is stored as JSON and must deserialize
    back to the original list with all items and order preserved.
    """
    reasons = [
        "ROI of 25.0% is below BUY threshold of 30.0%.",
        "High seller count: 25 sellers (max 20).",
    ]
    saved = repo.save(make_record(
        recommendation="WATCH",
        recommendation_reasons=reasons,
    ))
    retrieved = repo.get_by_id(saved.id)

    assert retrieved.recommendation_reasons == reasons


def test_optional_fields_preserved_as_none(repo: EvaluationRepository):
    """
    Optional fields that are None on save should be None on retrieval,
    not empty strings or zero values.
    SQLite stores these as NULL; _row_to_record must not coerce them.
    """
    saved = repo.save(make_record(
        product_upc=None,
        retailer_url=None,
        amazon_review_rating=None,
    ))
    retrieved = repo.get_by_id(saved.id)

    assert retrieved.product_upc is None
    assert retrieved.retailer_url is None
    assert retrieved.amazon_review_rating is None


# ---------------------------------------------------------------------------
# Factory override correctness
# ---------------------------------------------------------------------------

def test_factory_override_replaces_default_field(repo: EvaluationRepository):
    """
    make_record() must correctly apply overrides to fields that have
    defaults in the factory. Confirms the defaults-dict pattern works
    correctly for all fields, not just optional ones.
    """
    record = make_record(retailer_price=99.99)
    assert record.retailer_price == 99.99

    saved = repo.save(record)
    retrieved = repo.get_by_id(saved.id)
    assert retrieved.retailer_price == 99.99


# ---------------------------------------------------------------------------
# Connection reliability
# ---------------------------------------------------------------------------

def test_repeated_operations_do_not_lock_database(repo: EvaluationRepository):
    """
    Performing multiple save and retrieval operations in sequence must
    not leave connections open or cause database locking errors.
    The @contextmanager in connection.py closes connections in finally,
    ensuring each operation releases its connection before the next begins.
    """
    for i in range(5):
        repo.save(make_record(product_name=f"Product {i}"))

    results = repo.list_all()
    assert len(results) == 5

    for record in results:
        retrieved = repo.get_by_id(record.id)
        assert retrieved is not None


# ---------------------------------------------------------------------------
# list_all with limit
# ---------------------------------------------------------------------------

def test_list_all_with_limit_caps_results(repo: EvaluationRepository):
    """
    list_all(limit=N) returns at most N records even when more exist.
    """
    for _ in range(5):
        repo.save(make_record())

    results = repo.list_all(limit=3)
    assert len(results) == 3


def test_list_all_with_limit_returns_newest_n(repo: EvaluationRepository):
    """
    list_all(limit=N) returns the N newest records, not arbitrary ones.
    Ordering by evaluated_at DESC is preserved when limit is applied.
    """
    base = datetime(2026, 7, 13, 10, 0, 0, tzinfo=timezone.utc)
    oldest = repo.save(make_record(evaluated_at=base))
    middle = repo.save(make_record(evaluated_at=base + timedelta(hours=1)))
    newest = repo.save(make_record(evaluated_at=base + timedelta(hours=2)))

    results = repo.list_all(limit=2)

    assert len(results) == 2
    assert results[0].id == newest.id
    assert results[1].id == middle.id
    assert not any(r.id == oldest.id for r in results)


def test_list_all_without_limit_returns_all_records(repo: EvaluationRepository):
    """
    list_all() with no argument returns every record, preserving backward
    compatibility with callers that do not pass a limit.
    """
    for _ in range(5):
        repo.save(make_record())

    results = repo.list_all()
    assert len(results) == 5


def test_list_all_limit_zero_raises_value_error(repo: EvaluationRepository):
    """
    list_all(limit=0) must raise ValueError before executing any SQL.
    Zero is not a meaningful page size and likely indicates a bug in
    the calling code.
    """
    with pytest.raises(ValueError):
        repo.list_all(limit=0)


# ---------------------------------------------------------------------------
# list_by_asin with limit
# ---------------------------------------------------------------------------

def test_list_by_asin_with_limit_caps_results(repo: EvaluationRepository):
    """
    list_by_asin(asin, limit=N) returns at most N records for that ASIN
    even when more matching records exist.
    """
    for _ in range(5):
        repo.save(make_record(asin="B000EXAMPLE"))

    results = repo.list_by_asin("B000EXAMPLE", limit=2)
    assert len(results) == 2
    assert all(r.asin == "B000EXAMPLE" for r in results)


def test_list_by_asin_limit_zero_raises_value_error(repo: EvaluationRepository):
    """
    list_by_asin(asin, limit=0) must raise ValueError before executing
    any SQL. Zero is not a meaningful page size.
    """
    with pytest.raises(ValueError):
        repo.list_by_asin("B000EXAMPLE", limit=0)