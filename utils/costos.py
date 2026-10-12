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


def flete_mes(h: pd.DataFrame, tipo: str, year: int) -> pd.DataFrame:
    """Mediana del flete por contenedor por mes de ETD del año, para un tipo de contenedor, con la variación contra
    el mes anterior y contra el mismo mes del año anterior. Última fila (mes NaT) = año completo."""
    cols = ["mes", "n", "mediana", "var_mes", "anio_ant", "var_anio"]
    d = h[(h["tipo_ctnr"] == tipo) & (h["flete_por_ctnr"] > 0) & h["etd"].notna()] if h is not None and len(h) \
        else pd.DataFrame(columns=["etd", "flete_por_ctnr"])
    if d.empty:
        return pd.DataFrame(columns=cols)
    d = d.assign(mes=d["etd"].dt.to_period("M").dt.to_timestamp())
    med = d.groupby("mes")["flete_por_ctnr"].median()
    n = d.groupby("mes")["flete_por_ctnr"].size()
    rows = []
    for m in sorted(x for x in med.index if x.year == year):
        prev = med.get(m - pd.DateOffset(months=1), np.nan)
        ya = med.get(m - pd.DateOffset(years=1), np.nan)
        v = med[m]
        rows.append({"mes": m, "n": int(n[m]), "mediana": float(v),
                     "var_mes": v / prev - 1 if prev == prev and prev else np.nan, "anio_ant": ya,
                     "var_anio": v / ya - 1 if ya == ya and ya else np.nan})
    este = d[d["mes"].dt.year == year]
    ant = d[(d["mes"].dt.year == year - 1) & (d["mes"].dt.month <= (este["mes"].dt.month.max() if len(este) else 12))]
    if len(este):
        a, b = float(este["flete_por_ctnr"].median()), float(ant["flete_por_ctnr"].median()) if len(ant) else np.nan
        rows.append({"mes": pd.NaT, "n": int(len(este)), "mediana": a, "var_mes": np.nan, "anio_ant": b,
                     "var_anio": a / b - 1 if b == b and b else np.nan})
    return pd.DataFrame(rows, columns=cols)


def mercado_mes(cot: pd.DataFrame | None, tipo: str, hasta: pd.Timestamp) -> pd.DataFrame:
    """Mediana de «Valor Flete» de «Cotizaciones Maritimos Negociado» por mes (de «Validez Quincena Desde»), para un
    tipo de contenedor, hasta el mes de `hasta` inclusive. Mismo criterio que el reporte de fletes de la gerencia:
    todas las cotizaciones (todos los puertos y agentes); en 40ST/40HQ también entran las que no tienen tipo cargado.
    Columnas: mes, n, mediana, var_mes (vs mes anterior) y anio_ant / var_anio (vs mismo mes del año anterior)."""
    cols = ["mes", "n", "mediana", "var_mes", "anio_ant", "var_anio"]
    if cot is None or cot.empty or "flete" not in cot:
        return pd.DataFrame(columns=cols)
    tipos = cot["tipo_ctnr"]
    sel = (tipos == tipo) | (tipos.isna() if tipo == "40ST/40HQ" else False)
    d = cot[sel & (cot["flete"] > 0) & cot["validez_desde"].notna()]
    if d.empty:
        return pd.DataFrame(columns=cols)
    mes = d["validez_desde"].dt.to_period("M").dt.to_timestamp()
    g = d.groupby(mes)["flete"]
    med, n = g.median(), g.size()
    tope = pd.Timestamp(hasta).to_period("M").to_timestamp()
    rows = []
    for m in sorted(x for x in med.index if x <= tope):
        v = float(med[m])
        prev = med.get(m - pd.DateOffset(months=1), np.nan)
        ya = med.get(m - pd.DateOffset(years=1), np.nan)
        rows.append({"mes": m, "n": int(n[m]), "mediana": v,
                     "var_mes": v / prev - 1 if prev == prev and prev else np.nan,
                     "anio_ant": ya, "var_anio": v / ya - 1 if ya == ya and ya else np.nan})
    return pd.DataFrame(rows, columns=cols)


def puente(prev: pd.DataFrame, cur: pd.DataFrame) -> dict:
    """Puente del flete marítimo pagado entre dos períodos: cuánto de la variación es volumen (más contenedores),
    mezcla (otro reparto entre 20 ST / 40 ST-HQ / 40 NOR) y precio (cada equipo más caro o más barato).

    Descomposición exacta de totales (por eso usa el flete promedio por contenedor de cada equipo, no la mediana):
      volumen = (Q1 − Q0) × P̄0 · mezcla = Σ (s1ᵢ − s0ᵢ) × Q1 × p0ᵢ · precio = Σ q1ᵢ × (p1ᵢ − p0ᵢ)
    Un equipo que no estaba en el período anterior entra entero en mezcla (a su precio actual)."""
    def agg(d):
        d = d[(d["flete_pagado"] > 0) & d["tipo_ctnr"].notna()]
        g = d.groupby("tipo_ctnr").agg(q=("contenedores", "sum"), v=("flete_pagado", "sum"))
        g["p"] = g["v"] / g["q"]
        return g
    a, b = agg(prev), agg(cur)
    if a.empty or b.empty:
        return {}
    q0, q1 = a["q"].sum(), b["q"].sum()
    v0, v1 = a["v"].sum(), b["v"].sum()
    p0 = v0 / q0
    tipos = a.index.union(b.index)
    s0 = (a["q"] / q0).reindex(tipos).fillna(0)
    s1 = (b["q"] / q1).reindex(tipos).fillna(0)
    pi0 = a["p"].reindex(tipos)
    pi1 = b["p"].reindex(tipos)
    pi0_f = pi0.fillna(pi1)                       # equipo nuevo: su precio actual
    vol = (q1 - q0) * p0
    mix = float(((s1 - s0) * q1 * pi0_f).sum()) + (q1 * (s0 * pi0_f).sum() - q1 * p0)
    precio = float((b["q"].reindex(tipos).fillna(0) * (pi1.fillna(pi0_f) - pi0_f)).sum())
    return {"base": v0, "volumen": vol, "mezcla": mix, "precio": precio, "final": v1,
            "q0": q0, "q1": q1, "residuo": v1 - (v0 + vol + mix + precio)}


