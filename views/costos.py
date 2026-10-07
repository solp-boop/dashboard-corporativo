"""Costos y captura (nivel 2): cuánto pagamos, cuánto capturamos y dónde hay oportunidad.

Reúne lo que antes estaba en «Fletes y gastos pagados» y «Cotizaciones», en cuatro pestañas:
Gasto · Captura · Tarifas y negociación · Validación.
"""
from __future__ import annotations

import pandas as pd
import plotly.graph_objects as go
import streamlit as st

from components import charts
from components.kpi_cards import KPI, cert_status, cert_sub, kpi_row
from components.layout import chart_title, empty, guard, require, section
from components.tables import ColSpec, data_table
from config import settings
from config.mappings import MODOS_MARITIMOS
from utils import calculations as calc
from utils import captura as cap
from utils import costos as cs
from utils import formatting as fmt
from utils import freight
from views import cotizaciones, fletes_pagados
from views._common import ctx, filtered, month_labels, today

DIMS = [("forwarder", "Agente"), ("puerto", "Puerto"), ("medio", "Medio"), ("tipo_ctnr", "Tipo de contenedor"),
        ("linea", "Línea marítima"), ("responsable", "Responsable")]
COST_PARTS = [("flete_pagado", "Flete internacional"), ("gastos_locales", "Gastos locales ARG"),
              ("gastos_origen", "Gastos en origen")]


def _ventana_prev(filters, t):
    if not filters.start:
        return None
    end = min(pd.Timestamp(filters.end), t) if filters.end else t
    return pd.Timestamp(filters.start) - pd.DateOffset(years=1), end - pd.DateOffset(years=1)


def _datos(bundle, filters, use_period=True):
    t = today()
    h = filtered(bundle, "historicas", filters, use_period=use_period)
    a = filtered(bundle, "aereos", filters, use_period=use_period) if bundle.get("aereos") is not None else None
    if h is not None:
        h = freight.add_market_reference(h[h["modo"].isin(MODOS_MARITIMOS) & (h["etd"] <= t) & (h["flete_pagado"] > 0)],
                                         bundle.get("cotizaciones"))
    return h, a, cs.pagos(h, a, t)


def render() -> None:
    bundle, filters = ctx()
    if require(bundle, "historicas") is None:
        return
    t = today()
    h, a, p = _datos(bundle, filters)
    _, _, p_all = _datos(bundle, filters, use_period=False)
    ventana = _ventana_prev(filters, t)
    p_prev = p_all[p_all["etd"].between(*ventana)] if ventana else None
    tabs = st.tabs(["Gasto", "Captura", "Tarifas y negociación", "Validación", "Contenedores y cargas especiales"])
    with tabs[0]:
        _gasto(bundle, h, a, p, p_all, p_prev)
    with tabs[1]:
        _captura(bundle, filters, h, ventana)
    with tabs[2]:
        _tarifas(bundle, h)
    with tabs[3]:
        _validacion(h, a)
    with tabs[4]:
        from views import resumen
        with guard("Contenedores"):
            resumen.render_contenedores(bundle, filters)
        resumen.render_especiales(bundle, filters)


