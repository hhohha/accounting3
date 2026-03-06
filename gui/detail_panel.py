import tkinter as tk
from tkinter import ttk
from typing import Optional

from models.transaction import Transaction


def _fmt_decimal(value) -> str:
    if value is None:
        return "—"
    return f"{value:,.2f}"


def _fmt_date(value) -> str:
    if value is None:
        return "—"
    return value.strftime("%Y-%m-%d")


def _str_or_dash(value: str) -> str:
    return value if value else "—"


class DetailPanel(ttk.Frame):
    """Side panel that displays full details of the selected transaction."""

    # (label, attribute, formatter)
    # Grouped with None rows acting as section separators rendered as thin lines.
    FIELDS = [
        # ── Core ──────────────────────────────────────────────────────────
        ("Date",              "date",              _fmt_date),
        ("Value Date",        "value_date",        _fmt_date),
        ("Description",       "description",       _str_or_dash),
        ("Amount",            "amount",            _fmt_decimal),
        ("Currency",          "currency",          _str_or_dash),
        ("Fee",               "fee",               _fmt_decimal),
        None,
        # ── Counterparty ──────────────────────────────────────────────────
        ("Counterparty",      "counterparty_name", _str_or_dash),
        ("Counterparty ID",   "counterparty_id",   _str_or_dash),
        None,
        # ── Transaction info ──────────────────────────────────────────────
        ("Type",              "transaction_type",  _str_or_dash),
        ("Transaction ID",    "transaction_id",    _str_or_dash),
        None,
        # ── Payment symbols / references ──────────────────────────────────
        ("Variable Symbol",   "variable_symbol",   _str_or_dash),
        ("Constant Symbol",   "constant_symbol",   _str_or_dash),
        ("Specific Symbol",   "specific_symbol",   _str_or_dash),
        ("Payment Reference", "payment_reference", _str_or_dash),
        ("BIC / SWIFT",       "bic_swift",         _str_or_dash),
        None,
        # ── Foreign currency ──────────────────────────────────────────────
        ("Original Amount",   "original_amount",   _fmt_decimal),
        ("Original Currency", "original_currency", _str_or_dash),
        ("Exchange Rate",     "exchange_rate",      _fmt_decimal),
        None,
        # ── Messages ──────────────────────────────────────────────────────
        ("Recipient Message", "recipient_message", _str_or_dash),
    ]

    def __init__(self, parent: tk.Widget, **kwargs):
        super().__init__(parent, **kwargs)
        self._value_vars: dict[str, tk.StringVar] = {}
        self._build()

    def _build(self) -> None:
        # Scrollable canvas so all fields remain reachable on small windows
        canvas = tk.Canvas(self, borderwidth=0, highlightthickness=0)
        scrollbar = ttk.Scrollbar(self, orient="vertical", command=canvas.yview)
        canvas.configure(yscrollcommand=scrollbar.set)

        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        self._inner = ttk.Frame(canvas)
        self._inner_id = canvas.create_window((0, 0), window=self._inner, anchor="nw")

        self._inner.bind("<Configure>", lambda e: canvas.configure(
            scrollregion=canvas.bbox("all")
        ))
        canvas.bind("<Configure>", lambda e: canvas.itemconfig(
            self._inner_id, width=e.width
        ))

        # Mouse-wheel scrolling
        canvas.bind_all("<MouseWheel>",
                        lambda e: canvas.yview_scroll(int(-1 * (e.delta / 120)), "units"))
        canvas.bind_all("<Button-4>",
                        lambda e: canvas.yview_scroll(-1, "units"))
        canvas.bind_all("<Button-5>",
                        lambda e: canvas.yview_scroll(1, "units"))

        # ── Header ────────────────────────────────────────────────────────
        row = 0
        ttk.Label(self._inner, text="Transaction Detail",
                  font=("TkDefaultFont", 11, "bold")).grid(
            row=row, column=0, columnspan=2, sticky="w", padx=12, pady=(12, 6)
        )
        row += 1
        ttk.Separator(self._inner, orient="horizontal").grid(
            row=row, column=0, columnspan=2, sticky="ew", padx=8, pady=(0, 6)
        )
        row += 1

        # ── Field rows ────────────────────────────────────────────────────
        for item in self.FIELDS:
            if item is None:
                # Section separator
                ttk.Separator(self._inner, orient="horizontal").grid(
                    row=row, column=0, columnspan=2, sticky="ew",
                    padx=8, pady=(4, 4)
                )
                row += 1
                continue

            label_text, attr, _ = item
            ttk.Label(self._inner, text=f"{label_text}:", anchor="e").grid(
                row=row, column=0, sticky="ne", padx=(12, 6), pady=2
            )
            var = tk.StringVar(value="—")
            self._value_vars[attr] = var
            ttk.Label(self._inner, textvariable=var, anchor="w",
                      wraplength=210, justify="left").grid(
                row=row, column=1, sticky="w", padx=(0, 12), pady=2
            )
            row += 1

        self._inner.columnconfigure(1, weight=1)

    def update(self, transaction: Transaction) -> None:
        """Populate the panel with data from the given transaction."""
        for item in self.FIELDS:
            if item is None:
                continue
            label_text, attr, formatter = item
            value = getattr(transaction, attr, None)
            self._value_vars[attr].set(formatter(value))

    def clear(self) -> None:
        """Reset all fields to empty state."""
        for var in self._value_vars.values():
            var.set("—")
