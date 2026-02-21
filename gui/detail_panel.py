import tkinter as tk
from tkinter import ttk
from typing import Optional

from models.transaction import Transaction


class DetailPanel(ttk.Frame):
    """Side panel that displays full details of the selected transaction."""

    FIELDS = [
        ("Date", "date"),
        ("Description", "description"),
        ("Amount", "amount"),
        ("Category", "category"),
        ("Balance", "balance"),
        ("Account", "account"),
        ("Notes", "notes"),
    ]

    def __init__(self, parent: tk.Widget, **kwargs):
        super().__init__(parent, **kwargs)
        self._value_vars: dict[str, tk.StringVar] = {}
        self._build()

    def _build(self) -> None:
        header = ttk.Label(self, text="Transaction Detail", font=("TkDefaultFont", 11, "bold"))
        header.grid(row=0, column=0, columnspan=2, sticky="w", padx=12, pady=(12, 8))

        ttk.Separator(self, orient="horizontal").grid(
            row=1, column=0, columnspan=2, sticky="ew", padx=8, pady=(0, 8)
        )

        for idx, (label_text, field_name) in enumerate(self.FIELDS, start=2):
            ttk.Label(self, text=f"{label_text}:", anchor="e").grid(
                row=idx, column=0, sticky="e", padx=(12, 6), pady=3
            )
            var = tk.StringVar()
            self._value_vars[field_name] = var
            ttk.Label(self, textvariable=var, anchor="w", wraplength=200).grid(
                row=idx, column=1, sticky="w", padx=(0, 12), pady=3
            )

        self.columnconfigure(1, weight=1)

    def update(self, transaction: Transaction) -> None:
        """Populate the panel with data from the given transaction."""
        self._value_vars["date"].set(transaction.date.strftime("%Y-%m-%d"))
        self._value_vars["description"].set(transaction.description)
        amount = transaction.amount
        self._value_vars["amount"].set(f"{'−' if amount < 0 else '+'}{abs(amount):,.2f}")
        self._value_vars["category"].set(transaction.category or "—")
        if transaction.balance is not None:
            self._value_vars["balance"].set(f"{transaction.balance:,.2f}")
        else:
            self._value_vars["balance"].set("—")
        self._value_vars["account"].set(transaction.account or "—")
        self._value_vars["notes"].set(transaction.notes or "—")

    def clear(self) -> None:
        """Reset all fields to empty state."""
        for var in self._value_vars.values():
            var.set("—")