# ---------------------------------------------------------------------------
def _gasto(bundle, h, a, p, p_all, p_prev) -> None:
    from utils import panorama as pan
    t = today()
    section("¿Cuánto pagamos?", "Marítimo y aéreo zarpados con flete pagado: flete + gastos en origen + gastos locales.")
    if p.empty:
        empty()
        return
    with guard("KPIs de gasto"):
        ind = pan.costo(p, p_all, t)
        fl = calc.describe(h["flete_por_ctnr"]) if h is not None and len(h) else calc.describe(pd.Series(dtype=float))
        kg = calc.describe((a["flete_pagado"] / a["chargeable"].where(a["chargeable"] > 0))[
            (a["etd"] <= t) & (a["flete_pagado"] > 0)]) if a is not None and len(a) and "chargeable" in a \
            else calc.describe(pd.Series(dtype=float))
        cm3 = calc.describe(h["costo_por_m3"]) if h is not None and len(h) else calc.describe(pd.Series(dtype=float))
        kpi_row([
            KPI(ind.nombre, ind.valor, sub=ind.sub, delta=ind.delta, tono=ind.tono, help=ind.ayuda),
            KPI("Flete por contenedor", fmt.fmt_usd(fl.median, compact=False) if fl.enough else "—",
                sub=f"Marítimo · mediana · P25–P75 {fmt.fmt_usd(fl.p25, compact=False)}–"
                    f"{fmt.fmt_usd(fl.p75, compact=False)}" if fl.enough else "Marítimo"),
            KPI("Aéreo · USD por kg", f"USD {fmt.fmt_num(kg.median, 1)}" if kg.enough else "—",
                sub=f"Mediana sobre chargeable · n={fmt.fmt_int(kg.n)}" if kg.enough else "Sin chargeable cargado"),
            KPI("Costo por m³", fmt.fmt_usd(cm3.median, compact=False) if cm3.enough else "—",
                sub="Marítimo · mediana del costo total / m³"),
        ])
    c1, c2 = st.columns(2, gap="medium")
    with c1, guard("Costo mensual"):
        chart_title("Costo logístico por mes", "USD por mes de ETD · marítimo y aéreo")
        m = p.assign(mes=calc.month_start(p["etd"]))
        months = sorted(m["mes"].unique())[-12:]
        if not months:
            empty()
        else:
            fig = go.Figure()
            for i, (col, label) in enumerate(COST_PARTS):
                s = m.groupby("mes")[col].apply(lambda x: x.clip(lower=0).sum()).reindex(months).fillna(0)
                fig.add_bar(x=month_labels(pd.Series(months)), y=s.values, name=label,
                            marker=dict(color=settings.SERIES[i], cornerradius=3),
                            hovertemplate=f"%{{x}} · {label}: USD %{{y:,.0f}}<extra></extra>")
            fig.update_layout(barmode="stack")
            charts.theme(fig, y_title="USD")
            charts.show(fig, key="co_mes")
    with c2, guard("Pagado vs mercado"):
        chart_title("Flete por contenedor: pagado vs mercado",
                    "Marítimo, destino Argentina · mediana pagada vs mediana de mercado y mejor cotización del mes")
        _pagado_vs_mercado_chart(bundle, h)

    section("¿Dónde se va el gasto?", "Por dimensión, ordenado por gasto. Hacé clic en una fila para ver sus embarques.")
    with guard("Gasto por dimensión"):
        nombres = dict(DIMS)
        dim = st.segmented_control("Ver por", list(nombres), default="forwarder", format_func=nombres.get,
                                   key="co_dim", label_visibility="collapsed") or "forwarder"
        tb = cs.por_dimension(p, dim, p_prev)
        if tb.empty:
            empty()
        else:
            show = pd.DataFrame({
                nombres[dim]: tb["grupo"], "Embarques": tb["embarques"].map(lambda v: fmt.fmt_int(v)),
                "Gasto (USD)": tb["gasto"].map(lambda v: fmt.fmt_int(v)),
                "% del gasto": (tb["pct_gasto"] * 100).round(0),
                "Flete / cont. (USD)": tb["flete_ctnr"].map(lambda v: fmt.fmt_int(v) if v == v else None), "Costo / FOB": tb["incidencia"].map(lambda v: fmt.fmt_pct(v, 1) if v == v else None),
                "vs mercado": (tb["vs_mercado"] * 100).round(0),
            })
            config = {
                "Gasto (USD)": st.column_config.TextColumn("Gasto (USD)"),
                "% del gasto": st.column_config.ProgressColumn("% del gasto", format="%d %%", min_value=0, max_value=100),
                "Flete / cont. (USD)": st.column_config.TextColumn("Flete / cont. (USD)", help="Mediana, solo marítimo"),
                "Costo / FOB": st.column_config.TextColumn("Costo / FOB"),
                "vs mercado": st.column_config.NumberColumn("vs mercado", format="%+d %%",
                                                            help="Flete pagado vs mediana de mercado del mes, "
                                                                 "ponderado por contenedores. Negativo = debajo"),
            }
            if tb["delta_ctnr"].notna().any():
                show["Δ flete / cont. (USD)"] = tb["delta_ctnr"].map(
                    lambda v: ("+" if v > 0 else "") + fmt.fmt_int(v) if v == v else None)
                config["Δ flete / cont. (USD)"] = st.column_config.TextColumn(
                    "Δ flete / cont. (USD)", help="Contra el mismo período del año anterior")
            ev = st.dataframe(show, column_config=config, hide_index=True, width="stretch",
                              height=min(420, 38 + 35 * len(show)), on_select="rerun", selection_mode="single-row",
                              key=f"co_tabla_{dim}", placeholder="—")
            filas = ev.selection.rows if ev is not None and hasattr(ev, "selection") else []
            i = filas[0] if filas and filas[0] < len(tb) else 0
            grupo = tb.iloc[i]["grupo"]
            c = cs.casos(p, dim, grupo).sort_values("costo", ascending=False)
            st.markdown(f'<div class="section-sub"><b>{fmt.plural(len(c), "embarque")} · '
                        f'{nombres[dim].lower()}: {grupo}</b></div>', unsafe_allow_html=True)
            data_table(c, [
                ColSpec("embarque", "Embarque"), ColSpec("medio", "Medio"), ColSpec("etd", "ETD", "date"),
                ColSpec("forwarder", "Agente"), ColSpec("puerto", "Puerto"), ColSpec("tipo_ctnr", "Tipo"),
                ColSpec("contenedores", "Cont.", "int"), ColSpec("flete_pagado", "Flete (USD)", "usd"),
                ColSpec("flete_por_ctnr", "Flete / cont.", "usd"), ColSpec("mercado_mes", "Mercado / cont.", "usd"),
                ColSpec("vs_mercado", "vs mercado", "pct"), ColSpec("gastos_origen", "Origen (USD)", "usd"),
                ColSpec("gastos_locales", "Locales (USD)", "usd"), ColSpec("costo", "Costo total (USD)", "usd"),
                ColSpec("responsable", "Responsable"),
            ], key=f"co_casos_{dim}", filename="gasto_por_embarque", search=len(c) > 12)


