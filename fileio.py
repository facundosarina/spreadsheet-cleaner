"""
fileio.py

Reading and writing the files people actually have, which is not the same as
the files a tutorial has.

A spreadsheet exported from Excel in Argentina is usually semicolon-separated
and encoded as Windows-1252, not comma-separated UTF-8. An .xlsx may hold four
sheets. Getting any of that wrong looks, from the outside, exactly like the
tool being broken -- so it is detected here and shown to the person for
confirmation instead of guessed at silently.
"""

from __future__ import annotations

import csv
import io
import zipfile
from dataclasses import dataclass, field

import pandas as pd

CSV_ENCODINGS = ["utf-8-sig", "utf-8", "cp1252", "latin-1"]
CSV_SEPARATORS = [",", ";", "\t", "|"]

EXCEL_SUFFIXES = (".xlsx", ".xlsm", ".xls")


class FileProblem(Exception):
    """Raised with a message meant for a person, not a stack trace."""


@dataclass
class ReadPlan:
    """How a file was read, so the person can correct it."""

    kind: str                      # "csv" or "excel"
    encoding: str | None = None
    separator: str | None = None
    sheet: str | None = None
    sheets: list[str] = field(default_factory=list)

    def describe(self) -> dict[str, str]:
        if self.kind == "csv":
            names = {",": "comma", ";": "semicolon", "\t": "tab", "|": "pipe"}
            return {
                "separator": names.get(self.separator or ",", self.separator or ","),
                "encoding": self.encoding or "utf-8",
            }
        return {"sheet": self.sheet or ""}


# --------------------------------------------------------------------- read ---

def sniff_csv(content: bytes) -> tuple[str, str]:
    """Return (encoding, separator) for a CSV file's raw bytes."""
    text = None
    used_encoding = "utf-8"
    for encoding in CSV_ENCODINGS:
        try:
            text = content.decode(encoding)
            used_encoding = encoding
            break
        except UnicodeDecodeError:
            continue
    if text is None:
        raise FileProblem("unreadable-encoding")

    sample = "\n".join(text.splitlines()[:20])
    try:
        dialect = csv.Sniffer().sniff(sample, delimiters="".join(CSV_SEPARATORS))
        return used_encoding, dialect.delimiter
    except csv.Error:
        # Sniffer gives up on short or irregular files; fall back to counting.
        header = sample.splitlines()[0] if sample.splitlines() else ""
        best = max(CSV_SEPARATORS, key=header.count)
        return used_encoding, best if header.count(best) else ","


def excel_sheet_names(content: bytes, filename: str) -> list[str]:
    try:
        book = pd.ExcelFile(io.BytesIO(content), engine=_excel_engine(filename))
        return list(book.sheet_names)
    except Exception as error:  # noqa: BLE001 - surfaced to the person as text
        raise FileProblem(str(error)) from error


def _excel_engine(filename: str) -> str:
    return "xlrd" if filename.lower().endswith(".xls") else "openpyxl"


def read_table(content: bytes, filename: str, plan: ReadPlan | None = None
               ) -> tuple[pd.DataFrame, ReadPlan]:
    """Read a CSV or Excel file into strings, returning the plan that was used."""
    lower = filename.lower()

    if lower.endswith(EXCEL_SUFFIXES):
        sheets = excel_sheet_names(content, filename)
        sheet = (plan.sheet if plan and plan.sheet in sheets else sheets[0]) if sheets else None
        try:
            df = pd.read_excel(
                io.BytesIO(content), sheet_name=sheet, dtype=str,
                engine=_excel_engine(filename),
            )
        except Exception as error:  # noqa: BLE001
            raise FileProblem(str(error)) from error
        return df.fillna(""), ReadPlan(kind="excel", sheet=sheet, sheets=sheets)

    if plan and plan.kind == "csv" and plan.encoding and plan.separator:
        encoding, separator = plan.encoding, plan.separator
    else:
        encoding, separator = sniff_csv(content)

    try:
        df = pd.read_csv(
            io.BytesIO(content), dtype=str, keep_default_na=False,
            encoding=encoding, sep=separator, engine="python",
        )
    except Exception as error:  # noqa: BLE001
        raise FileProblem(str(error)) from error

    return df.fillna(""), ReadPlan(kind="csv", encoding=encoding, separator=separator)


# -------------------------------------------------------------------- write ---

def to_csv_bytes(df: pd.DataFrame) -> bytes:
    """UTF-8 with a BOM, so Excel opens accents correctly on the first try."""
    return df.to_csv(index=False).encode("utf-8-sig")


def to_excel_bytes(sheets: dict[str, pd.DataFrame]) -> bytes:
    """Write one or more sheets, keeping every value as text.

    Text matters: an ID number written as a number loses its leading zeros and
    a long one turns into 4.5E+10 the moment the file is reopened.
    """
    buffer = io.BytesIO()
    with pd.ExcelWriter(buffer, engine="openpyxl") as writer:
        for name, frame in sheets.items():
            safe = str(name)[:31] or "Sheet1"
            frame.astype(str).to_excel(writer, sheet_name=safe, index=False)
    return buffer.getvalue()


def to_zip_bytes(files: dict[str, bytes]) -> bytes:
    buffer = io.BytesIO()
    with zipfile.ZipFile(buffer, "w", zipfile.ZIP_DEFLATED) as archive:
        for name, blob in files.items():
            archive.writestr(name, blob)
    return buffer.getvalue()


def output_name(filename: str, suffix: str, extension: str) -> str:
    stem = filename.rsplit(".", 1)[0] if "." in filename else filename
    return f"{stem}_{suffix}.{extension}"
