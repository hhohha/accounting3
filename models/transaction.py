from dataclasses import dataclass, field
from datetime import date
from decimal import Decimal
from typing import Optional


@dataclass
class Transaction:
    id: int
    date: date
    description: str
    amount: Decimal
    category: str = ""
    balance: Optional[Decimal] = None
    account: str = ""
    notes: str = ""


SAMPLE_TRANSACTIONS = [
    Transaction(
        id=1,
        date=date(2024, 1, 2),
        description="Monthly Rent",
        amount=Decimal("-1200.00"),
        category="Housing",
        balance=Decimal("3800.00"),
        account="Checking",
        notes="January rent",
    ),
    Transaction(
        id=2,
        date=date(2024, 1, 5),
        description="Salary",
        amount=Decimal("3500.00"),
        category="Income",
        balance=Decimal("7300.00"),
        account="Checking",
        notes="Monthly salary",
    ),
    Transaction(
        id=3,
        date=date(2024, 1, 8),
        description="Supermarket",
        amount=Decimal("-87.45"),
        category="Groceries",
        balance=Decimal("7212.55"),
        account="Checking",
        notes="Weekly grocery run",
    ),
    Transaction(
        id=4,
        date=date(2024, 1, 12),
        description="Electric Bill",
        amount=Decimal("-64.20"),
        category="Utilities",
        balance=Decimal("7148.35"),
        account="Checking",
        notes="",
    ),
    Transaction(
        id=5,
        date=date(2024, 1, 15),
        description="Restaurant",
        amount=Decimal("-32.00"),
        category="Dining",
        balance=Decimal("7116.35"),
        account="Checking",
        notes="Dinner with friends",
    ),
    Transaction(
        id=6,
        date=date(2024, 1, 18),
        description="Online Transfer",
        amount=Decimal("-500.00"),
        category="Savings",
        balance=Decimal("6616.35"),
        account="Checking",
        notes="Transfer to savings account",
    ),
    Transaction(
        id=7,
        date=date(2024, 1, 22),
        description="Freelance Payment",
        amount=Decimal("750.00"),
        category="Income",
        balance=Decimal("7366.35"),
        account="Checking",
        notes="Web design project",
    ),
]