def _pagado_vs_mercado_chart(bundle, h) -> None:
    tipos = fletes_pagados.TIPOS
    tipo = st.segmented_control("Tipo de contenedor", tipos, default=tipos[0], key="co_tipo",
                                label_visibility="collapsed") or tipos[0]
    if h is None or h.empty:
        empty()
        return
    tt = h[(h["tipo_ctnr"] == tipo) & (h["destino"] == "Argentina")].assign(mes=lambda x: calc.month_start(x["etd"]))
    cot = bundle.get("cotizaciones")
    cot_ar = cot[cot["destino"] == "Argentina"] if cot is not None and "destino" in cot else None
    mk = freight.market_by_month(cot_ar) if cot_ar is not None else pd.DataFrame()
    mk = mk[mk["tipo_ctnr"] == tipo].set_index("mes") if len(mk) else mk
    months = sorted(tt["mes"].unique())[-12:]
    if not months:
        empty(f"No hay embarques {tipo} con flete cargado en el período.")
        return
    x = month_labels(pd.Series(months))
    paid = tt.groupby("mes")["flete_por_ctnr"].median().reindex(months)
    fig = go.Figure()
    fig.add_scatter(x=x, y=paid.values, name="Pagado (mediana)", mode="lines+markers",
                    line=dict(color=settings.SERIES[0], width=2.5), marker=dict(size=8),
                    hovertemplate="Pagado: USD %{y:,.0f}<extra></extra>")
    if len(mk):
        fig.add_scatter(x=x, y=mk["mercado"].reindex(months).values, name="Mediana de mercado", mode="lines+markers",
                        line=dict(color=settings.SERIES[1], width=2), marker=dict(size=8),
                        hovertemplate="Mercado: USD %{y:,.0f}<extra></extra>")
        fig.add_scatter(x=x, y=mk["mejor"].reindex(months).values, name="Mejor cotización", mode="lines",
                        line=dict(color=settings.SERIES[2], width=1.5, dash="dash"),
                        hovertemplate="Mejor: USD %{y:,.0f}<extra></extra>")
    charts.theme(fig, y_title="USD por contenedor")
    charts.show(fig, key="co_vs_mercado")


