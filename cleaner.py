"""
cleaner.py

The cleaning engine. Every rule is a small, independent function that takes one
raw value and returns (clean_value, note). `note` is None when nothing changed,
otherwise a short human-readable description of what was fixed -- that is what
feeds the change report in the app.

Nothing here touches Streamlit, so the rules can be tested on their own
(see test_cleaner.py).
"""

from __future__ import annotations

import re
import unicodedata
from datetime import datetime

# Particles that stay lowercase inside Spanish surnames.
_PARTICLES = {"de", "del", "la", "las", "los", "y", "da", "do", "van", "von"}

_EMAIL_RE = re.compile(r"^[^@\s]+@[^@\s]+\.[a-z]{2,}$")

# Typos people actually make when typing an email by hand.
_DOMAIN_TYPOS = {
    "gmail.con": "gmail.com",
    "gmail.comm": "gmail.com",
    "gmai.com": "gmail.com",
    "gmial.com": "gmail.com",
    "hotmial.com": "hotmail.com",
    "hotmail.con": "hotmail.com",
    "yahoo.con": "yahoo.com",
    "outlok.com": "outlook.com",
}

_MONTHS_ES = {
    "enero": 1, "febrero": 2, "marzo": 3, "abril": 4, "mayo": 5, "junio": 6,
    "julio": 7, "agosto": 8, "septiembre": 9, "setiembre": 9, "octubre": 10,
    "noviembre": 11, "diciembre": 12,
}

# Longest and most specific first: "U$S 402,71" must read as USD, not ARS.
CURRENCY_SYMBOLS = [
    ("u$s", "USD"), ("us$", "USD"), ("usd", "USD"), ("u$d", "USD"),
    ("eur", "EUR"), ("€", "EUR"),
    ("ars", "ARS"), ("$", "ARS"),
]


def note(code: str, review: bool = False, **params) -> dict:
    """A machine-readable note.

    The app has to show these in three languages, so a rule returns a code and
    its parameters, never a finished English sentence. `review=True` marks the
    ones the tool refuses to decide on its own.
    """
    return {"code": code, "review": review, **params}


def _blank(value) -> bool:
    return value is None or str(value).strip() == "" or str(value).strip().lower() in {"nan", "none", "-", "--", "s/d"}


# --------------------------------------------------------------------------
# Names
# --------------------------------------------------------------------------

def clean_name(value):
    """Trim, collapse inner spaces and apply Title Case, keeping particles low."""
    if _blank(value):
        return "", None
    raw = str(value)
    collapsed = re.sub(r"\s+", " ", raw).strip()
    words = []
    for i, word in enumerate(collapsed.split(" ")):
        low = word.lower()
        if i > 0 and low in _PARTICLES:
            words.append(low)
        else:
            words.append(low[:1].upper() + low[1:])
    result = " ".join(words)
    if result == raw:
        return result, None
    if raw != raw.strip() or "  " in raw:
        return result, note("spaces")
    return result, note("caps")


# --------------------------------------------------------------------------
# DNI (Argentine national ID): 7 or 8 digits
# --------------------------------------------------------------------------

def clean_dni(value):
    if _blank(value):
        return "", None
    raw = str(value).strip()
    digits = re.sub(r"\D", "", raw)
    if not digits:
        return raw, note("no_digits", review=True)
    if len(digits) < 7 or len(digits) > 8:
        return digits, note("digits", review=True, n=len(digits), expected="7-8")
    if digits == raw:
        return digits, None
    return digits, note("format")


# --------------------------------------------------------------------------
# CUIT (Argentine tax ID): 11 digits with a check digit
# --------------------------------------------------------------------------

_CUIT_WEIGHTS = [5, 4, 3, 2, 7, 6, 5, 4, 3, 2]


def cuit_check_digit(first_ten: str) -> int:
    total = sum(int(d) * w for d, w in zip(first_ten, _CUIT_WEIGHTS))
    rest = 11 - (total % 11)
    if rest == 11:
        return 0
    if rest == 10:
        return 9
    return rest


def clean_cuit(value):
    if _blank(value):
        return "", None
    raw = str(value).strip()
    digits = re.sub(r"\D", "", raw)
    if len(digits) != 11:
        return raw, note("digits", review=True, n=len(digits), expected="11")
    formatted = f"{digits[:2]}-{digits[2:10]}-{digits[10]}"
    if cuit_check_digit(digits[:10]) != int(digits[10]):
        return formatted, note("check_digit", review=True)
    if formatted == raw:
        return formatted, None
    return formatted, note("format")


# --------------------------------------------------------------------------
# Phone numbers (Argentina)
# --------------------------------------------------------------------------

