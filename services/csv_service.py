"""
Parser for Czech bank CSV exports.

Expected column order (semicolon-delimited):
  Datum zauctovani;Datum provedeni;Protistrana;Nazev protiuctu;Castka;Mena;
  Originalni castka;Originalni mena;Smenny kurz;VS;KS;SS;
  Identifikace transakce;Typ transakce;Popis pro me;Zprava pro prijemce;
  Reference platby;BIC / SWIFT;Poplatek

English mapping used in Transaction model:
  Datum zauctovani   -> date            (posting/accounting date)
  Datum provedeni    -> value_date      (transaction execution date, stored in notes)
  Protistrana        -> account         (counterparty identifier / account number)
  Nazev protiuctu    -> counterparty    (counterparty name, prepended to description)
  Castka             -> amount
  Mena               -> currency        (appended to notes)
  Typ transakce      -> category        (transaction type)
  Popis pro me       -> description     (personal description/memo)
  Zprava pro prijemce-> notes           (message for recipient)
  Identifikace trans.-> (used as id seed)
"""

import csv
import re
from datetime import date, datetime
from decimal import Decimal, InvalidOperation
from pathlib import Path
from typing import Optional

from models.transaction import Transaction

# Czech -> English column mapping
_COL_POSTING_DATE = "Datum zauctovani"
_COL_VALUE_DATE = "Datum provedeni"
_COL_COUNTERPARTY_ID = "Protistrana"
_COL_COUNTERPARTY_NAME = "Nazev protiuctu"
_COL_AMOUNT = "Castka"
_COL_CURRENCY = "Mena"
_COL_ORIG_AMOUNT = "Originalni castka"
_COL_ORIG_CURRENCY = "Originalni mena"
_COL_EXCHANGE_RATE = "Smenny kurz"
_COL_VAR_SYMBOL = "VS"
_COL_CONST_SYMBOL = "KS"
_COL_SPEC_SYMBOL = "SS"
_COL_TX_ID = "Identifikace transakce"
_COL_TX_TYPE = "Typ transakce"
_COL_DESCRIPTION = "Popis pro me"
_COL_MESSAGE = "Zprava pro prijemce"
_COL_REFERENCE = "Reference platby"
_COL_BIC = "BIC / SWIFT"
_COL_FEE = "Poplatek"

REQUIRED_COLUMNS = {
    _COL_POSTING_DATE, _COL_AMOUNT, _COL_DESCRIPTION,
}


def _try_encodings(filepath: Path) -> str:
    """Detect encoding by trying UTF-8 BOM, UTF-8, then Windows-1250."""
    for enc in ("utf-8-sig", "utf-8", "cp1250", "iso-8859-2"):
        try:
            with filepath.open(encoding=enc) as fh:
                fh.read(1024)
            return enc
        except (UnicodeDecodeError, ValueError):
            continue
    return "utf-8-sig"  # fallback


def _parse_date(value: str) -> Optional[date]:
    """Parse DD.MM.YYYY or YYYY-MM-DD date strings."""
    value = value.strip()
    if not value:
        return None
    for fmt in ("%d.%m.%Y", "%Y-%m-%d", "%d/%m/%Y"):
        try:
            return datetime.strptime(value, fmt).date()
        except ValueError:
            continue
    return None


def _parse_amount(value: str) -> Optional[Decimal]:
    """
    Parse Czech-formatted numbers: '1 234,56' or '-1234,56' or '1.234,56'.
    Returns None if the string is empty or unparseable.
    """
    value = value.strip()
    if not value:
        return None
    # Remove non-breaking spaces, regular spaces, and periods used as thousands sep
    cleaned = re.sub(r"[\s\xa0.]", "", value)
    # Replace comma decimal separator with period
    cleaned = cleaned.replace(",", ".")
    try:
        return Decimal(cleaned)
    except InvalidOperation:
        return None


def _build_description(row: dict) -> str:
    """
    Compose a human-readable description in English from available fields.
    Priority: Popis pro me, then counterparty name, then transaction type.
    """
    parts = []
    personal = row.get(_COL_DESCRIPTION, "").strip()
    counterparty = row.get(_COL_COUNTERPARTY_NAME, "").strip()
    tx_type = row.get(_COL_TX_TYPE, "").strip()

    if personal:
        parts.append(personal)
    if counterparty and counterparty not in parts:
        parts.append(counterparty)
    if not parts and tx_type:
        parts.append(tx_type)
    return " | ".join(parts) if parts else "—"


