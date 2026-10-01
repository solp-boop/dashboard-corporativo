"""Cálculos de fletes: mercado, comparación pagado vs mercado y recomendación de forwarder.

Sin Streamlit, para poder testearlo.
"""
from __future__ import annotations

from dataclasses import dataclass

import numpy as np
import pandas as pd

from config import settings
from utils import calculations as calc


# ---------------------------------------------------------------------------
# Mercado
# ---------------------------------------------------------------------------
def vigentes(cot: pd.DataFrame, fecha: pd.Timestamp, tipo: str | None = None,
             puerto: str | None = None) -> pd.DataFrame:
    d = cot[(cot["validez_desde"] <= fecha) & (cot["validez_hasta"] >= fecha)]
    if tipo:
        d = d[d["tipo_ctnr"] == tipo]
    if puerto:
        d = d[d["puerto"] == puerto]
    return d


def best_by_forwarder(d: pd.DataFrame, value: str = "flete") -> pd.DataFrame:
    """La opción más barata de cada forwarder (una fila por forwarder)."""
    if d.empty:
        return d
    idx = d.dropna(subset=[value]).groupby("forwarder")[value].idxmin()
    return d.loc[idx].sort_values(value)


def market(d: pd.DataFrame) -> tuple[float, float, str]:
    """(promedio de mercado, mejor tarifa, forwarder de la mejor tarifa).

    El promedio se calcula sobre la mejor tarifa de cada forwarder, para que un
    agente con muchas líneas cotizadas no pese más que otro.
    """
    if d.empty:
        return np.nan, np.nan, ""
    best = best_by_forwarder(d)
    return float(best["flete"].mean()), float(best["flete"].iloc[0]), str(best["forwarder"].iloc[0])


def market_by_month(cot: pd.DataFrame) -> pd.DataFrame:
    """Promedio de mercado y mejor oferta por mes (inicio de validez) y tipo de contenedor."""
    d = cot.dropna(subset=["validez_desde", "tipo_ctnr"]).copy()
    if d.empty:
        return pd.DataFrame(columns=["mes", "tipo_ctnr", "mercado", "mejor", "n_ffww"])
    d["mes"] = calc.month_start(d["validez_desde"])
    rows = []
    for (mes, tipo), g in d.groupby(["mes", "tipo_ctnr"]):
        p, b, _ = market(g)
        rows.append({"mes": mes, "tipo_ctnr": tipo, "mercado": p, "mejor": b, "n_ffww": g["forwarder"].nunique()})
    return pd.DataFrame(rows)


def add_market_reference(hist: pd.DataFrame, cot: pd.DataFrame | None) -> pd.DataFrame:
    """Agrega al histórico el promedio de mercado del mes de ETD y la diferencia pagado vs mercado."""
    out = hist.copy()
    out["mercado_mes"] = np.nan
    out["vs_mercado"] = np.nan
    if cot is None or cot.empty or out.empty:
        return out
    # El mercado se calcula por destino (las tarifas a México no se comparan con Argentina).
    refs = {}
    for dest in out["destino"].dropna().unique() if "destino" in out else []:
        sub = cot[cot["destino"] == dest] if "destino" in cot else cot
        refs[dest] = market_by_month(sub).set_index(["mes", "tipo_ctnr"])["mercado"]
    meses = calc.month_start(out["etd"])
    vals = []
    for mes, tipo, dest in zip(meses, out["tipo_ctnr"], out.get("destino", pd.Series(index=out.index))):
        mk = refs.get(dest)
        vals.append(mk.get((mes, tipo), np.nan) if (mk is not None and tipo) else np.nan)
    out["mercado_mes"] = vals
    out["vs_mercado"] = (out["flete_por_ctnr"] - out["mercado_mes"]) / out["mercado_mes"]
    return out


