"""
pipeline.py

Applies the rules from cleaner.py to a whole table: works out what each column
holds, cleans it row by row, records every change with a code the interface can
translate, and separates the values a person still has to decide on.
"""

from __future__ import annotations

import re
import unicodedata

import pandas as pd

import cleaner

KINDS = ["name", "dni", "cuit", "phone", "email", "date", "amount", "category", "text"]

# Header keywords -> column kind. Checked in order, Spanish and English.
_HEADER_HINTS = [
    ("cuit", "cuit"), ("cuil", "cuit"), ("tax id", "cuit"),
    ("dni", "dni"), ("documento", "dni"), ("nro doc", "dni"), ("id number", "dni"),
    ("email", "email"), ("mail", "email"), ("correo", "email"),
    ("tel", "phone"), ("cel", "phone"), ("phone", "phone"), ("movil", "phone"),
    ("whatsapp", "phone"),
    ("fecha", "date"), ("date", "date"), ("vencimiento", "date"), ("alta", "date"),
    ("importe", "amount"), ("monto", "amount"), ("amount", "amount"),
    ("total", "amount"), ("precio", "amount"), ("saldo", "amount"), ("pago", "amount"),
    ("nombre", "name"), ("apellido", "name"), ("cliente", "name"),
    ("razon social", "name"), ("name", "name"), ("titular", "name"),
    ("proveedor", "name"),
]


def _slug(text: str) -> str:
    text = unicodedata.normalize("NFKD", str(text).lower()).encode("ascii", "ignore").decode()
    return re.sub(r"[^a-z0-9 ]", " ", text).strip()


def detect_kind(header: str, sample: pd.Series) -> str:
    """Guess what a column holds, from its header first and its values second."""
    slug = _slug(header)
    for hint, kind in _HEADER_HINTS:
        if hint in slug:
            return kind

    values = [str(v).strip() for v in sample.dropna().head(25) if str(v).strip()]
    if not values:
        return "text"

    def share(predicate) -> float:
        return sum(1 for v in values if predicate(v)) / len(values)

    if share(lambda v: "@" in v) > 0.6:
        return "email"
    if share(lambda v: re.match(r"^\d{1,4}[/\-.]\d{1,2}[/\-.]\d{2,4}$", v)) > 0.6:
        return "date"
    if share(lambda v: re.search(r"[$€]|u\$s", v.lower())) > 0.5:
        return "amount"
    if share(lambda v: len(re.sub(r"\D", "", v)) == 11) > 0.6:
        return "cuit"
    if share(lambda v: 7 <= len(re.sub(r"\D", "", v)) <= 8 and not re.search(r"[a-z]", v.lower())) > 0.6:
        return "dni"

    # A short list of repeated labels written inconsistently ("Activo", "activo",
    # "ACTIVO") is a category column, not free text.
    normalised = {re.sub(r"\s+", " ", v).strip().lower() for v in values}
    if len(normalised) <= 12 and len(normalised) < len({v.strip() for v in values}):
        return "category"
    return "text"


def detect_kinds(df: pd.DataFrame) -> dict[str, str]:
    return {column: detect_kind(column, df[column]) for column in df.columns}


def canonical_categories(values) -> dict[str, str]:
    """Map every spelling of a label to the one used most often in the column."""
    counts: dict[str, dict[str, int]] = {}
    for value in values:
        if cleaner._blank(value):
            continue
        tidy = re.sub(r"\s+", " ", str(value)).strip()
        counts.setdefault(tidy.lower(), {}).setdefault(tidy, 0)
        counts[tidy.lower()][tidy] += 1
    return {key: max(variants, key=variants.get) for key, variants in counts.items()}