def concepto_mes(h: pd.DataFrame, tipo: str, year: int, col: str = "flete_por_ctnr") -> pd.DataFrame:
    """flete_mes para otro concepto por contenedor (locales_por_ctnr, origen_por_ctnr)."""
    if h is None or h.empty or col not in h:
        return pd.DataFrame(columns=["mes", "n", "mediana", "var_mes", "anio_ant", "var_anio"])
    return flete_mes(h.assign(flete_por_ctnr=h[col]), tipo, year)


EQUIPOS = {"20ST": "20 ST", "40ST/40HQ": "40 ST / 40 HQ", "40NOR": "40 NOR"}


def equipos(h: pd.DataFrame) -> pd.DataFrame:
    """Por tipo de contenedor: contenedores, flete por contenedor, capacidad, ocupación y flete por m³ (cargado y de
    capacidad), todo por mediana. El costo por m³ cargado es el que compara equipos de distinto tamaño."""
    cols = ["equipo", "contenedores", "flete_ctnr", "capacidad", "ocupacion", "m3_cargado", "flete_m3", "flete_m3_cap",
            "n"]
    d = h[(h["flete_por_ctnr"] > 0) & h["tipo_ctnr"].notna() & (h["m3"] > 0) & (h["contenedores"] > 0)]
    if d.empty:
        return pd.DataFrame(columns=cols)
    cap = d["capacidad"].where(d["capacidad"] > 0) if "capacidad" in d else pd.Series(np.nan, index=d.index)
    d = d.assign(cap=cap, m3_ctnr=d["m3"] / d["contenedores"])
    d["ocup"] = d["m3_ctnr"] / d["cap"]
    d["f_m3"] = d["flete_por_ctnr"] / d["m3_ctnr"]
    d["f_m3_cap"] = d["flete_por_ctnr"] / d["cap"]
    g = d.groupby("tipo_ctnr").agg(contenedores=("contenedores", "sum"), flete_ctnr=("flete_por_ctnr", "median"),
                                   capacidad=("cap", "median"), ocupacion=("ocup", "median"),
                                   m3_cargado=("m3_ctnr", "median"), flete_m3=("f_m3", "median"),
                                   flete_m3_cap=("f_m3_cap", "median"), n=("embarque", "nunique")).reset_index()
    g["equipo"] = g["tipo_ctnr"].map(EQUIPOS).fillna(g["tipo_ctnr"])
    return g[cols].sort_values("contenedores", ascending=False).reset_index(drop=True)


def espacio_vacio(h: pd.DataFrame, umbral: float) -> dict:
    """Contenedores por debajo del umbral de ocupación y el flete pagado por el espacio que viajó vacío
    (flete × (1 − ocupación)). Es una cota: no toda carga se puede consolidar."""
    d = h[(h["flete_por_ctnr"] > 0) & (h["m3"] > 0) & (h["contenedores"] > 0)]
    cap = d["capacidad"].where(d["capacidad"] > 0) if "capacidad" in d else pd.Series(np.nan, index=d.index)
    d = d.assign(ocup=(d["m3"] / d["contenedores"]) / cap).dropna(subset=["ocup"])
    bajo = d[d["ocup"] < umbral]
    vacio = float((bajo["flete_pagado"] * (1 - bajo["ocup"].clip(upper=1))).sum())
    return {"n": int(len(d)), "bajos": int(len(bajo)), "cont_bajos": float(bajo["contenedores"].sum()),
            "pct": len(bajo) / len(d) if len(d) else np.nan, "usd_vacio": vacio, "casos": bajo}


def imo_sobrecosto(h: pd.DataFrame) -> dict:
    """Sobrecosto IMO comparable: misma ruta (puerto), equipo y mes; mediana IMO − mediana no IMO en cada celda donde
    hay de los dos, y la mediana de esas diferencias."""
    d = h[(h["flete_por_ctnr"] > 0) & h["tipo_ctnr"].notna()].copy()
    if "dg" not in d or d.empty:
        return {"n_celdas": 0}
    d["dg"] = d["dg"].fillna(False).astype(bool)
    d["mes"] = d["etd"].dt.to_period("M")
    g = d.groupby(["puerto", "tipo_ctnr", "mes", "dg"])["flete_por_ctnr"].median().unstack("dg")
    if True not in g or False not in g:
        return {"n_celdas": 0, "n_imo": int(d["dg"].sum())}
    g = g.dropna(subset=[True, False])
    dif = g[True] - g[False]
    return {"n_celdas": int(len(dif)), "n_imo": int(d["dg"].sum()), "dif_med": float(dif.median()) if len(dif) else np.nan,
            "pct_med": float((dif / g[False]).median()) if len(dif) else np.nan}