# ---------------------------------------------------------------------------
# Desempeño histórico de cada forwarder
# ---------------------------------------------------------------------------
def service_by_forwarder(hist: pd.DataFrame, months: int = 12,
                         today: pd.Timestamp | None = None) -> pd.DataFrame:
    """Métricas de servicio de los últimos `months` meses (embarques marítimos zarpados)."""
    today = today or pd.Timestamp.today().normalize()
    d = hist[(hist["etd"] <= today) & (hist["etd"] >= today - pd.DateOffset(months=months))]
    rows = []
    for ffww, g in d.groupby("forwarder"):
        dev = g["desvio_etd"].dropna()
        cons_ok, n_cons = calc.cumplimiento(g["dias_consolidacion"], g["sla_consolidacion"])
        val = g["resultado_validacion"].dropna() if "resultado_validacion" in g else pd.Series(dtype=object)
        rows.append({
            "forwarder": ffww,
            "embarques_12m": len(g),
            "instr_etd": g["dias_agente"].median(),
            "etd_en_fecha": (dev.abs() <= settings.ETD_TOLERANCIA_DIAS).mean() if len(dev) else np.nan,
            "n_etd": len(dev),
            "cumple_sla": cons_ok if n_cons else np.nan,
            "observados": (val == "Observado").mean() if len(val) else np.nan,
        })
    return pd.DataFrame(rows)


# ---------------------------------------------------------------------------
# Recomendación
# ---------------------------------------------------------------------------
PRIORIDADES = {
    "Precio": 0.85,
    "Equilibrado": 0.70,
    "Servicio": 0.50,
}


@dataclass
class Recomendacion:
    opciones: pd.DataFrame      # ranking completo
    mercado: float              # promedio de mercado (costo total)
    fecha: pd.Timestamp


def recommend(cot: pd.DataFrame, hist: pd.DataFrame | None, fecha: pd.Timestamp, tipo: str,
              puerto: str | None = None, peso_precio: float = 0.70) -> Recomendacion:
    """Ordena los forwarders con tarifa vigente por un puntaje de precio + servicio.

    - Costo total por contenedor = flete + gastos locales ARG de la cotización.
      Si la cotización no trae locales, se usa la mediana de locales vigentes
      (y se marca como estimado).
    - Precio: 1 para la opción más barata; las demás, en proporción (mejor / costo).
    - Servicio (historial 12 meses): % de ETD cumplido (±3 días) y rapidez de
      instrucción → ETD. Sin historial suficiente se usa un valor neutro (0,5).
    """
    vig = vigentes(cot, fecha, tipo, puerto).copy()
    if vig.empty:
        return Recomendacion(pd.DataFrame(), np.nan, fecha)

    loc_med = vig.loc[vig["locales_arg"] > 0, "locales_arg"].median()
    vig["locales_estimados"] = ~(vig["locales_arg"] > 0)
    vig["locales_calc"] = vig["locales_arg"].where(vig["locales_arg"] > 0, loc_med)
    vig["costo_total"] = vig["flete"] + vig["locales_calc"].fillna(0)
    best = best_by_forwarder(vig, "costo_total").copy()

    svc = service_by_forwarder(hist) if hist is not None and not hist.empty else pd.DataFrame(
        columns=["forwarder", "embarques_12m", "instr_etd", "etd_en_fecha", "n_etd", "cumple_sla", "observados"])
    best = best.merge(svc, on="forwarder", how="left")
    best["embarques_12m"] = best["embarques_12m"].fillna(0).astype(int)

    best["score_precio"] = best["costo_total"].min() / best["costo_total"]
    enough = best["embarques_12m"] >= settings.MIN_SAMPLE
    rap = best["instr_etd"].min() / best["instr_etd"]
    svc_score = 0.6 * best["etd_en_fecha"] + 0.4 * rap
    best["score_servicio"] = svc_score.where(enough & svc_score.notna(), 0.5)
    best["historial"] = np.where(enough, "Con historial", "Sin historial suficiente")
    best["puntaje"] = peso_precio * best["score_precio"] + (1 - peso_precio) * best["score_servicio"]
    best = best.sort_values(["puntaje", "costo_total"], ascending=[False, True]).reset_index(drop=True)
    best.insert(0, "ranking", range(1, len(best) + 1))
    prom = float(best["costo_total"].mean())
    best["vs_promedio"] = (best["costo_total"] - prom) / prom
    return Recomendacion(best, prom, fecha)


