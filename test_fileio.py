"""
Tests for reading the files people actually have: semicolon separators,
Windows-1252 accents, Excel workbooks with more than one sheet, and the
round trip back out. Run with:  python -m pytest -q
"""

import pandas as pd

import fileio


def test_reads_a_plain_utf8_comma_csv():
    content = "nombre,dni\nLucía Vega,28327518\n".encode("utf-8")
    df, plan = fileio.read_table(content, "clientes.csv")
    assert plan.kind == "csv"
    assert plan.separator == ","
    assert df.loc[0, "nombre"] == "Lucía Vega"


def test_reads_the_semicolon_windows_csv_excel_exports_here():
    text = "nombre;dni\nMartín Gómez;24269701\nRocío Ruiz;30111222\n"
    content = text.encode("cp1252")
    df, plan = fileio.read_table(content, "clientes.csv")
    assert plan.separator == ";"
    assert plan.encoding in {"cp1252", "latin-1"}
    # The accent survived the round trip, which is the whole point.
    assert df.loc[0, "nombre"] == "Martín Gómez"
    assert list(df.columns) == ["nombre", "dni"]


def test_reads_a_tab_separated_file():
    content = "nombre\tdni\nAna Sosa\t28327518\nLeo Paz\t30111222\n".encode("utf-8")
    df, plan = fileio.read_table(content, "clientes.csv")
    assert plan.separator == "\t"
    assert len(df) == 2


def test_excel_with_several_sheets_reports_them_all():
    sheets = {
        "Clientes": pd.DataFrame({"nombre": ["Ana Sosa"], "dni": ["28327518"]}),
        "Pagos": pd.DataFrame({"razon": ["Leo Paz"], "importe": ["1.234,56"]}),
    }
    content = fileio.to_excel_bytes(sheets)

    df, plan = fileio.read_table(content, "base.xlsx")
    assert plan.kind == "excel"
    assert plan.sheets == ["Clientes", "Pagos"]
    assert plan.sheet == "Clientes"          # the first one, and it says so
    assert list(df.columns) == ["nombre", "dni"]

    # And the person can pick a different one.
    other, used = fileio.read_table(
        content, "base.xlsx", fileio.ReadPlan(kind="excel", sheet="Pagos")
    )
    assert used.sheet == "Pagos"
    assert list(other.columns) == ["razon", "importe"]


def test_excel_output_keeps_values_as_text():
    """An ID written as a number loses its leading zeros; keep everything text."""
    frame = pd.DataFrame({"dni": ["01234567"], "cuit": ["20-33572249-4"]})
    content = fileio.to_excel_bytes({"limpio": frame})
    back, _ = fileio.read_table(content, "limpio.xlsx")
    assert back.loc[0, "dni"] == "01234567"
    assert back.loc[0, "cuit"] == "20-33572249-4"


def test_zip_bundle_contains_every_file():
    import io
    import zipfile

    blob = fileio.to_zip_bytes({"a.csv": b"x", "b.csv": b"y"})
    with zipfile.ZipFile(io.BytesIO(blob)) as archive:
        assert sorted(archive.namelist()) == ["a.csv", "b.csv"]


def test_output_names_keep_the_original_stem():
    assert fileio.output_name("clientes.csv", "limpio", "csv") == "clientes_limpio.csv"
    assert fileio.output_name("base.xlsx", "paquete", "zip") == "base_paquete.zip"
