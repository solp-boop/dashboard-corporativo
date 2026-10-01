"""Tiempos de consolidación de SKU nuevos y top ranking contra el objetivo de −15 %.

Unidad: SO (Embarques Historicos tiene una fila por SO × producto; se cuentan SO
distintas). Tiempo: columna "Tiempo de consolidacion" de Embarques Historicos.
Estructura (mono / consolidado): la del embarque en Reservas Históricas.

Sin Streamlit, para poder testearlo.
"""
from __future__ import annotations

import numpy as np
import pandas as pd

from config import settings
from utils import calculations as calc

GRUPOS = {"es_nuevo": "SKU nuevos", "es_top": f"Top ranking (1–{settings.TOP_RANKING_MAX})"}
ESTRUCTURAS = ["Consolidado", "Monoproveedor"]


def base_lines(eh: pd.DataFrame, today: pd.Timestamp) -> pd.DataFrame:
    """Líneas marítimas ya zarpadas con tiempo de consolidación y estructura."""
    d = eh[eh["maritimo"] & eh["etd"].notna() & (eh["etd"] <= today)
           & eh["tiempo_consolidacion"].notna() & eh["estructura"].isin(ESTRUCTURAS)].copy()
    d["mes"] = calc.month_start(d["etd"])
    return d


def per_so(d: pd.DataFrame) -> pd.DataFrame:
    """Una fila por SO: mediana del tiempo de sus líneas (suele ser el mismo valor)."""
    return (d.groupby(["so", "mes", "estructura"], as_index=False)
              .agg(tiempo=("tiempo_consolidacion", "median")))


def monthly(d: pd.DataFrame, grupo: str) -> pd.DataFrame:
    g = per_so(d[d[grupo]])
    if g.empty:
        return pd.DataFrame(columns=["mes", "estructura", "so", "mediana"])
    return g.groupby(["mes", "estructura"], as_index=False).agg(so=("so", "nunique"), mediana=("tiempo", "median"))


def periods(m: pd.DataFrame, today: pd.Timestamp) -> tuple[list, list, str]:
    """Meses base y meses de comparación para un grupo.

    Base: el período configurado (BASE_DESDE–BASE_HASTA). Si el grupo no tiene
    datos ahí, se toman los primeros 3 meses con datos (y se avisa).
    Comparación: los últimos COMPARACION_MESES meses cerrados posteriores a la base.
    """
    months = sorted(m["mes"].unique())
    b0, b1 = pd.Timestamp(settings.BASE_DESDE), pd.Timestamp(settings.BASE_HASTA)
    base = [x for x in months if b0 <= x <= b1]
    nota = ""
    if not base:
        base = months[:3]
        if base:
            nota = (f"Sin datos en el período base configurado; se usa como base "
                    f"{base[0]:%m/%Y}–{base[-1]:%m/%Y} (primeros meses con datos).")
    this_month = today.to_period("M").to_timestamp()
    after = [x for x in months if base and x > base[-1] and x < this_month]
    comp = after[-settings.COMPARACION_MESES:]
    return base, comp, nota


def summary(d: pd.DataFrame, today: pd.Timestamp) -> pd.DataFrame:
    """Por grupo × estructura: base, actual, variación y si cumple el objetivo."""
    rows = []
    for grupo, label in GRUPOS.items():
        m_all = monthly(d, grupo)
        so = per_so(d[d[grupo]])
        base, comp, nota = periods(m_all, today)
        for est in ESTRUCTURAS:
            s = so[so["estructura"] == est]
            b = s[s["mes"].isin(base)]["tiempo"]
            c = s[s["mes"].isin(comp)]["tiempo"]
            base_med = float(b.median()) if len(b) else np.nan
            comp_med = float(c.median()) if len(c) else np.nan
            objetivo = base_med * (1 - settings.REDUCCION_OBJETIVO) if base_med == base_med else np.nan
            var = (comp_med - base_med) / base_med if base_med and comp_med == comp_med else np.nan
            enough = len(b) >= settings.MIN_SAMPLE and len(c) >= settings.MIN_SAMPLE
            rows.append({
                "grupo": label, "estructura": est,
                "so_anio": int(s["so"].nunique()),
                "base": base_med, "base_n": int(len(b)),
                "base_txt": f"{base[0]:%m/%y}–{base[-1]:%m/%y}" if base else "—",
                "actual": comp_med, "actual_n": int(len(c)),
                "actual_txt": f"{comp[0]:%m/%y}–{comp[-1]:%m/%y}" if comp else "—",
                "objetivo": objetivo, "variacion": var,
                "estado": ("" if not enough or var != var else
                           "Cumple" if var <= -settings.REDUCCION_OBJETIVO else
                           "Reduce, sin llegar" if var < 0 else "No reduce"),
                "nota": nota,
            })
    return pd.DataFrame(rows)
