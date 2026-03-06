"""
SQLAlchemy ORM model mirroring the transactions table defined in schema.sql.
Provides conversion helpers between the ORM row and the Transaction dataclass.
"""

from __future__ import annotations

from datetime import date
from decimal import Decimal
from typing import Optional

from sqlalchemy import (
    Column, Date, DateTime, Integer, Numeric, String, Text, func
)
from sqlalchemy.orm import DeclarativeBase

from models.transaction import Transaction


class Base(DeclarativeBase):
    pass


class TransactionRecord(Base):
    __tablename__ = "transactions"

    id                = Column(Integer,       primary_key=True, autoincrement=True)
    date              = Column(Date,          nullable=False)
    value_date        = Column(Date,          nullable=True)
    description       = Column(String(500),   nullable=False, default="")
    amount            = Column(Numeric(15, 4), nullable=False)
    currency          = Column(String(10),    nullable=False, default="")
    counterparty_id   = Column(String(100),   nullable=False, default="")
    counterparty_name = Column(String(255),   nullable=False, default="")
    original_amount   = Column(Numeric(15, 4), nullable=True)
    original_currency = Column(String(10),    nullable=False, default="")
    exchange_rate     = Column(Numeric(15, 6), nullable=True)
    variable_symbol   = Column(String(20),    nullable=False, default="")
    constant_symbol   = Column(String(20),    nullable=False, default="")
    specific_symbol   = Column(String(20),    nullable=False, default="")
    transaction_id    = Column(String(100),   nullable=True,  unique=True)
    transaction_type  = Column(String(100),   nullable=False, default="")
    recipient_message = Column(String(500),   nullable=False, default="")
    payment_reference = Column(String(255),   nullable=False, default="")
    bic_swift         = Column(String(20),    nullable=False, default="")
    fee               = Column(Numeric(15, 4), nullable=True)

    # ------------------------------------------------------------------
    # Conversion helpers
    # ------------------------------------------------------------------

    def to_transaction(self) -> Transaction:
        """Convert ORM row -> Transaction dataclass."""
        return Transaction(
            id=self.id or 0,
            date=self.date,
            value_date=self.value_date,
            description=self.description or "",
            amount=Decimal(str(self.amount)),
            currency=self.currency or "",
            counterparty_id=self.counterparty_id or "",
            counterparty_name=self.counterparty_name or "",
            original_amount=Decimal(str(self.original_amount)) if self.original_amount is not None else None,
            original_currency=self.original_currency or "",
            exchange_rate=Decimal(str(self.exchange_rate)) if self.exchange_rate is not None else None,
            variable_symbol=self.variable_symbol or "",
            constant_symbol=self.constant_symbol or "",
            specific_symbol=self.specific_symbol or "",
            transaction_id=self.transaction_id or "",
            transaction_type=self.transaction_type or "",
            recipient_message=self.recipient_message or "",
            payment_reference=self.payment_reference or "",
            bic_swift=self.bic_swift or "",
            fee=Decimal(str(self.fee)) if self.fee is not None else None,
        )

    @staticmethod
    def from_transaction(tx: Transaction) -> TransactionRecord:
        """Convert Transaction dataclass -> ORM row (for insert/update)."""
        return TransactionRecord(
            date=tx.date,
            value_date=tx.value_date,
            description=tx.description,
            amount=tx.amount,
            currency=tx.currency,
            counterparty_id=tx.counterparty_id,
            counterparty_name=tx.counterparty_name,
            original_amount=tx.original_amount,
            original_currency=tx.original_currency,
            exchange_rate=tx.exchange_rate,
            variable_symbol=tx.variable_symbol,
            constant_symbol=tx.constant_symbol,
            specific_symbol=tx.specific_symbol,
            # Store None instead of empty string so UNIQUE allows multiples
            transaction_id=tx.transaction_id if tx.transaction_id else None,
            transaction_type=tx.transaction_type,
            recipient_message=tx.recipient_message,
            payment_reference=tx.payment_reference,
            bic_swift=tx.bic_swift,
            fee=tx.fee,
        )
