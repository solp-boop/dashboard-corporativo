"""Proyección: lo que está en Planificación de cargas, por mes de ETD o ETA.

La base es la solapa Planif cargas (una fila por línea de SO), así el volumen y el FOB coinciden con la planilla y
con Pipeline. FOB = «Fob total Origen».

- Reservado: SO cuyo embarque está en Reservas. Contenedores reales del embarque, repartidos entre sus líneas
  por m³ (la suma da el total del embarque).
- Embarcado: SO cuyo embarque ya está en Reservas Históricas (sigue en Planif).
- Por reservar: el resto. Contenedores estimados con settings.M3_POR_CONTENEDOR, solo si viaja en barco
  (misma regla que Pipeline).

Los meses anteriores al actual se agrupan en ANTERIOR, los posteriores a la ventana en MAS_ADELANTE y lo que no
tiene la fecha elegida en SIN_FECHA, para que el total sea siempre el de la planilla.
Mono / consolidado y medio se expresan en % del volumen (m³). Sin Streamlit, para poder testearlo.
"""
from __future__ import annotations

import numpy as np
import pandas as pd

from config import settings
from utils import calculations as calc
from utils import data_cleaning as dc
from utils.data_cleaning import id_key

ANTERIOR = pd.Timestamp("1900-01-01")
MAS_ADELANTE = pd.Timestamp("2100-01-01")
SIN_FECHA = pd.Timestamp("2200-01-01")
MEDIOS = ["Marítimo", "Otro"]


def es_maritimo(df: pd.DataFrame) -> pd.Series:
    """SO que viajan en barco según la modalidad de costeo (Barco… o Costo Híbrido Puerto ZFLP)."""
    if "modalidad" not in df:
        return pd.Series(True, index=df.index)
    mod = df["modalidad"].map(lambda v: dc.fold(v) if isinstance(v, str) and v else "")
    return mod.str.startswith("barco") | mod.str.contains("costo hibrido puerto zflp", regex=False)


def etiqueta(m: pd.Timestamp, today: pd.Timestamp, larga: bool = False) -> str:
    """Texto del mes: «Anterior», «Más adelante», «Sin fecha» o el mes (con * si es el actual)."""
    from utils import formatting as fmt
    especiales = {ANTERIOR: "Anterior", MAS_ADELANTE: "Más adelante", SIN_FECHA: "Sin fecha"}
    if m in especiales:
        return especiales[m]
    actual = m == today.to_period("M").to_timestamp()
    if larga:
        return fmt.fmt_month(m, long=True) + (" · en curso" if actual else "")
    return fmt.fmt_month(m) + ("*" if actual else "")


def _agrupar(fecha: pd.Series, today: pd.Timestamp, meses: int) -> pd.Series:
    mes = calc.month_start(fecha)
    desde = today.to_period("M").to_timestamp()
    hasta = desde + pd.DateOffset(months=meses)
    return mes.mask(mes < desde, ANTERIOR).mask(mes >= hasta, MAS_ADELANTE).fillna(SIN_FECHA)


