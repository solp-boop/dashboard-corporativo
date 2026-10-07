"""Panorama (nivel 1): ¿estamos bien o mal? 8 indicadores y lo que necesita atención."""
from __future__ import annotations

import html

import pandas as pd
import streamlit as st

from components import sla as sla_view
from components.kpi_cards import KPI, kpi_row
from components.layout import guard, section
from config import settings
from utils import bandeja, freight, productos, sla
from utils import formatting as fmt
from utils import panorama as pan
from views._common import ctx, filtered, periodo_txt, today


def _kpi(i: pan.Indicador) -> KPI:
    return KPI(i.nombre, i.valor, unit=i.unidad, sub=i.sub, status=i.estado, badge=i.badge, help=i.ayuda,
               delta=i.delta, tono=i.tono, link=i.destino)


def _row(label: str, inds: list[pan.Indicador]) -> None:
    st.markdown(f'<div class="row-label">{html.escape(label)}</div>', unsafe_allow_html=True)
    kpi_row([_kpi(i) for i in inds], columns=4, cls="panorama")


def _ventana(filters, t: pd.Timestamp) -> tuple[pd.Timestamp, pd.Timestamp]:
    start = pd.Timestamp(filters.start) if filters.start else pd.Timestamp(t.year, 1, 1)
    end = min(pd.Timestamp(filters.end), t) if filters.end else t
    return start, end


def _con_flete(df: pd.DataFrame | None, t: pd.Timestamp) -> pd.DataFrame:
    if df is None:
        return pd.DataFrame()
    return df[(df["etd"] <= t) & (df["flete_pagado"] > 0)]


def _zarpado_todos(h: pd.DataFrame, r: pd.DataFrame | None, t: pd.Timestamp) -> pd.DataFrame:
    """Embarques zarpados (todos los modos): Históricas + los que ya salieron y siguen en Reservas."""
    from utils.data_cleaning import id_key
    real = h[h["etd"] <= t]
    if r is None or r.empty:
        return real
    rr = r[(r["etd"] <= t) & r["responsable"].notna()] if "responsable" in r else r[r["etd"] <= t]
    rr = rr[~id_key(rr["embarque"]).isin(set(id_key(real["embarque"])))]
    return pd.concat([real, rr], ignore_index=True, sort=False) if len(rr) else real


def _concat(*dfs) -> pd.DataFrame:
    partes = [x for x in dfs if len(x)]
    if partes:
        return pd.concat(partes, ignore_index=True, sort=False)
    return pd.DataFrame(columns=["etd", "flete_pagado", "gastos_origen", "gastos_locales", "fob"])


def _tiempos(bundle, filters, t) -> list[pan.Indicador]:
    out = []
    h_f, h_all = filtered(bundle, "historicas", filters), filtered(bundle, "historicas", filters, use_period=False)
    r_f, r_all = filtered(bundle, "reservas", filters), filtered(bundle, "reservas", filters, use_period=False)
    if h_f is not None:
        # Lo zarpado incluye lo que ya salió y todavía está en Reservas.
        z, z_all = sla.zarpados_con_reservas(h_f, r_f, t), sla.zarpados_con_reservas(h_all, r_all, t)
        out.append(pan.sla_consolidacion(z, z_all, t))
    a_f, a_all = filtered(bundle, "aereos", filters), filtered(bundle, "aereos", filters, use_period=False)
    if a_f is not None:
        out.append(pan.punta_aereo(sla_view.air_zarpados(a_f, t), sla_view.air_zarpados(a_all, t), t))
    if h_f is not None:
        out.append(pan.punta_maritimo(z[z["eta"] <= t], z_all[z_all["eta"] <= t], t))   # ETA futura = estimada
    if bundle.get("emb_hist") is not None and len(bundle.get("emb_hist")):
        du = productos.base_universo(bundle.get("emb_hist"), t, bundle.get("aereos"), bundle.get("planif"))
        out.append(pan.time_to_market(productos.objetivo_universo(du, t)))
    return out


