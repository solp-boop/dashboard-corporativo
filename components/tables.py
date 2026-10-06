"""Tabla con búsqueda, orden (nativo), semáforo y exportación CSV / Excel.

La exportación descarga exactamente las filas que se ven: filtros globales +
búsqueda de la tabla.
"""
from __future__ import annotations

import io
from dataclasses import dataclass

import pandas as pd
import streamlit as st

from utils.data_cleaning import fold

pd.set_option("styler.render.max_elements", 5_000_000)

ICONS = {"Dentro de SLA": "🟢", "Atención": "🟡", "Fuera de SLA": "🔴"}


@dataclass
class ColSpec:
    source: str
    label: str
    kind: str = "text"     # text | int | num | usd | days | date | pct | status | bool
    width: str | None = None


def with_status_icon(s: pd.Series) -> pd.Series:
    return s.map(lambda v: f"{ICONS.get(v, '')} {v}".strip() if isinstance(v, str) and v else "")


def _display_frame(df: pd.DataFrame, cols: list[ColSpec]) -> tuple[pd.DataFrame, dict]:
    out = pd.DataFrame(index=df.index)
    config = {}
    for c in cols:
        if c.source not in df:
            continue
        s = df[c.source]
        if c.kind == "status":
            out[c.label] = with_status_icon(s)
            config[c.label] = st.column_config.TextColumn(c.label, width=c.width)
        elif c.kind == "date":
            out[c.label] = pd.to_datetime(s, errors="coerce")
            config[c.label] = st.column_config.DateColumn(c.label, format="DD/MM/YYYY", width=c.width)
        elif c.kind in ("int", "days"):
            out[c.label] = pd.to_numeric(s, errors="coerce").round(0).astype("Int64")
            config[c.label] = st.column_config.NumberColumn(c.label, width=c.width)
        elif c.kind == "num":
            out[c.label] = pd.to_numeric(s, errors="coerce").round(1)
            config[c.label] = st.column_config.NumberColumn(c.label, width=c.width)
        elif c.kind == "usd":
            out[c.label] = pd.to_numeric(s, errors="coerce").round(0)
            config[c.label] = st.column_config.NumberColumn(c.label, width=c.width)
        elif c.kind == "pct":
            out[c.label] = pd.to_numeric(s, errors="coerce") * 100
            config[c.label] = st.column_config.NumberColumn(c.label, width=c.width)
        elif c.kind == "bool":
            out[c.label] = s.map(lambda v: "Sí" if v is True else ("No" if v is False else ""))
            config[c.label] = st.column_config.TextColumn(c.label, width=c.width)
        else:
            out[c.label] = s.astype(object).where(s.notna(), "")
            config[c.label] = st.column_config.TextColumn(c.label, width=c.width)
    return out.reset_index(drop=True), config


def _formatters(cols: list[ColSpec], present) -> dict:
    """Formato es-AR (punto de miles, coma decimal) para mostrar; los valores siguen siendo números (ordenan bien)."""
    from utils import formatting as fmt

    def n0(v):
        return "" if pd.isna(v) else fmt.fmt_int(v)

    def n1(v):
        return "" if pd.isna(v) else fmt.fmt_num(v, 1)

    def pct(v):
        return "" if pd.isna(v) else fmt._es(f"{float(v):,.0f}") + " %"

    by_kind = {"int": n0, "days": n0, "usd": n0, "num": n1, "pct": pct}
    return {c.label: by_kind[c.kind] for c in cols if c.kind in by_kind and c.label in present}


def _search(df: pd.DataFrame, query: str) -> pd.DataFrame:
    q = fold(query)
    if not q:
        return df
    text = df.astype(str).apply(lambda col: col.map(fold)).agg(" ".join, axis=1)
    return df[text.str.contains(q, regex=False)]


def to_csv(df: pd.DataFrame) -> bytes:
    # ';' y coma decimal: abre bien en Excel con configuración regional argentina.
    return df.to_csv(index=False, sep=";", decimal=",", date_format="%d/%m/%Y").encode("utf-8-sig")


def to_excel(df: pd.DataFrame, sheet: str = "Datos") -> bytes:
    buf = io.BytesIO()
    with pd.ExcelWriter(buf, engine="openpyxl", date_format="DD/MM/YYYY") as xw:
        df.to_excel(xw, index=False, sheet_name=sheet[:31])
        ws = xw.sheets[sheet[:31]]
        for i, col in enumerate(df.columns, start=1):
            lengths = df[col].map(lambda v: len(str(v)) if v is not None and v == v else 0)
            p90 = float(lengths.quantile(0.9)) if len(df) else 0.0
            width = min(45, max(10, len(str(col)) + 2, int(p90 if p90 == p90 else 0) + 2))
            ws.column_dimensions[ws.cell(row=1, column=i).column_letter].width = width
        ws.freeze_panes = "A2"
    return buf.getvalue()


def data_table(df: pd.DataFrame, cols: list[ColSpec], key: str, filename: str,
               height: int | None = None, search: bool = True, caption: str = "",
               row_styles: pd.Series | None = None) -> None:
    """row_styles: CSS por fila (alineado con el índice de df), p. ej. para resaltar un récord."""
    display, config = _display_frame(df, cols)
    formatters = _formatters(cols, set(display.columns))
    styles = (row_styles.reindex(df.index).fillna("").reset_index(drop=True)
              if row_styles is not None else None)
    top = st.columns([4, 1, 1]) if search else st.columns([2, 1, 1])
    query = ""
    if search:
        query = top[0].text_input("Buscar en la tabla", key=f"q_{key}", placeholder="Buscar…",
                                  label_visibility="collapsed")
    shown = _search(display, query) if query else display
    top[1].download_button("Excel", icon=":material/download:", data=lambda d=shown: to_excel(d), file_name=f"{filename}.xlsx",
                           mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                           key=f"xl_{key}", width="stretch", disabled=shown.empty)
    top[2].download_button("CSV", icon=":material/download:", data=lambda d=shown: to_csv(d), file_name=f"{filename}.csv",
                           mime="text/csv", key=f"csv_{key}", width="stretch", disabled=shown.empty)
    if shown.empty:
        st.caption("Sin filas para mostrar.")
        return
    rows = len(shown)
    h = height or min(560, 38 + 35 * rows)
    data = shown.style.format(formatters, na_rep="—")
    if styles is not None and styles.loc[shown.index].ne("").any():
        css = styles.loc[shown.index]
        data = data.apply(lambda row: [css[row.name]] * len(row), axis=1)
    st.dataframe(data, column_config=config, hide_index=True, height=h, width="stretch", placeholder="—")
    st.caption((caption + " · " if caption else "") + f"{rows:,} filas".replace(",", "."))
