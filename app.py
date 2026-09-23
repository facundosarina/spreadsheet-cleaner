"""
app.py

Fila Limpia -- the interface.

The app is a sequence, not a dashboard: upload, confirm how the file was read,
clean, resolve what is doubtful, download. Each screen shows one job. The
cleaning rules live in cleaner.py, the table-level work in pipeline.py, the
file formats in fileio.py and every sentence in i18n.py; this file only decides
what is on screen.
"""

from __future__ import annotations

import hashlib

import pandas as pd
import streamlit as st

import fileio
import i18n
import pipeline
from i18n import kind_label, reason_text, t

ACCENT = "#17868F"
HIGHLIGHT = "rgba(23, 134, 143, 0.18)"
DEMOS = {
    "demo_clients": "data/clientes_sucio.csv",
    "demo_payments": "data/pagos_sucio.csv",
}

st.set_page_config(page_title="Fila Limpia", page_icon="🧽", layout="wide")


# ---------------------------------------------------------------- session ---

def state() -> dict:
    if "step" not in st.session_state:
        st.session_state.update(
            step="upload", lang=i18n.DEFAULT_LANGUAGE, file=None, plan=None,
            raw=None, kinds=None, result=None, decisions={}, resolved=set(),
            dupes={}, review_pos=0, is_demo=False,
        )
    return st.session_state


def reset_to_upload() -> None:
    for key in ("file", "plan", "raw", "kinds", "result"):
        st.session_state[key] = None
    st.session_state.update(step="upload", decisions={}, resolved=set(),
                            dupes={}, review_pos=0, is_demo=False)


def load_file(name: str, content: bytes, is_demo: bool = False) -> None:
    """Read a file into the session, or leave an error on screen."""
    lang = st.session_state["lang"]
    try:
        raw, plan = fileio.read_table(content, name)
    except fileio.FileProblem as problem:
        message = str(problem).lower()
        if "unreadable-encoding" in message:
            st.error(t(lang, "err_encoding", name=name))
        elif "xlrd" in message or "xls" in message and name.lower().endswith(".xls"):
            st.error(t(lang, "err_xls"))
        else:
            st.error(t(lang, "err_read", name=name))
        return

    if raw.empty:
        st.error(t(lang, "err_empty"))
        return

    st.session_state.update(
        file={"name": name, "content": content,
              "hash": hashlib.md5(content).hexdigest()},
        plan=plan, raw=raw, kinds=pipeline.detect_kinds(raw), result=None,
        decisions={}, resolved=set(), dupes={}, review_pos=0,
        is_demo=is_demo, step="confirm",
    )


# ------------------------------------------------------------------ pieces ---

def header(lang: str) -> None:
    left, right = st.columns([4, 1])
    with left:
        st.markdown(f"### 🧽 {t(lang, 'app_name')}")
        st.caption(t(lang, "tagline"))
    with right:
        codes = list(i18n.LANGUAGES.keys())
        chosen = st.selectbox(
            t(lang, "language"), codes, index=codes.index(lang),
            format_func=lambda c: i18n.LANGUAGES[c], key="lang_picker",
            label_visibility="collapsed",
        )
        if chosen != lang:
            st.session_state["lang"] = chosen
            st.rerun()


def steps_bar(lang: str, current: str) -> None:
    order = ["upload", "confirm", "review", "result"]
    labels = {
        "upload": t(lang, "step_upload"), "confirm": t(lang, "step_confirm"),
        "review": t(lang, "step_review"), "result": t(lang, "step_download"),
    }
    position = order.index(current) if current in order else 0
    marks = [
        f"**{labels[key]}**" if index == position else labels[key]
        for index, key in enumerate(order)
    ]
    st.caption(" › ".join(marks))


def final_frame() -> pd.DataFrame:
    """The clean table with the person's review decisions applied."""
    result = st.session_state["result"]
    frame = result["clean"].copy()
    for (row_index, column), value in st.session_state["decisions"].items():
        if column in frame.columns and row_index in frame.index:
            frame.loc[row_index, column] = value
    dropped = [r for r, choice in st.session_state["dupes"].items() if choice == "delete"]
    if dropped:
        frame = frame.drop(index=[r for r in dropped if r in frame.index])
    return frame