def _volumen_costos(bundle, filters, t) -> list[pan.Indicador]:
    out = []
    h_f, h_all = filtered(bundle, "historicas", filters), filtered(bundle, "historicas", filters, use_period=False)
    a_f, a_all = filtered(bundle, "aereos", filters), filtered(bundle, "aereos", filters, use_period=False)
    if h_f is None:
        return out
    start, end = _ventana(filters, t)
    p0, p1 = pan.ventana_anterior(start, end)
    yoy = filters.start is not None          # sin inicio de período no hay «mismo período del año anterior»
    # El volumen del año está arriba, en «Nuestro año» (con su comparación contra el año anterior).

    m_f, m_all = _con_flete(pan.maritimos(h_f), t), _con_flete(pan.maritimos(h_all), t)
    pagos = _concat(m_f, _con_flete(a_f, t))
    pagos_all = _concat(m_all, _con_flete(a_all, t))
    out.append(pan.costo(pagos, pagos_all, t))

    from utils import captura as cap
    neg = freight.negotiation(bundle.get("cotizaciones"), bundle.get("cot_sin_negociar"))
    hay_neg = bundle.get("cot_sin_negociar") is not None and len(bundle.get("cot_sin_negociar")) > 0
    nor = freight.nor_savings(m_f)
    nor = nor.dropna(subset=["ahorro"]) if len(nor) else nor
    nor_prev = neg_prev = None
    if yoy:
        m_prev = m_all[m_all["etd"].between(p0, p1)]
        nor_prev = freight.nor_savings(m_prev)
        nor_prev = nor_prev.dropna(subset=["ahorro"]) if len(nor_prev) else nor_prev
        neg_prev = cap.por_negociacion(m_prev, neg)
    out.append(pan.captura(nor, nor_prev, cap.por_negociacion(m_f, neg), neg_prev, hay_neg))

    cot = bundle.get("cotizaciones")
    hm = freight.add_market_reference(m_f, cot)
    hm_all = freight.add_market_reference(m_all, cot)
    pct, n = freight.vs_mercado_ponderado(hm)
    last = t.to_period("M").to_timestamp() - pd.offsets.MonthBegin(1)
    prev = last - pd.offsets.MonthBegin(1)
    mes = hm_all["etd"].dt.to_period("M").dt.to_timestamp() if len(hm_all) else pd.Series(dtype="datetime64[ns]")
    def pct_mes(m):
        if not len(hm_all):
            return float("nan")
        v, k = freight.vs_mercado_ponderado(hm_all[mes == m])
        return v if k >= settings.MIN_SAMPLE else float("nan")

    p_last, p_prev = pct_mes(last), pct_mes(prev)
    out.append(pan.vs_mercado(pct, n, p_last, p_prev, t))
    return out


def _atencion(bundle, filters) -> None:
    from views.accion import casos
    df = casos(bundle, filters)
    res = bandeja.resumen_situaciones(df)
    orden = [bandeja.TIPOS["forwarder"], bandeja.TIPOS["sla"], "datos"]
    datos = res[res["tipo"].isin([bandeja.TIPOS["dato"], bandeja.TIPOS["cerrado"]])]
    filas = {r["tipo"]: (int(r["casos"]), int(r["alta"])) for _, r in res.iterrows()}
    filas["datos"] = (int(datos["casos"].sum()), int(datos["alta"].sum()))
    nombres = {bandeja.TIPOS["forwarder"]: "Confirmar o reclamar al forwarder",
               bandeja.TIPOS["sla"]: "Operaciones en riesgo de SLA", "datos": "Datos a corregir en la planilla"}
    alta = int((df["prioridad"] == "Alta").sum()) if len(df) else 0
    section("Necesita atención",
            f"{fmt.fmt_int(len(df))} casos abiertos, {fmt.fmt_int(alta)} de prioridad alta. Cada uno abre la "
            "Bandeja de acción con la operación y la acción sugerida.")
    tiles = []
    for k in orden:
        n, a = filas.get(k, (0, 0))
        sub = f"{fmt.fmt_int(a)} de prioridad alta" if a else "sin prioridad alta"
        tiles.append(f'<a href="accion" target="_self"><div class="n">{fmt.fmt_int(n)}</div>'
                     f'<div class="t">{html.escape(nombres[k])}</div><div class="s">{sub}</div></a>')
    st.markdown(f'<div class="atencion">{"".join(tiles)}</div>', unsafe_allow_html=True)


def render() -> None:
    bundle, filters = ctx()
    t = today()
    with guard("Nuestro año"):
        from views.resumen import render_anio
        render_anio(bundle, filters, numerado=False, compacto=True)
    section("¿Cómo estamos?",
            f"Embarques que zarparon {periodo_txt(filters)}. Cada recuadro abre su detalle; el ⓘ explica el cálculo.")
    with guard("Tiempos"):
        _row("Tiempos", _tiempos(bundle, filters, t))
    with guard("Volumen y costos"):
        _row("Costos", _volumen_costos(bundle, filters, t))
    with guard("Necesita atención"):
        _atencion(bundle, filters)
