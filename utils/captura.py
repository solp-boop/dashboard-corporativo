"""Captura: lo que la gestión ahorró con una decisión, por fuente.

- Negociación de tarifas: a cada embarque marítimo se le asigna la tarifa con la que salió (mismo forwarder,
  puerto, tipo de contenedor y destino, vigente a la fecha de ETD (zarpe), con el flete
  negociado más parecido a lo pagado, y pagando menos que la tarifa original). Captura = (tarifa sin negociar − tarifa negociada) × contenedores. Si ninguna tarifa
  vigente se parece a lo pagado (± TOLERANCIA), el embarque no suma: no hay evidencia de que haya salido con ella.
- 40 NOR: (mediana pagada por un 40 ST/HQ ese mes − flete pagado por el 40 NOR) × contenedores (utils.freight).

Sin Streamlit, para poder testearlo.
"""
from __future__ import annotations

import numpy as np
import pandas as pd

from utils import calculations as calc
from utils.data_cleaning import fold

TOLERANCIA = 0.15      # el flete pagado tiene que estar a ± 15 % del negociado para asignar la tarifa

COLS = ["embarque", "etd", "mes", "forwarder", "puerto", "tipo_ctnr", "contenedores", "flete_por_ctnr",
        "flete_original", "flete_negociado", "rebaja", "captura"]


def por_negociacion(hist: pd.DataFrame, neg: pd.DataFrame) -> pd.DataFrame:
    """Una fila por embarque con tarifa negociada asignada. neg = freight.negotiation(cot, sin)."""
    if hist is None or hist.empty or neg is None or neg.empty:
        return pd.DataFrame(columns=COLS)
    h = hist[(hist["flete_por_ctnr"] > 0) & hist["tipo_ctnr"].notna() & hist["forwarder"].notna()].copy()
    if h.empty:
        return pd.DataFrame(columns=COLS)
    h["_fecha"] = h["etd"]   # la tarifa que aplica es la vigente al zarpe
    h["_f"], h["_p"] = h["forwarder"].map(fold), h["puerto"].map(fold)
    n = neg[neg["rebaja"].notna()].copy()
    n["_f"], n["_p"] = n["forwarder"].map(fold), n["puerto"].map(fold)
    extra = ["destino"] if "destino" in n else []
    m = h.reset_index().merge(n[["_f", "_p", "tipo_ctnr", "validez_desde", "validez_hasta", "flete_original",
                                 "flete_negociado", "rebaja"] + extra].rename(columns={"destino": "_dest_tarifa"}),
                              on=["_f", "_p", "tipo_ctnr"], how="inner")
    m = m[(m["_fecha"] >= m["validez_desde"]) & (m["_fecha"] <= m["validez_hasta"])]
    if extra and "destino" in m:
        # misma ruta: la tarifa tiene que ser del mismo destino (sin destino cargado, no se descarta)
        m = m[m["_dest_tarifa"].isna() | m["destino"].isna()
              | (m["_dest_tarifa"].map(fold) == m["destino"].map(fold))]
    if m.empty:
        return pd.DataFrame(columns=COLS)
    # Evidencia de que salió con la tarifa negociada: pagó menos que la original, está más cerca de la
    # negociada que de la original y a ± TOLERANCIA de lo pagado.
    m["_dif"] = (m["flete_por_ctnr"] - m["flete_negociado"]).abs() / m["flete_por_ctnr"]
    m = m[(m["_dif"] <= TOLERANCIA) & (m["flete_por_ctnr"] < m["flete_original"])
          & ((m["flete_por_ctnr"] - m["flete_negociado"]).abs() < (m["flete_por_ctnr"] - m["flete_original"]).abs())]
    m = m.sort_values("_dif").drop_duplicates("index")
    m["rebaja"] = m["rebaja"].clip(lower=0)
    m["captura"] = m["rebaja"] * m["contenedores"].fillna(1)
    m["mes"] = calc.month_start(m["etd"])
    return m[COLS].sort_values("etd", ascending=False).reset_index(drop=True)


def mensual(neg_casos: pd.DataFrame, nor: pd.DataFrame) -> pd.DataFrame:
    """Captura por mes de ETD y fuente: columnas mes, negociacion, nor, total, acumulado."""
    partes = []
    if neg_casos is not None and len(neg_casos):
        partes.append(neg_casos.groupby("mes")["captura"].sum().rename("negociacion"))
    if nor is not None and len(nor):
        partes.append(nor.groupby("mes")["ahorro"].sum().rename("nor"))
    if not partes:
        return pd.DataFrame(columns=["mes", "negociacion", "nor", "total", "acumulado"])
    g = pd.concat(partes, axis=1).fillna(0.0).sort_index()
    for c in ("negociacion", "nor"):
        if c not in g:
            g[c] = 0.0
    g["total"] = g["negociacion"] + g["nor"]
    g["acumulado"] = g["total"].cumsum()
    return g.reset_index().rename(columns={"index": "mes"})


