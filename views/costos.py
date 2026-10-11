"""Costos y captura (nivel 2): cuánto pagamos, cuánto capturamos y dónde hay oportunidad.

Reúne lo que antes estaba en «Fletes y gastos pagados» y «Cotizaciones», en cuatro pestañas:
Gasto · Captura · Tarifas y negociación · Validación.
"""
from __future__ import annotations

import pandas as pd
import plotly.graph_objects as go
import streamlit as st

from components import charts
from components import sla as sla_view
from components.kpi_cards import KPI, cert_status, cert_sub, kpi_row
from components.layout import chart_title, empty, guard, require, section
from components.tables import ColSpec, data_table, solo_descarga
from config import settings
from config.mappings import MODOS_MARITIMOS
from utils import calculations as calc
from utils import bandeja
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
    h_all, _, p_all = _datos(bundle, filters, use_period=False)
    ventana = _ventana_prev(filters, t)
    p_prev = p_all[p_all["etd"].between(*ventana)] if ventana else None
    # Solo se dibuja la vista elegida (con pestañas se calculaban todas en cada interacción).
    vistas = {"gasto": "Gasto", "captura": "Captura", "tarifas": "Tarifas, negociación y validación",
              "contenedores": "Contenedores y cargas especiales"}
    pedida = st.query_params.get("vista")
    pedida = "tarifas" if pedida == "validacion" else pedida
    if pedida in vistas and pedida != st.session_state.get("_costos_qp"):
        st.session_state["costos_vista"] = pedida
    st.session_state.setdefault("costos_vista", "gasto")
    vista = st.segmented_control("Vista", list(vistas), format_func=vistas.get, key="costos_vista",
                                 label_visibility="collapsed") or "gasto"
    st.session_state["_costos_qp"] = vista
    if st.query_params.get("vista") != vista:
        st.query_params["vista"] = vista
    if vista == "gasto":
        _gasto(bundle, h, a, p, p_all, p_prev, h_all)
    elif vista == "captura":
        _captura(bundle, filters, h, ventana)
    elif vista == "tarifas":
        _tarifas(bundle, h)
        _validacion(h, a)
    else:
        from views import resumen
        with guard("Contenedores"):
            resumen.render_contenedores(bundle, filters)
        resumen.render_especiales(bundle, filters)