# ---------------------------------------------------------------------------
def _captura(bundle, filters, h, ventana) -> None:
    section("¿Cuánto capturamos?",
            "Ahorro conseguido por una decisión de la gestión, que se puede sumar: rebaja al negociar tarifas y uso de "
            "40 NOR. La posición contra el mercado está en «Tarifas y negociación» y no se suma acá.")
    if h is None or h.empty:
        empty()
        return
    with guard("Captura"):
        neg = freight.negotiation(bundle.get("cotizaciones"), bundle.get("cot_sin_negociar"))
        casos_neg = cap.por_negociacion(h, neg)
        nor = freight.nor_savings(h)
        nor = nor.dropna(subset=["ahorro"]) if len(nor) else nor
        r = cap.resumen(casos_neg, nor)
        hay_sin = bundle.get("cot_sin_negociar") is not None and len(bundle.get("cot_sin_negociar"))
        prev_txt = ""
        if ventana:
            hp = filtered(bundle, "historicas", filters, use_period=False)
            hp = hp[hp["modo"].isin(MODOS_MARITIMOS) & hp["etd"].between(*ventana) & (hp["flete_pagado"] > 0)]
            nor_p = freight.nor_savings(hp)
            r0 = cap.resumen(cap.por_negociacion(hp, neg), nor_p.dropna(subset=["ahorro"]) if len(nor_p) else nor_p)
            d = r["total"] - r0["total"]
            prev_txt = (f"{'▲' if d > 0 else '▼' if d < 0 else '='} {fmt.fmt_usd(abs(d))} vs mismo período del año "
                        f"anterior ({fmt.fmt_usd(r0['total'])})")
        kpi_row([
            KPI("Captura total", fmt.fmt_usd(r["total"]), delta=prev_txt,
                tono="good" if prev_txt.startswith("▲") else ("bad" if prev_txt.startswith("▼") else "neutral"),
                sub=(f"negociación {fmt.fmt_usd(r['negociacion'])}" if hay_sin else
                     "negociación: falta la solapa sin negociar") + f" · 40 NOR {fmt.fmt_usd(r['nor'])}"),
            KPI("Negociación de tarifas", fmt.fmt_usd(r["negociacion"]) if hay_sin else "—",
                sub=(f"<b>{fmt.fmt_int(r['neg_emb'])}</b> embarques con su tarifa identificada" if hay_sin else
                     "Falta la solapa «Cotizaciones Maritimos SIN NEGOCIAR»"),
                help="(Tarifa sin negociar − tarifa negociada) × contenedores, para los embarques cuyo flete pagado "
                     f"coincide (± {fmt.fmt_pct(cap.TOLERANCIA)}) con una tarifa negociada vigente del mismo forwarder, "
                     "puerto y tipo de contenedor. Los embarques sin coincidencia no suman."),
            KPI("Uso de 40 NOR", fmt.fmt_usd(r["nor"]),
                sub=f"<b>{fmt.fmt_int(r['nor_cont'])}</b> contenedores vs 40 ST/HQ del mismo mes",
                help="(Mediana pagada por un 40 ST/HQ ese mes − flete pagado por el 40 NOR) × contenedores."),
        ], columns=3)
        g = cap.mensual(casos_neg, nor)
        if len(g):
            chart_title("Captura por mes", "USD por mes de ETD y fuente · la línea es el acumulado del período")
            x = month_labels(g["mes"])
            fig = go.Figure()
            fig.add_bar(x=x, y=g["negociacion"], name="Negociación de tarifas",
                        marker=dict(color=settings.SERIES[0], cornerradius=3),
                        hovertemplate="%{x} · negociación: USD %{y:,.0f}<extra></extra>")
            fig.add_bar(x=x, y=g["nor"], name="40 NOR", marker=dict(color=settings.SERIES[1], cornerradius=3),
                        hovertemplate="%{x} · 40 NOR: USD %{y:,.0f}<extra></extra>")
            fig.add_scatter(x=x, y=g["acumulado"], name="Acumulado", mode="lines+markers", yaxis="y2",
                            line=dict(color=settings.SERIES[2], width=2),
                            hovertemplate="%{x} · acumulado: USD %{y:,.0f}<extra></extra>")
            fig.update_layout(barmode="stack", yaxis2=dict(overlaying="y", side="right", showgrid=False,
                                                           tickformat=",.0f", rangemode="tozero"))
            charts.theme(fig, y_title="USD por mes")
            charts.show(fig, key="co_captura_mes")
    c1, c2 = st.columns(2, gap="medium")
    with c1, guard("Detalle negociación"):
        chart_title("Negociación · embarques con su tarifa", "Tarifa sin negociar vs negociada, por contenedor")
        if casos_neg.empty:
            empty("Sin embarques con tarifa identificada." if hay_sin else
                  "Falta la solapa de cotizaciones sin negociar.")
        else:
            data_table(casos_neg, [
                ColSpec("embarque", "Embarque"), ColSpec("etd", "ETD", "date"), ColSpec("forwarder", "Agente"),
                ColSpec("puerto", "Puerto"), ColSpec("tipo_ctnr", "Tipo"), ColSpec("contenedores", "Cont.", "int"),
                ColSpec("flete_original", "Sin negociar (USD)", "usd"),
                ColSpec("flete_negociado", "Negociada (USD)", "usd"), ColSpec("flete_por_ctnr", "Pagado (USD)", "usd"),
                ColSpec("captura", "Captura (USD)", "usd"),
            ], key="co_neg", filename="captura_negociacion", search=len(casos_neg) > 12)
    with c2, guard("Detalle 40 NOR"):
        chart_title("40 NOR · por mes", "Contenedores 40 NOR contra la mediana pagada por un 40 ST/HQ")
        if nor.empty:
            empty("Sin embarques en 40 NOR con flete pagado en el período.")
        else:
            gn = nor.groupby("mes").agg(embarques=("embarque", "count"), contenedores=("contenedores", "sum"),
                                        nor=("flete_por_ctnr", "median"), hq=("ref_hq", "first"),
                                        ahorro=("ahorro", "sum")).reset_index()
            gn["mes_txt"] = gn["mes"].map(lambda m: fmt.fmt_month(m, long=True))
            data_table(gn.iloc[::-1], [
                ColSpec("mes_txt", "Mes ETD"), ColSpec("contenedores", "Cont.", "int"),
                ColSpec("hq", "40 ST/HQ (USD)", "usd"), ColSpec("nor", "40 NOR (USD)", "usd"),
                ColSpec("ahorro", "Ahorro (USD)", "usd"),
            ], key="co_nor", filename="captura_40nor", search=False)


