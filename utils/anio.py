"""«Nuestro año»: lo embarcado en el año calendario, mes a mes.

Fuente: Reservas Históricas (una fila por embarque, todos los modos).
Mes = mes de ETD. Sin Streamlit, para poder testearlo.
"""
from __future__ import annotations

import numpy as np
import pandas as pd

from config.mappings import MODOS_MARITIMOS
from utils import calculations as calc

MEDIOS = ["Marítimo", "Aéreo", "Courier", "Camión", "Otro"]
ESTRUCTURAS = ["Monoproveedor", "Consolidado"]


def medio(modo) -> str:
    if modo in MODOS_MARITIMOS:
        return "Marítimo"
    if modo == "Aéreo":
        return "Aéreo"
    if modo == "Courier":
        return "Courier"
    if modo == "Terrestre":
        return "Camión"
    return "Otro"


def del_anio(hist: pd.DataFrame, year: int) -> pd.DataFrame:
    d = hist[hist["etd"].dt.year == year].copy()
    d["medio"] = d["modo"].map(medio)
    d["mes"] = calc.month_start(d["etd"])
    d["cnt_mar"] = d["contenedores"].where(d["medio"] == "Marítimo", 0).fillna(0)
    return d


def _fila(g: pd.DataFrame) -> dict:
    n = int(g["embarque"].nunique())
    con_est = g["estructura"].isin(ESTRUCTURAS)
    n_est = int(con_est.sum())
    row = {
        "embarques": n,
        "contenedores": float(g["cnt_mar"].sum()),
        "fob_simi": float(g["fob_simi"].sum()),
        "m3": float(g["m3"].sum()),
        "pct_mono": (g["estructura"] == "Monoproveedor").sum() / n_est if n_est else np.nan,
        "pct_cons": (g["estructura"] == "Consolidado").sum() / n_est if n_est else np.nan,
    }
    for m in MEDIOS:
        row[f"pct_{m}"] = (g["medio"] == m).sum() / len(g) if len(g) else np.nan
    return row


def mensual(d: pd.DataFrame) -> pd.DataFrame:
    """Una fila por mes + fila de total del año."""
    rows = [{"mes": mes, **_fila(g)} for mes, g in d.groupby("mes")]
    out = pd.DataFrame(rows)
    if out.empty:
        return out
    total = {"mes": pd.NaT, **_fila(d)}
    return pd.concat([out, pd.DataFrame([total])], ignore_index=True)


def medios_presentes(d: pd.DataFrame) -> list[str]:
    return [m for m in MEDIOS if (d["medio"] == m).any()]
