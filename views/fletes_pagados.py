"""Fletes y gastos pagados: cuánto pagamos, a quién, y cómo se compara con el mercado."""
from __future__ import annotations

import numpy as np
import pandas as pd
import plotly.graph_objects as go
import streamlit as st

from components import charts
from components.kpi_cards import KPI, cert_status, cert_sub, kpi_row
from components.layout import chart_title, coverage, empty, filter_notes, guard, require, section
from components.tables import ColSpec, data_table
from config import settings
from config.mappings import MODOS_MARITIMOS
from utils import calculations as calc
from utils import formatting as fmt
from utils import freight
from views._common import ctx, filtered, month_labels, today

TIPOS = ["40ST/40HQ", "20ST", "40NOR"]
COST_PARTS = [("flete_pagado", "Flete internacional"), ("gastos_locales", "Gastos locales ARG"),
              ("gastos_origen", "Gastos en origen")]


def _cert(d: pd.DataFrame) -> tuple[float, int]:
    ok = d["flete_pagado"] > 0
    pag = d.loc[ok, "flete_pagado"].sum()
    return (d.loc[ok, "flete_certificado"].sum() / pag if pag else np.nan), int(ok.sum())


def by_forwarder(d: pd.DataFrame) -> pd.DataFrame:
    rows = []
    for ffww, g in d.groupby("forwarder"):
        cert, _ = _cert(g)
        val = g["resultado_validacion"].dropna()
        rows.append({
            "forwarder": ffww, "embarques": len(g), "contenedores": g["contenedores"].sum(),
            "flete_total": g["flete_pagado"].sum(min_count=1), "costo_total": g["costo_total"].sum(min_count=1),
            "flete_ctnr": g["flete_por_ctnr"].median(), "locales_ctnr": g["locales_por_ctnr"].median(),
            "costo_m3": g["costo_por_m3"].median(), "vs_mercado": freight.vs_mercado_ponderado(g)[0],
            "certificado": cert, "observados": int((val == "Observado").sum()),
        })
    return pd.DataFrame(rows).sort_values("costo_total", ascending=False) if rows else pd.DataFrame()


