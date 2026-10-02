"""Indicadores del Resumen: transit time, ocupación de contenedores, 20 ST y cargas IMO / DG.

Sin Streamlit, para poder testearlo. Tiempos por mediana; siempre se devuelve n.
"""
from __future__ import annotations

from dataclasses import dataclass, field

import numpy as np
import pandas as pd

from config import settings
from utils.data_cleaning import fold

TIPOS_CTNR = ["20 ST", "40 ST", "40 HQ", "40 NOR"]


# ---------------------------------------------------------------------------
# Transit time
# ---------------------------------------------------------------------------
@dataclass
class TT:
    n: int = 0
    mediana: float = np.nan
    p90: float = np.nan
    n_sobre: int = 0
    umbral: float = np.nan
    # comparación: último trimestre cerrado vs el anterior
    q_act: str = ""
    q_prev: str = ""
    med_act: float = np.nan
    med_prev: float = np.nan
    n_act: int = 0
    n_prev: int = 0

    @property
    def pct_sobre(self) -> float:
        return self.n_sobre / self.n if self.n else np.nan

    @property
    def enough(self) -> bool:
        return self.n >= settings.MIN_SAMPLE

    @property
    def comparable(self) -> bool:
        return self.n_act >= settings.MIN_SAMPLE and self.n_prev >= settings.MIN_SAMPLE


def _q(ts: pd.Timestamp) -> str:
    return f"Q{(ts.month - 1) // 3 + 1} {ts.year}"


def transit_time(d: pd.DataFrame, col: str, umbral: float, today: pd.Timestamp) -> TT:
    """Mediana, P90 y casos sobre el umbral; más el último trimestre cerrado vs el anterior."""
    x = d.dropna(subset=[col, "etd"])
    v = x[col]
    out = TT(n=int(v.size), umbral=umbral)
    if v.empty:
        return out
    out.mediana, out.p90 = float(v.median()), float(v.quantile(0.9))
    out.n_sobre = int((v > umbral).sum())
    this_q = today.to_period("Q").to_timestamp()
    q_act = this_q - pd.offsets.QuarterBegin(1, startingMonth=1)
    q_prev = q_act - pd.offsets.QuarterBegin(1, startingMonth=1)
    qx = x["etd"].dt.to_period("Q").dt.to_timestamp()
    a, p = x.loc[qx == q_act, col], x.loc[qx == q_prev, col]
    out.q_act, out.q_prev = _q(q_act), _q(q_prev)
    out.n_act, out.n_prev = int(a.size), int(p.size)
    out.med_act = float(a.median()) if len(a) else np.nan
    out.med_prev = float(p.median()) if len(p) else np.nan
    return out


# ---------------------------------------------------------------------------
# Ocupación de contenedores
# ---------------------------------------------------------------------------
def tipo_ctnr(tipo_carga) -> str | None:
    f = fold(tipo_carga).upper().replace(" ", "") if tipo_carga is not None else ""
    return {"20ST": "20 ST", "20GP": "20 ST", "40ST": "40 ST", "40GP": "40 ST", "40HQ": "40 HQ",
            "40HC": "40 HQ", "40NOR": "40 NOR"}.get(f)


def ocupacion(z: pd.DataFrame) -> pd.DataFrame:
    """Una fila por embarque FCL: tipo, contenedores, capacidad y ocupación (m³ / capacidad total)."""
    d = z.copy()
    d["tipo"] = d["tipo_carga"].map(tipo_ctnr)
    d = d[d["tipo"].notna() & (d["contenedores"] > 0) & (d["m3"] > 0)]
    cap_col = d["capacidad"] if "capacidad" in d else pd.Series(np.nan, index=d.index)
    d["cap"] = cap_col.where(cap_col > 0, d["tipo"].map(settings.CAPACIDAD_CTNR))
    d = d[d["cap"] > 0]
    d["ocupacion"] = d["m3"] / (d["contenedores"] * d["cap"])
    d["bajo"] = d["ocupacion"] < settings.OCUPACION_UMBRAL
    return d


def _wmedian(values: pd.Series, weights: pd.Series) -> float:
    """Mediana ponderada (cada contenedor del embarque cuenta con la ocupación del embarque)."""
    if values.empty:
        return np.nan
    o = np.argsort(values.values)
    v, w = values.values[o], weights.values[o]
    c = np.cumsum(w)
    return float(v[np.searchsorted(c, c[-1] / 2)])


def ocupacion_resumen(occ: pd.DataFrame) -> pd.DataFrame:
    """Por tipo + total: contenedores, mediana de ocupación, bajo / sobre el umbral."""
    rows = []
    for tipo in TIPOS_CTNR + ["Total"]:
        g = occ if tipo == "Total" else occ[occ["tipo"] == tipo]
        if g.empty:
            continue
        cnt = float(g["contenedores"].sum())
        bajo = float(g.loc[g["bajo"], "contenedores"].sum())
        rows.append({"tipo": tipo, "contenedores": cnt, "embarques": len(g),
                     "mediana": _wmedian(g["ocupacion"], g["contenedores"]),
                     "cap": float(g["cap"].median()),
                     "bajo": bajo, "ok": cnt - bajo, "pct_ok": (cnt - bajo) / cnt if cnt else np.nan})
    return pd.DataFrame(rows)