def pending_count() -> int:
    review = st.session_state["result"]["review"]
    if review.empty:
        return 0
    keys = {(row["row_index"], row["column"]) for _, row in review.iterrows()}
    return len(keys - st.session_state["resolved"])


def changes_table(lang: str, frame: pd.DataFrame) -> pd.DataFrame:
    if frame.empty:
        return frame
    out = pd.DataFrame({
        t(lang, "row"): frame["row"],
        t(lang, "column"): frame["column"],
        t(lang, "changed_from"): frame["before"],
        t(lang, "changed_to"): frame["after"],
        t(lang, "what_changed"): [
            reason_text(lang, row["code"], **row["params"]) for _, row in frame.iterrows()
        ],
    })
    return out.reset_index(drop=True)


def highlighted(frame: pd.DataFrame, cells: set) -> "pd.io.formats.style.Styler":
    def style(data: pd.DataFrame):
        marks = pd.DataFrame("", index=data.index, columns=data.columns)
        for row_index, column in cells:
            if row_index in marks.index and column in marks.columns:
                marks.loc[row_index, column] = f"background-color: {HIGHLIGHT}"
        return marks

    return frame.style.apply(style, axis=None)


def download_bundle(lang: str) -> None:
    """Downloads, in the format the file arrived in."""
    file_info = st.session_state["file"]
    plan = st.session_state["plan"]
    result = st.session_state["result"]
    frame = final_frame()

    changes = changes_table(lang, result["changes"])
    pending = changes_table(lang, result["review"])

    is_excel = plan.kind == "excel"
    if is_excel:
        clean_bytes = fileio.to_excel_bytes({"limpio": frame})
        clean_name = fileio.output_name(file_info["name"], "limpio", "xlsx")
        clean_mime = "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    else:
        clean_bytes = fileio.to_csv_bytes(frame)
        clean_name = fileio.output_name(file_info["name"], "limpio", "csv")
        clean_mime = "text/csv"

    left, right = st.columns(2)
    with left:
        st.download_button(t(lang, "download_clean"), clean_bytes,
                           file_name=clean_name, mime=clean_mime,
                           type="primary", width="stretch")
    with right:
        bundle = {
            clean_name: clean_bytes,
            "cambios.csv": fileio.to_csv_bytes(changes),
            "pendientes.csv": fileio.to_csv_bytes(pending),
        }
        st.download_button(
            t(lang, "download_pack"), fileio.to_zip_bytes(bundle),
            file_name=fileio.output_name(file_info["name"], "paquete", "zip"),
            mime="application/zip", width="stretch",
        )


# ------------------------------------------------------------------ screens ---

def screen_upload(lang: str) -> None:
    st.write("")
    left, middle, right = st.columns([1, 2, 1])
    with middle:
        st.subheader(t(lang, "intro"))
        st.caption(t(lang, "scope_note"))
        uploaded = st.file_uploader(
            t(lang, "drop_here"), type=["csv", "xlsx", "xlsm", "xls"],
            label_visibility="visible",
        )
        st.caption(t(lang, "formats"))
        if uploaded is not None:
            load_file(uploaded.name, uploaded.getvalue())
            if st.session_state["step"] == "confirm":
                st.rerun()

        st.write("")
        st.caption(f"— {t(lang, 'or')} —")
        demo_left, demo_right = st.columns(2)
        for column, key in zip((demo_left, demo_right), DEMOS):
            with column:
                if st.button(t(lang, key), width="stretch"):
                    path = DEMOS[key]
                    with open(path, "rb") as handle:
                        load_file(path.split("/")[-1], handle.read(), is_demo=True)
                    if st.session_state["step"] == "confirm":
                        st.rerun()
        st.write("")
        st.info(t(lang, "privacy"), icon="🔒")


