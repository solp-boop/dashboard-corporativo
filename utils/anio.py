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


# ---------------------------------------------------------------------------
# Shippers: FOB colocado por mes de ETA
# ---------------------------------------------------------------------------
def shippers_base(hist: pd.DataFrame | None, res: pd.DataFrame | None, year: int) -> pd.DataFrame:
    """Una fila por embarque con ETA en el año: shipper, mes de ETA, FOB y fuente.

    Reservas Históricas → «Fob SIMI Total». Reservas (en curso) → «FOB Total Real»; si está vacío, se usa
    «Fob SIMI Total» y se marca. Si un embarque está en las dos, manda Históricas.
    """
    from utils.data_cleaning import fold, id_key
    partes = []
    if hist is not None and len(hist):
        h = hist[["embarque", "shipper", "eta", "fob_simi"]].rename(columns={"fob_simi": "fob"})
        partes.append(h.assign(fuente="Históricas", fob_simi_suplente=False))
    if res is not None and len(res):
        real = res["fob_real"] if "fob_real" in res else pd.Series(np.nan, index=res.index)
        usa_simi = ~(real > 0) & (res["fob_simi"] > 0)
        r = res[["embarque", "shipper", "eta"]].assign(fob=real.where(real > 0, res["fob_simi"]),
                                                        fuente="Reservas", fob_simi_suplente=usa_simi)
        partes.append(r)
    if not partes:
        return pd.DataFrame(columns=["embarque", "shipper", "eta", "fob", "fuente", "mes"])
    d = pd.concat(partes, ignore_index=True)
    d = d[d["eta"].notna() & (d["eta"].dt.year == year)].copy()
    d["_k"] = id_key(d["embarque"])
    d["_o"] = (d["fuente"] == "Reservas").astype(int)
    d = d.sort_values("_o").drop_duplicates("_k", keep="first")
    d["shipper"] = d["shipper"].map(lambda v: " ".join(str(v).split()) if isinstance(v, str) and v.strip() else "Sin shipper")
    # mismo shipper escrito distinto (mayúsculas / acentos / espacios): se agrupa y se muestra la forma más usada
    key = d["shipper"].map(lambda v: fold(v).upper())
    nombre = d.groupby(key)["shipper"].agg(lambda s: s.value_counts().index[0])
    d["shipper"] = key.map(nombre)
    d["mes"] = calc.month_start(d["eta"])
    d["fob"] = pd.to_numeric(d["fob"], errors="coerce").fillna(0.0)
    return d.drop(columns=["_k", "_o"])


def shippers_pivot(d: pd.DataFrame) -> tuple[pd.DataFrame, list]:
    """Shipper × mes de ETA (FOB), más total, % del año y fila de total. Devuelve (tabla, meses)."""
    meses = sorted(d["mes"].dropna().unique())
    p = d.pivot_table(index="shipper", columns="mes", values="fob", aggfunc="sum", fill_value=0.0).reindex(columns=meses)
    p["total"] = p.sum(axis=1)
    p["embarques"] = d.groupby("shipper")["embarque"].nunique()
    p = p.sort_values("total", ascending=False)
    tot = p.sum(numeric_only=True)
    tot["embarques"] = d["embarque"].nunique()
    gran = float(tot["total"])
    p["pct"] = p["total"] / gran if gran else np.nan
    tot["pct"] = 1.0 if gran else np.nan
    out = pd.concat([p, pd.DataFrame([tot], index=["Total"])])
    return out.reset_index(names="shipper"), meses
