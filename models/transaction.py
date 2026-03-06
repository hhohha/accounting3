from dataclasses import dataclass, field
from datetime import date
from decimal import Decimal
from typing import Optional


@dataclass
class Transaction:
    # Internal row id (sequential, not from bank)
    id: int

    # Core fields
    date: date                                  # Datum zauctovani  – posting/accounting date
    description: str                            # Popis pro me      – personal description/memo
    amount: Decimal                             # Castka            – transaction amount
    currency: str = ""                          # Mena              – currency code (e.g. CZK)

    # Dates
    value_date: Optional[date] = None           # Datum provedeni   – execution/value date

    # Counterparty
    counterparty_id: str = ""                   # Protistrana       – counterparty account number
    counterparty_name: str = ""                 # Nazev protiuctu   – counterparty name

    # Original (foreign-currency) amount
    original_amount: Optional[Decimal] = None   # Originalni castka
    original_currency: str = ""                 # Originalni mena
    exchange_rate: Optional[Decimal] = None     # Smenny kurz

    # Czech payment symbols
    variable_symbol: str = ""                   # VS
    constant_symbol: str = ""                   # KS
    specific_symbol: str = ""                   # SS

    # Transaction metadata
    transaction_id: str = ""                    # Identifikace transakce
    transaction_type: str = ""                  # Typ transakce

    # Messages / references
    recipient_message: str = ""                 # Zprava pro prijemce
    payment_reference: str = ""                 # Reference platby
    bic_swift: str = ""                         # BIC / SWIFT

    # Fee charged for the transaction
    fee: Optional[Decimal] = None               # Poplatek


SAMPLE_TRANSACTIONS = [
    Transaction(
        id=1,
        date=date(2024, 1, 2),
        description="Monthly Rent",
        amount=Decimal("-1200.00"),
        currency="CZK",
        value_date=date(2024, 1, 2),
        counterparty_id="CZ6508000000192000145399",
        counterparty_name="Property Management s.r.o.",
        transaction_type="Outgoing payment",
        variable_symbol="0000000001",
    ),
    Transaction(
        id=2,
        date=date(2024, 1, 5),
        description="Salary",
        amount=Decimal("52000.00"),
        currency="CZK",
        value_date=date(2024, 1, 5),
        counterparty_id="CZ5503000000000123456789",
        counterparty_name="Acme Corp a.s.",
        transaction_type="Incoming payment",
        variable_symbol="20240105",
    ),
    Transaction(
        id=3,
        date=date(2024, 1, 8),
        description="Supermarket",
        amount=Decimal("-2145.50"),
        currency="CZK",
        value_date=date(2024, 1, 8),
        counterparty_name="Albert supermarket",
        transaction_type="Card payment",
    ),
    Transaction(
        id=4,
        date=date(2024, 1, 12),
        description="Electric Bill",
        amount=Decimal("-1564.20"),
        currency="CZK",
        value_date=date(2024, 1, 11),
        counterparty_id="CZ3055000000001144885566",
        counterparty_name="PRE distribuce a.s.",
        transaction_type="Outgoing payment",
        variable_symbol="8800112244",
        constant_symbol="0308",
    ),
    Transaction(
        id=5,
        date=date(2024, 1, 15),
        description="Restaurant",
        amount=Decimal("-820.00"),
        currency="CZK",
        value_date=date(2024, 1, 15),
        counterparty_name="Restaurace U Zlateho Kohouta",
        transaction_type="Card payment",
    ),
    Transaction(
        id=6,
        date=date(2024, 1, 18),
        description="Online Transfer",
        amount=Decimal("-15000.00"),
        currency="CZK",
        value_date=date(2024, 1, 18),
        counterparty_id="CZ7801000000001234567890",
        counterparty_name="My Savings Account",
        transaction_type="Outgoing payment",
        recipient_message="Transfer to savings",
    ),
    Transaction(
        id=7,
        date=date(2024, 1, 22),
        description="Freelance Payment",
        amount=Decimal("18750.00"),
        currency="CZK",
        value_date=date(2024, 1, 22),
        counterparty_id="CZ2401000000001111222233",
        counterparty_name="StartUp s.r.o.",
        transaction_type="Incoming payment",
        variable_symbol="20240122",
        recipient_message="Web design project invoice #42",
    ),
    Transaction(
        id=8,
        date=date(2024, 1, 25),
        description="Amazon purchase",
        amount=Decimal("-1243.60"),
        currency="CZK",
        value_date=date(2024, 1, 25),
        counterparty_name="Amazon EU SARL",
        transaction_type="Card payment",
        original_amount=Decimal("-49.99"),
        original_currency="EUR",
        exchange_rate=Decimal("24.876"),
    ),
]