def screen_confirm(lang: str) -> None:
    raw = st.session_state["raw"]
    plan = st.session_state["plan"]
    file_info = st.session_state["file"]

    if st.session_state["is_demo"]:
        st.warning(f"**{t(lang, 'demo_badge')}** · {file_info['name']}", icon="🧪")

    st.subheader(t(lang, "confirm_title"))
    st.write(t(lang, "detected_rows", rows=len(raw), cols=len(raw.columns)))

    described = plan.describe()
    if plan.kind == "csv":
        st.caption(
            f"{t(lang, 'read_as')}: {t(lang, 'separator')} «{described['separator']}» · "
            f"{t(lang, 'encoding')} {described['encoding']}"
        )
    elif len(plan.sheets) > 1:
        st.caption(t(lang, "which_sheet"))
        sheet = st.selectbox(t(lang, "sheet"), plan.sheets,
                             index=plan.sheets.index(plan.sheet))
        if sheet != plan.sheet:
            new_plan = fileio.ReadPlan(kind="excel", sheet=sheet, sheets=plan.sheets)
            frame, used = fileio.read_table(file_info["content"], file_info["name"], new_plan)
            st.session_state.update(raw=frame, plan=used, kinds=pipeline.detect_kinds(frame))
            st.rerun()

    st.write("")
    head = st.columns([3, 3, 4])
    head[0].caption(t(lang, "column"))
    head[1].caption(t(lang, "detected_type"))
    head[2].caption(t(lang, "example"))

    for column in raw.columns:
        row = st.columns([3, 3, 4])
        row[0].write(f"**{column}**")
        with row[1]:
            st.session_state["kinds"][column] = st.selectbox(
                column, pipeline.KINDS,
                index=pipeline.KINDS.index(st.session_state["kinds"].get(column, "text")),
                format_func=lambda k: kind_label(lang, k),
                key=f"kind_{file_info['hash']}_{column}",
                label_visibility="collapsed",
            )
        sample = [str(v) for v in raw[column].head(5) if str(v).strip()]
        row[2].caption(sample[0] if sample else "—")

    st.write("")
    left, right = st.columns([1, 3])
    with left:
        if st.button(t(lang, "clean_button", rows=len(raw)), type="primary",
                     width="stretch"):
            st.session_state["result"] = pipeline.clean_table(raw, st.session_state["kinds"])
            st.session_state.update(step="result", decisions={}, resolved=set(),
                                    dupes={}, review_pos=0)
            st.rerun()
    with right:
        if st.button(t(lang, "start_over")):
            reset_to_upload()
            st.rerun()


def screen_result(lang: str) -> None:
    result = st.session_state["result"]
    pending = pending_count()
    dupes = result["duplicates"]
    undecided_dupes = [r for r in dupes["row_index"] if r not in st.session_state["dupes"]] \
        if not dupes.empty else []

    if st.session_state["is_demo"]:
        st.warning(f"**{t(lang, 'demo_badge')}** · {st.session_state['file']['name']}", icon="🧪")

    st.subheader(t(lang, "result_title"))

    tiles = st.columns(3)
    tiles[0].metric(t(lang, "fixed"), f"{len(result['changes']):,}")
    tiles[1].metric(t(lang, "pending"), f"{pending:,}")
    tiles[2].metric(t(lang, "dupes"), f"{len(undecided_dupes):,}")

    if pending or undecided_dupes:
        left, right = st.columns([1, 3])
        with left:
            if st.button(t(lang, "review_cta", n=pending + len(undecided_dupes)),
                         type="primary", width="stretch"):
                st.session_state.update(step="review", review_pos=0)
                st.rerun()
        with right:
            with st.expander(t(lang, "download_anyway")):
                download_bundle(lang)
    else:
        st.success(t(lang, "all_clear"))
        download_bundle(lang)

    st.write("")
    tab_changes, tab_dupes, tab_table = st.tabs(
        [t(lang, "changes_tab"), t(lang, "dupes_tab"), t(lang, "table_tab")]
    )

    with tab_changes:
        if result["changes"].empty:
            st.info(t(lang, "no_changes"))
        else:
            st.dataframe(changes_table(lang, result["changes"]), height=380,
                         hide_index=True)

    with tab_dupes:
        if dupes.empty:
            st.info("—")
        else:
            table = pd.DataFrame({
                t(lang, "row"): dupes["row"],
                t(lang, "column"): dupes["column"],
                "": dupes["value"],
                t(lang, "first_seen", row=""): dupes["first_row"].fillna("—"),
            })
            st.dataframe(table, height=300, hide_index=True)

    with tab_table:
        st.caption(t(lang, "highlight_note"))
        st.dataframe(highlighted(final_frame(), result["changed_cells"]), height=420)

    if st.button(t(lang, "start_over")):
        reset_to_upload()
        st.rerun()


