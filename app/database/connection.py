import sqlite3
from contextlib import contextmanager
from pathlib import Path

DEFAULT_DB_PATH = Path(__file__).parent.parent.parent / "data" / "arbitrage.db"


@contextmanager
def get_connection(db_path: Path = DEFAULT_DB_PATH):
    """
    Context manager that opens a SQLite connection, yields it,
    commits on success, rolls back on exception, and always closes.

    Usage:
        with get_connection(db_path) as conn:
            conn.execute(...)

    The sqlite3.Connection context manager only handles commit/rollback —
    it does not close the connection. This wrapper ensures the connection
    is always closed in the finally block regardless of outcome.
    """
    db_path.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(str(db_path))
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    try:
        yield conn
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


def initialize_database(db_path: Path = DEFAULT_DB_PATH) -> None:
    """
    Create all tables and indexes if they do not already exist.
    Safe to call on every application startup — uses IF NOT EXISTS throughout.
    """
    with get_connection(db_path) as conn:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS evaluations (
                -- identity
                id                          INTEGER PRIMARY KEY AUTOINCREMENT,
                evaluated_at                TEXT    NOT NULL,

                -- product / retailer
                -- required: only successful evaluations are persisted
                product_name                TEXT    NOT NULL,
                product_brand               TEXT,
                product_upc                 TEXT,
                product_category            TEXT,
                retailer_name               TEXT,
                retailer_price              REAL    NOT NULL,
                retailer_url                TEXT,

                -- amazon listing snapshot
                -- required: pipeline cannot succeed without these
                asin                        TEXT    NOT NULL,
                amazon_price                REAL    NOT NULL,
                amazon_bsr                  INTEGER,
                amazon_category             TEXT,
                amazon_title                TEXT    NOT NULL,
                amazon_brand                TEXT,
                amazon_seller_count         INTEGER,
                amazon_review_rating        REAL,

                -- cost assumptions
                amazon_referral_fee_percent REAL    NOT NULL,
                fba_fee                     REAL    NOT NULL,
                shipping_to_you             REAL    NOT NULL,
                shipping_to_amazon          REAL    NOT NULL,
                prep_cost                   REAL    NOT NULL,
                cashback_percent            REAL    NOT NULL,
                sales_tax_percent           REAL    NOT NULL,
                coupon_discount             REAL    NOT NULL,
                storage_cost                REAL    NOT NULL,
                return_risk_percent         REAL    NOT NULL,
                misc_buffer                 REAL    NOT NULL,

                -- profit result
                net_profit                  REAL    NOT NULL,
                roi_percent                 REAL    NOT NULL,
                margin_percent              REAL    NOT NULL,
                total_cost                  REAL    NOT NULL,
                total_fees                  REAL    NOT NULL,
                cashback_amount             REAL    NOT NULL,
                sales_tax_amount            REAL    NOT NULL,
                return_risk_cost            REAL    NOT NULL,

                -- recommendation
                recommendation              TEXT    NOT NULL,
                recommendation_reasons      TEXT    NOT NULL
            )
        """)

        conn.execute("""
            CREATE INDEX IF NOT EXISTS idx_evaluations_asin_evaluated_at
            ON evaluations (asin, evaluated_at DESC)
        """)