def _build_notes(row: dict) -> str:
    """Collect supplementary fields into a readable notes string."""
    note_parts = []

    value_date = row.get(_COL_VALUE_DATE, "").strip()
    if value_date:
        note_parts.append(f"Value date: {value_date}")

    message = row.get(_COL_MESSAGE, "").strip()
    if message:
        note_parts.append(f"Message: {message}")

    reference = row.get(_COL_REFERENCE, "").strip()
    if reference:
        note_parts.append(f"Ref: {reference}")

    vs = row.get(_COL_VAR_SYMBOL, "").strip()
    ks = row.get(_COL_CONST_SYMBOL, "").strip()
    ss = row.get(_COL_SPEC_SYMBOL, "").strip()
    symbols = "/".join(x for x in (vs, ks, ss) if x)
    if symbols:
        note_parts.append(f"VS/KS/SS: {symbols}")

    orig_amount = row.get(_COL_ORIG_AMOUNT, "").strip()
    orig_currency = row.get(_COL_ORIG_CURRENCY, "").strip()
    if orig_amount and orig_currency:
        note_parts.append(f"Original: {orig_amount} {orig_currency}")

    exchange_rate = row.get(_COL_EXCHANGE_RATE, "").strip()
    if exchange_rate and exchange_rate not in ("1", "1,0", "1.0", ""):
        note_parts.append(f"Rate: {exchange_rate}")

    fee = row.get(_COL_FEE, "").strip()
    if fee:
        parsed_fee = _parse_amount(fee)
        if parsed_fee and parsed_fee != Decimal("0"):
            note_parts.append(f"Fee: {fee}")

    bic = row.get(_COL_BIC, "").strip()
    if bic:
        note_parts.append(f"BIC: {bic}")

    return "\n".join(note_parts)


def _row_to_transaction(row: dict, row_index: int) -> Transaction:
    posting_date = _parse_date(row.get(_COL_POSTING_DATE, "")) or date.today()
    amount = _parse_amount(row.get(_COL_AMOUNT, "")) or Decimal("0")
    currency = row.get(_COL_CURRENCY, "").strip()
    description = _build_description(row)
    account = row.get(_COL_COUNTERPARTY_ID, "").strip() or row.get(_COL_COUNTERPARTY_NAME, "").strip()
    category = row.get(_COL_TX_TYPE, "").strip()
    notes = _build_notes(row)

    # Build a numeric id from tx id field or fall back to row index
    tx_id_raw = row.get(_COL_TX_ID, "").strip()
    try:
        tx_id = int(re.sub(r"\D", "", tx_id_raw)) if tx_id_raw else row_index
    except (ValueError, OverflowError):
        tx_id = row_index

    # Append currency to description if non-empty and not the default
    if currency:
        description = f"{description} ({currency})" if currency not in description else description

    return Transaction(
        id=tx_id,
        date=posting_date,
        description=description,
        amount=amount,
        category=category,
        balance=None,
        account=account,
        notes=notes,
    )


class CSVImportError(Exception):
    """Raised when the CSV file cannot be parsed as a Czech bank export."""


def import_transactions(filepath: str | Path) -> list[Transaction]:
    """
    Parse a Czech bank CSV file and return a list of Transaction objects.

    Raises:
        CSVImportError: if the file cannot be read or lacks required columns.
    """
    path = Path(filepath)
    if not path.exists():
        raise CSVImportError(f"File not found: {filepath}")

    encoding = _try_encodings(path)

    try:
        with path.open(encoding=encoding, newline="") as fh:
            reader = csv.DictReader(fh, delimiter=";")
            try:
                fieldnames = reader.fieldnames
            except Exception as exc:
                raise CSVImportError(f"Cannot read CSV headers: {exc}") from exc

            if not fieldnames:
                raise CSVImportError("The file appears to be empty or has no header row.")

            missing = REQUIRED_COLUMNS - set(fieldnames)
            if missing:
                raise CSVImportError(
                    f"File is missing required columns: {', '.join(sorted(missing))}.\n"
                    f"Found columns: {', '.join(fieldnames)}"
                )

            transactions: list[Transaction] = []
            for row_index, row in enumerate(reader, start=1):
                try:
                    tx = _row_to_transaction(row, row_index)
                    transactions.append(tx)
                except Exception as exc:
                    # Skip malformed rows but continue processing
                    continue

    except (OSError, IOError) as exc:
        raise CSVImportError(f"Cannot open file: {exc}") from exc

    if not transactions:
        raise CSVImportError("No valid transactions were found in the file.")

    return transactions
