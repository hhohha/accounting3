"""
Parser for Czech bank CSV exports.

Expected column order (semicolon-delimited):
  Datum zauctovani;Datum provedeni;Protistrana;Nazev protiuctu;Castka;Mena;
  Originalni castka;Originalni mena;Smenny kurz;VS;KS;SS;
  Identifikace transakce;Typ transakce;Popis pro me;Zprava pro prijemce;
  Reference platby;BIC / SWIFT;Poplatek
"""

import csv
import re
from datetime import date, datetime
from decimal import Decimal, InvalidOperation
from pathlib import Path
from typing import Optional

from models.transaction import Transaction

# Czech column name constants
_COL_POSTING_DATE    = "Datum zauctovani"
_COL_VALUE_DATE      = "Datum provedeni"
_COL_COUNTERPARTY_ID = "Protistrana"
_COL_COUNTERPARTY    = "Nazev protiuctu"
_COL_AMOUNT          = "Castka"
_COL_CURRENCY        = "Mena"
_COL_ORIG_AMOUNT     = "Originalni castka"
_COL_ORIG_CURRENCY   = "Originalni mena"
_COL_EXCHANGE_RATE   = "Smenny kurz"
_COL_VS              = "VS"
_COL_KS              = "KS"
_COL_SS              = "SS"
_COL_TX_ID           = "Identifikace transakce"
_COL_TX_TYPE         = "Typ transakce"
_COL_DESCRIPTION     = "Popis pro me"
_COL_MESSAGE         = "Zprava pro prijemce"
_COL_REFERENCE       = "Reference platby"
_COL_BIC             = "BIC / SWIFT"
_COL_FEE             = "Poplatek"

REQUIRED_COLUMNS = {_COL_POSTING_DATE, _COL_AMOUNT}


def _try_encodings(filepath: Path) -> str:
    for enc in ("utf-8-sig", "utf-8", "cp1250", "iso-8859-2"):
        try:
            with filepath.open(encoding=enc) as fh:
                fh.read(1024)
            return enc
        except (UnicodeDecodeError, ValueError):
            continue
    return "utf-8-sig"


def _parse_date(value: str) -> Optional[date]:
    value = value.strip()
    if not value:
        return None
    for fmt in ("%d.%m.%Y", "%Y-%m-%d", "%d/%m/%Y"):
        try:
            return datetime.strptime(value, fmt).date()
        except ValueError:
            continue
    return None


def _parse_decimal(value: str) -> Optional[Decimal]:
    """
    Parse Czech-formatted numbers: '1 234,56' or '-1 234,56' or '1.234,56'.
    Returns None for empty or unparseable strings.
    """
    value = value.strip()
    if not value:
        return None
    # Remove spaces, non-breaking spaces, and period thousands separators
    cleaned = re.sub(r"[\s\xa0.]", "", value)
    cleaned = cleaned.replace(",", ".")
    try:
        return Decimal(cleaned)
    except InvalidOperation:
        return None


def _get(row: dict, col: str) -> str:
    return row.get(col, "").strip()


def _row_to_transaction(row: dict, row_index: int) -> Transaction:
    posting_date = _parse_date(_get(row, _COL_POSTING_DATE)) or date.today()
    value_date   = _parse_date(_get(row, _COL_VALUE_DATE))
    amount       = _parse_decimal(_get(row, _COL_AMOUNT)) or Decimal("0")
    orig_amount  = _parse_decimal(_get(row, _COL_ORIG_AMOUNT))
    exchange_rate = _parse_decimal(_get(row, _COL_EXCHANGE_RATE))
    fee          = _parse_decimal(_get(row, _COL_FEE))

    # Build internal id: prefer numeric portion of bank transaction id
    tx_id_raw = _get(row, _COL_TX_ID)
    try:
        tx_id = int(re.sub(r"\D", "", tx_id_raw)) if tx_id_raw else row_index
    except (ValueError, OverflowError):
        tx_id = row_index

    return Transaction(
        id=tx_id,
        date=posting_date,
        value_date=value_date,
        description=_get(row, _COL_DESCRIPTION),
        amount=amount,
        currency=_get(row, _COL_CURRENCY),
        counterparty_id=_get(row, _COL_COUNTERPARTY_ID),
        counterparty_name=_get(row, _COL_COUNTERPARTY),
        original_amount=orig_amount,
        original_currency=_get(row, _COL_ORIG_CURRENCY),
        exchange_rate=exchange_rate,
        variable_symbol=_get(row, _COL_VS),
        constant_symbol=_get(row, _COL_KS),
        specific_symbol=_get(row, _COL_SS),
        transaction_id=tx_id_raw,
        transaction_type=_get(row, _COL_TX_TYPE),
        recipient_message=_get(row, _COL_MESSAGE),
        payment_reference=_get(row, _COL_REFERENCE),
        bic_swift=_get(row, _COL_BIC),
        fee=fee,
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
                except Exception:
                    continue  # skip malformed rows

    except (OSError, IOError) as exc:
        raise CSVImportError(f"Cannot open file: {exc}") from exc

    if not transactions:
        raise CSVImportError("No valid transactions were found in the file.")

    return transactions
