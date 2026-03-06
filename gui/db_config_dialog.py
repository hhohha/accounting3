"""
Modal dialog for entering MySQL connection settings.

Usage:
    dlg = DBConfigDialog(parent, initial=saved_config)
    if dlg.result:
        host, port, user, password, database = dlg.result
"""

import tkinter as tk
from tkinter import ttk
from typing import Optional


class DBConfigDialog(tk.Toplevel):
    def __init__(self, parent: tk.Widget, initial: Optional[dict] = None):
        super().__init__(parent)
        self.title("Database Connection")
        self.resizable(False, False)
        self.grab_set()  # modal

        self.result: Optional[tuple] = None  # (host, port, user, password, database)

        init = initial or {}
        self._vars = {
            "host":     tk.StringVar(value=init.get("host",     "localhost")),
            "port":     tk.StringVar(value=init.get("port",     "3306")),
            "user":     tk.StringVar(value=init.get("user",     "")),
            "password": tk.StringVar(value=init.get("password", "")),
            "database": tk.StringVar(value=init.get("database", "accounting3")),
        }

        self._build()
        self._center_on_parent(parent)
        self.wait_window(self)

    def _build(self) -> None:
        pad = {"padx": 10, "pady": 4}
        frame = ttk.Frame(self, padding=16)
        frame.pack(fill=tk.BOTH, expand=True)

        fields = [
            ("Host",     "host",     False),
            ("Port",     "port",     False),
            ("User",     "user",     False),
            ("Password", "password", True),
            ("Database", "database", False),
        ]

        self._entries: dict[str, ttk.Entry] = {}
        for row_idx, (label, key, secret) in enumerate(fields):
            ttk.Label(frame, text=f"{label}:", anchor="e").grid(
                row=row_idx, column=0, sticky="e", **pad
            )
            show = "*" if secret else ""
            entry = ttk.Entry(frame, textvariable=self._vars[key], show=show, width=28)
            entry.grid(row=row_idx, column=1, sticky="ew", **pad)
            self._entries[key] = entry

        frame.columnconfigure(1, weight=1)

        # Buttons
        btn_frame = ttk.Frame(frame)
        btn_frame.grid(row=len(fields), column=0, columnspan=2, pady=(12, 0), sticky="e")

        ttk.Button(btn_frame, text="Cancel", command=self.destroy).pack(side=tk.RIGHT, padx=(8, 0))
        ttk.Button(btn_frame, text="Connect", command=self._on_connect).pack(side=tk.RIGHT)

        # Allow Enter key to submit
        self.bind("<Return>", lambda _: self._on_connect())
        self.bind("<Escape>", lambda _: self.destroy())

        # Focus the first empty field
        for key in ("host", "port", "user", "password", "database"):
            if not self._vars[key].get():
                self._entries[key].focus_set()
                break
        else:
            self._entries["host"].focus_set()

    def _on_connect(self) -> None:
        host     = self._vars["host"].get().strip()
        port_str = self._vars["port"].get().strip()
        user     = self._vars["user"].get().strip()
        password = self._vars["password"].get()
        database = self._vars["database"].get().strip()

        if not host:
            self._entries["host"].focus_set()
            return
        try:
            port = int(port_str)
            if not (1 <= port <= 65535):
                raise ValueError
        except ValueError:
            self._entries["port"].focus_set()
            return
        if not user:
            self._entries["user"].focus_set()
            return
        if not database:
            self._entries["database"].focus_set()
            return

        self.result = (host, port, user, password, database)
        self.destroy()

    def _center_on_parent(self, parent: tk.Widget) -> None:
        self.update_idletasks()
        pw = parent.winfo_rootx() + parent.winfo_width() // 2
        ph = parent.winfo_rooty() + parent.winfo_height() // 2
        w, h = self.winfo_width(), self.winfo_height()
        self.geometry(f"+{pw - w // 2}+{ph - h // 2}")