def base(res: pd.DataFrame | None, planif: pd.DataFrame | None, hist: pd.DataFrame | None) -> pd.DataFrame:
    """Una fila por línea de Planif: fuente, SO, embarque, etd, eta, contenedores, m³, FOB, estructura y medio."""
    cols = ["fuente", "id", "embarque", "etd", "eta", "contenedores", "m3", "fob", "estructura", "medio"]
    if planif is None or planif.empty:
        return pd.DataFrame(columns=cols)
    p = planif
    k = id_key(p["embarque"].fillna(""))
    cnt, est_res = {}, {}
    if res is not None and len(res):
        r = res.assign(_k=id_key(res["embarque"]))
        cnt = dict(zip(r["_k"], r["contenedores"].fillna(0)))
        est_res = dict(zip(r["_k"], r["estructura"]))
    en_hist = set(id_key(hist["embarque"])) if hist is not None and len(hist) else set()
    reservado = (p["embarque"].notna() & k.isin(cnt.keys())).to_numpy()
    embarcado = (p["embarque"].notna() & k.isin(en_hist)).to_numpy() & ~reservado
    mar = es_maritimo(p).to_numpy()
    m3 = p["m3"].fillna(0).clip(lower=0)
    fob = p["fob"] if "fob" in p else p.get("fob_origen", pd.Series(0.0, index=p.index))
    d = pd.DataFrame({
        "fuente": np.select([reservado, embarcado], ["Reservado", "Embarcado"], "Por reservar"),
        "id": p["so"].astype(str).to_numpy(), "embarque": p["embarque"].to_numpy(), "_k": k.to_numpy(),
        "etd": p["etd"].to_numpy(), "eta": p["eta"].to_numpy() if "eta" in p else pd.NaT,
        "m3": m3.to_numpy(), "fob": pd.to_numeric(fob, errors="coerce").fillna(0).to_numpy(),
        "estructura": p["estructura"].to_numpy(), "medio": np.where(mar, "Marítimo", "Otro"),
    })
    # Estructura: si Planif no la tiene, la del embarque en Reservas.
    d["estructura"] = d["estructura"].where(d["estructura"].notna(), d["_k"].map(est_res))
    # Contenedores reales del embarque, repartidos por m³ entre sus líneas.
    rv = d["fuente"] == "Reservado"
    tot = d[rv].groupby("_k")["m3"].transform("sum")
    n = d[rv].groupby("_k")["m3"].transform("size")
    share = (d.loc[rv, "m3"] / tot).where(tot > 0, 1 / n)
    d["contenedores"] = 0.0
    d.loc[rv, "contenedores"] = share * d.loc[rv, "_k"].map(cnt).astype(float)
    pr_ = (d["fuente"] == "Por reservar") & (d["medio"] == "Marítimo")
    d.loc[pr_, "contenedores"] = d.loc[pr_, "m3"] / settings.M3_POR_CONTENEDOR
    return d[cols]


def _fila(g: pd.DataFrame) -> dict:
    m3 = float(g["m3"].sum())
    est = g[g["estructura"].isin(["Monoproveedor", "Consolidado"])]
    m3_est = float(est["m3"].sum())
    rv = g[g["fuente"] == "Reservado"]
    row = {
        "so": int(g["id"].nunique()),
        "embarques": int(rv["embarque"].nunique()),
        "so_por_reservar": int(g.loc[g["fuente"] == "Por reservar", "id"].nunique()),
        "contenedores": float(rv["contenedores"].sum()),
        "contenedores_est": float(g.loc[g["fuente"] == "Por reservar", "contenedores"].sum()),
        "m3": m3, "fob": float(g["fob"].sum()),
        "pct_mono": float(est.loc[est["estructura"] == "Monoproveedor", "m3"].sum() / m3_est) if m3_est else np.nan,
        "pct_cons": float(est.loc[est["estructura"] == "Consolidado", "m3"].sum() / m3_est) if m3_est else np.nan,
    }
    row["contenedores_total"] = float(np.round(row["contenedores"] + row["contenedores_est"]))
    return row


def mensual(d: pd.DataFrame, today: pd.Timestamp, meses: int = 6, fecha: str = "etd") -> pd.DataFrame:
    """Una fila por mes de `fecha` (ETD o ETA), del actual a `meses` − 1 meses adelante, + ANTERIOR / MAS_ADELANTE /
    SIN_FECHA si hay, + total (mes NaT)."""
    if d.empty:
        return pd.DataFrame()
    x = d.assign(mes=_agrupar(d[fecha], today, meses))
    rows = [{"mes": m, **_fila(g)} for m, g in x.groupby("mes")]
    rows.append({"mes": pd.NaT, **_fila(x)})
    return pd.DataFrame(rows)


def por_estructura(d: pd.DataFrame, today: pd.Timestamp, meses: int = 6, fecha: str = "etd") -> pd.DataFrame:
    """Por mes de `fecha` y estructura (Monoproveedor / Consolidado / Sin dato): contenedores, m³ y FOB."""
    if d.empty:
        return pd.DataFrame(columns=["mes", "estructura", "contenedores", "m3", "fob"])
    x = d.assign(mes=_agrupar(d[fecha], today, meses))
    x["estructura"] = x["estructura"].where(x["estructura"].isin(["Monoproveedor", "Consolidado"]), "Sin dato")
    g = x.groupby(["mes", "estructura"]).agg(contenedores=("contenedores", "sum"), m3=("m3", "sum"),
                                             fob=("fob", "sum"))
    return g.reset_index()
