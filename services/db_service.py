"""
Database service: connect to MySQL, load all transactions, save one transaction.

Upsert logic for save():
  - If the transaction has a non-empty transaction_id, use MySQL's
    ON DUPLICATE KEY UPDATE to insert-or-update based on the unique index.
  - If transaction_id is absent, always insert a new row.
"""

from __future__ import annotations

from typing import Optional

from sqlalchemy import create_engine, text
from sqlalchemy.exc import SQLAlchemyError, IntegrityError
from sqlalchemy.orm import sessionmaker, Session

from models.database import Base, TransactionRecord
from models.transaction import Transaction


class DBError(Exception):
    """Raised for connection or query failures."""


class DBService:
    def __init__(self) -> None:
        self._engine = None
        self._Session = None

    # ------------------------------------------------------------------
    # Connection
    # ------------------------------------------------------------------

    def connect(self, host: str, port: int, user: str,
                password: str, database: str) -> None:
        """
        Open (and verify) a connection to MySQL.
        Raises DBError on failure.
        """
        url = (
            f"mysql+pymysql://{user}:{password}@{host}:{port}/{database}"
            "?charset=utf8mb4"
        )
        try:
            engine = create_engine(url, pool_pre_ping=True, echo=False)
            # Verify the connection is actually usable
            with engine.connect() as conn:
                conn.execute(text("SELECT 1"))
        except SQLAlchemyError as exc:
            raise DBError(f"Cannot connect to database: {exc}") from exc

        self._engine = engine
        self._Session = sessionmaker(bind=engine, autocommit=False, autoflush=False)

    @property
    def is_connected(self) -> bool:
        return self._engine is not None

    def disconnect(self) -> None:
        if self._engine:
            self._engine.dispose()
            self._engine = None
            self._Session = None

    # ------------------------------------------------------------------
    # Load
    # ------------------------------------------------------------------

    def load_all(self) -> list[Transaction]:
        """
        Return all rows from the transactions table ordered by date descending.
        Raises DBError if not connected or on query failure.
        """
        self._require_connection()
        try:
            with self._Session() as session:
                records = (
                    session.query(TransactionRecord)
                    .order_by(TransactionRecord.date.desc())
                    .all()
                )
                return [r.to_transaction() for r in records]
        except SQLAlchemyError as exc:
            raise DBError(f"Failed to load transactions: {exc}") from exc

    # ------------------------------------------------------------------
    # Save (upsert)
    # ------------------------------------------------------------------

    def save(self, tx: Transaction) -> bool:
        """
        Persist a single transaction to the database.

        - With transaction_id: INSERT … ON DUPLICATE KEY UPDATE (upsert).
        - Without transaction_id: plain INSERT (always creates a new row).

        Returns True if a new row was inserted, False if an existing row
        was updated.
        Raises DBError on failure.
        """
        self._require_connection()

        if tx.transaction_id:
            return self._upsert(tx)
        else:
            return self._insert(tx)

    def _insert(self, tx: Transaction) -> bool:
        record = TransactionRecord.from_transaction(tx)
        try:
            with self._Session() as session:
                session.add(record)
                session.commit()
            return True
        except SQLAlchemyError as exc:
            raise DBError(f"Failed to insert transaction: {exc}") from exc

    def _upsert(self, tx: Transaction) -> bool:
        """MySQL-specific INSERT … ON DUPLICATE KEY UPDATE."""
        from sqlalchemy.dialects.mysql import insert as mysql_insert

        data = {
            "date":              tx.date,
            "value_date":        tx.value_date,
            "description":       tx.description,
            "amount":            tx.amount,
            "currency":          tx.currency,
            "counterparty_id":   tx.counterparty_id,
            "counterparty_name": tx.counterparty_name,
            "original_amount":   tx.original_amount,
            "original_currency": tx.original_currency,
            "exchange_rate":     tx.exchange_rate,
            "variable_symbol":   tx.variable_symbol,
            "constant_symbol":   tx.constant_symbol,
            "specific_symbol":   tx.specific_symbol,
            "transaction_id":    tx.transaction_id or None,
            "transaction_type":  tx.transaction_type,
            "recipient_message": tx.recipient_message,
            "payment_reference": tx.payment_reference,
            "bic_swift":         tx.bic_swift,
            "fee":               tx.fee,
        }

        stmt = mysql_insert(TransactionRecord).values(**data)
        # On duplicate transaction_id: update all mutable columns
        update_cols = {k: v for k, v in data.items() if k != "transaction_id"}
        stmt = stmt.on_duplicate_key_update(**update_cols)

        try:
            with self._Session() as session:
                result = session.execute(stmt)
                session.commit()
                # rowcount == 1 → inserted; 2 → updated (MySQL convention)
                return result.rowcount == 1
        except SQLAlchemyError as exc:
            raise DBError(f"Failed to save transaction: {exc}") from exc

    # ------------------------------------------------------------------
    # Internal
    # ------------------------------------------------------------------

    def _require_connection(self) -> None:
        if not self.is_connected:
            raise DBError("Not connected to a database. Use connect() first.")
