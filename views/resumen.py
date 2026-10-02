"""Resumen ejecutivo: nuestro año, ¿cumplimos SLA?, ¿cuánto pagamos y capturamos?"""
from __future__ import annotations

import numpy as np
import pandas as pd
import streamlit as st

from components import sla as sla_view
from components.layout import chart_title, empty, guard, require, section
from config import settings
from utils import calculations as calc
from utils import formatting as fmt
from utils import productos, sla
from components.kpi_cards import KPI, kpi_row
from components.tables import ColSpec, data_table
from utils import anio
from views._common import ctx, filtered, periodo_txt, split_html, today


def render_anio(bundle, filters) -> None:
    """Nuestro año: lo embarcado en el año calendario, total y mes a mes."""
    t = today()
    hist = filtered(bundle, "historicas", filters, use_period=False)
    section(f"Nuestro {t.year}",
            f"Embarques de Reservas Históricas con ETD en {t.year}, por mes de ETD. "
            "Contenedores: solo marítimos. Estructura: sobre los embarques con monoproveedor / consolidado cargado.")
    if hist is None or hist.empty:
        empty()
        return
    d = anio.del_anio(hist, t.year)
    if d.empty:
        empty(f"Sin embarques con ETD en {t.year} para los filtros seleccionados.")
        return
    tab = anio.mensual(d)
    tot = tab.iloc[-1]
    kpi_row([
        KPI("Embarques", fmt.fmt_int(tot["embarques"])),
        KPI("Contenedores", fmt.fmt_int(tot["contenedores"]), sub="marítimos"),
        KPI("FOB SIMI", fmt.fmt_usd(tot["fob_simi"])),
        KPI("Volumen", fmt.fmt_int(tot["m3"]), unit="m³"),
    ])
    colors = dict(zip(anio.MEDIOS, settings.SERIES + ["#8A8F98"]))
    medios = split_html([(m, int((d["medio"] == m).sum()), colors[m],
                          f" · {fmt.fmt_int(d.loc[d['medio'] == m, 'cnt_mar'].sum())} cont." if m == "Marítimo" else "")
                         for m in anio.medios_presentes(d)])
    est = split_html([(e, int((d["estructura"] == e).sum()), c, "")
                      for e, c in zip(anio.ESTRUCTURAS, (settings.SERIES[0], settings.SERIES[2]))])
    st.markdown(f"""<div class="today-grid even">
          <div class="panel"><div class="panel-title">Medio de envío</div>{medios}</div>
          <div class="panel"><div class="panel-title">Estructura</div>{est}</div>
        </div>""", unsafe_allow_html=True)

    show = tab.copy()
    this_month = t.to_period("M").to_timestamp()
    show["mes_txt"] = [f"Total {t.year}" if pd.isna(m) else
                       fmt.fmt_month(m, long=True) + (" · en curso" if m == this_month else "")
                       for m in show["mes"]]
    cols = [ColSpec("mes_txt", "Mes", width="medium"), ColSpec("embarques", "Embarques", "int"),
            ColSpec("contenedores", "Contenedores", "int"), ColSpec("fob_simi", "FOB SIMI (USD)", "usd"),
            ColSpec("m3", "M3", "num"), ColSpec("pct_mono", "% Mono", "pct"), ColSpec("pct_cons", "% Consolidado", "pct")]
    cols += [ColSpec(f"pct_{m}", f"% {m}", "pct") for m in anio.medios_presentes(d)]
    data_table(show, cols, key="anio", filename=f"embarques_{t.year}", search=False)