# ---------------------------------------------------------------------------
def _gasto(bundle, h, a, p, p_all, p_prev, h_all=None) -> None:
    from utils import panorama as pan
    t = today()
    section("¿Cuánto pagamos?", "Embarques marítimos y aéreos zarpados en el período, con flete pagado. Costo total = "
                                "flete internacional + gastos en origen + gastos en destino.")
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
        def parte(col):
            v = p[col].clip(lower=0).fillna(0)
            mar, aer = float(v[p["medio"] == "Marítimo"].sum()), float(v[p["medio"] == "Aéreo"].sum())
            return mar + aer, f"marítimo {fmt.fmt_usd(mar)} · aéreo {fmt.fmt_usd(aer)}"
        tot_costo = float(p["costo"].sum())
        partes = {}
        for col, nombre, ayuda in (
                ("flete_pagado", "Flete internacional pagado", "Columna «Flete Int PAGADO» (marítimo) y «Flete "
                 "total» (aéreo) de los embarques zarpados del período."),
                ("gastos_origen", "Gastos en origen", "«TOTAL GASTOS ORIGEN» (marítimo) y «Gastos en Origen» (aéreo)."),
                ("gastos_locales", "Gastos en destino (locales)", "«Gastos Locales» de marítimo y aéreo.")):
            v, sub = parte(col)
            partes[col] = KPI(nombre, fmt.fmt_usd(v), help=ayuda,
                              sub=f"<b>{fmt.fmt_pct(v / tot_costo if tot_costo else float('nan'))}</b> del costo · {sub}")
        kpi_row(list(partes.values()) + [
            KPI("Costo logístico total", ind.valor, sub=ind.sub, delta=ind.delta, tono=ind.tono,
                help=ind.ayuda + f" {fmt.fmt_int(len(p))} embarques con flete pagado.")])
        kpi_row([
            KPI("Flete por contenedor", fmt.fmt_usd(fl.median, compact=False) if fl.enough else "—",
                sub=f"Marítimo · mediana · P25–P75 {fmt.fmt_usd(fl.p25, compact=False)}–"
                    f"{fmt.fmt_usd(fl.p75, compact=False)}" if fl.enough else "Marítimo"),
            KPI("Aéreo · USD por kg", f"USD {fmt.fmt_num(kg.median, 1)}" if kg.enough else "—",
                sub=f"Mediana sobre chargeable · n={fmt.fmt_int(kg.n)}" if kg.enough else "Sin chargeable cargado"),
            KPI("Costo por m³", fmt.fmt_usd(cm3.median, compact=False) if cm3.enough else "—",
                sub="Marítimo · mediana del costo total / m³"),
        ], columns=4)
    with guard("Flete por contenedor mes a mes"):
        t = today()
        section(f"Flete por contenedor · mes a mes {t.year}",
                "Mediana del flete pagado por contenedor (marítimo, todos los destinos del filtro), variación contra el "
                f"mes anterior y contra el mismo mes de {t.year - 1}. Rojo = subió; verde = bajó. * mes en curso.")
        tipo = st.segmented_control("Contenedor", ["40ST/40HQ", "20ST", "40NOR"], default="40ST/40HQ",
                                    key="co_flete_mes_tipo", label_visibility="collapsed") or "40ST/40HQ"
        sla_view.flete_mes_matrix(cs.flete_mes(h_all if h_all is not None else h, tipo, t.year), t)

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
    section("¿Cuánto capturamos?", "Plata que dejamos de pagar gracias a una decisión del equipo.")
    st.markdown(
        '<div class="panel" style="margin-bottom:.8rem"><div class="panel-title">Cómo se lee</div>'
        '<div style="font-size:.88rem;line-height:1.55;color:var(--ink-2)">'
        '<b>1 · Negociación de tarifas.</b> El agente cotiza una tarifa, la negociamos y sale más barata. Captura = '
        '(tarifa original − tarifa negociada) × contenedores. <i>Ej.: cotizó USD 2.000, cerramos en USD 1.800 y '
        'mandamos 3 contenedores → USD 600.</i> Solo cuenta si lo que pagamos coincide con la tarifa negociada.<br>'
        '<b>2 · Uso de 40 NOR.</b> Mandar la carga en 40 NOR en vez de 40 ST/HQ. Captura = (lo que pagamos en la '
        'mediana por un 40 ST/HQ ese mes − lo que pagamos por el 40 NOR) × contenedores. <i>Ej.: el 40 HQ salió USD '
        '1.400, el 40 NOR USD 1.100 → USD 300 por contenedor.</i> Puede dar negativo si ese mes el 40 NOR salió más caro.'
        '<br><b>Captura total = 1 + 2.</b> La comparación contra el mercado está en «Tarifas y negociación» y no se suma.'
        '</div></div>', unsafe_allow_html=True)
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
            KPI("Captura total (1 + 2)", fmt.fmt_usd(r["total"]), delta=prev_txt,
                tono="good" if prev_txt.startswith("▲") else ("bad" if prev_txt.startswith("▼") else "neutral"),
                sub=(f"negociación {fmt.fmt_usd(r['negociacion'])}" if hay_sin else
                     "negociación: falta la solapa sin negociar") + f" · 40 NOR {fmt.fmt_usd(r['nor'])}"),
            KPI("1 · Negociación de tarifas", fmt.fmt_usd(r["negociacion"]) if hay_sin else "—",
                sub=(f"<b>{fmt.fmt_int(r['neg_emb'])}</b> embarques con su tarifa identificada" if hay_sin else
                     "Falta la solapa «Cotizaciones Maritimos SIN NEGOCIAR»"),
                help="(Tarifa sin negociar − tarifa negociada) × contenedores, para los embarques cuyo flete pagado "
                     f"coincide (± {fmt.fmt_pct(cap.TOLERANCIA)}) con una tarifa negociada vigente del mismo forwarder, "
                     "puerto y tipo de contenedor. Los embarques sin coincidencia no suman."),
            KPI("2 · Uso de 40 NOR", fmt.fmt_usd(r["nor"]),
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
    with guard("Captura por trimestre"):
        t = today()
        qq = cap.por_trimestre(casos_neg, nor, t.year)
        q_act = f"Q{(t.month - 1) // 3 + 1}"
        chart_title(f"Resultado por trimestre · {t.year}", "Negociación de tarifas + uso de 40 NOR · * en curso")
        kpi_row([KPI(f"{r['q']}{'*' if r['q'] == q_act else ''} · captura", fmt.fmt_usd(r["total"]),
                     status="ok" if r["total"] > 0 else ("bad" if r["total"] < 0 else ""),
                     sub=f"negociación {fmt.fmt_usd(r['negociacion'])} · 40 NOR {fmt.fmt_usd(r['nor'])} "
                         f"({fmt.fmt_int(r['nor_cont'])} cont.)") for _, r in qq.iterrows()], columns=4)

    with guard("Captura por agente"):
        ag = cap.por_agente(h, casos_neg, nor)
        chart_title("Captura por agente", "Ordenado por captura total del período")
        data_table(ag, [
            ColSpec("agente", "Agente"), ColSpec("negociacion", "1 · Negociación (USD)", "usd"),
            ColSpec("nor", "2 · 40 NOR (USD)", "usd"), ColSpec("total", "Captura total (USD)", "usd"),
            ColSpec("embarques", "Embarques del período", "int"),
            ColSpec("con_tarifa", "Embarques con tarifa negociada", "int"),
        ], key="co_cap_agente", filename="captura_por_agente", search=False)

    with guard("Descargas captura"):
        partes = []
        if len(casos_neg):
            partes.append(casos_neg.assign(v=casos_neg["captura"])[["forwarder", "mes", "v"]])
        if len(nor):
            partes.append(nor.assign(v=nor["ahorro"])[["forwarder", "mes", "v"]])
        if partes:
            mm = pd.concat(partes, ignore_index=True).assign(forwarder=lambda x: x["forwarder"].fillna("Sin agente"))
            pv = mm.pivot_table(index="forwarder", columns="mes", values="v", aggfunc="sum", fill_value=0)
            pv = pv.loc[pv.sum(axis=1).sort_values(ascending=False).index]
            pv.loc["Total"] = pv.sum()
            pv["Total"] = pv.sum(axis=1)
            pv.columns = [fmt.fmt_month(c).capitalize() if c != "Total" else c for c in pv.columns]
            pv = pv.reset_index().rename(columns={"forwarder": "Agente"})
            solo_descarga(pv, [ColSpec("Agente", "Agente")] + [ColSpec(c, c, "usd") for c in pv.columns[1:]],
                          key="co_cap_mes_agente", filename="captura_mes_por_agente",
                          label="Descargar captura mes por agente")
        c1, c2 = st.columns(2, gap="medium")
        with c1:
            solo_descarga(casos_neg, [
                ColSpec("embarque", "Embarque"), ColSpec("etd", "ETD", "date"), ColSpec("forwarder", "Agente"),
                ColSpec("puerto", "Puerto"), ColSpec("tipo_ctnr", "Tipo"), ColSpec("contenedores", "Cont.", "int"),
                ColSpec("flete_original", "Sin negociar (USD)", "usd"),
                ColSpec("flete_negociado", "Negociada (USD)", "usd"), ColSpec("flete_por_ctnr", "Pagado (USD)", "usd"),
                ColSpec("captura", "Captura (USD)", "usd"),
            ], key="co_neg", filename="captura_negociacion", label="Descargar embarques con tarifa negociada")
        with c2:
            solo_descarga(nor, [
                ColSpec("embarque", "Embarque"), ColSpec("etd", "ETD", "date"), ColSpec("forwarder", "Agente"),
                ColSpec("puerto", "Puerto"), ColSpec("contenedores", "Cont.", "int"),
                ColSpec("ref_hq", "Mediana 40 ST/HQ del mes (USD)", "usd"),
                ColSpec("flete_por_ctnr", "Pagado 40 NOR (USD)", "usd"), ColSpec("ahorro", "Ahorro (USD)", "usd"),
            ], key="co_nor", filename="captura_40nor", label="Descargar embarques 40 NOR")


# ---------------------------------------------------------------------------
def _tarifas(bundle, h) -> None:
    from utils import negociar
    t = today()
    dias = settings.NEGOCIAR_VENTANA_DIAS
    cot = bundle.get("cotizaciones")
    section("Cotizaciones: ¿cuál es la menor y con quién negociar?",
            "Tarifas de «Cotizaciones Maritimos Negociado» (destino Argentina) para las rutas que usamos en los "
            f"últimos {dias} días. La mejor tarifa es la menor. Verde = la menor de la ruta; ● = el agente con el que más "
            "embarcamos esa ruta. Por contenedor, en USD.")
    if h is None or h.empty:
        empty()
        return
    with guard("Cotizaciones"):
        cur = negociar.periodo(cot, t, "curso")
        prox = negociar.periodo(cot, t, "proxima")
        rango = lambda c: (f"{c['validez_desde'].min():%d/%m} – {c['validez_hasta'].max():%d/%m}"  # noqa: E731
                           if len(c) else "sin tarifas")
        opciones = {"curso": f"En curso ({rango(cur)})", "proxima": f"Próximas ({rango(prox)})"}
        cual = st.segmented_control("Período", list(opciones), default="curso", format_func=opciones.get,
                                    key="co_cot_periodo", label_visibility="collapsed") or "curso"
        todas = st.toggle("Ver también rutas que no usamos", value=False, key="co_cot_todas")
        m, agentes = negociar.matriz(h, cot, t, cual, dias, solo_nuestras=not todas)
        if m.empty:
            empty("Todavía no hay cotizaciones cargadas para las próximas quincenas." if cual == "proxima" else
                  "No hay cotizaciones vigentes para nuestras rutas.")
        else:
            neg = m[m["estado"] == "Negociar"]
            ahorro_mes = float(((neg["tarifa_principal"] - neg["menor"]) * neg["contenedores"]).sum()) / (dias / 30)
            var = m["var"].median()
            kpi_row([
                KPI("Tarifas recibidas", fmt.fmt_int(len(negociar.periodo(cot, t, cual))),
                    sub=f"de <b>{fmt.fmt_int(len(agentes))}</b> agentes · {opciones[cual].lower()}"),
                KPI("Rutas para negociar", fmt.fmt_int(len(neg)), status="warn" if len(neg) else "ok",
                    sub=f"nuestro agente no tiene la menor · {fmt.fmt_int((m['estado'] == 'Pedir').sum())} sin "
                        "cotización de nuestro agente"),
                KPI("Ahorro si igualan la menor", fmt.fmt_usd(ahorro_mes), sub="por mes, al ritmo de los últimos "
                    f"{dias} días", help="(Tarifa de nuestro agente − menor tarifa) × contenedores por mes, en las rutas "
                                         "para negociar."),
                KPI("Menor tarifa vs período anterior", (("▲ " if var > 0 else "▼ ") + fmt.fmt_pct(abs(var)))
                    if var == var else "—", status=("bad" if var > 0 else "ok") if var == var else "",
                    sub="mediana de las rutas", help="Cuánto cambió la menor tarifa de cada ruta contra el período "
                                                     "anterior (para «Próximas», contra el en curso)."),
            ])
            sla_view.cotizaciones_matrix(m, agentes)
            solo_descarga(m, [ColSpec("puerto", "Puerto"), ColSpec("tipo_ctnr", "Contenedor"),
                              ColSpec("contenedores", f"Cont. {dias} d", "int"), ColSpec("agente", "Agente principal")]
                          + [ColSpec(a, a, "usd") for a in agentes]
                          + [ColSpec("menor", "Menor (USD)", "usd"), ColSpec("menor_agente", "La ofrece"),
                             ColSpec("menor_linea", "Línea"), ColSpec("var", "vs anterior", "pct"),
                             ColSpec("negociar", "Con quién negociar")],
                          key=f"co_cot_{cual}", filename=f"cotizaciones_{cual}_{t:%Y%m%d}",
                          label="Descargar cuadro")
    with st.expander("Todas las cotizaciones: mapa de tarifas y evolución del mercado"):
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
    section("Validación de fletes y certificación", "Resultado de la validación de Logística Internacional y "
                                                    "flete certificado por fuera.")
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
                sub=f"Con diferencia o datos faltantes · <b>{fmt.fmt_int(v.get('Sin validar', 0))}</b> sin validar"),
            KPI("Certificado · marítimo", fmt.fmt_pct(cert_m), status=st_m, badge=b_m,
                sub=cert_sub() + " · certificado / pagado"),
            _cert_aereo(aa, cert_a),
        ])
        cols = [ColSpec("embarque", "Embarque"), ColSpec("etd", "ETD", "date"), ColSpec("forwarder", "Agente"),
                ColSpec("responsable", "Responsable (analista)"), ColSpec("resultado_validacion", "Resultado"),
                ColSpec("motivo_observacion", "Motivo", width="medium"),
                ColSpec("flete_pagado", "Flete pagado (USD)", "usd"), ColSpec("flete_cotizado", "Flete cotizado (USD)", "usd"),
                ColSpec("gastos_origen", "Origen (USD)", "usd"), ColSpec("gastos_locales", "Locales (USD)", "usd")]
        pend = bandeja.pendientes_validar(h, today())
        obs = h[h["resultado_validacion"] == "Observado"].sort_values("etd", ascending=False)
        c1, c2 = st.columns(2, gap="medium")
        with c1:
            solo_descarga(pend, cols, key="co_pend", filename=f"fletes_pendientes_de_validar_{today():%Y%m%d}",
                          label="Descargar pendientes de validar")
            st.caption("Para reclamar a cada analista: embarques zarpados sin resultado de validación.")
        with c2:
            solo_descarga(obs, cols, key="co_obs", filename=f"fletes_observados_{today():%Y%m%d}",
                          label="Descargar observados")
            st.caption("Para reclamar a cada agente el ajuste. También están en la Bandeja de acción.")
