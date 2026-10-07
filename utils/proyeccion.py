"""Proyección: lo que está en Reservas / Planificación y todavía no pasó a Históricas, por mes de ETD.

Fuentes, sin contar dos veces:
- Reservado: Reservas que no están en Históricas (marítimo, courier, camión; los AIR se toman de Seguimiento Aéreos).
- Aéreo: Seguimiento Aéreos activos.
- Por reservar: SO de Planificación cuyo embarque todavía no está en Reservas ni en Históricas.
  Sus contenedores se estiman con settings.M3_POR_CONTENEDOR (no hay contenedor asignado todavía).

Los meses anteriores al actual se agrupan en ANTERIOR (como en Pipeline) y los posteriores a la ventana en
MAS_ADELANTE, para que el total coincida con lo cargado.

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

ANTERIOR = pd.Timestamp("1900-01-01")
MAS_ADELANTE = pd.Timestamp("2100-01-01")


def etiqueta(m: pd.Timestamp, today: pd.Timestamp, larga: bool = False) -> str:
    """Texto del mes: «Anterior», «Más adelante» o el mes (con * si es el actual)."""
    from utils import formatting as fmt
    if m == ANTERIOR:
        return "Anterior"
    if m == MAS_ADELANTE:
        return "Más adelante"
    actual = m == today.to_period("M").to_timestamp()
    if larga:
        return fmt.fmt_month(m, long=True) + (" · en curso" if actual else "")
    return fmt.fmt_month(m) + ("*" if actual else "")


def _agrupar(mes: pd.Series, today: pd.Timestamp, meses: int) -> pd.Series:
    desde = today.to_period("M").to_timestamp()
    hasta = desde + pd.DateOffset(months=meses)
    return mes.mask(mes < desde, ANTERIOR).mask(mes >= hasta, MAS_ADELANTE)


def _fob(df: pd.DataFrame, *cols: str) -> pd.Series:
    out = pd.Series(np.nan, index=df.index, dtype=float)
    for c in cols:
        if c in df:
            out = out.fillna(pd.to_numeric(df[c], errors="coerce").where(lambda s: s > 0))
    return out.fillna(0.0)


def base(res: pd.DataFrame | None, planif: pd.DataFrame | None, aer: pd.DataFrame | None,
         hist: pd.DataFrame | None, today: pd.Timestamp) -> pd.DataFrame:
    """Una fila por embarque reservado / aéreo activo / SO por reservar, con mes, m³, FOB, estructura y medio.
    `today` se mantiene por compatibilidad: el corte por mes se hace en mensual / por_estructura."""
    partes = []
    ya = set()
    en_hist = set(id_key(hist["embarque"])) if hist is not None and len(hist) else set()
    if res is not None and len(res):
        r = res[res["etd"].notna() & ~id_key(res["embarque"]).isin(en_hist)]
        r = r[~r["embarque"].astype(str).str.strip().str.upper().str.startswith("AIR")]
        ya |= set(id_key(res["embarque"]))
        partes.append(pd.DataFrame({
            "fuente": "Reservado", "id": r["embarque"].astype(str), "etd": r["etd"],
            "contenedores": r["contenedores"].fillna(0), "m3": r["m3"].fillna(0), "fob": _fob(r, "fob_real", "fob_simi"),
            "estructura": r["estructura"], "medio": r["modo"].map(medio) if "modo" in r else "Marítimo",
        }))
    if aer is not None and len(aer):
        a = aer[(aer["activo"] if "activo" in aer else True) & aer["etd"].notna()]
        partes.append(pd.DataFrame({
            "fuente": "Reservado", "id": a["embarque"].astype(str), "etd": a["etd"], "contenedores": 0.0,
            "m3": a["m3"].fillna(0) if "m3" in a else 0.0, "fob": _fob(a, "fob_simi"), "estructura": None,
            "medio": "Aéreo",
        }))
    ya |= en_hist
    if planif is not None and len(planif):
        p = planif[planif["etd"].notna()]
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
        "contenedores": float(res["contenedores"].sum()), "contenedores_est": float(np.round(cont_est)),
        "m3": m3, "fob": float(g["fob"].sum()),
        "pct_mono": float(est.loc[est["estructura"] == "Monoproveedor", "m3"].sum() / m3_est) if m3_est else np.nan,
        "pct_cons": float(est.loc[est["estructura"] == "Consolidado", "m3"].sum() / m3_est) if m3_est else np.nan,
    }
    row["contenedores_total"] = row["contenedores"] + row["contenedores_est"]
    for md in MEDIOS:
        row[f"pct_{md}"] = float(g.loc[g["medio"] == md, "m3"].sum() / m3) if m3 else np.nan
    return row


def mensual(d: pd.DataFrame, today: pd.Timestamp, meses: int = 6) -> pd.DataFrame:
    """Una fila por mes, del actual a `meses` − 1 meses adelante, + ANTERIOR / MAS_ADELANTE si hay, + total (NaT)."""
    if d.empty:
        return pd.DataFrame()
    x = d.assign(mes=_agrupar(d["mes"], today, meses))
    rows = [{"mes": m, **_fila(g)} for m, g in x.groupby("mes")]
    rows.append({"mes": pd.NaT, **_fila(x)})
    return pd.DataFrame(rows)


def por_estructura(d: pd.DataFrame, today: pd.Timestamp, meses: int = 6) -> pd.DataFrame:
    """Por mes de ETD y estructura (Monoproveedor / Consolidado / Sin dato): contenedores, m³ y FOB.

    Contenedores: los reales de lo reservado; lo que no tiene reserva (marítimo) se estima con M3_POR_CONTENEDOR."""
    if d.empty:
        return pd.DataFrame(columns=["mes", "estructura", "contenedores", "m3", "fob"])
    x = d.assign(mes=_agrupar(d["mes"], today, meses))
    est = np.where((x["fuente"] == "Por reservar") & (x["medio"] == "Marítimo"),
                   x["m3"] / settings.M3_POR_CONTENEDOR, x["contenedores"].fillna(0))
    x["cont"] = est
    x["estructura"] = x["estructura"].where(x["estructura"].isin(["Monoproveedor", "Consolidado"]), "Sin dato")
    g = x.groupby(["mes", "estructura"]).agg(contenedores=("cont", "sum"), m3=("m3", "sum"), fob=("fob", "sum"))
    return g.reset_index()