def render() -> None:
    bundle, filters = ctx()
    base = require(bundle, "historicas")
    if base is None:
        return
    d = filtered(bundle, "historicas", filters)
    d = d[d["modo"].isin(MODOS_MARITIMOS) & (d["etd"] <= today())]
    d = freight.add_market_reference(d, bundle.get("cotizaciones"))
    filter_notes(base, filters, "Reservas Históricas")
    st.caption("Embarques marítimos ya zarpados (Reservas Históricas). Los montos por contenedor dividen el total "
               "del embarque por la cantidad de contenedores. «vs mercado» compara el flete pagado con la mediana "
               "de las cotizaciones del mismo mes y tipo de contenedor.")
    con_flete = d[d["flete_pagado"] > 0]
    if d.empty:
        empty()
        return

    section("¿Cuánto pagamos?")
    with guard("KPIs de costos"):
        cert, n_cert = _cert(d)
        s_cert, b_cert = (cert_status(cert)
                          if n_cert >= settings.MIN_SAMPLE else ("", ""))
        fl = calc.describe(con_flete["flete_por_ctnr"])
        vm_pct, vm_n = freight.vs_mercado_ponderado(d)
        cm3 = calc.describe(con_flete["costo_por_m3"])
        llen = calc.describe(d["indice_carga"])
        kpi_row([
            KPI("Costo logístico total", fmt.fmt_usd(con_flete["costo_total"].sum()),
                sub=f"Flete <b>{fmt.fmt_usd(con_flete['flete_pagado'].sum())}</b> · "
                    f"locales {fmt.fmt_usd(con_flete['gastos_locales'].sum())} · "
                    f"origen {fmt.fmt_usd(con_flete['gastos_origen'].sum())}"),
            KPI("Flete por contenedor", fmt.fmt_usd(fl.median, compact=False) if fl.enough else "—",
                sub=f"Mediana · P25–P75 {fmt.fmt_usd(fl.p25, compact=False)}–{fmt.fmt_usd(fl.p75, compact=False)}"
                if fl.enough else "Sin datos suficientes"),
            KPI("Pagado vs mercado", fmt.fmt_pct(vm_pct, signed=True) if vm_n >= settings.MIN_SAMPLE else "—",
                status=("ok" if vm_pct <= 0 else "warn") if vm_n >= settings.MIN_SAMPLE else "",
                sub=f"Total pagado vs mercado, por contenedor · {fmt.fmt_int(vm_n)} embarques con cotización del mes"),
            KPI("Costo por m³", fmt.fmt_usd(cm3.median, compact=False) if cm3.enough else "—",
                sub=f"Mediana · llenado de contenedor {fmt.fmt_pct(llen.median)}" if llen.enough else "Mediana"),
            KPI("Flete certificado", fmt.fmt_pct(cert) if n_cert >= settings.MIN_SAMPLE else "—",
                status=s_cert, badge=b_cert,
                sub=cert_sub() + " · certificado / pagado"),
        ])
        coverage(len(con_flete), len(d), "embarques con flete pagado cargado")

    c1, c2 = st.columns(2, gap="medium")
    with c1, guard("Costo mensual"):
        chart_title("Costo logístico por mes", "USD por mes de ETD · flete + gastos locales + gastos en origen")
        m = con_flete.assign(mes=calc.month_start(con_flete["etd"]))
        months = sorted(m["mes"].unique())[-12:]
        if not months:
            empty()
        else:
            fig = go.Figure()
            for i, (col, label) in enumerate(COST_PARTS):
                s = m.groupby("mes")[col].sum().reindex(months).fillna(0)
                if s.sum() == 0:
                    continue
                fig.add_bar(x=month_labels(pd.Series(months)), y=s.values, name=label,
                            marker=dict(color=settings.SERIES[i], cornerradius=3),
                            hovertemplate=f"%{{x}} · {label}: USD %{{y:,.0f}}<extra></extra>")
            fig.update_layout(barmode="stack")
            charts.theme(fig, y_title="USD")
            charts.show(fig, key="fp_mes")

    with c2, guard("Pagado vs mercado"):
        chart_title("Flete por contenedor: pagado vs mercado",
                    "Destino Argentina · mediana pagada vs mediana de mercado y mejor cotización del mes")
        tipo = st.segmented_control("Tipo de contenedor", TIPOS, default=TIPOS[0], key="fp_tipo",
                                    label_visibility="collapsed") or TIPOS[0]
        t = con_flete[(con_flete["tipo_ctnr"] == tipo) & (con_flete["destino"] == "Argentina")].assign(mes=lambda x: calc.month_start(x["etd"]))
        cot = bundle.get("cotizaciones")
        cot_ar = cot[cot["destino"] == "Argentina"] if cot is not None else None
        mk = freight.market_by_month(cot_ar) if cot_ar is not None else pd.DataFrame()
        mk = mk[mk["tipo_ctnr"] == tipo].set_index("mes") if len(mk) else mk
        months = sorted(t["mes"].unique())[-12:]
        if not months:
            empty(f"No hay embarques {tipo} con flete cargado en el período.")
        else:
            x = month_labels(pd.Series(months))
            paid = t.groupby("mes")["flete_por_ctnr"].median().reindex(months)
            n = t.groupby("mes").size().reindex(months).fillna(0)
            fig = go.Figure()
            fig.add_scatter(x=x, y=paid.values, name="Pagado (mediana)", mode="lines+markers",
                            line=dict(color=settings.SERIES[0], width=2.5), marker=dict(size=8), customdata=n.values,
                            hovertemplate="Pagado: USD %{y:,.0f} (%{customdata} emb.)<extra></extra>")
            if len(mk):
                fig.add_scatter(x=x, y=mk["mercado"].reindex(months).values, name="Mediana de mercado",
                                mode="lines+markers", line=dict(color=settings.SERIES[1], width=2),
                                marker=dict(size=8), hovertemplate="Mercado (mediana): USD %{y:,.0f}<extra></extra>")
                fig.add_scatter(x=x, y=mk["mejor"].reindex(months).values, name="Mejor cotización",
                                mode="lines", line=dict(color=settings.SERIES[2], width=1.5, dash="dash"),
                                hovertemplate="Mejor: USD %{y:,.0f}<extra></extra>")
            charts.theme(fig, y_title="USD por contenedor")
            charts.show(fig, key="fp_vs_mercado")

    section("Ahorro por usar 40 NOR",
            "Cada contenedor 40 NOR contra la mediana pagada por un 40 ST/40 HQ en el mismo mes (Argentina y otros "
            "destinos). «Por m³» corrige por la menor capacidad del 40 NOR.")
    with guard("Ahorro 40 NOR"):
        nor = freight.nor_savings(con_flete)
        nor = nor.dropna(subset=["ahorro"]) if len(nor) else nor
        if nor.empty:
            empty("No hay embarques en 40 NOR con flete pagado en el período.")
        else:
            cap_hq, cap_nor = nor.attrs.get("cap_hq"), nor.attrs.get("cap_nor")
            kpi_row([
                KPI("Ahorro por contenedor", fmt.fmt_usd(nor["ahorro"].sum()),
                    sub=f"<b>{fmt.fmt_int(nor['contenedores'].sum())}</b> contenedores · {fmt.fmt_int(len(nor))} embarques"),
                KPI("Ahorro por m³", fmt.fmt_usd(nor["ahorro_m3"].sum()) if nor["ahorro_m3"].notna().any() else "—",
                    sub=f"Capacidad 40 NOR {fmt.fmt_int(cap_nor)} m³ vs 40 ST/HQ {fmt.fmt_int(cap_hq)} m³"),
                KPI("Diferencia por contenedor", fmt.fmt_usd((nor["ref_hq"] - nor["flete_por_ctnr"]).median(), compact=False),
                    sub="Mediana: 40 ST/HQ − 40 NOR"),
            ], columns=3)
            g = nor.groupby("mes").agg(embarques=("embarque", "count"), contenedores=("contenedores", "sum"),
                                       nor=("flete_por_ctnr", "median"), hq=("ref_hq", "first"),
                                       ahorro=("ahorro", "sum"), ahorro_m3=("ahorro_m3", "sum")).reset_index()
            g["mes_txt"] = g["mes"].map(lambda m: fmt.fmt_month(m, long=True))
            data_table(g.iloc[::-1], [
                ColSpec("mes_txt", "Mes ETD"), ColSpec("embarques", "Embarques", "int"),
                ColSpec("contenedores", "Contenedores", "int"), ColSpec("hq", "40 ST/HQ · mediana (USD)", "usd"),
                ColSpec("nor", "40 NOR · mediana (USD)", "usd"), ColSpec("ahorro", "Ahorro (USD)", "usd"),
                ColSpec("ahorro_m3", "Ahorro por m³ (USD)", "usd"),
            ], key="fp_nor", filename="ahorro_40nor", search=False)

    section("¿A quién le pagamos?", "Por forwarder, ordenado por costo total. Montos por contenedor = mediana.")
    with guard("Tabla por forwarder"):
        data_table(by_forwarder(d), [
            ColSpec("forwarder", "Forwarder"), ColSpec("embarques", "Embarques", "int"),
            ColSpec("contenedores", "Cont.", "int"), ColSpec("costo_total", "Costo total (USD)", "usd"),
            ColSpec("flete_total", "Flete pagado (USD)", "usd"), ColSpec("flete_ctnr", "Flete / cont. (USD)", "usd"),
            ColSpec("locales_ctnr", "Locales / cont. (USD)", "usd"), ColSpec("costo_m3", "Costo / m³ (USD)", "usd"),
            ColSpec("vs_mercado", "vs mercado", "pct"), ColSpec("certificado", "% certificado", "pct"),
            ColSpec("observados", "Observados", "int"),
        ], key="fp_ffww", filename="fletes_por_forwarder", search=False)

    section("Validación de fletes", "Resultado de la validación de Logística Internacional sobre cada embarque.")
    with guard("Validación"):
        v = d["resultado_validacion"].fillna("Sin validar").value_counts()
        kpi_row([
            KPI("Validados", fmt.fmt_int(v.get("Validado", 0)),
                sub=fmt.fmt_pct(v.get("Validado", 0) / len(d)) + " de los embarques"),
            KPI("Observados", fmt.fmt_int(v.get("Observado", 0)),
                status="warn" if v.get("Observado", 0) else "", sub="Con diferencia o datos faltantes"),
            KPI("Sin validar", fmt.fmt_int(v.get("Sin validar", 0)),
                sub=fmt.fmt_pct(v.get("Sin validar", 0) / len(d)) + " de los embarques"),
        ], columns=3)
        obs = d[d["resultado_validacion"] == "Observado"].sort_values("etd", ascending=False)
        if len(obs):
            data_table(obs, [
                ColSpec("embarque", "Embarque"), ColSpec("etd", "ETD", "date"), ColSpec("forwarder", "Forwarder"),
                ColSpec("motivo_observacion", "Motivo", width="medium"),
                ColSpec("flete_pagado", "Flete pagado (USD)", "usd"), ColSpec("flete_cotizado", "Flete cotizado (USD)", "usd"),
                ColSpec("gastos_locales", "Locales (USD)", "usd"), ColSpec("responsable", "Responsable"),
            ], key="fp_obs", filename="fletes_observados")

    section("Detalle por embarque")
    with guard("Detalle"):
        data_table(d.sort_values("etd", ascending=False), [
            ColSpec("embarque", "Embarque"), ColSpec("etd", "ETD", "date"), ColSpec("forwarder", "Forwarder"),
            ColSpec("puerto", "Puerto"), ColSpec("linea", "Línea"), ColSpec("tipo_carga", "Tipo"),
            ColSpec("contenedores", "Cont.", "int"), ColSpec("m3", "M3", "num"),
            ColSpec("flete_pagado", "Flete (USD)", "usd"), ColSpec("flete_por_ctnr", "Flete / cont.", "usd"),
            ColSpec("mercado_mes", "Mercado / cont.", "usd"), ColSpec("vs_mercado", "vs mercado", "pct"),
            ColSpec("gastos_locales", "Locales (USD)", "usd"), ColSpec("gastos_origen", "Origen (USD)", "usd"),
            ColSpec("costo_total", "Costo total (USD)", "usd"), ColSpec("costo_por_m3", "USD / m³", "usd"),
            ColSpec("flete_certificado", "Certificado (USD)", "usd"), ColSpec("resultado_validacion", "Validación"),
        ], key="fp_detalle", filename="fletes_pagados")

    aer = bundle.get("aereos")
    if aer is not None:
        section("Aéreos", "Seguimiento Aéreos · mismo período.")
        with guard("Fletes aéreos"):
            a = filtered(bundle, "aereos", filters)
            a = a[(a["etd"] <= today()) & (a["flete_pagado"] > 0)]
            if a.empty:
                empty()
            else:
                usd_kg = (a["flete_pagado"] / a["chargeable"].where(a["chargeable"] > 0))
                kg = calc.describe(usd_kg)
                cert_a = a["flete_certificado"].sum() / a["flete_pagado"].sum()
                kpi_row([
                    KPI("Flete aéreo pagado", fmt.fmt_usd(a["flete_pagado"].sum()),
                        sub=f"<b>{fmt.fmt_int(len(a))}</b> embarques"),
                    KPI("USD por kg (chargeable)", fmt.fmt_num(kg.median, 2) if kg.enough else "—",
                        sub="Mediana · " + (f"P25–P75 {fmt.fmt_num(kg.p25, 2)}–{fmt.fmt_num(kg.p75, 2)}" if kg.enough else "")),
                    KPI("Gastos en origen", fmt.fmt_usd(a["gastos_origen"].sum())),
                    KPI("Gastos locales", fmt.fmt_usd(a["gastos_locales"].sum())),
                    KPI("Flete certificado", fmt.fmt_pct(cert_a)),
                ])
                g = a.assign(usd_kg=usd_kg).groupby("forwarder").agg(
                    embarques=("embarque", "count"), flete=("flete_pagado", "sum"),
                    usd_kg=("usd_kg", "median"), kg=("chargeable", "sum")).reset_index().sort_values("flete", ascending=False)
                data_table(g, [
                    ColSpec("forwarder", "Forwarder"), ColSpec("embarques", "Embarques", "int"),
                    ColSpec("flete", "Flete pagado (USD)", "usd"), ColSpec("kg", "Chargeable (kg)", "int"),
                    ColSpec("usd_kg", "USD / kg (mediana)", "num"),
                ], key="fp_aer", filename="fletes_aereos", search=False)
