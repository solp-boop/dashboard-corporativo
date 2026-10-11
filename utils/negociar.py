"""Tarifas y negociación: qué pagamos hoy, qué ofrece el mercado vigente y con quién negociar.

Por puerto × tipo de contenedor (solo rutas que usamos en los últimos `dias` días, destino Argentina):
- Pagamos: mediana del flete por contenedor pagado en esa ventana.
- Agente principal: con quién embarcamos más contenedores en la ventana.
- Mercado vigente: tarifas de «Cotizaciones Maritimos Negociado» vigentes hoy (validez desde ≤ hoy ≤ hasta),
  mismo puerto, tipo y destino. Mediana y mejor tarifa (con su agente).
- Acción: si el agente principal ya tiene la mejor tarifa, OK; si no, negociar con él para bajar a la mejor
  (o pedirle cotización si no tiene tarifa vigente). Potencial por mes = (tarifa vigente del agente − mejor
  tarifa vigente) × contenedores por mes de la ventana. Todo con tarifas de hoy.

Sin Streamlit, para poder testearlo. Todo por mediana.
"""
from __future__ import annotations

import numpy as np
import pandas as pd

from utils.data_cleaning import fold

COLS = ["puerto", "tipo_ctnr", "embarques", "contenedores", "pagamos", "agente", "tarifa_agente", "mercado",
        "mejor", "mejor_agente", "agentes_cotizan", "brecha", "potencial_mes", "accion", "estado"]
TOL = 0.02   # dentro del 2 % de la mejor tarifa = «ya tiene la mejor»


def vigentes(cot: pd.DataFrame | None, today: pd.Timestamp, destino: str = "Argentina") -> pd.DataFrame:
    if cot is None or cot.empty:
        return pd.DataFrame(columns=["forwarder", "puerto", "tipo_ctnr", "flete"])
    c = cot[(cot["validez_desde"] <= today) & (cot["validez_hasta"] >= today) & (cot["flete"] > 0)]
    if "destino" in c:
        c = c[c["destino"] == destino]
    return c


def situacion(hist: pd.DataFrame, cot: pd.DataFrame | None, today: pd.Timestamp, dias: int = 60,
              destino: str = "Argentina") -> pd.DataFrame:
    if hist is None or hist.empty:
        return pd.DataFrame(columns=COLS)
    h = hist[(hist["etd"] <= today) & (hist["etd"] > today - pd.Timedelta(days=dias)) & (hist["flete_por_ctnr"] > 0)
             & hist["tipo_ctnr"].notna() & hist["puerto"].notna()]
    if "destino" in h:
        h = h[h["destino"] == destino]
    if h.empty:
        return pd.DataFrame(columns=COLS)
    v = vigentes(cot, today, destino)
    v = v.assign(_p=v["puerto"].map(fold), _f=v["forwarder"].map(fold)) if len(v) else v
    meses = dias / 30.0
    rows = []
    for (pto, tipo), g in h.groupby(["puerto", "tipo_ctnr"]):
        cont = float(g["contenedores"].fillna(1).sum())
        agente = (g.assign(_c=g["contenedores"].fillna(1)).groupby("forwarder")["_c"].sum().idxmax()
                  if g["forwarder"].notna().any() else None)
        pagamos = float(g["flete_por_ctnr"].median())
        c = v[(v["_p"] == fold(pto)) & (v["tipo_ctnr"] == tipo)] if len(v) else v
        mercado = float(c["flete"].median()) if len(c) else np.nan
        if len(c):
            por_ag = c.groupby("forwarder")["flete"].median()
            mejor, mejor_ag = float(por_ag.min()), por_ag.idxmin()
            tarifa_ag = c.loc[c["_f"] == fold(agente), "flete"].median() if agente else np.nan
            n_ag = int(len(por_ag))
        else:
            mejor, mejor_ag, tarifa_ag, n_ag = np.nan, None, np.nan, 0
        # Brecha con tarifas de hoy (lo pagado en la ventana puede ser de otra quincena y otro mercado).
        brecha = tarifa_ag - mejor if mejor == mejor and tarifa_ag == tarifa_ag else np.nan
        potencial = max(brecha, 0) * cont / meses if brecha == brecha else np.nan
        if mejor != mejor:
            accion, estado = "Sin tarifas vigentes para comparar: pedir cotizaciones", "Sin dato"
        elif tarifa_ag != tarifa_ag:
            accion, estado = (f"Pedir cotización a {agente} (no tiene tarifa vigente); la mejor es "
                              f"USD {mejor:,.0f} de {mejor_ag}").replace(",", "."), "Revisar"
        elif tarifa_ag <= mejor * (1 + TOL):
            accion, estado = f"OK: {agente} tiene la mejor tarifa vigente", "OK"
        else:
            accion, estado = (f"Negociar con {agente}: bajar de USD {tarifa_ag:,.0f} a USD {mejor:,.0f} "
                              f"(tarifa de {mejor_ag})").replace(",", "."), "Negociar"
        rows.append({"puerto": pto, "tipo_ctnr": tipo, "embarques": int(g["embarque"].nunique()),
                     "contenedores": cont, "pagamos": pagamos, "agente": agente, "tarifa_agente": tarifa_ag,
                     "mercado": mercado, "mejor": mejor, "mejor_agente": mejor_ag, "agentes_cotizan": n_ag,
                     "brecha": brecha, "potencial_mes": potencial, "accion": accion, "estado": estado})
    out = pd.DataFrame(rows, columns=COLS)
    orden = {"Negociar": 0, "Revisar": 1, "OK": 2, "Sin dato": 3}
    return out.assign(_o=out["estado"].map(orden)).sort_values(["_o", "potencial_mes", "contenedores"],
                                                               ascending=[True, False, False]).drop(columns="_o") \
        .reset_index(drop=True)


def ranking_agentes(cot: pd.DataFrame | None, hist: pd.DataFrame, today: pd.Timestamp, dias: int = 60,
                    destino: str = "Argentina") -> pd.DataFrame:
    """Por agente con tarifas vigentes: en cuántas de NUESTRAS rutas cotiza, en cuántas es el más barato y
    cuánto más caro que la mejor está, en mediana."""
    v = vigentes(cot, today, destino)
    h = hist[(hist["etd"] <= today) & (hist["etd"] > today - pd.Timedelta(days=dias))]
    if v.empty or h.empty:
        return pd.DataFrame(columns=["forwarder", "rutas", "mejor_en", "vs_mejor"])
    rutas = {(fold(p), t) for p, t in zip(h["puerto"], h["tipo_ctnr"]) if isinstance(p, str) and isinstance(t, str)}
    v = v.assign(_p=v["puerto"].map(fold))
    v = v[[(p, t) in rutas for p, t in zip(v["_p"], v["tipo_ctnr"])]]
    if v.empty:
        return pd.DataFrame(columns=["forwarder", "rutas", "mejor_en", "vs_mejor"])
    g = v.groupby(["_p", "tipo_ctnr", "forwarder"], as_index=False)["flete"].median()
    g["mejor"] = g.groupby(["_p", "tipo_ctnr"])["flete"].transform("min")
    g["es_mejor"] = g["flete"] <= g["mejor"] * (1 + TOL)
    g["vs"] = g["flete"] / g["mejor"] - 1
    out = g.groupby("forwarder").agg(rutas=("flete", "size"), mejor_en=("es_mejor", "sum"),
                                     vs_mejor=("vs", "median")).reset_index()
    return out.sort_values(["mejor_en", "vs_mejor"], ascending=[False, True]).reset_index(drop=True)
