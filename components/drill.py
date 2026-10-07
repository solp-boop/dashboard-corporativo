"""Diagnóstico con drill-down: ¿qué lo explica? → clic en una fila → sus operaciones."""
from __future__ import annotations

import pandas as pd
import streamlit as st

from components.tables import ColSpec, data_table
from utils import diagnostico as dg
from utils import formatting as fmt


def diagnostico(df: pd.DataFrame, dims: list[dg.Dimension], valor: str, limite: str | None, key: str,
                casos_cols: list[ColSpec], id_col: str = "embarque", prev: pd.DataFrame | None = None,
                prev_txt: str = "", unidad: str = "operaciones") -> None:
    """Selector de dimensión + tabla por valor (ordenada por contribución al desvío) + operaciones del valor elegido."""
    if df is None or df.empty:
        st.markdown('<div class="empty">Sin operaciones para analizar.</div>', unsafe_allow_html=True)
        return
    dims = [d for d in dims if d.clave in df]
    nombres = {d.clave: d.nombre for d in dims}
    elegido = st.segmented_control("Ver por", list(nombres), default=dims[0].clave, format_func=nombres.get,
                                   key=f"{key}_dim", label_visibility="collapsed") or dims[0].clave
    t = dg.explicar(df, elegido, valor, limite, id_col=id_col, prev=prev)
    if t.empty:
        st.markdown('<div class="empty">Sin datos para esta dimensión.</div>', unsafe_allow_html=True)
        return
    con_lim = limite is not None and t["fuera"].sum() > 0
    show = pd.DataFrame({
        nombres[elegido]: t["grupo"],
        "Ops": t["ops"].astype(int),
        "Mediana (d)": t["mediana"].round(0),
        "P90 (d)": t["p90"].round(0),
    })
    config = {
        nombres[elegido]: st.column_config.TextColumn(nombres[elegido], width="medium"),
        "Ops": st.column_config.NumberColumn("Ops", help=f"Cantidad de {unidad}"),
        "Mediana (d)": st.column_config.NumberColumn("Mediana (d)", format="%d"),
        "P90 (d)": st.column_config.NumberColumn("P90 (d)", format="%d",
                                                 help="El 10 % más lento tarda más que esto"),
    }
    if con_lim:
        show["Fuera"] = t["fuera"].astype(int)
        show["% fuera"] = (t["pct_fuera"] * 100).round(0)
        show["Explica del desvío"] = (t["contrib"] * 100).round(0)
        show["Exceso (d)"] = t["exceso"].round(0)
        config.update({
            "Fuera": st.column_config.NumberColumn("Fuera", help="Operaciones que superan su objetivo"),
            "% fuera": st.column_config.NumberColumn("% fuera", format="%d %%",
                                                     help="Fuera / operaciones con objetivo"),
            "Explica del desvío": st.column_config.ProgressColumn(
                "Explica del desvío", format="%d %%", min_value=0, max_value=100,
                help="Qué parte de todas las operaciones fuera de objetivo corresponde a este valor"),
            "Exceso (d)": st.column_config.NumberColumn("Exceso (d)", format="%d",
                                                        help="Mediana de días por encima del objetivo, de las que se pasan"),
        })
    if t["delta"].notna().any():
        show["Δ mediana (d)"] = t["delta"].round(0)
        config["Δ mediana (d)"] = st.column_config.NumberColumn(
            "Δ mediana (d)", format="%+d", help=f"Mediana actual menos la de {prev_txt or 'el período de comparación'}")
    alto = min(420, 38 + 35 * len(show))
    ev = st.dataframe(show, column_config=config, hide_index=True, width="stretch", height=alto,
                      on_select="rerun", selection_mode="single-row", key=f"{key}_tabla_{elegido}", placeholder="—")
    filas = ev.selection.rows if ev is not None and hasattr(ev, "selection") else []
    i = filas[0] if filas and filas[0] < len(t) else 0
    grupo = t.iloc[i]["grupo"]
    st.caption(("Ordenado por cuánto explica del desvío. " if con_lim else "")
               + "Hacé clic en una fila para ver sus operaciones."
               + (" Una operación con varios valores (p. ej. varios proveedores) cuenta en cada uno."
                  if any(d.multiple and d.clave == elegido for d in dims) else ""))

    c = dg.casos(df, elegido, grupo)
    if limite is not None and limite in c:
        c = c.assign(_exc=(c[valor] - c[limite]).clip(lower=0)).sort_values("_exc", ascending=False)
        if con_lim and st.toggle("Solo las que se pasan del objetivo", value=True, key=f"{key}_solo"):
            c = c[c[valor] > c[limite]]
    for col in c.columns:
        if c[col].map(lambda x: isinstance(x, (list, tuple, set))).any():
            c = c.assign(**{col: c[col].map(dg.texto_lista)})
    st.markdown(f'<div class="section-sub"><b>{fmt.plural(len(c), "operación", "operaciones")} · '
                f'{nombres[elegido].lower()}: {grupo}</b></div>', unsafe_allow_html=True)
    data_table(c, casos_cols, key=f"{key}_casos", filename=f"operaciones_{key}", search=len(c) > 12)
