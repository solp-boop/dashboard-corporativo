"""Aéreos y courier (Seguimiento Aéreos): estado actual y tiempos por tramo."""
from __future__ import annotations

import numpy as np
import pandas as pd
import plotly.graph_objects as go
import streamlit as st

from components import charts
from components.kpi_cards import KPI, kpi_row
from components.layout import chart_title, coverage, empty, filter_notes, guard, require, section
from components.tables import ColSpec, data_table
from config import settings
from utils import calculations as calc
from utils import formatting as fmt
from views._common import ctx, filtered, month_labels, stat_sub

TRAMOS = [
    ("dias_packeo_wh", "Packeo → WH"),
    ("dias_wh_etd", "WH → ETD"),
    ("dias_etd_eta", "ETD → ETA"),
    ("dias_eta_caldas", "ETA → Caldas"),
]


def render() -> None:
    bundle, filters = ctx()
    base = require(bundle, "aereos")
    if base is None:
        return
    df = filtered(bundle, "aereos", filters)
    filter_notes(base, filters, "Seguimiento Aéreos")
    if df.empty:
        empty()
        return
    act = df[df["activo"]]

    section("Aéreos en gestión", "Embarques cuyo estadio no es ENTREGADO / NACIONALIZADO.")
    with guard("KPIs aéreos"):
        tot = calc.describe(df["dias_total_aereo"])
        kpi_row([
            KPI("Aéreos activos", fmt.fmt_int(len(act)), sub=f"de <b>{fmt.fmt_int(len(df))}</b> en el período"),
            KPI("Volumen activo", fmt.fmt_num(act["m3"].sum(), 0), unit="m³",
                sub=f"<b>{fmt.fmt_int(act['unidades'].sum())}</b> unidades"),
            KPI("FOB activo", fmt.fmt_usd(act["fob"].sum())),
            KPI("Chargeable weight", fmt.fmt_int(act["chargeable"].sum()), unit="kg"),
            KPI("Packeo → Caldas (mediana)", fmt.fmt_int(tot.median) if tot.enough else "—", unit="d",
                sub=stat_sub(tot)),
        ])
        coverage(tot.n, len(df), "embarques con fecha de packeo y ETA Caldas válidas")

    c1, c2 = st.columns([3, 2], gap="medium")
    with c1, guard("Tiempos por tramo"):
        chart_title("Tiempo total por mes de ETD", "Mediana de packeo mínimo → ETA Caldas · barra = P25 a P75")
        d = df.dropna(subset=["dias_total_aereo", "etd"]).copy()
        d["mes"] = calc.month_start(d["etd"])
        g = d.groupby("mes")["dias_total_aereo"].agg(
            n="count", med="median", p25=lambda s: s.quantile(.25), p75=lambda s: s.quantile(.75)).reset_index()
        g = g.tail(12)
        if g.empty:
            empty()
        else:
            fig = go.Figure(go.Bar(
                x=month_labels(g["mes"]), y=g["med"], marker=dict(color=settings.SERIES[0], cornerradius=4),
                error_y=dict(type="data", symmetric=False, array=g["p75"] - g["med"],
                             arrayminus=g["med"] - g["p25"], color=settings.COLORS["slate"], thickness=1.2, width=4),
                customdata=np.stack([g["n"], g["p25"], g["p75"]], axis=1),
                text=[f"{fmt.fmt_int(v)} d" for v in g["med"]], textposition="inside",
                hovertemplate="%{x}<br>Mediana: %{y:.0f} d<br>P25–P75: %{customdata[1]:.0f}–%{customdata[2]:.0f} d"
                              "<br>n=%{customdata[0]}<extra></extra>",
            ))
            charts.theme(fig, y_title="días", legend=False)
            charts.show(fig, key="aer_total_mes")

    with c2, guard("Estadios"):
        chart_title("Embarques activos por estadio")
        g = act.groupby("estadio").size().sort_values(ascending=False)
        if g.empty:
            empty("No hay aéreos activos.")
        else:
            charts.show(charts.hbar(g.index, g.values, text=[str(v) for v in g.values],
                                    hover="%{y}: %{x} embarques<extra></extra>", x_title="embarques"),
                        key="aer_estadio")

    section("¿En qué tramo se demora?", "Mediana de cada tramo por mes de ETD (días). "
            "Los tramos se calculan por separado: no se suman para dar el total.")
    with guard("Tabla de tramos"):
        d = df.dropna(subset=["etd"]).copy()
        d["mes"] = calc.month_start(d["etd"])
        rows = []
        for mes, sub in d.groupby("mes"):
            r = {"mes": fmt.fmt_month(mes, long=True), "embarques": len(sub)}
            for col, label in TRAMOS:
                r[label] = sub[col].median()
            r["Total"] = sub["dias_total_aereo"].median()
            rows.append(r)
        t = pd.DataFrame(rows).iloc[::-1]
        data_table(t, [ColSpec("mes", "Mes ETD"), ColSpec("embarques", "Embarques", "int")]
                   + [ColSpec(lbl, lbl, "days") for _, lbl in TRAMOS] + [ColSpec("Total", "Total (d)", "days")],
                   key="aer_tramos", filename="aereos_tramos", search=False)

    section("Participación por tipo de negocio")
    with guard("Tipo de negocio"):
        g = df.groupby(df["tipo_negocio"].fillna("Sin clasificar")).agg(
            embarques=("embarque", "count"), m3=("m3", "sum"), unidades=("unidades", "sum"),
            fob=("fob", "sum"), total=("dias_total_aereo", "median")).reset_index()
        g["pct"] = g["embarques"] / g["embarques"].sum()
        g = g.sort_values("embarques", ascending=False)
        data_table(g, [
            ColSpec("tipo_negocio", "Tipo de negocio"), ColSpec("embarques", "Embarques", "int"),
            ColSpec("pct", "% embarques", "pct"), ColSpec("m3", "M3", "num"),
            ColSpec("unidades", "Unidades", "int"), ColSpec("fob", "FOB (USD)", "usd"),
            ColSpec("total", "Packeo→Caldas mediana (d)", "days"),
        ], key="aer_tn", filename="aereos_tipo_negocio", search=False)

    section("Detalle de aéreos activos")
    with guard("Tabla de aéreos"):
        data_table(act.sort_values("etd"), [
            ColSpec("embarque", "Embarque"), ColSpec("estadio", "Estadio"), ColSpec("empresa", "Empresa"),
            ColSpec("tipo_negocio", "Tipo de negocio"), ColSpec("forwarder", "Forwarder"),
            ColSpec("puerto", "Origen"), ColSpec("tipo_carga", "Tipo"),
            ColSpec("f_packeo_min", "Packeo mín.", "date"), ColSpec("f_ingreso_wh", "Ingreso WH", "date"),
            ColSpec("etd", "ETD", "date"), ColSpec("eta", "ETA", "date"), ColSpec("eta_caldas", "ETA Caldas", "date"),
            ColSpec("m3", "M3", "num"), ColSpec("chargeable", "Chargeable (kg)", "int"),
            ColSpec("fob", "FOB (USD)", "usd"), ColSpec("guia", "Guía"),
            ColSpec("observaciones", "Observaciones", width="large"),
        ], key="aer_tabla", filename="aereos_activos")