# ---------------------------------------------------------------------------
def _tarifas(bundle, h) -> None:
    section("¿Dónde podemos renegociar?",
            "Combinaciones de agente, puerto y contenedor donde pagamos por encima de la mediana de mercado del mes. "
            "«En juego» = lo pagado por encima del mercado en el período.")
    with guard("Oportunidades"):
        if h is None or h.empty:
            empty()
        else:
            pct, n = freight.vs_mercado_ponderado(h)
            op = cap.oportunidades(h)
            neg = freight.negotiation(bundle.get("cotizaciones"), bundle.get("cot_sin_negociar"))
            rb = cap.rebaja_por_forwarder(neg)
            tol = settings.PAGADO_VS_MERCADO_TOLERANCIA
            kpi_row([
                KPI("Pagado vs mercado", fmt.fmt_pct(pct, signed=True) if n >= settings.MIN_SAMPLE else "—",
                    status=("ok" if pct <= 0 else "warn" if pct <= tol else "bad") if n >= settings.MIN_SAMPLE else "",
                    sub=f"{fmt.fmt_int(n)} embarques comparados con el mercado de su mes"),
                KPI("En juego", fmt.fmt_usd(op["en_juego"].sum()) if len(op) else "—",
                    status="warn" if len(op) else "ok", sub=f"en {fmt.fmt_int(len(op))} combinaciones"),
                KPI("Rebaja al negociar", fmt.fmt_pct(neg["rebaja_pct"].median()) if len(neg) else "—",
                    sub=f"mediana sobre {fmt.fmt_int(len(neg))} tarifas" if len(neg) else
                    "Falta la solapa de cotizaciones sin negociar"),
            ], columns=3)
            if len(op):
                data_table(op, [
                    ColSpec("forwarder", "Agente"), ColSpec("puerto", "Puerto"), ColSpec("tipo_ctnr", "Contenedor"),
                    ColSpec("embarques", "Embarques", "int"), ColSpec("contenedores", "Cont.", "int"),
                    ColSpec("pagado", "Pagado / cont. (USD)", "usd"), ColSpec("mercado", "Mercado / cont. (USD)", "usd"),
                    ColSpec("dif_pct", "Diferencia", "pct"), ColSpec("en_juego", "En juego (USD)", "usd"),
                ], key="co_oport", filename="oportunidades_renegociacion", search=False,
                    caption="Medianas por contenedor · ordenado por USD en juego")
            if len(rb):
                st.markdown('<div class="section-sub"><b>Rebaja obtenida al negociar, por forwarder</b></div>',
                            unsafe_allow_html=True)
                data_table(rb, [
                    ColSpec("forwarder", "Forwarder"), ColSpec("tarifas", "Tarifas negociadas", "int"),
                    ColSpec("rebaja_usd", "Rebaja / cont. (USD, mediana)", "usd"),
                    ColSpec("rebaja_pct", "Rebaja (mediana)", "pct"),
                ], key="co_rebaja", filename="rebaja_por_forwarder", search=False)
    with st.expander("Cotizaciones vigentes: ranking de forwarders, mapa de tarifas y evolución del mercado"):
        cotizaciones.render()


