"""Cotizaciones: ¿con quién conviene embarcar?

Compara las tarifas vigentes (flete + gastos locales) y las combina con el
desempeño real de cada forwarder en los últimos 12 meses.
"""
from __future__ import annotations

import datetime as dt

import numpy as np
import pandas as pd
import plotly.graph_objects as go
import streamlit as st

from components import charts
from components.kpi_cards import KPI, kpi_row
from components.layout import chart_title, empty, esc, filter_notes, guard, require, section
from components.tables import ColSpec, data_table
from config import settings
from config.mappings import MODOS_MARITIMOS
from utils import calculations as calc
from utils import formatting as fmt
from utils import freight
from views._common import ctx, filtered, month_labels, today

TIPOS = ["40ST/40HQ", "20ST", "40NOR"]
TODOS = "Todos los puertos"


def _txt(v) -> str:
    return "" if v is None or (isinstance(v, float) and v != v) else str(v)


def _fmt_pct_or(v, txt="—"):
    return fmt.fmt_pct(v) if v == v and v is not None else txt


def render() -> None:
    bundle, filters = ctx()
    base = require(bundle, "cotizaciones")
    if base is None:
        return
    cot = filtered(bundle, "cotizaciones", filters, use_period=False)
    filter_notes(base, filters.without_period(), "Cotizaciones")
    hist = bundle.get("historicas")
    if hist is not None:
        hist = hist[hist["modo"].isin(MODOS_MARITIMOS)]

    section("¿Con quién conviene embarcar?",
            "Elegí puerto, contenedor y fecha. Se comparan las tarifas vigentes ese día (flete + gastos locales ARG) "
            "y el desempeño de cada forwarder en los últimos 12 meses.")
    c0, c1, c2, c3, c4 = st.columns([1, 1.3, 1.1, 1, 1.1])
    destinos = sorted(cot["destino"].dropna().unique()) or ["Argentina"]
    destino = c0.selectbox("Destino", destinos,
                           index=destinos.index("Argentina") if "Argentina" in destinos else 0, key="ct_dest")
    cot = cot[cot["destino"] == destino]
    fecha = c3.date_input("Fecha de embarque", value=dt.date.today(), format="DD/MM/YYYY", key="ct_fecha")
    fecha = pd.Timestamp(fecha)
    tipo = c2.selectbox("Tipo de contenedor", TIPOS, key="ct_tipo")
    ports = sorted(freight.vigentes(cot, fecha, tipo)["puerto"].dropna().unique())
    puerto = c1.selectbox("Puerto de origen (POL)", [TODOS] + ports, key="ct_pol")
    prioridad = c4.selectbox("Prioridad", list(freight.PRIORIDADES), index=1, key="ct_prio",
                             help="Precio: pesa 85 % el costo. Equilibrado: 70 %. Servicio: 50 %.")
    puerto = None if puerto == TODOS else puerto

    with guard("Recomendación"):
        rec = freight.recommend(cot, hist, fecha, tipo, puerto, freight.PRIORIDADES[prioridad])
        op = rec.opciones
        if op.empty:
            empty(f"No hay cotizaciones {tipo} vigentes el {fecha:%d/%m/%Y}"
                  + (f" para {puerto}" if puerto else "") + ". Probá con otra fecha o puerto.")
            return

        top = op.iloc[0]
        cheapest = op.loc[op["costo_total"].idxmin()]
        ahorro = rec.mercado - top["costo_total"]
        hist_txt = (f"<b>{fmt.fmt_int(top['embarques_12m'])}</b> embarques en 12 meses · ETD en fecha "
                    f"<b>{_fmt_pct_or(top['etd_en_fecha'])}</b> · instrucción→ETD "
                    f"<b>{fmt.fmt_days(top['instr_etd'])}</b>"
                    if top["historial"] == "Con historial" else "Sin historial suficiente en los últimos 12 meses")
        kpi_row([
            KPI("Recomendado", str(top["forwarder"]), status="ok", badge=f"#{int(top['ranking'])}",
                sub=f"POL <b>{esc(top['puerto'])}</b> · línea {esc(_txt(top.get('linea')) or '—')} · "
                    f"vigente hasta {fmt.fmt_date(top['validez_hasta'])}"),
            KPI("Costo por contenedor", fmt.fmt_usd(top["costo_total"], compact=False),
                sub=f"Flete {fmt.fmt_usd(top['flete'], compact=False)} + locales "
                    f"{fmt.fmt_usd(top['locales_calc'], compact=False)}"
                    + (" (estimados)" if top["locales_estimados"] else "")),
            KPI("vs promedio de mercado", fmt.fmt_pct(top["vs_promedio"], signed=True),
                sub=f"Ahorro <b>{fmt.fmt_usd(ahorro, compact=False)}</b> por contenedor · promedio "
                    f"{fmt.fmt_usd(rec.mercado, compact=False)}"),
            KPI("Desempeño", _fmt_pct_or(top["etd_en_fecha"]) if top["historial"] == "Con historial" else "—",
                unit=" ETD en fecha" if top["historial"] == "Con historial" else "", sub=hist_txt),
        ])
        if cheapest["forwarder"] != top["forwarder"]:
            st.caption(f"La opción más barata es **{cheapest['forwarder']}** "
                       f"({fmt.fmt_usd(cheapest['costo_total'], compact=False)}), pero queda "
                       f"#{int(cheapest['ranking'])} por su desempeño histórico. Con prioridad «Precio» pesa más el costo.")
        tt = top.get("tt")
        extra = []
        if tt == tt and tt is not None:
            extra.append(f"TT {fmt.fmt_int(tt)} d")
        if _txt(top.get("dias_libres")):
            extra.append(f"{_txt(top['dias_libres'])} días libres")
        if _txt(top.get("transbordo")):
            extra.append(f"transbordo: {_txt(top['transbordo'])}")
        if extra:
            st.caption("Condiciones de la opción recomendada: " + " · ".join(extra))

    c1, c2 = st.columns([3, 2], gap="medium")
    with c1, guard("Comparación de opciones"):
        chart_title("Costo por contenedor de cada forwarder", "Mejor opción vigente de cada uno · flete + locales ARG")
        o = op.sort_values("costo_total")
        fig = go.Figure()
        fig.add_bar(y=o["forwarder"], x=o["flete"], name="Flete", orientation="h",
                    marker=dict(color=settings.SERIES[0], cornerradius=3),
                    hovertemplate="%{y} · flete: USD %{x:,.0f}<extra></extra>")
        fig.add_bar(y=o["forwarder"], x=o["locales_calc"], name="Gastos locales ARG", orientation="h",
                    marker=dict(color=settings.SERIES[1], cornerradius=3),
                    text=[fmt.fmt_usd(v, compact=False) for v in o["costo_total"]], textposition="outside",
                    cliponaxis=False, hovertemplate="%{y} · locales: USD %{x:,.0f}<extra></extra>")
        fig.update_layout(barmode="stack")
        charts.theme(fig, height=max(260, 34 * len(o) + 90), y_title="USD por contenedor", horizontal=True)
        fig.update_yaxes(autorange="reversed")
        fig.update_xaxes(range=[0, o["costo_total"].max() * 1.25])
        fig.add_vline(x=rec.mercado, line=dict(color=settings.COLORS["slate"], width=1.5, dash="dash"),
                      annotation_text="Promedio", annotation_position="top",
                      annotation_font=dict(size=11, color=settings.COLORS["slate"]))
        charts.show(fig, key="ct_opciones")

    with c2, guard("Cómo se calcula"):
        chart_title("Cómo se arma el ranking")
        w = freight.PRIORIDADES[prioridad]
        st.markdown(
            f"""
- **Precio ({fmt.fmt_pct(w)})**: la opción más barata vale 1; las demás, en proporción.
- **Servicio ({fmt.fmt_pct(1 - w)})**, con los embarques de los últimos 12 meses:
  - % de ETD cumplidos (±{settings.ETD_TOLERANCIA_DIAS} días de la ETD estimada), 60 %;
  - rapidez de instrucción → ETD, 40 %.
- Con menos de {settings.MIN_SAMPLE} embarques de historial, el servicio cuenta como neutro (0,5).
- Si la cotización no trae gastos locales, se usa la mediana de las vigentes y se marca como estimado.
"""
        )

    section("Ranking completo")
    with guard("Tabla de opciones"):
        data_table(op, [
            ColSpec("ranking", "#", "int"), ColSpec("forwarder", "Forwarder"), ColSpec("agente", "Agente origen"),
            ColSpec("puerto", "POL"), ColSpec("linea", "Línea"), ColSpec("costo_total", "Costo / cont. (USD)", "usd"),
            ColSpec("flete", "Flete (USD)", "usd"), ColSpec("locales_calc", "Locales (USD)", "usd"),
            ColSpec("vs_promedio", "vs promedio", "pct"), ColSpec("tt", "TT (d)", "days"),
            ColSpec("dias_libres", "Días libres"), ColSpec("embarques_12m", "Embarques 12 m", "int"),
            ColSpec("etd_en_fecha", "% ETD en fecha", "pct"), ColSpec("instr_etd", "Instr.→ETD (d)", "days"),
            ColSpec("cumple_sla", "% SLA consol.", "pct"), ColSpec("puntaje", "Puntaje", "num"),
            ColSpec("validez_hasta", "Vigente hasta", "date"),
        ], key="ct_ranking", filename=f"ranking_{tipo.replace('/', '-')}_{fecha:%Y%m%d}", search=False)

    section("Mapa de tarifas vigentes", f"Mejor costo por contenedor (flete + locales) por puerto y tipo · {fecha:%d/%m/%Y}")
    with guard("Mapa de tarifas"):
        rows = []
        for t in TIPOS:
            v = freight.vigentes(cot, fecha, t)
            if v.empty:
                continue
            loc_med = v.loc[v["locales_arg"] > 0, "locales_arg"].median()
            v = v.assign(costo=v["flete"] + v["locales_arg"].where(v["locales_arg"] > 0, loc_med).fillna(0))
            for pol, g in v.groupby("puerto"):
                b = g.loc[g["costo"].idxmin()]
                rows.append({"puerto": pol, "tipo": t, "txt": f"{fmt.fmt_usd(b['costo'], compact=False)} · {b['forwarder']}",
                             "n": g["forwarder"].nunique()})
        if not rows:
            empty()
        else:
            m = pd.DataFrame(rows)
            piv = m.pivot(index="puerto", columns="tipo", values="txt").reindex(columns=[t for t in TIPOS if t in set(m["tipo"])])
            nff = m.groupby("puerto")["n"].max()
            piv["Forwarders cotizando"] = nff
            piv = piv.reset_index().rename(columns={"puerto": "POL"}).sort_values("Forwarders cotizando", ascending=False)
            data_table(piv, [ColSpec("POL", "POL")] + [ColSpec(t, t) for t in TIPOS if t in piv.columns]
                       + [ColSpec("Forwarders cotizando", "Forwarders", "int")],
                       key="ct_mapa", filename=f"mapa_tarifas_{fecha:%Y%m%d}", search=False)

    section("Evolución del mercado", f"{tipo} · destino {destino} · promedio de mercado y mejor oferta por mes de inicio de validez")
    with guard("Evolución mensual"):
        h = filtered(bundle, "cotizaciones", filters)
        h = h[h["destino"] == destino]
        mk = freight.market_by_month(h[h["validez_desde"] <= today()])
        mk = mk[mk["tipo_ctnr"] == tipo].sort_values("mes").tail(12)
        if mk.empty:
            empty()
        else:
            mk["target"] = mk["mercado"] * (1 - settings.TARGET_DESCUENTO_FLETE)
            x = month_labels(mk["mes"])
            fig = go.Figure()
            fig.add_scatter(x=x, y=mk["mercado"], name="Promedio de mercado", mode="lines+markers",
                            line=dict(color=settings.SERIES[0], width=2), marker=dict(size=8), customdata=mk["n_ffww"],
                            hovertemplate="Promedio: USD %{y:,.0f} (%{customdata} forwarders)<extra></extra>")
            fig.add_scatter(x=x, y=mk["mejor"], name="Mejor oferta", mode="lines+markers",
                            line=dict(color=settings.SERIES[2], width=2), marker=dict(size=8),
                            hovertemplate="Mejor: USD %{y:,.0f}<extra></extra>")
            fig.add_scatter(x=x, y=mk["target"], name=f"Target (−{fmt.fmt_pct(settings.TARGET_DESCUENTO_FLETE)})",
                            mode="lines", line=dict(color=settings.COLORS["slate"], width=1.5, dash="dash"),
                            hovertemplate="Target: USD %{y:,.0f}<extra></extra>")
            charts.theme(fig, y_title="USD por contenedor (flete)")
            charts.show(fig, key="ct_mes")
