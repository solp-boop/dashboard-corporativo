"""«¿Qué lo explica?» como descarga: se elige la dimensión y se baja el Excel (no se muestra en pantalla)."""
from __future__ import annotations

import pandas as pd
import streamlit as st

from components.tables import ColSpec, solo_descarga
from utils import diagnostico as dg


def diagnostico(df: pd.DataFrame, dims: list[dg.Dimension], valor: str, limite: str | None, key: str,
                casos_cols: list[ColSpec], id_col: str = "embarque", prev: pd.DataFrame | None = None,
                prev_txt: str = "", unidad: str = "operaciones") -> None:
    """Selector de dimensión + botón de descarga.

    El Excel trae dos solapas: «Detalle» (cada operación, las que se pasan primero) y «Por <dimensión>» (operaciones,
    mediana, P90, fuera de objetivo, cuánto explica del desvío y Δ contra el período anterior)."""
    if df is None or df.empty:
        st.markdown('<div class="empty">Sin operaciones para analizar.</div>', unsafe_allow_html=True)
        return
    dims = [d for d in dims if d.clave in df]
    nombres = {d.clave: d.nombre for d in dims}
    c1, c2 = st.columns([2, 3], gap="small", vertical_alignment="bottom")
    elegido = c1.selectbox("Analizar por", list(nombres), format_func=nombres.get, key=f"{key}_dim")
    t = dg.explicar(df, elegido, valor, limite, id_col=id_col, prev=prev)
    nombre = nombres[elegido]
    resumen_cols = [ColSpec("grupo", nombre), ColSpec("ops", unidad.capitalize(), "int"),
                    ColSpec("mediana", "Mediana (d)", "days"), ColSpec("p90", "P90 (d)", "days")]
    if limite is not None:
        resumen_cols += [ColSpec("fuera", "Fuera de objetivo", "int"), ColSpec("pct_fuera", "% fuera", "pct"),
                         ColSpec("contrib", "Explica del desvío", "pct"), ColSpec("exceso", "Exceso (d)", "days")]
    if len(t) and t["delta"].notna().any():
        resumen_cols.append(ColSpec("delta", f"Δ mediana vs {prev_txt or 'período anterior'} (d)", "days"))

    c = df.copy()
    if limite is not None and limite in c:
        c = c.assign(_exc=(c[valor] - c[limite]).clip(lower=0)).sort_values("_exc", ascending=False)
    for col in c.columns:
        if c[col].map(lambda x: isinstance(x, (list, tuple, set))).any():
            c = c.assign(**{col: c[col].map(dg.texto_lista)})
    with c2:
        solo_descarga(c, casos_cols, key=f"{key}_{elegido}", filename=f"analisis_{key}_por_{elegido}",
                      label=f"Descargar análisis por {nombre.lower()}",
                      hojas={f"Por {nombre}": (t, resumen_cols)})
    st.caption(f"El Excel trae el resumen por {nombre.lower()} (ordenado por cuánto explica de los fuera de objetivo) "
               f"y el detalle de cada operación. No se muestra en pantalla.")
