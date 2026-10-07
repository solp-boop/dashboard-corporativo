"""Costos (nivel 2): ¿dónde se va el gasto? Corte por dimensión. Sin Streamlit, para poder testearlo."""
from __future__ import annotations

import numpy as np
import pandas as pd

from config.mappings import MODOS_MARITIMOS

SIN_DATO = "Sin dato"


def pagos(hist: pd.DataFrame | None, aer: pd.DataFrame | None, today: pd.Timestamp) -> pd.DataFrame:
    """Marítimos y aéreos zarpados con flete pagado, en un solo formato.

    costo = flete + gastos en origen + gastos locales. Aéreo: tipo de contenedor «Aéreo», sin referencia de mercado.
    """
    partes = []
    if hist is not None and len(hist):
        h = hist[hist["modo"].isin(MODOS_MARITIMOS) & (hist["etd"] <= today) & (hist["flete_pagado"] > 0)].copy()
        h["medio"] = "Marítimo"
        partes.append(h)
    if aer is not None and len(aer):
        a = aer[(aer["etd"] <= today) & (aer["flete_pagado"] > 0)].copy()
        a["medio"] = "Aéreo"
        a["tipo_ctnr"] = "Aéreo"
        partes.append(a)
    if not partes:
        return pd.DataFrame(columns=["embarque", "etd", "medio", "costo", "flete_pagado"])
    d = pd.concat(partes, ignore_index=True, sort=False)
    d["costo"] = (d["flete_pagado"].clip(lower=0).fillna(0) + d["gastos_origen"].clip(lower=0).fillna(0)
                  + d["gastos_locales"].clip(lower=0).fillna(0))
    for c in ("mercado_mes", "flete_por_ctnr", "contenedores", "fob", "responsable", "linea", "puerto", "forwarder"):
        if c not in d:
            d[c] = np.nan
    return d


def _vs_mercado(g: pd.DataFrame) -> float:
    ok = g["mercado_mes"].notna() & g["flete_por_ctnr"].notna()
    m = float((g.loc[ok, "mercado_mes"] * g.loc[ok, "contenedores"].fillna(1)).sum())
    p = float((g.loc[ok, "flete_por_ctnr"] * g.loc[ok, "contenedores"].fillna(1)).sum())
    return (p - m) / m if m else np.nan


def por_dimension(d: pd.DataFrame, dim: str, prev: pd.DataFrame | None = None) -> pd.DataFrame:
    """Una fila por valor de la dimensión, ordenada por gasto: embarques, contenedores, gasto, % del gasto,
    flete por contenedor (mediana), costo / FOB, pagado vs mercado y Δ del flete por contenedor contra `prev`."""
    cols = ["grupo", "embarques", "contenedores", "gasto", "pct_gasto", "flete_ctnr", "incidencia", "vs_mercado",
            "delta_ctnr"]
    if d is None or d.empty or dim not in d:
        return pd.DataFrame(columns=cols)
    x = d.assign(_g=d[dim].map(lambda v: SIN_DATO if v is None or (isinstance(v, float) and np.isnan(v))
                               or str(v).strip() == "" else str(v).strip()))
    total = float(x["costo"].sum())
    rows = []
    for k, g in x.groupby("_g"):
        fob = g.loc[g["fob"] > 0]
        rows.append({
            "grupo": k, "embarques": g["embarque"].nunique(), "contenedores": g["contenedores"].sum(min_count=1),
            "gasto": float(g["costo"].sum()), "flete_ctnr": g["flete_por_ctnr"].median(),
            "incidencia": float(fob["costo"].sum() / fob["fob"].sum()) if fob["fob"].sum() else np.nan,
            "vs_mercado": _vs_mercado(g),
        })
    t = pd.DataFrame(rows)
    t["pct_gasto"] = t["gasto"] / total if total else np.nan
    if prev is not None and len(prev) and dim in prev:
        p = prev.assign(_g=prev[dim].map(lambda v: SIN_DATO if v is None or (isinstance(v, float) and np.isnan(v))
                                         or str(v).strip() == "" else str(v).strip()))
        t["delta_ctnr"] = t["flete_ctnr"] - t["grupo"].map(p.groupby("_g")["flete_por_ctnr"].median())
    else:
        t["delta_ctnr"] = np.nan
    t["_sd"] = t["grupo"] == SIN_DATO
    return t.sort_values(["_sd", "gasto"], ascending=[True, False])[cols].reset_index(drop=True)


def casos(d: pd.DataFrame, dim: str, grupo: str) -> pd.DataFrame:
    v = d[dim].map(lambda x: SIN_DATO if x is None or (isinstance(x, float) and np.isnan(x)) or str(x).strip() == ""
                   else str(x).strip())
    return d[v == grupo]
