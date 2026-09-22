"""
Tests for the cleaning rules. Run with:  python -m pytest -q
Each case is a real shape of mess found in hand-kept spreadsheets.
"""

import cleaner


def test_name_fixes_spacing_and_case():
    assert cleaner.clean_name("  MARTÍN   gómez ")[0] == "Martín Gómez"
    assert cleaner.clean_name("florencia de la fuente")[0] == "Florencia de la Fuente"
    assert cleaner.clean_name("Lucía Vega")[1] is None  # already clean, no note


def test_dni_strips_dots_and_flags_wrong_length():
    assert cleaner.clean_dni("28.327.518")[0] == "28327518"
    assert cleaner.clean_dni(" 24269701 ")[0] == "24269701"
    assert cleaner.clean_dni("315251")[1].startswith("REVIEW")


def test_cuit_formats_and_validates_check_digit():
    value, note = cleaner.clean_cuit("20335722494")
    assert value == "20-33572249-4"
    assert note == "standardised format"
    assert cleaner.clean_cuit("20245214166")[1].startswith("REVIEW")
    assert cleaner.clean_cuit("2033572249")[1].startswith("REVIEW")  # 10 digits


def test_phone_handles_every_local_habit():
    expected = "+54 9 11 67970168"
    for written in ["011 15 67970168", "+54 9 11 67970168", "1167970168",
                    "0054 9 1167970168", "(11) 6797-0168"]:
        assert cleaner.clean_phone(written)[0] == expected, written


def test_email_trims_and_fixes_known_typos():
    assert cleaner.clean_email("  Lucia.Vega@Gmail.com ")[0] == "lucia.vega@gmail.com"
    assert cleaner.clean_email("tomas@gmail.con")[0] == "tomas@gmail.com"
    assert cleaner.clean_email("sinarroba.gmail.com")[1].startswith("REVIEW")


def test_dates_convert_to_iso():
    assert cleaner.clean_date("17/02/2024")[0] == "2024-02-17"
    assert cleaner.clean_date("19/6/25")[0] == "2025-06-19"
    assert cleaner.clean_date("2025-07-17")[0] == "2025-07-17"
    assert cleaner.clean_date("3 de marzo de 2026")[0] == "2026-03-03"
    assert cleaner.clean_date("31/02/2026")[1].startswith("REVIEW")


def test_ambiguous_dates_follow_the_column():
    day_first_column = ["05/06/2026", "25/06/2026", "07/03/2026"]
    assert cleaner.column_is_day_first(day_first_column) is True
    month_first_column = ["06/25/2026", "03/07/2026"]
    assert cleaner.column_is_day_first(month_first_column) is False
    # The same text reads as two different dates depending on the column.
    assert cleaner.clean_date("05/06/2026", day_first=True)[0] == "2026-06-05"
    assert cleaner.clean_date("05/06/2026", day_first=False)[0] == "2026-05-06"


def test_amounts_read_both_decimal_conventions():
    assert cleaner.clean_amount("$ 133.136,27")[0] == 133136.27
    assert cleaner.clean_amount("USD 1,234.56")[:2] == (1234.56, "USD")
    assert cleaner.clean_amount("U$S 402,71")[:2] == (402.71, "USD")
    assert cleaner.clean_amount("59.244,04")[0] == 59244.04
    assert cleaner.clean_amount("270774.10")[0] == 270774.10


def test_a_lone_separator_with_three_digits_is_thousands():
    # "$ 310.799" is three hundred ten thousand pesos, not 310 and change.
    assert cleaner.clean_amount("$ 310.799")[0] == 310799.0
    assert cleaner.clean_amount("1.234.567")[0] == 1234567.0
    assert cleaner.clean_amount("12,500")[0] == 12500.0
    # Two digits after the mark is a real decimal.
    assert cleaner.clean_amount("402,71")[0] == 402.71
    assert cleaner.clean_amount("795.57")[0] == 795.57


def test_blank_values_stay_blank():
    for rule in (cleaner.clean_name, cleaner.clean_dni, cleaner.clean_email):
        assert rule("")[0] == ""
        assert rule("   ")[0] == ""
