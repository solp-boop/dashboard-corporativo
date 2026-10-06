"""Tiempos de consolidación de SKU nuevos y top ranking contra el objetivo de −15 %.

Por trimestre del año: Q1 es la base; el objetivo es bajar la mediana un 15 % y se
compara el último trimestre cerrado contra la base.

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
    d = _solo_destino(d)
    d["mes"] = calc.month_start(d["etd"])
    return d


def _solo_destino(d: pd.DataFrame) -> pd.DataFrame:
    if settings.PRODUCTOS_DESTINO and "destino" in d:
        from utils.data_cleaning import fold
        return d[d["destino"].map(lambda v: fold(v) == fold(settings.PRODUCTOS_DESTINO) if isinstance(v, str) else False)]
    return d


EXCLUIDOS = ("muestra", "repuesto")   # tipos de negocio que no entran en el universo de time to market


def muestras(aereos: pd.DataFrame | None, planif: pd.DataFrame | None) -> tuple[set, set]:
    """(embarques, SO) a excluir: muestras y repuestos.

    Aéreos con tipo MUESTRAS / REPUESTOS en Seguimiento Aéreos y SO «Muestras» / «Repuestos» en Planificación.
    """
    from utils.data_cleaning import fold, id_key

    def es_excluido(v) -> bool:
        return isinstance(v, str) and any(k in fold(v) for k in EXCLUIDOS)

    embs, sos = set(), set()
    if aereos is not None and len(aereos):
        col = aereos["tipo_sla"] if "tipo_sla" in aereos else aereos.get("tipo_negocio")
        if col is not None:
            embs = set(id_key(aereos.loc[col.map(es_excluido), "embarque"].dropna()))
    if planif is not None and len(planif) and "tipo_negocio" in planif:
        sos = set(planif.loc[planif["tipo_negocio"].map(es_excluido), "so"].dropna().astype(str))
    return embs, sos


def base_universo(eh: pd.DataFrame, today: pd.Timestamp, aereos=None, planif=None) -> pd.DataFrame:
    """Universo completo de SO (marítimas y aéreas) ya zarpadas, sin muestras ni repuestos, con tiempo válido."""
    from utils.data_cleaning import id_key
    d = eh[eh["etd"].notna() & (eh["etd"] <= today) & eh["tiempo_consolidacion"].notna()].copy()
    d = _solo_destino(d)
    embs, sos = muestras(aereos, planif)
    d = d[~id_key(d["embarque"]).isin(embs) & ~d["so"].astype(str).isin(sos)]
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


def quarters(year: int) -> list[pd.Timestamp]:
    return [pd.Timestamp(year, m, 1) for m in (1, 4, 7, 10)]


def q_label(q: pd.Timestamp) -> str:
    return f"Q{(q.month - 1) // 3 + 1}"


def summary(d: pd.DataFrame, today: pd.Timestamp) -> pd.DataFrame:
    """Por grupo × estructura: mediana por trimestre del año, base, actual y objetivo.

    Base: Q1 del año (si no tiene al menos MIN_SAMPLE SO, el primer trimestre que sí, y se avisa).
    Actual: el último trimestre cerrado posterior a la base.
    Objetivo: base − 15 %. Variación = actual vs base.
    """
    year = today.year
    qs = quarters(year)
    this_q = today.to_period("Q").to_timestamp()
    rows = []
    for grupo, label in GRUPOS.items():
        so = per_so(d[d[grupo]])
        so = so[so["mes"].dt.year == year].assign(q=lambda x: x["mes"].dt.to_period("Q").dt.to_timestamp())
        for est in ESTRUCTURAS:
            s = so[so["estructura"] == est]
            row = {"grupo": label, "estructura": est, "so_anio": int(s["so"].nunique()), "nota": ""}
            stats = {}
            for q in qs:
                t = s[s["q"] == q]["tiempo"]
                stats[q] = (float(t.median()) if len(t) else np.nan, int(len(t)))
                row[q_label(q)], row[q_label(q) + "_n"] = stats[q]
            row["anio"] = float(s["tiempo"].median()) if len(s) else np.nan
            row["anio_n"] = int(len(s))
            con_datos = [q for q in qs if stats[q][1] >= settings.MIN_SAMPLE and q < this_q]
            base_q = qs[0] if stats[qs[0]][1] >= settings.MIN_SAMPLE else (con_datos[0] if con_datos else None)
            if base_q is not None and base_q != qs[0]:
                row["nota"] = f"{label}: sin datos suficientes en Q1, la base es {q_label(base_q)}."
            cerrados = [q for q in qs if base_q is not None and base_q < q < this_q and stats[q][1] > 0]
            act_q = cerrados[-1] if cerrados else None
            base_med, base_n = stats[base_q] if base_q is not None else (np.nan, 0)
            act_med, act_n = stats[act_q] if act_q is not None else (np.nan, 0)
            objetivo = base_med * (1 - settings.REDUCCION_OBJETIVO) if base_med == base_med else np.nan
            var = (act_med - base_med) / base_med if base_med and act_med == act_med else np.nan
            enough = base_n >= settings.MIN_SAMPLE and act_n >= settings.MIN_SAMPLE
            row.update({
                "base": base_med, "base_n": base_n, "base_q": q_label(base_q) if base_q is not None else "",
                "base_txt": q_label(base_q) if base_q is not None else "—",
                "actual": act_med, "actual_n": act_n, "actual_q": q_label(act_q) if act_q is not None else "",
                "actual_txt": q_label(act_q) if act_q is not None else "—",
                "objetivo": objetivo, "variacion": var,
                "estado": ("" if not enough or var != var else
                           "Cumple" if var <= -settings.REDUCCION_OBJETIVO else
                           "Reduce, sin llegar" if var < 0 else "No reduce"),
            })
            rows.append(row)
    return pd.DataFrame(rows)


def mes_a_mes(d: pd.DataFrame, year: int) -> pd.DataFrame:
    """Por mes de ETD del año: SO, mínimo, mediana y máximo de consolidación (días por SO), sin abrir por estructura.

    Grupos: todas las SO, SKU nuevos y top ranking. Columnas «{grupo}|so», «|min», «|med», «|max».
    La última fila (mes NaT) es el total del año.
    """
    x = d[d["mes"].dt.year == year].assign(todas=True)
    grupos = {"todas": "Todas las SO", **GRUPOS}
    meses = sorted(x["mes"].unique())
    rows = []
    for mes in meses + [pd.NaT]:
        r = {"mes": mes}
        sub_m = x if pd.isna(mes) else x[x["mes"] == mes]
        for g in grupos:
            sg = sub_m[sub_m[g].fillna(False).astype(bool)]
            so = sg.groupby(["so", "mes"], as_index=False).agg(tiempo=("tiempo_consolidacion", "median"))
            t = so["tiempo"]
            r[f"{g}|so"] = int(so["so"].nunique())
            r[f"{g}|min"] = float(t.min()) if len(t) else np.nan
            r[f"{g}|med"] = float(t.median()) if len(t) else np.nan
            r[f"{g}|max"] = float(t.max()) if len(t) else np.nan
        rows.append(r)
    out = pd.DataFrame(rows)
    out.attrs["grupos"] = grupos
    return out
