import json
import sqlite3
from dataclasses import replace
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

from app.database.connection import DEFAULT_DB_PATH, get_connection, initialize_database
from app.models.evaluation import EvaluationRecord


class EvaluationRepository:
    """
    Handles persistence and retrieval of EvaluationRecord instances.

    Each instance targets one SQLite database file.
    Tables and indexes are created automatically on first use.

    Does not import FastAPI or Pydantic.
    All SQL uses parameterized queries.
    """

    def __init__(self, db_path: Path = DEFAULT_DB_PATH):
        self.db_path = db_path
        initialize_database(db_path)

    def save(self, record: EvaluationRecord) -> EvaluationRecord:
        """
        Insert a new evaluation row and return a new EvaluationRecord
        with its generated database ID populated.

        The input record is never mutated — frozen=True enforces this.
        dataclasses.replace() constructs a new instance with id set.

        evaluated_at must be timezone-aware. Naive datetimes raise ValueError
        before any database operation is attempted.
        """
        if record.evaluated_at.tzinfo is None:
            raise ValueError(
                "evaluated_at must be timezone-aware. "
                "Use datetime.now(timezone.utc) or attach tzinfo explicitly. "
                f"Got: {record.evaluated_at!r}"
            )

        # Normalize to UTC and format with microseconds for consistent storage
        evaluated_at_utc = record.evaluated_at.astimezone(timezone.utc)
        evaluated_at_iso = evaluated_at_utc.isoformat()
        reasons_json = json.dumps(record.recommendation_reasons)

        with get_connection(self.db_path) as conn:
            cursor = conn.execute(
                """
                INSERT INTO evaluations (
                    evaluated_at,
                    product_name, product_brand, product_upc,
                    product_category, retailer_name, retailer_price,
                    retailer_url,
                    asin, amazon_price, amazon_bsr, amazon_category,
                    amazon_title, amazon_brand, amazon_seller_count,
                    amazon_review_rating,
                    amazon_referral_fee_percent, fba_fee,
                    shipping_to_you, shipping_to_amazon,
                    prep_cost, cashback_percent, sales_tax_percent,
                    coupon_discount, storage_cost, return_risk_percent,
                    misc_buffer,
                    net_profit, roi_percent, margin_percent,
                    total_cost, total_fees, cashback_amount,
                    sales_tax_amount, return_risk_cost,
                    recommendation, recommendation_reasons
                ) VALUES (
                    ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?,
                    ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?,
                    ?, ?, ?, ?, ?
                )
                """,
                (
                    evaluated_at_iso,
                    record.product_name, record.product_brand,
                    record.product_upc, record.product_category,
                    record.retailer_name, record.retailer_price,
                    record.retailer_url,
                    record.asin, record.amazon_price, record.amazon_bsr,
                    record.amazon_category, record.amazon_title,
                    record.amazon_brand, record.amazon_seller_count,
                    record.amazon_review_rating,
                    record.amazon_referral_fee_percent, record.fba_fee,
                    record.shipping_to_you, record.shipping_to_amazon,
                    record.prep_cost, record.cashback_percent,
                    record.sales_tax_percent, record.coupon_discount,
                    record.storage_cost, record.return_risk_percent,
                    record.misc_buffer,
                    record.net_profit, record.roi_percent,
                    record.margin_percent, record.total_cost,
                    record.total_fees, record.cashback_amount,
                    record.sales_tax_amount, record.return_risk_cost,
                    record.recommendation, reasons_json,
                ),
            )
            generated_id = cursor.lastrowid

        # Return a new frozen record with id populated.
        # The original record is unchanged — frozen=True prevents mutation.
        return replace(record, id=generated_id)

    def get_by_id(self, evaluation_id: int) -> Optional[EvaluationRecord]:
        """
        Return the evaluation with the given ID, or None if not found.
        """
        with get_connection(self.db_path) as conn:
            row = conn.execute(
                "SELECT * FROM evaluations WHERE id = ?",
                (evaluation_id,),
            ).fetchone()

        if row is None:
            return None
        return self._row_to_record(row)

    def list_all(self) -> list[EvaluationRecord]:
        """
        Return all evaluations ordered by most recent first.
        Ties in evaluated_at are broken by id DESC.
        """
        with get_connection(self.db_path) as conn:
            rows = conn.execute(
                "SELECT * FROM evaluations ORDER BY evaluated_at DESC, id DESC"
            ).fetchall()
        return [self._row_to_record(row) for row in rows]

    def list_by_asin(self, asin: str) -> list[EvaluationRecord]:
        """
        Return all evaluations for a specific ASIN, most recent first.
        Uses the composite index on (asin, evaluated_at DESC).
        """
        with get_connection(self.db_path) as conn:
            rows = conn.execute(
                """
                SELECT * FROM evaluations
                WHERE asin = ?
                ORDER BY evaluated_at DESC, id DESC
                """,
                (asin,),
            ).fetchall()
        return [self._row_to_record(row) for row in rows]

    # --- Private helpers ---

    @staticmethod
    def _row_to_record(row: sqlite3.Row) -> EvaluationRecord:
        """
        Convert a sqlite3.Row into an EvaluationRecord.

        Handles:
        - JSON deserialization of recommendation_reasons
        - ISO 8601 text back to timezone-aware datetime (UTC)
        - NULL columns becoming None for optional fields
        """
        return EvaluationRecord(
            id=row["id"],
            evaluated_at=datetime.fromisoformat(row["evaluated_at"]),
            product_name=row["product_name"],
            product_brand=row["product_brand"],
            product_upc=row["product_upc"],
            product_category=row["product_category"],
            retailer_name=row["retailer_name"],
            retailer_price=row["retailer_price"],
            retailer_url=row["retailer_url"],
            asin=row["asin"],
            amazon_price=row["amazon_price"],
            amazon_bsr=row["amazon_bsr"],
            amazon_category=row["amazon_category"],
            amazon_title=row["amazon_title"],
            amazon_brand=row["amazon_brand"],
            amazon_seller_count=row["amazon_seller_count"],
            amazon_review_rating=row["amazon_review_rating"],
            amazon_referral_fee_percent=row["amazon_referral_fee_percent"],
            fba_fee=row["fba_fee"],
            shipping_to_you=row["shipping_to_you"],
            shipping_to_amazon=row["shipping_to_amazon"],
            prep_cost=row["prep_cost"],
            cashback_percent=row["cashback_percent"],
            sales_tax_percent=row["sales_tax_percent"],
            coupon_discount=row["coupon_discount"],
            storage_cost=row["storage_cost"],
            return_risk_percent=row["return_risk_percent"],
            misc_buffer=row["misc_buffer"],
            net_profit=row["net_profit"],
            roi_percent=row["roi_percent"],
            margin_percent=row["margin_percent"],
            total_cost=row["total_cost"],
            total_fees=row["total_fees"],
            cashback_amount=row["cashback_amount"],
            sales_tax_amount=row["sales_tax_amount"],
            return_risk_cost=row["return_risk_cost"],
            recommendation=row["recommendation"],
            recommendation_reasons=json.loads(row["recommendation_reasons"]),
        )