def _clean_value(kind: str, raw_value, day_first: bool, canonical: dict):
    """Route one value to its rule. Returns (value, currency, note)."""
    if kind == "name":
        value, note = cleaner.clean_name(raw_value)
    elif kind == "dni":
        value, note = cleaner.clean_dni(raw_value)
    elif kind == "cuit":
        value, note = cleaner.clean_cuit(raw_value)
    elif kind == "phone":
        value, note = cleaner.clean_phone(raw_value)
    elif kind == "email":
        value, note = cleaner.clean_email(raw_value)
    elif kind == "date":
        value, note = cleaner.clean_date(raw_value, day_first)
    elif kind == "amount":
        return cleaner.clean_amount(raw_value)
    elif kind == "category":
        if cleaner._blank(raw_value):
            return "", None, None
        tidy = re.sub(r"\s+", " ", str(raw_value)).strip()
        value = canonical.get(tidy.lower(), tidy)
        note = cleaner.note("unified") if value != str(raw_value) else None
    else:
        if cleaner._blank(raw_value):
            return "", None, None
        value = re.sub(r"\s+", " ", str(raw_value)).strip()
        note = cleaner.note("spaces") if value != str(raw_value) else None
    return value, None, note


def clean_table(df: pd.DataFrame, kinds: dict[str, str]) -> dict:
    """Clean every column and return the results plus a full change log."""
    clean = pd.DataFrame(index=df.index)
    changes: list[dict] = []
    review: list[dict] = []
    changed_cells: set[tuple] = set()

    for column in df.columns:
        kind = kinds.get(column, "text")
        original = df[column]
        day_first = cleaner.column_is_day_first(original) if kind == "date" else True
        canonical = canonical_categories(original) if kind == "category" else {}
        if kind == "amount":
            clean[f"{column} (moneda)"] = ""

        for row_index, raw_value in original.items():
            value, currency, note = _clean_value(kind, raw_value, day_first, canonical)
            clean.loc[row_index, column] = value
            if currency:
                clean.loc[row_index, f"{column} (moneda)"] = currency

            if not note:
                continue

            entry = {
                "row_index": row_index,
                "row": int(row_index) + 2,  # +2 = header row plus 1-based rows
                "column": column,
                "kind": kind,
                "before": "" if cleaner._blank(raw_value) else str(raw_value),
                "after": "" if value is None else str(value),
                "code": note["code"],
                "params": {k: v for k, v in note.items() if k not in {"code", "review"}},
            }
            if note.get("review"):
                review.append(entry)
            else:
                changes.append(entry)
                changed_cells.add((row_index, column))

    # Keep the original column order, with each currency column right after the
    # amount it belongs to.
    ordered: list[str] = []
    for column in df.columns:
        ordered.append(column)
        if f"{column} (moneda)" in clean.columns:
            ordered.append(f"{column} (moneda)")
    clean = clean[ordered]

    return {
        "clean": clean,
        "changes": pd.DataFrame(changes),
        "review": pd.DataFrame(review),
        "duplicates": find_duplicates(clean, kinds),
        "changed_cells": changed_cells,
    }


def find_duplicates(clean: pd.DataFrame, kinds: dict[str, str]) -> pd.DataFrame:
    """Flag repeats by identity column (DNI/CUIT/email), then by whole row."""
    key_columns = [c for c, k in kinds.items() if k in {"dni", "cuit", "email"} and c in clean.columns]
    rows: list[dict] = []
    seen_rows: set = set()

    for column in key_columns:
        values = clean[column].astype(str).str.strip()
        values = values[values != ""]
        counts = values.value_counts()
        for key in counts[counts > 1].index:
            matching = list(values[values == key].index)
            for position, row_index in enumerate(matching):
                if position == 0 or row_index in seen_rows:
                    continue
                seen_rows.add(row_index)
                rows.append({
                    "row_index": row_index,
                    "row": int(row_index) + 2,
                    "column": column,
                    "value": key,
                    "first_row_index": matching[0],
                    "first_row": int(matching[0]) + 2,
                })

    exact = clean.duplicated(keep="first")
    for row_index in clean.index[exact]:
        if row_index in seen_rows:
            continue
        seen_rows.add(row_index)
        rows.append({
            "row_index": row_index,
            "row": int(row_index) + 2,
            "column": "",
            "value": "",
            "first_row_index": None,
            "first_row": None,
        })

    if not rows:
        return pd.DataFrame(columns=["row_index", "row", "column", "value",
                                     "first_row_index", "first_row"])
    return pd.DataFrame(rows).sort_values("row").reset_index(drop=True)
