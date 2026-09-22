"""
app.py

Streamlit front end for the spreadsheet cleaner. Run with:

    streamlit run app.py

Upload a messy CSV or Excel file (or load one of the two sample files), and the
app works out what each column holds, fixes what it can, and lists what a person
still has to decide.
"""

from __future__ import annotations

import io

import pandas as pd
import plotly.express as px
import streamlit as st

import pipeline

st.set_page_config(page_title="Spreadsheet Cleaner", page_icon="🧹", layout="wide")

BAR_COLOR = "#17868F"

SAMPLES = {
    "Client list (45 rows)": "data/clientes_sucio.csv",
    "Payments list (40 rows)": "data/pagos_sucio.csv",
}

KIND_OPTIONS = list(pipeline.KIND_LABELS.keys())


@st.cache_data
def read_table(content: bytes, filename: str) -> pd.DataFrame:
    buffer = io.BytesIO(content)
    if filename.lower().endswith((".xlsx", ".xls")):
        df = pd.read_excel(buffer, dtype=str)
    else:
        df = pd.read_csv(buffer, dtype=str, keep_default_na=False)
    return df.fillna("")


def to_csv_bytes(df: pd.DataFrame) -> bytes:
    return df.to_csv(index=False).encode("utf-8-sig")


# ---------------------------------------------------------------- sidebar ---

st.sidebar.header("Data")
source = st.sidebar.radio("Where does the file come from?", ["Sample file", "Upload my own"])

raw = None
if source == "Sample file":
    choice = st.sidebar.selectbox("Sample", list(SAMPLES.keys()))
    with open(SAMPLES[choice], "rb") as fh:
        raw = read_table(fh.read(), SAMPLES[choice])
    st.sidebar.caption("Invented data, built to contain the mistakes real hand-kept files have.")
else:
    uploaded = st.sidebar.file_uploader("CSV or Excel", type=["csv", "xlsx", "xls"])
    if uploaded is not None:
        raw = read_table(uploaded.getvalue(), uploaded.name)
    else:
        st.sidebar.info("Pick a file to get started.")

st.sidebar.header("Time saved")
seconds_per_fix = st.sidebar.slider(
    "Seconds it takes to find and fix one field by hand", 3, 30, 10
)

# ------------------------------------------------------------------- main ---

st.title("Spreadsheet Cleaner")
st.write(
    "Hand-kept lists drift: the same name written three ways, ID numbers with and "
    "without dots, dates in two conventions, amounts that are text instead of "
    "numbers. This reads a file, fixes what has one right answer, and hands back "
    "the rows that need a person."
)

if raw is None:
    st.stop()

if raw.empty:
    st.warning("That file has no rows.")
    st.stop()

# Column kinds: detected, then editable.
if "kinds_for" not in st.session_state or st.session_state["kinds_for"] != list(raw.columns):
    st.session_state["kinds_for"] = list(raw.columns)
    st.session_state["kinds"] = {c: pipeline.detect_kind(c, raw[c]) for c in raw.columns}

with st.expander("Columns detected — change any that got read wrong", expanded=False):
    columns = st.columns(min(4, len(raw.columns)))
    for index, column in enumerate(raw.columns):
        with columns[index % len(columns)]:
            st.session_state["kinds"][column] = st.selectbox(
                column,
                KIND_OPTIONS,
                index=KIND_OPTIONS.index(st.session_state["kinds"].get(column, "text")),
                format_func=lambda k: pipeline.KIND_LABELS[k],
                key=f"kind_{column}",
            )

kinds = st.session_state["kinds"]
result = pipeline.clean_table(raw, kinds)
clean, changes, review, duplicates = (
    result["clean"], result["changes"], result["review"], result["duplicates"]
)

minutes_saved = round(len(changes) * seconds_per_fix / 60)

row = st.columns(5)
row[0].metric("Rows", f"{len(raw):,}")
row[1].metric("Fields corrected", f"{len(changes):,}")
row[2].metric("Rows to review", f"{len(review):,}")
row[3].metric("Duplicates found", f"{len(duplicates):,}")
row[4].metric("Time saved", f"~{minutes_saved} min")
st.caption(
    f"Time saved assumes {seconds_per_fix} seconds to spot and fix one field by hand — "
    "change that assumption in the sidebar."
)

st.divider()

tab_result, tab_changes, tab_review, tab_duplicates = st.tabs(
    ["Before and after", f"What changed ({len(changes)})",
     f"Needs a person ({len(review)})", f"Duplicates ({len(duplicates)})"]
)

with tab_result:
    left, right = st.columns(2)
    with left:
        st.subheader("Before")
        st.dataframe(raw, height=420)
    with right:
        st.subheader("After")
        st.dataframe(clean, height=420)

    st.download_button(
        "Download the clean file (CSV)",
        to_csv_bytes(clean),
        file_name="clean.csv",
        mime="text/csv",
    )

with tab_changes:
    if changes.empty:
        st.success("Nothing needed fixing in this file.")
    else:
        per_column = (
            changes.groupby("column").size().sort_values(ascending=True).reset_index(name="fixes")
        )
        figure = px.bar(
            per_column,
            x="fixes",
            y="column",
            orientation="h",
            text="fixes",
            title="Fields corrected, by column",
        )
        figure.update_traces(
            marker_color=BAR_COLOR,
            marker_line_width=0,
            textposition="outside",
            cliponaxis=False,
            hovertemplate="%{y}: %{x} fixes<extra></extra>",
        )
        figure.update_layout(
            height=60 + 34 * len(per_column),
            margin=dict(l=0, r=30, t=50, b=10),
            xaxis_title=None,
            yaxis_title=None,
            showlegend=False,
            bargap=0.35,
        )
        figure.update_xaxes(showgrid=False, showticklabels=False, zeroline=False)
        figure.update_yaxes(showgrid=False)
        st.plotly_chart(figure)

        picked = st.multiselect(
            "Filter by column", sorted(changes["column"].unique()), default=[]
        )
        table = changes[changes["column"].isin(picked)] if picked else changes
        st.dataframe(table, height=360)
        st.download_button(
            "Download the change log (CSV)",
            to_csv_bytes(changes),
            file_name="changes.csv",
            mime="text/csv",
        )

with tab_review:
    st.write(
        "These are the values the app deliberately did **not** guess at: a broken "
        "check digit, an impossible date, an address with no @. They stay as they "
        "were in the clean file."
    )
    if review.empty:
        st.success("Nothing needs a second look.")
    else:
        st.dataframe(review, height=360)
        st.download_button(
            "Download the review list (CSV)",
            to_csv_bytes(review),
            file_name="needs_review.csv",
            mime="text/csv",
        )

with tab_duplicates:
    st.write(
        "Repeats are found after cleaning, so the same person written two "
        "different ways still lines up. Nothing is deleted — the rows are listed "
        "so you decide."
    )
    if duplicates.empty:
        st.success("No repeated rows.")
    else:
        st.dataframe(duplicates, height=300)
        st.download_button(
            "Download the duplicate list (CSV)",
            to_csv_bytes(duplicates),
            file_name="duplicates.csv",
            mime="text/csv",
        )