def render() -> None:
    bundle, filters = ctx()

    # ------------------------------------------------------------------ año
    with guard("Nuestro año"):
        render_anio(bundle, filters)

    # ------------------------------------------------------------------ SLA
    periodo = periodo_txt(filters)
    section("¿Estamos cumpliendo SLA?",
            f"Embarques que zarparon {periodo}, mes a mes. El mes en curso se muestra rayado porque está "
            f"incompleto. Objetivo de cumplimiento: {fmt.fmt_pct(settings.CUMPLIMIENTO_OBJETIVO)}. "
            "La apertura por mes cerrado, estructura, puerto y forwarder está en Lead times y SLA.")
    c_mar, c_aer = st.columns(2, gap="medium")
    with c_mar:
        st.markdown('<div class="row-label">Marítimo</div>', unsafe_allow_html=True)
        if require(bundle, "historicas") is not None:
            with guard("SLA marítimo"):
                t = today()
                hist = filtered(bundle, "historicas", filters)
                z = sla.zarpados(hist, t)
                pct, n = calc.cumplimiento(z["dias_consolidacion"], z["sla_consolidacion"])
                n_ok = int((z["dias_consolidacion"] <= z["sla_consolidacion"]).sum())
                last = t.to_period("M").to_timestamp() - pd.offsets.MonthBegin(1)
                cl = sla.celda(z[calc.month_start(z["etd"]) == last], "cumplimiento")
                st.markdown(
                    f'<div class="panel"><div class="panel-title">Cumplimiento SLA de consolidación · período</div>'
                    f'<div class="mode-head"><span class="big">'
                    f'{fmt.fmt_pct(pct) if n >= settings.MIN_SAMPLE else "—"}</span>'
                    f'<span class="lbl">{fmt.fmt_int(n_ok)} de {fmt.fmt_int(n)} embarques dentro del SLA · '
                    f'{fmt.fmt_month(last, long=True).split()[0].lower()}: {fmt.fmt_pct(cl.valor)}</span></div></div>',
                    unsafe_allow_html=True)
                chart_title("Cumplimiento mes a mes", "% de embarques con consolidación dentro del SLA")
                sla_view.compliance_chart(sla.monthly_compliance(z), t, key="res_sla_mar")
    with c_aer:
        st.markdown('<div class="row-label">Aéreo</div>', unsafe_allow_html=True)
        if require(bundle, "aereos") is not None:
            with guard("SLA aéreo"):
                t = today()
                a = sla_view.air_zarpados(filtered(bundle, "aereos", filters), t)
                vig = a[a["sla_vigente"] & a["sla_aereo"].notna()]
                pct_a, n_a = calc.cumplimiento(vig["dias_aereo"], vig["sla_aereo"])
                ok_a = int((vig["dias_aereo"] <= vig["sla_aereo"]).sum())
                st.markdown(
                    f'<div class="panel"><div class="panel-title">Cumplimiento SLA aéreo · desde '
                    f'{settings.SLA_AEREO_DESDE:%d/%m/%Y}</div>'
                    f'<div class="mode-head"><span class="big">'
                    f'{fmt.fmt_pct(pct_a) if n_a >= settings.MIN_SAMPLE else "—"}</span>'
                    f'<span class="lbl">{fmt.fmt_int(ok_a)} de {fmt.fmt_int(n_a)} embarques dentro del SLA · '
                    f'cada embarque contra el SLA de su tipo</span></div></div>',
                    unsafe_allow_html=True)
                chart_title("Cumplimiento mes a mes",
                            "% de embarques dentro del SLA de su tipo de negocio. En gris, meses anteriores "
                            "al SLA (referencia)")
                sla_view.air_compliance_chart(a, t, key="res_sla_aer")

    # ------------------------------------------------------------------ objetivo −15 %
    if bundle.get("emb_hist") is not None:
        section("Objetivo −15 % · consolidación de SKU nuevos y top ranking",
                "Tiempo de consolidación por SO, separado en monoproveedor y consolidado. "
                "La evolución mes a mes está en Lead times y SLA.")
        with guard("Objetivo −15 %"):
            d = productos.base_lines(bundle.get("emb_hist"), today())
            sla_view.productos_table(productos.summary(d, today()))

    # ------------------------------------------------------------------ fletes
    if bundle.get("historicas") is not None:
        render_fletes(bundle, filters)