# ---------------------------------------------------------------------------
def _cert_aereo(aa, cert_a) -> KPI:
    """Aéreo: sin objetivo; el estado lo da la tendencia (último mes cerrado vs primer mes con certificación)."""
    from views.resumen import _cert_tendencia
    if aa is None or aa.empty:
        return KPI("Certificado · aéreo", "—", badge="Sin objetivo")
    k = _cert_tendencia(aa, lambda d: (float(d["flete_certificado"].sum() / d["flete_pagado"].sum())
                                       if len(d) and d["flete_pagado"].sum() else float("nan")))
    return KPI("Certificado · aéreo", fmt.fmt_pct(cert_a), badge="Sin objetivo", status=k.status,
               sub=(f"{k.value} último mes cerrado · " + k.sub) if k.value != "—" else "Se espera que baje")


def _validacion(h, a) -> None:
    section("Validación y certificación", "Resultado de la validación de Logística Internacional y flete certificado "
                                          "por fuera.")
    if h is None or h.empty:
        empty()
        return
    with guard("Validación"):
        v = h["resultado_validacion"].fillna("Sin validar").value_counts()
        cert_m, n_m = fletes_pagados._cert(h)
        aa = a[(a["etd"] <= today()) & (a["flete_pagado"] > 0)] if a is not None and len(a) else None
        cert_a = float(aa["flete_certificado"].sum() / aa["flete_pagado"].sum()) if aa is not None and len(aa) else float("nan")
        st_m, b_m = cert_status(cert_m) if n_m >= settings.MIN_SAMPLE else ("", "")
        kpi_row([
            KPI("Validados", fmt.fmt_int(v.get("Validado", 0)), sub=fmt.fmt_pct(v.get("Validado", 0) / len(h))
                + " de los embarques marítimos"),
            KPI("Observados", fmt.fmt_int(v.get("Observado", 0)), status="warn" if v.get("Observado", 0) else "",
                sub="Con diferencia o datos faltantes"),
            KPI("Certificado · marítimo", fmt.fmt_pct(cert_m), status=st_m, badge=b_m,
                sub=cert_sub() + " · certificado / pagado"),
            _cert_aereo(aa, cert_a),
        ])
        obs = h[h["resultado_validacion"] == "Observado"].sort_values("etd", ascending=False)
        if len(obs):
            data_table(obs, [
                ColSpec("embarque", "Embarque"), ColSpec("etd", "ETD", "date"), ColSpec("forwarder", "Forwarder"),
                ColSpec("motivo_observacion", "Motivo", width="medium"),
                ColSpec("flete_pagado", "Flete pagado (USD)", "usd"), ColSpec("flete_cotizado", "Flete cotizado (USD)", "usd"),
                ColSpec("gastos_locales", "Locales (USD)", "usd"), ColSpec("responsable", "Responsable"),
            ], key="co_obs", filename="fletes_observados")
        with st.expander("Por forwarder: costo, vs mercado, certificado y observados"):
            data_table(fletes_pagados.by_forwarder(h), [
                ColSpec("forwarder", "Forwarder"), ColSpec("embarques", "Embarques", "int"),
                ColSpec("contenedores", "Cont.", "int"), ColSpec("costo_total", "Costo total (USD)", "usd"),
                ColSpec("flete_ctnr", "Flete / cont. (USD)", "usd"), ColSpec("locales_ctnr", "Locales / cont. (USD)", "usd"),
                ColSpec("vs_mercado", "vs mercado", "pct"), ColSpec("certificado", "% certificado", "pct"),
                ColSpec("observados", "Observados", "int"),
            ], key="co_ffww", filename="fletes_por_forwarder", search=False)
