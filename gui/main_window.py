import tkinter as tk
from tkinter import ttk, messagebox, filedialog
from decimal import Decimal
from typing import Optional

from models.transaction import Transaction, SAMPLE_TRANSACTIONS
from gui.detail_panel import DetailPanel
from services.csv_service import import_transactions, CSVImportError


class MainWindow(tk.Tk):
    """Main application window for the personal finance manager."""

    COLUMN_DEFS = [
        ("date",             "Date",         120, "center"),
        ("description",      "Description",  220, "w"),
        ("counterparty_name","Counterparty",  180, "w"),
        ("amount",           "Amount",        110, "e"),
        ("currency",         "Currency",       60, "center"),
        ("transaction_type", "Type",          140, "w"),
    ]

    def __init__(self):
        super().__init__()
        self.title("Personal Finance Manager")
        self.minsize(800, 500)
        self.geometry("1100x620")

        self._transactions: dict[str, Transaction] = {}

        self._apply_style()
        self._build_ui()
        self._load_sample_data()

    # ------------------------------------------------------------------
    # Style
    # ------------------------------------------------------------------

    def _apply_style(self) -> None:
        style = ttk.Style(self)
        style.theme_use("clam")

        style.configure("Treeview", rowheight=26, font=("TkDefaultFont", 10))
        style.configure("Treeview.Heading", font=("TkDefaultFont", 10, "bold"))
        style.map("Treeview", background=[("selected", "#3a7ebf")])

        style.configure("oddrow.Treeview", background="#f5f5f5")
        style.configure("evenrow.Treeview", background="#ffffff")

        style.configure("Detail.TFrame", relief="flat", background="#fafafa")
        style.configure("Buttons.TFrame", relief="groove")

    # ------------------------------------------------------------------
    # UI construction
    # ------------------------------------------------------------------

    def _build_ui(self) -> None:
        self.columnconfigure(0, weight=1)
        self.rowconfigure(0, weight=1)

        # --- Main paned window (table | detail) ---
        paned = ttk.PanedWindow(self, orient=tk.HORIZONTAL)
        paned.grid(row=0, column=0, sticky="nsew", padx=6, pady=(6, 3))

        # Left: transaction table
        table_frame = ttk.Frame(paned)
        paned.add(table_frame, weight=3)
        self._build_table(table_frame)

        # Right: detail panel
        self._detail_panel = DetailPanel(paned, style="Detail.TFrame", padding=4)
        self._detail_panel.clear()
        paned.add(self._detail_panel, weight=1)

        # --- Bottom button bar ---
        btn_frame = ttk.Frame(self, style="Buttons.TFrame", padding=(8, 6))
        btn_frame.grid(row=1, column=0, sticky="ew", padx=6, pady=(3, 6))

        ttk.Button(btn_frame, text="Load from DB", command=self._on_load_db).pack(
            side=tk.LEFT, padx=(0, 8)
        )
        ttk.Button(btn_frame, text="Import from File", command=self._on_import_file).pack(
            side=tk.LEFT
        )

    def _build_table(self, parent: ttk.Frame) -> None:
        parent.columnconfigure(0, weight=1)
        parent.rowconfigure(0, weight=1)

        columns = [col_id for col_id, *_ in self.COLUMN_DEFS]
        self._tree = ttk.Treeview(parent, columns=columns, show="headings", selectmode="browse")

        for col_id, heading, width, anchor in self.COLUMN_DEFS:
            self._tree.heading(col_id, text=heading, command=lambda c=col_id: self._sort_by(c))
            self._tree.column(col_id, width=width, minwidth=60, anchor=anchor)

        # Scrollbars
        vsb = ttk.Scrollbar(parent, orient="vertical", command=self._tree.yview)
        hsb = ttk.Scrollbar(parent, orient="horizontal", command=self._tree.xview)
        self._tree.configure(yscrollcommand=vsb.set, xscrollcommand=hsb.set)

        self._tree.grid(row=0, column=0, sticky="nsew")
        vsb.grid(row=0, column=1, sticky="ns")
        hsb.grid(row=1, column=0, sticky="ew")

        # Alternating row colours
        self._tree.tag_configure("oddrow",  background="#f5f5f5")
        self._tree.tag_configure("evenrow", background="#ffffff")
        self._tree.tag_configure("positive", foreground="#1a7a1a")
        self._tree.tag_configure("negative", foreground="#c0392b")

        self._tree.bind("<<TreeviewSelect>>", self._on_row_selected)

    # ------------------------------------------------------------------
    # Data loading
    # ------------------------------------------------------------------

    def _load_sample_data(self) -> None:
        self._populate_table(SAMPLE_TRANSACTIONS)

    def _populate_table(self, transactions: list[Transaction]) -> None:
        """Clear the table and insert the given transactions."""
        for item in self._tree.get_children():
            self._tree.delete(item)
        self._transactions.clear()
        self._detail_panel.clear()

        for idx, txn in enumerate(transactions):
            amount_str = self._format_amount(txn.amount)
            tags = ["oddrow" if idx % 2 else "evenrow"]
            tags.append("negative" if txn.amount < 0 else "positive")

            item_id = self._tree.insert(
                "",
                "end",
                values=(
                    txn.date.strftime("%Y-%m-%d"),
                    txn.description,
                    txn.counterparty_name,
                    amount_str,
                    txn.currency,
                    txn.transaction_type,
                ),
                tags=tags,
            )
            self._transactions[item_id] = txn

    # ------------------------------------------------------------------
    # Event handlers
    # ------------------------------------------------------------------

    def _on_row_selected(self, event=None) -> None:
        selection = self._tree.selection()
        if not selection:
            self._detail_panel.clear()
            return
        item_id = selection[0]
        txn = self._transactions.get(item_id)
        if txn:
            self._detail_panel.update(txn)

    def _on_load_db(self) -> None:
        messagebox.showinfo("Load from DB", "Not yet implemented.")

    def _on_import_file(self) -> None:
        filepath = filedialog.askopenfilename(
            title="Import CSV File",
            filetypes=[("CSV files", "*.csv"), ("All files", "*.*")],
        )
        if not filepath:
            return  # user cancelled

        try:
            transactions = import_transactions(filepath)
        except CSVImportError as exc:
            messagebox.showerror("Import Failed", str(exc))
            return

        self._populate_table(transactions)
        messagebox.showinfo(
            "Import Complete",
            f"Imported {len(transactions)} transaction(s) from:\n{filepath}",
        )

    # ------------------------------------------------------------------
    # Sorting
    # ------------------------------------------------------------------

    def _sort_by(self, col: str) -> None:
        """Sort table rows by the clicked column header (toggle asc/desc)."""
        items = [(self._tree.set(k, col), k) for k in self._tree.get_children("")]
        reverse = getattr(self, f"_sort_reverse_{col}", False)
        items.sort(reverse=reverse)
        for i, (_, k) in enumerate(items):
            self._tree.move(k, "", i)
            tags = list(self._tree.item(k, "tags"))
            # Re-apply row colour after sort
            tags = [t for t in tags if t not in ("oddrow", "evenrow")]
            tags.append("oddrow" if i % 2 else "evenrow")
            self._tree.item(k, tags=tags)
        setattr(self, f"_sort_reverse_{col}", not reverse)

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    @staticmethod
    def _format_amount(amount: Decimal) -> str:
        sign = "−" if amount < 0 else "+"
        return f"{sign}{abs(amount):,.2f}"