def clean_phone(value):
    """Normalise to +54 9 <area> <number>, stripping 0 and 15 prefixes."""
    if _blank(value):
        return "", None
    raw = str(value).strip()
    digits = re.sub(r"\D", "", raw)
    if not digits:
        return raw, note("no_digits", review=True)

    if digits.startswith("0054"):
        digits = digits[4:]
    elif digits.startswith("54"):
        digits = digits[2:]
    if digits.startswith("9"):
        digits = digits[1:]
    if digits.startswith("0"):
        digits = digits[1:]
    # "15" prefix sits between the area code and the number; drop it when the
    # remaining length says it is the mobile marker.
    if len(digits) == 12 and digits[2:4] == "15":
        digits = digits[:2] + digits[4:]
    elif len(digits) == 12 and digits[3:5] == "15":
        digits = digits[:3] + digits[5:]

    if len(digits) != 10:
        return raw, note("digits", review=True, n=len(digits), expected="10")

    area = digits[:2] if digits.startswith("11") else digits[:3]
    rest = digits[len(area):]
    formatted = f"+54 9 {area} {rest}"
    if formatted == raw:
        return formatted, None
    return formatted, note("format")


# --------------------------------------------------------------------------
# Email
# --------------------------------------------------------------------------

def clean_email(value):
    if _blank(value):
        return "", None
    raw = str(value)
    result = re.sub(r"\s+", "", raw).lower()
    changed = result != raw
    fixed_domain = False
    if "@" in result:
        local, _, domain = result.rpartition("@")
        if domain in _DOMAIN_TYPOS:
            result = f"{local}@{_DOMAIN_TYPOS[domain]}"
            fixed_domain = True
    if not _EMAIL_RE.match(result):
        return result, note("bad_email", review=True)
    if fixed_domain:
        return result, note("domain")
    return result, note("spaces") if changed else None


# --------------------------------------------------------------------------
# Dates
# --------------------------------------------------------------------------

def _try_numeric_date(raw: str, day_first: bool):
    match = re.match(r"^(\d{1,4})[/\-.](\d{1,2})[/\-.](\d{2,4})$", raw)
    if not match:
        return None
    a, b, c = match.groups()
    if len(a) == 4:  # yyyy-mm-dd
        year, month, day = int(a), int(b), int(c)
    else:
        year = int(c)
        if year < 100:
            year += 2000 if year < 70 else 1900
        first, second = int(a), int(b)
        if first > 12:
            day, month = first, second
        elif second > 12:
            month, day = first, second
        else:
            day, month = (first, second) if day_first else (second, first)
    try:
        return datetime(year, month, day).date()
    except ValueError:
        return None


def _try_written_date(raw: str):
    match = re.match(r"^(\d{1,2})\s*(?:de\s+)?([a-záéíóú]+)\.?\s*(?:de\s+)?(\d{4})$", raw, re.IGNORECASE)
    if not match:
        return None
    day, month_name, year = match.groups()
    key = unicodedata.normalize("NFKD", month_name.lower()).encode("ascii", "ignore").decode()
    for name, number in _MONTHS_ES.items():
        if name.startswith(key[:3]):
            try:
                return datetime(int(year), number, int(day)).date()
            except ValueError:
                return None
    return None


def column_is_day_first(values) -> bool:
    """Decide dd/mm vs mm/dd for a whole column.

    If any row has a first component above 12, the column must be day-first.
    That single unambiguous row settles every ambiguous one around it, which is
    exactly the judgement call a person makes by eye.
    """
    for value in values:
        if _blank(value):
            continue
        match = re.match(r"^(\d{1,2})[/\-.](\d{1,2})[/\-.]\d{2,4}$", str(value).strip())
        if match:
            first, second = int(match.group(1)), int(match.group(2))
            if first > 12:
                return True
            if second > 12:
                return False
    return True  # Latin America writes dd/mm by default


def clean_date(value, day_first: bool = True):
    if _blank(value):
        return "", None
    raw = str(value).strip()
    parsed = _try_numeric_date(raw, day_first) or _try_written_date(raw)
    if parsed is None:
        return raw, note("bad_date", review=True)
    result = parsed.isoformat()
    if result == raw:
        return result, None
    return result, note("iso")


# --------------------------------------------------------------------------
# Amounts
# --------------------------------------------------------------------------

def clean_amount(value):
    """Return (amount_as_float, currency, note) from messy money text."""
    if _blank(value):
        return None, "", None
    raw = str(value).strip()
    lowered = raw.lower()

    currency = ""
    for symbol, code in CURRENCY_SYMBOLS:
        if symbol in lowered:
            currency = code
            break

    body = re.sub(r"[^\d,.\-]", "", raw)
    if not re.search(r"\d", body):
        return None, currency, note("no_digits", review=True)

    dots, commas = body.count("."), body.count(",")
    if dots and commas:
        # Both present: whichever comes last is the decimal mark.
        if body.rfind(",") > body.rfind("."):
            body = body.replace(".", "").replace(",", ".")
        else:
            body = body.replace(",", "")
    elif dots or commas:
        separator = "." if dots else ","
        tail = body.rsplit(separator, 1)[1]
        # One separator with exactly three digits after it is a thousands mark:
        # "310.799" is three hundred ten thousand, not three hundred and change.
        if body.count(separator) > 1 or len(tail) == 3:
            body = body.replace(separator, "")
        elif separator == ",":
            body = body.replace(",", ".")

    try:
        amount = round(float(body), 2)
    except ValueError:
        return None, currency, note("bad_number", review=True)

    return amount, currency, note("number") if f"{amount:.2f}" != raw else None