def screen_review(lang: str) -> None:
    result = st.session_state["result"]
    review = result["review"]
    dupes = result["duplicates"]

    cases: list[tuple] = []
    for _, row in review.iterrows():
        key = (row["row_index"], row["column"])
        if key not in st.session_state["resolved"]:
            cases.append(("value", row))
    if not dupes.empty:
        for _, row in dupes.iterrows():
            if row["row_index"] not in st.session_state["dupes"]:
                cases.append(("dupe", row))

    total = len(review) + (0 if dupes.empty else len(dupes))
    done = total - len(cases)

    st.subheader(t(lang, "review_title"))
    st.progress(done / total if total else 1.0,
                text=t(lang, "reviewed", done=done, total=total))

    if not cases:
        st.success(t(lang, "review_done"))
        if st.button(t(lang, "download_clean"), type="primary"):
            st.session_state["step"] = "result"
            st.rerun()
        return

    position = min(st.session_state["review_pos"], len(cases) - 1)
    kind, case = cases[position]
    st.caption(t(lang, "case_of", i=position + 1, n=len(cases)))

    if kind == "value":
        st.markdown(
            f"**{t(lang, 'row')} {case['row']} · {case['column']}** — "
            f"{t(lang, 'problem').lower()}: {reason_text(lang, case['code'], **case['params'])}"
        )
        st.text(f"{t(lang, 'original_value')}: {case['before']}")
        edited = st.text_input(t(lang, "your_value"), value=str(case["after"]),
                               key=f"fix_{case['row_index']}_{case['column']}")
        one, two, three = st.columns(3)
        with one:
            if st.button(t(lang, "apply_fix"), type="primary", width="stretch"):
                st.session_state["decisions"][(case["row_index"], case["column"])] = edited
                st.session_state["resolved"].add((case["row_index"], case["column"]))
                st.rerun()
        with two:
            if st.button(t(lang, "keep_original"), width="stretch"):
                st.session_state["decisions"][(case["row_index"], case["column"])] = case["before"]
                st.session_state["resolved"].add((case["row_index"], case["column"]))
                st.rerun()
        with three:
            if st.button(t(lang, "skip"), width="stretch"):
                st.session_state["review_pos"] = position + 1
                st.rerun()
    else:
        st.markdown(f"**{t(lang, 'dupe_question')}**")
        frame = final_frame()
        rows = [case["row_index"]]
        if case["first_row_index"] is not None and case["first_row_index"] in frame.index:
            rows.insert(0, case["first_row_index"])
        st.dataframe(frame.loc[rows], height=120)
        if case["column"]:
            st.caption(
                f"{case['column']}: {case['value']} · "
                + t(lang, "first_seen", row=case["first_row"])
            )
        one, two, three = st.columns(3)
        with one:
            if st.button(t(lang, "delete_dupe"), type="primary", width="stretch"):
                st.session_state["dupes"][case["row_index"]] = "delete"
                st.rerun()
        with two:
            if st.button(t(lang, "keep_both"), width="stretch"):
                st.session_state["dupes"][case["row_index"]] = "keep"
                st.rerun()
        with three:
            if st.button(t(lang, "skip"), width="stretch"):
                st.session_state["review_pos"] = position + 1
                st.rerun()

    st.write("")
    if st.button(f"← {t(lang, 'result_title')}"):
        st.session_state["step"] = "result"
        st.rerun()


# --------------------------------------------------------------------- run ---

session = state()
language = session["lang"]

header(language)
steps_bar(language, session["step"])
st.divider()

if session["step"] == "upload":
    screen_upload(language)
elif session["step"] == "confirm":
    screen_confirm(language)
elif session["step"] == "review":
    screen_review(language)
else:
    screen_result(language)
