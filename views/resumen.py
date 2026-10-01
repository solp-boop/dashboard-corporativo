"""Resumen ejecutivo: ¿cómo estamos?, ¿cumplimos SLA?, ¿qué requiere atención?"""
from __future__ import annotations

import numpy as np
import pandas as pd
import streamlit as st

from components import sla as sla_view
from components.layout import chart_title, empty, guard, require, section
from components.tables import ColSpec, data_table
from config import settings
from utils import calculations as calc
from utils import formatting as fmt
from utils import productos, sla
from views._common import ctx, en_curso, filtered, kpis_en_curso, periodo_txt, today


def alerts(res: pd.DataFrame) -> pd.DataFrame:
    """Embarques en curso que requieren acción, con el motivo."""
    t = today()
    horizon = t + pd.Timedelta(days=settings.ALERT_HORIZON_DAYS)
    upcoming = res["etd"].between(t, horizon)
    reasons = pd.Series([[] for _ in range(len(res))], index=res.index)

    def add(mask, text):
        for i in res.index[mask.fillna(False)]:
            reasons[i] = reasons[i] + [text if isinstance(text, str) else text(res.loc[i])]

    mar = res["grupo_modo"] == "Marítimo" if "grupo_modo" in res else pd.Series(True, index=res.index)
    add(upcoming & ~res["etd_ok"], "ETD sin confirmar por el forwarder")
    docs_missing = mar & ((res["draft_bl"].fillna("NO").astype(str).str.upper() != "SI") |
                          (res["pl_final"].fillna("NO").astype(str).str.upper() != "SI"))
    sailed = res["etd"].between(t - pd.Timedelta(days=30), t - pd.Timedelta(days=3))
    add(sailed & docs_missing, "Zarpó hace más de 3 días sin Draft BL / Packing list final")
    future = res["etd"] >= t
    add(future & mar & (res["estado_consolidacion"] == calc.SEMAFORO_BAD),
        lambda r: f"Consolidación proyectada {fmt.fmt_int(r['dias_consolidacion'])} d "
                  f"(SLA {fmt.fmt_int(r['sla_consolidacion'])} d)")
    add(res["etd"].isna() & res["f_instruccion"].notna(), "Instruido sin ETD cargado")

    out = res[reasons.map(len) > 0].copy()
    out["motivo"] = reasons[out.index].map(" · ".join)
    out["n_motivos"] = reasons[out.index].map(len)
    days_to = (out["etd"] - t).dt.days
    out["prioridad"] = np.where(days_to.le(3) | (out["n_motivos"] >= 2), "Alta", "Media")
    return out.sort_values(["prioridad", "etd"], ascending=[True, True])


def render() -> None:
    bundle, filters = ctx()

    # ------------------------------------------------------------------ hoy
    section("¿Cómo estamos hoy?")
    res = None
    with guard("Operación en curso"):
        res, info = en_curso(bundle, filters)
        if res.empty:
            empty()
        else:
            kpis_en_curso(res, info)

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

    # ------------------------------------------------------------------ atención
    section("¿Qué operaciones requieren atención?",
            f"ETD en los próximos {settings.ALERT_HORIZON_DAYS} días sin confirmar, zarpados sin documentación, "
            "consolidación proyectada fuera de SLA o instruidos sin ETD.")
    if res is not None:
        with guard("Alertas"):
            al = alerts(res)
            if al.empty:
                empty("No hay alertas para los filtros seleccionados.")
            else:
                data_table(al, [
                    ColSpec("prioridad", "Prioridad"),
                    ColSpec("embarque", "Embarque"),
                    ColSpec("grupo_modo", "Modo"),
                    ColSpec("motivo", "Motivo", width="large"),
                    ColSpec("etd", "ETD", "date"),
                    ColSpec("forwarder", "Forwarder"),
                    ColSpec("puerto", "Puerto"),
                    ColSpec("responsable", "Responsable"),
                    ColSpec("m3", "M3", "num"),
                    ColSpec("estado_consolidacion", "Consolidación", "status"),
                ], key="alertas", filename="alertas_embarques")


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

        neg = freight.negotiation(cot, bundle.get("cot_sin_negociar"))
        if len(neg) and filters.has_period:
            if filters.start:
                neg = neg[neg["validez_desde"] >= pd.Timestamp(filters.start)]
            if filters.end:
                neg = neg[neg["validez_desde"] <= pd.Timestamp(filters.end)]
        neg = neg[neg["validez_desde"] <= t] if len(neg) else neg
        mej = neg[neg["rebaja"] > 0] if len(neg) else neg

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
                sub=(f"Flete marítimo {fmt.fmt_pct(-ah_pct, signed=True)} vs promedio de mercado · "
                     f"{fmt.fmt_int(n_ref)} embarques") if n_ref else "Sin cotizaciones para comparar"),
            KPI("Rebaja negociada", fmt.fmt_pct(mej["rebaja_pct"].median()) if len(mej) else "—",
                sub=(f"<b>{fmt.fmt_int(len(mej))}</b> tarifas mejoradas · mediana "
                     f"{fmt.fmt_usd(mej['rebaja'].median(), compact=False)} por contenedor") if len(mej)
                else "Sin tarifas renegociadas en el período"),
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
                   "marítimos. «Ahorro vs mercado» compara el flete por contenedor con el promedio de las "
                   "cotizaciones del mismo mes, tipo de contenedor y destino. «Rebaja negociada» compara cada "
                   "tarifa negociada con la original del forwarder. «Ahorro por usar 40 NOR» compara el flete pagado de cada "
                   "contenedor 40 NOR con la mediana pagada por un 40 ST/HQ ese mismo mes; «por m³» corrige por la "
                   "menor capacidad del 40 NOR.")

        c1, c2 = st.columns(2, gap="medium")
        with c1:
            chart_title("Costo pagado por mes", "USD · marítimo y aéreo, por mes de ETD")
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
            chart_title("Ahorro vs mercado por mes", "USD · flete marítimo. Positivo = pagamos menos que el promedio")
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