@dataclass
class Uso20:
    total: float = 0                 # contenedores 20 ST
    bajos: float = 0                 # con ocupación < umbral
    con_dato: float = 0              # de los bajos, con prioridad / motivo cargado
    justificados: float = 0
    tiene_campo: bool = False
    detalle: pd.DataFrame = field(default_factory=pd.DataFrame)

    @property
    def pct_justificados(self) -> float:
        return self.justificados / self.bajos if self.tiene_campo and self.bajos and self.con_dato else np.nan


def uso_20st(occ: pd.DataFrame) -> Uso20:
    v = occ[occ["tipo"] == "20 ST"]
    out = Uso20(total=float(v["contenedores"].sum()), bajos=float(v.loc[v["bajo"], "contenedores"].sum()))
    bajos = v[v["bajo"]]
    out.detalle = bajos
    if "prioridad_carga" in v and v["prioridad_carga"].notna().any():
        out.tiene_campo = True
        pr = bajos["prioridad_carga"]
        out.con_dato = float(bajos.loc[pr.notna(), "contenedores"].sum())
        just = pr.map(lambda x: fold(x) in settings.PRIORIDAD_JUSTIFICA if isinstance(x, str) else False)
        out.justificados = float(bajos.loc[just, "contenedores"].sum())
    return out


# ---------------------------------------------------------------------------
# Cargas especiales
# ---------------------------------------------------------------------------
@dataclass
class Especial:
    n: int = 0                       # operaciones especiales (IMO / DG)
    total: int = 0                   # operaciones del modo
    costo: float = np.nan            # mediana de la métrica de costo de las especiales
    n_costo: int = 0
    extra: float = np.nan            # mediana de (especial − referencia comparable)
    extra_pct: float = np.nan
    n_pares: int = 0                 # especiales con referencia comparable
    tt: float = np.nan
    tt_ref: float = np.nan
    n_tt: int = 0
    n_tt_ref: int = 0

    @property
    def pct(self) -> float:
        return self.n / self.total if self.total else np.nan

    @property
    def tt_comparable(self) -> bool:
        return self.n_tt >= settings.MIN_SAMPLE and self.n_tt_ref >= settings.MIN_SAMPLE

    @property
    def costo_comparable(self) -> bool:
        return self.n_pares >= settings.MIN_SAMPLE


def _especial(d: pd.DataFrame, costo_col: str, grupo: list[str], tt_col: str) -> Especial:
    es = d["dg"].fillna(False).astype(bool)
    e, r = d[es], d[~es]
    out = Especial(n=int(es.sum()), total=len(d))
    c = e[costo_col].dropna()
    out.costo, out.n_costo = (float(c.median()) if len(c) else np.nan), int(c.size)
    # Referencia comparable: mediana de las no especiales del mismo grupo (tipo / mes / destino).
    ref = r.dropna(subset=[costo_col]).groupby(grupo)[costo_col].median().rename("ref")
    pares = e.dropna(subset=[costo_col]).join(ref, on=grupo).dropna(subset=["ref"])
    out.n_pares = len(pares)
    if len(pares):
        diff = pares[costo_col] - pares["ref"]
        out.extra = float(diff.median())
        out.extra_pct = float((diff / pares["ref"]).median())
    te, tr = e[tt_col].dropna(), r[tt_col].dropna()
    out.tt, out.n_tt = (float(te.median()) if len(te) else np.nan), int(te.size)
    out.tt_ref, out.n_tt_ref = (float(tr.median()) if len(tr) else np.nan), int(tr.size)
    return out


def imo_maritimo(z: pd.DataFrame) -> Especial:
    """IMO marítimo (columna DG de Reservas Históricas). Costo: flete por contenedor.

    Comparable: mismo tipo de contenedor, mismo mes de ETD y mismo destino.
    """
    d = z[z["dg"].notna()].copy()
    d["mes"] = d["etd"].dt.to_period("M").dt.to_timestamp()
    d["tipo"] = d["tipo_carga"].map(tipo_ctnr)
    d["flete_ctnr"] = d["flete_por_ctnr"].where(d["flete_por_ctnr"] > 0)
    return _especial(d, "flete_ctnr", ["tipo", "mes", "destino"], "dias_tt")


def dg_aereo(a: pd.DataFrame) -> Especial:
    """DG aéreo (columna CARGA IMO de Seguimiento Aéreos, solo «Aéreo»). Costo: USD por kg chargeable.

    Comparable: mismo mes de ETD y mismo origen.
    """
    d = a[(a["modo"] == "Aéreo") & a["dg"].notna()].copy()
    d["mes"] = d["etd"].dt.to_period("M").dt.to_timestamp()
    d["usd_kg"] = (d["flete_pagado"] / d["chargeable"]).where((d["flete_pagado"] > 0) & (d["chargeable"] > 0))
    return _especial(d, "usd_kg", ["mes", "puerto"], "dias_etd_eta")
