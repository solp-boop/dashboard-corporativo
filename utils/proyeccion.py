"""Proyección: lo que todavía no zarpó, por mes de ETD.

Fuentes, sin contar dos veces:
- Reservado: Reservas con ETD desde hoy (marítimo, courier, camión; los AIR se toman de Seguimiento Aéreos).
- Aéreo: Seguimiento Aéreos activos con ETD desde hoy.
- Por reservar: SO de Planificación con ETD desde hoy cuyo embarque todavía no está en Reservas ni en Históricas.
  Sus contenedores se estiman con settings.M3_POR_CONTENEDOR (no hay contenedor asignado todavía).

Mono / consolidado y medio de envío se expresan en % del volumen (m³), porque lo reservado se cuenta en embarques
y lo planificado en SO. Sin Streamlit, para poder testearlo.
"""
from __future__ import annotations

import numpy as np
import pandas as pd

from config import settings
from utils import calculations as calc
from utils.anio import MEDIOS, medio
from utils.data_cleaning import id_key


def _fob(df: pd.DataFrame, *cols: str) -> pd.Series:
    out = pd.Series(np.nan, index=df.index, dtype=float)
    for c in cols:
        if c in df:
            out = out.fillna(pd.to_numeric(df[c], errors="coerce").where(lambda s: s > 0))
    return out.fillna(0.0)


def base(res: pd.DataFrame | None, planif: pd.DataFrame | None, aer: pd.DataFrame | None,
         hist: pd.DataFrame | None, today: pd.Timestamp) -> pd.DataFrame:
    """Una fila por embarque reservado / aéreo activo / SO por reservar, con mes, m³, FOB, estructura y medio."""
    partes = []
    ya = set()
    if res is not None and len(res):
        r = res[res["etd"] >= today]
        r = r[~r["embarque"].astype(str).str.strip().str.upper().str.startswith("AIR")]
        ya |= set(id_key(res["embarque"]))
        partes.append(pd.DataFrame({
            "fuente": "Reservado", "id": r["embarque"].astype(str), "etd": r["etd"],
            "contenedores": r["contenedores"].fillna(0), "m3": r["m3"].fillna(0), "fob": _fob(r, "fob_real", "fob_simi"),
            "estructura": r["estructura"], "medio": r["modo"].map(medio) if "modo" in r else "Marítimo",
        }))
    if aer is not None and len(aer):
        a = aer[(aer["activo"] if "activo" in aer else True) & (aer["etd"] >= today)]
        partes.append(pd.DataFrame({
            "fuente": "Reservado", "id": a["embarque"].astype(str), "etd": a["etd"], "contenedores": 0.0,
            "m3": a["m3"].fillna(0) if "m3" in a else 0.0, "fob": _fob(a, "fob_simi"), "estructura": None,
            "medio": "Aéreo",
        }))
    if hist is not None and len(hist):
        ya |= set(id_key(hist["embarque"]))
    if planif is not None and len(planif):
        p = planif[planif["etd"] >= today]
        sin_emb = p["embarque"].isna() | ~id_key(p["embarque"].fillna("")).isin(ya)
        p = p[sin_emb]
        m = p["modo"].map(lambda v: medio(v) if isinstance(v, str) and v.strip() else "Marítimo") \
            if "modo" in p else "Marítimo"
        partes.append(pd.DataFrame({
            "fuente": "Por reservar", "id": p["so"].astype(str), "etd": p["etd"],
            "contenedores": np.nan, "m3": p["m3"].fillna(0), "fob": _fob(p, "fob_origen", "fob_real", "fob_simi"),
            "estructura": p["estructura"], "medio": m,
        }))
    if not partes:
        return pd.DataFrame(columns=["fuente", "id", "etd", "mes", "contenedores", "m3", "fob", "estructura", "medio"])
    d = pd.concat(partes, ignore_index=True)
    d["mes"] = calc.month_start(d["etd"])
    return d


def _fila(g: pd.DataFrame) -> dict:
    res = g[g["fuente"] == "Reservado"]
    pla = g[g["fuente"] == "Por reservar"]
    m3 = float(g["m3"].sum())
    est = g[g["estructura"].isin(["Monoproveedor", "Consolidado"])]
    m3_est = float(est["m3"].sum())
    cont_est = float(pla.loc[pla["medio"] == "Marítimo", "m3"].sum()) / settings.M3_POR_CONTENEDOR
    row = {
        "embarques": int(res.loc[res["medio"] != "Aéreo", "id"].nunique()),
        "aereos": int(res.loc[res["medio"] == "Aéreo", "id"].nunique()),
        "so_por_reservar": int(pla["id"].nunique()),
        "contenedores": float(res["contenedores"].sum()), "contenedores_est": float(np.ceil(cont_est)),
        "m3": m3, "fob": float(g["fob"].sum()),
        "pct_mono": float(est.loc[est["estructura"] == "Monoproveedor", "m3"].sum() / m3_est) if m3_est else np.nan,
        "pct_cons": float(est.loc[est["estructura"] == "Consolidado", "m3"].sum() / m3_est) if m3_est else np.nan,
    }
    row["contenedores_total"] = row["contenedores"] + row["contenedores_est"]
    for md in MEDIOS:
        row[f"pct_{md}"] = float(g.loc[g["medio"] == md, "m3"].sum() / m3) if m3 else np.nan
    return row


def mensual(d: pd.DataFrame, today: pd.Timestamp, meses: int = 6) -> pd.DataFrame:
    """Una fila por mes, del actual a `meses` − 1 meses adelante, + fila de total (mes NaT).
    Lo que tiene ETD más allá queda afuera (attrs["mas_adelante"] = cantidad de registros)."""
    if d.empty:
        return pd.DataFrame()
    desde = today.to_period("M").to_timestamp()
    hasta = desde + pd.DateOffset(months=meses)
    x = d[(d["mes"] >= desde) & (d["mes"] < hasta)]
    if x.empty:
        return pd.DataFrame()
    rows = [{"mes": m, **_fila(g)} for m, g in x.groupby("mes")]
    rows.append({"mes": pd.NaT, **_fila(x)})
    out = pd.DataFrame(rows)
    out.attrs["mas_adelante"] = int((d["mes"] >= hasta).sum())
    return out