# ---------------------------------------------------------------------------
# Gestión: rebaja negociada y ahorro contra el mercado
# ---------------------------------------------------------------------------
NEG_KEYS = ["forwarder", "agente", "puerto", "linea", "tipo_ctnr", "validez_desde", "validez_hasta"]


def negotiation(cot: pd.DataFrame | None, sin: pd.DataFrame | None) -> pd.DataFrame:
    """Une cada tarifa negociada con su tarifa original (sin negociar).

    Devuelve una fila por tarifa con: flete_original, flete_negociado, rebaja (USD) y rebaja_pct.
    """
    cols = NEG_KEYS + ["flete"]
    if cot is None or sin is None or cot.empty or sin.empty:
        return pd.DataFrame(columns=NEG_KEYS + ["flete_original", "flete_negociado", "rebaja", "rebaja_pct"])
    a = sin[cols].rename(columns={"flete": "flete_original"})
    b = cot[cols + (["destino"] if "destino" in cot else [])].rename(columns={"flete": "flete_negociado"})
    m = a.merge(b, on=NEG_KEYS, how="inner").drop_duplicates(NEG_KEYS)
    m["rebaja"] = m["flete_original"] - m["flete_negociado"]
    m["rebaja_pct"] = m["rebaja"] / m["flete_original"]
    return m


def savings_vs_market(hist: pd.DataFrame) -> pd.Series:
    """USD ahorrados contra el promedio de mercado del mes, por embarque (negativo = pagamos más)."""
    return (hist["mercado_mes"] - hist["flete_por_ctnr"]) * hist["contenedores"]


def nor_savings(hist: pd.DataFrame) -> pd.DataFrame:
    """Ahorro por usar 40 NOR en lugar de 40 ST/40 HQ.

    Para cada embarque en 40 NOR: (mediana del flete por contenedor pagado en
    40 ST/40 HQ ese mismo mes − flete por contenedor pagado en 40 NOR) × contenedores.
    También se calcula por m³, porque el 40 NOR carga un poco menos: se usa la
    capacidad de cada tipo (columna "Capacidad contenedor").
    """
    d = hist[(hist["flete_por_ctnr"] > 0) & hist["etd"].notna()].copy()
    d["mes"] = calc.month_start(d["etd"])
    hq = d[d["tipo_ctnr"] == "40ST/40HQ"]
    nor = d[d["tipo_ctnr"] == "40NOR"].copy()
    if nor.empty:
        return nor.assign(ref_hq=np.nan, ahorro=np.nan, ahorro_m3=np.nan)
    ref = hq.groupby("mes")["flete_por_ctnr"].median()
    cap_hq = hq["capacidad"].median() if "capacidad" in hq and hq["capacidad"].notna().any() else np.nan
    cap_nor = nor["capacidad"].median() if "capacidad" in nor and nor["capacidad"].notna().any() else np.nan
    nor["ref_hq"] = nor["mes"].map(ref)
    nor["ahorro"] = (nor["ref_hq"] - nor["flete_por_ctnr"]) * nor["contenedores"]
    if cap_hq == cap_hq and cap_nor == cap_nor and cap_hq and cap_nor:
        nor["ahorro_m3"] = (nor["ref_hq"] / cap_hq - nor["flete_por_ctnr"] / cap_nor) * nor["m3"]
    else:
        nor["ahorro_m3"] = np.nan
    nor.attrs.update(cap_hq=cap_hq, cap_nor=cap_nor)
    return nor