def oportunidades(hist: pd.DataFrame) -> pd.DataFrame:
    """Dónde pagamos más que el mercado: forwarder × puerto × tipo de contenedor.

    hist con mercado_mes (freight.add_market_reference). USD en juego = Σ (pagado − mercado) × contenedores de
    los embarques que pagaron por encima de la mediana de mercado de su mes.
    """
    cols = ["forwarder", "puerto", "tipo_ctnr", "embarques", "contenedores", "pagado", "mercado", "dif_pct",
            "en_juego"]
    if hist is None or hist.empty or "mercado_mes" not in hist:
        return pd.DataFrame(columns=cols)
    d = hist[hist["mercado_mes"].notna() & (hist["flete_por_ctnr"] > 0)].copy()
    if d.empty:
        return pd.DataFrame(columns=cols)
    d["_exceso"] = ((d["flete_por_ctnr"] - d["mercado_mes"]).clip(lower=0) * d["contenedores"].fillna(1))
    g = d.groupby(["forwarder", "puerto", "tipo_ctnr"]).agg(
        embarques=("embarque", "count"), contenedores=("contenedores", "sum"),
        pagado=("flete_por_ctnr", "median"), mercado=("mercado_mes", "median"), en_juego=("_exceso", "sum"),
    ).reset_index()
    g["dif_pct"] = (g["pagado"] - g["mercado"]) / g["mercado"]
    g = g[(g["en_juego"] > 0) & (g["dif_pct"] > 0)]
    return g.sort_values("en_juego", ascending=False)[cols].reset_index(drop=True)


def rebaja_por_forwarder(neg: pd.DataFrame) -> pd.DataFrame:
    if neg is None or neg.empty:
        return pd.DataFrame(columns=["forwarder", "tarifas", "rebaja_usd", "rebaja_pct"])
    n = neg[neg["rebaja"].notna()]
    g = n.groupby("forwarder").agg(tarifas=("rebaja", "size"), rebaja_usd=("rebaja", "median"),
                                   rebaja_pct=("rebaja_pct", "median")).reset_index()
    return g.sort_values("tarifas", ascending=False)


def resumen(neg_casos: pd.DataFrame, nor: pd.DataFrame) -> dict:
    neg_v = float(neg_casos["captura"].sum()) if neg_casos is not None and len(neg_casos) else 0.0
    nor_v = float(nor["ahorro"].sum()) if nor is not None and len(nor) else 0.0
    return {"total": neg_v + nor_v, "negociacion": neg_v, "nor": nor_v,
            "neg_emb": int(len(neg_casos)) if neg_casos is not None else 0,
            "nor_cont": float(nor["contenedores"].sum()) if nor is not None and len(nor) else 0.0,
            "neg_cont": float(neg_casos["contenedores"].sum()) if neg_casos is not None and len(neg_casos) else np.nan}


def por_agente(hist: pd.DataFrame, neg_casos: pd.DataFrame, nor: pd.DataFrame) -> pd.DataFrame:
    """Una fila por agente: embarques marítimos con flete, cuántos tienen la tarifa identificada (cobertura),
    contenedores, captura por negociación, por 40 NOR y total; % de la negociación sobre la tarifa original."""
    cols = ["agente", "embarques", "con_tarifa", "cobertura", "contenedores", "negociacion", "nor", "total", "pct"]
    if hist is None or hist.empty:
        return pd.DataFrame(columns=cols)
    ag = lambda s: s.fillna("Sin agente").astype(str)  # noqa: E731
    base = hist.assign(agente=ag(hist["forwarder"])).groupby("agente").agg(
        embarques=("embarque", "nunique"), contenedores=("contenedores", "sum"))
    out = base.copy()
    if neg_casos is not None and len(neg_casos):
        n = neg_casos.assign(agente=ag(neg_casos["forwarder"]),
                             _orig=neg_casos["flete_original"] * neg_casos["contenedores"].fillna(1))
        gn = n.groupby("agente").agg(con_tarifa=("embarque", "nunique"), negociacion=("captura", "sum"),
                                     _orig=("_orig", "sum"))
        out = out.join(gn)
    if nor is not None and len(nor):
        out = out.join(nor.assign(agente=ag(nor["forwarder"])).groupby("agente")["ahorro"].sum().rename("nor"))
    for c in ("con_tarifa", "negociacion", "nor", "_orig"):
        if c not in out:
            out[c] = 0.0
    out = out.fillna({"con_tarifa": 0, "negociacion": 0.0, "nor": 0.0, "_orig": 0.0})
    out["cobertura"] = out["con_tarifa"] / out["embarques"]
    out["total"] = out["negociacion"] + out["nor"]
    out["pct"] = (out["negociacion"] / out["_orig"]).where(out["_orig"] > 0)
    return out.reset_index().sort_values("total", ascending=False)[cols].reset_index(drop=True)


def por_trimestre(neg_casos: pd.DataFrame, nor: pd.DataFrame, year: int) -> pd.DataFrame:
    """Q1..Q4 del año: negociación, 40 NOR, total y contenedores 40 NOR."""
    rows = []
    for q in range(1, 5):
        ini = pd.Timestamp(year, 3 * q - 2, 1)
        fin = ini + pd.DateOffset(months=3)
        n = neg_casos[(neg_casos["etd"] >= ini) & (neg_casos["etd"] < fin)] if neg_casos is not None and len(neg_casos) \
            else pd.DataFrame(columns=["captura"])
        r = nor[(nor["etd"] >= ini) & (nor["etd"] < fin)] if nor is not None and len(nor) \
            else pd.DataFrame(columns=["ahorro", "contenedores"])
        rows.append({"q": f"Q{q}", "negociacion": float(n["captura"].sum()), "nor": float(r["ahorro"].sum()),
                     "nor_cont": float(r["contenedores"].sum()), "neg_emb": int(len(n))})
    out = pd.DataFrame(rows)
    out["total"] = out["negociacion"] + out["nor"]
    return out