def render_fletes(bundle, filters) -> None:
    """¿Cuánto pagamos y cuánto capturamos? Resumen de la gestión de fletes."""
    import plotly.graph_objects as go

    from components import charts
    from components.kpi_cards import KPI, kpi_row
    from config.mappings import MODOS_MARITIMOS
    from utils import freight

    periodo = periodo_txt(filters)
    section("¿Cuánto pagamos y cuánto capturamos?",
            f"Embarques que zarparon {periodo}. El detalle por forwarder y por embarque está en "
            "Fletes y gastos pagados; las tarifas, en Cotizaciones.")
    with guard("Fletes y gastos"):
        t = today()
        cot = bundle.get("cotizaciones")
        h = filtered(bundle, "historicas", filters)
        h = h[h["modo"].isin(MODOS_MARITIMOS) & (h["etd"] <= t) & (h["flete_pagado"] > 0)]
        h = freight.add_market_reference(h, cot)
        a = bundle.get("aereos")
        a = filtered(bundle, "aereos", filters) if a is not None else pd.DataFrame()
        if len(a):
            a = a[(a["etd"] <= t) & (a["flete_pagado"] > 0)]

        flete = h["flete_pagado"].sum() + (a["flete_pagado"].sum() if len(a) else 0)
        origen = h["gastos_origen"].clip(lower=0).sum() + (a["gastos_origen"].clip(lower=0).sum() if len(a) else 0)
        destino = h["gastos_locales"].clip(lower=0).sum() + (a["gastos_locales"].clip(lower=0).sum() if len(a) else 0)
        total = flete + origen + destino

        ahorro = freight.savings_vs_market(h)
        n_ref = int(ahorro.notna().sum())
        ah_total = float(ahorro.sum())
        mercado_total = float((h["mercado_mes"] * h["contenedores"]).sum())
        ah_pct = ah_total / mercado_total if mercado_total else np.nan


        ok_cert = h["flete_pagado"] > 0
        cert = (h.loc[ok_cert, "flete_certificado"].sum() / h.loc[ok_cert, "flete_pagado"].sum()
                if ok_cert.any() else np.nan)
        cert_ok = cert == cert and cert >= settings.KPI_CERTIFICACION_TARGET
        nor = freight.nor_savings(h)
        nor_ok = nor.dropna(subset=["ahorro"]) if len(nor) else nor

        kpi_row([
            KPI("Costo logístico pagado", fmt.fmt_usd(total),
                sub=f"Flete <b>{fmt.fmt_usd(flete)}</b> · origen {fmt.fmt_usd(origen)} · destino {fmt.fmt_usd(destino)}"),
            KPI("Ahorro vs mercado", fmt.fmt_usd(ah_total) if n_ref else "—",
                status=("ok" if ah_total >= 0 else "bad") if n_ref >= settings.MIN_SAMPLE else "",
                sub=(f"Flete marítimo {fmt.fmt_pct(-ah_pct, signed=True)} vs mediana de mercado · "
                     f"{fmt.fmt_int(n_ref)} embarques") if n_ref else "Sin cotizaciones para comparar"),
            KPI("Ahorro por usar 40 NOR", fmt.fmt_usd(nor_ok["ahorro"].sum()) if len(nor_ok) else "—",
                status=("ok" if nor_ok["ahorro"].sum() >= 0 else "bad") if len(nor_ok) else "",
                sub=(f"<b>{fmt.fmt_int(nor_ok['contenedores'].sum())}</b> contenedores 40 NOR vs 40 ST/HQ del mismo mes"
                     + (f" · por m³: {fmt.fmt_usd(nor_ok['ahorro_m3'].sum())}" if nor_ok["ahorro_m3"].notna().any() else ""))
                if len(nor_ok) else "Sin embarques en 40 NOR"),
            KPI("Flete certificado", fmt.fmt_pct(cert),
                status="ok" if cert_ok else ("bad" if cert == cert else ""),
                sub=f"Objetivo ≥ {fmt.fmt_pct(settings.KPI_CERTIFICACION_TARGET)}"),
        ])
        con_origen = int((h["gastos_origen"] > 0).sum())
        st.caption(f"Gastos en origen cargados en {fmt.fmt_int(con_origen)} de {fmt.fmt_int(len(h))} embarques "
                   "marítimos. «Ahorro vs mercado» compara el flete por contenedor con la mediana de las "
                   "cotizaciones del mismo mes, tipo de contenedor y destino. «Ahorro por usar 40 NOR» compara el flete pagado de cada "
                   "contenedor 40 NOR con la mediana pagada por un 40 ST/HQ ese mismo mes; «por m³» corrige por la "
                   "menor capacidad del 40 NOR.")

        c1, c2 = st.columns(2, gap="medium")
        with c1:
            chart_title("Costo pagado por mes", "USD · total pagado (suma), marítimo y aéreo, por mes de ETD")
            parts = []
            for df_ in (h, a):
                if len(df_):
                    parts.append(df_.assign(mes=calc.month_start(df_["etd"]))[
                        ["mes", "flete_pagado", "gastos_origen", "gastos_locales"]])
            if not parts:
                empty()
            else:
                mm = pd.concat(parts).groupby("mes").sum(min_count=1).clip(lower=0).sort_index().tail(12)
                x = [fmt.fmt_month(m) for m in mm.index]
                fig = go.Figure()
                for i, (col, lab) in enumerate((("flete_pagado", "Flete"), ("gastos_origen", "Gastos en origen"),
                                                ("gastos_locales", "Gastos en destino"))):
                    fig.add_bar(x=x, y=mm[col].fillna(0), name=lab, marker=dict(color=settings.SERIES[i], cornerradius=3),
                                hovertemplate=f"%{{x}} · {lab}: USD %{{y:,.0f}}<extra></extra>")
                fig.update_layout(barmode="stack")
                charts.theme(fig, height=300, y_title="USD")
                charts.show(fig, key="res_costo_mes")
        with c2:
            chart_title("Ahorro vs mercado por mes", "USD · flete marítimo. Positivo = pagamos menos que la mediana de mercado")
            hh = h.assign(ah=ahorro, mes=calc.month_start(h["etd"])).dropna(subset=["ah"])
            if hh.empty:
                empty("Sin cotizaciones para comparar.")
            else:
                g = hh.groupby("mes")["ah"].agg(["sum", "size"]).sort_index().tail(12)
                fig = go.Figure(go.Bar(
                    x=[fmt.fmt_month(m) for m in g.index], y=g["sum"],
                    marker=dict(color=[settings.COLORS["green"] if v >= 0 else settings.COLORS["red"] for v in g["sum"]],
                                cornerradius=3),
                    text=[fmt.fmt_usd(v) for v in g["sum"]], textposition="outside", cliponaxis=False,
                    textfont=dict(size=11, color=settings.COLORS["slate"]), customdata=g["size"],
                    hovertemplate="%{x}<br>USD %{y:,.0f}<br>Embarques: %{customdata}<extra></extra>"))
                charts.theme(fig, height=300, y_title="USD", legend=False)
                fig.update_yaxes(rangemode="normal", zeroline=True, zerolinecolor=settings.COLORS["grey"])
                charts.show(fig, key="res_ahorro_mes")
