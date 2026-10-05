"""Histórico: volumen embarcado por mes y comparación con períodos anteriores."""
from __future__ import annotations

import numpy as np
import pandas as pd
import plotly.graph_objects as go
import streamlit as st

from components import charts
from components.kpi_cards import KPI, kpi_row
from components.layout import chart_title, empty, filter_notes, guard, require, section
from components.tables import ColSpec, data_table
from config import settings
from config.mappings import MODOS_MARITIMOS
from utils import calculations as calc
from utils import formatting as fmt
from views._common import ctx, filtered, month_labels, today


def monthly(df: pd.DataFrame, value_cols: dict[str, tuple[str, str]]) -> pd.DataFrame:
    d = df.dropna(subset=["etd"]).copy()
    d["mes"] = calc.month_start(d["etd"])
    g = d.groupby("mes").agg(**value_cols)
    if g.empty:
        return g.reset_index()
    full_range = pd.date_range(g.index.min(), g.index.max(), freq="MS")
    counts = [c for c, (_, how) in value_cols.items() if how in ("count", "sum")]
    g = g.reindex(full_range)
    g[counts] = g[counts].fillna(0)
    return g.rename_axis("mes").reset_index()


def render() -> None:
    bundle, filters = ctx()
    base = require(bundle, "historicas")
    if base is None:
        return
    # Sin período para poder comparar contra el año anterior; después se recorta.
    full = filtered(bundle, "historicas", filters, use_period=False)
    full = full[full["modo"].isin(MODOS_MARITIMOS) & (full["etd"] <= today())]
    filter_notes(base, filters, "Reservas Históricas")

    start = pd.Timestamp(filters.start) if filters.start else full["etd"].min()
    end = pd.Timestamp(filters.end) if filters.end else today()
    per = full[(full["etd"] >= start) & (full["etd"] <= end)]

    section("Marítimo embarcado", f"Reservas Históricas · ETD entre {start:%d/%m/%Y} y {end:%d/%m/%Y}.")
    if per.empty:
        empty()
        return
    with guard("KPIs históricos"):
        prev = full[(full["etd"] >= start - pd.DateOffset(years=1)) & (full["etd"] <= end - pd.DateOffset(years=1))]

        def yoy(col, agg="sum"):
            a = getattr(per[col], agg)() if col != "embarque" else len(per)
            b = getattr(prev[col], agg)() if col != "embarque" else len(prev)
            ch = calc.pct_change(a, b)
            return a, ("vs mismo período del año anterior: <b>" + fmt.fmt_pct(ch, signed=True) + "</b>"
                       if ch == ch else "Sin datos del año anterior")

        n, sub_n = yoy("embarque")
        c, sub_c = yoy("contenedores")
        m, sub_m = yoy("m3")
        f, sub_f = yoy("fob_simi")
        kpi_row([
            KPI("Embarques", fmt.fmt_int(n), sub=sub_n),
            KPI("Contenedores", fmt.fmt_int(c), sub=sub_c),
            KPI("Volumen", fmt.fmt_int(m), unit="m³", sub=sub_m),
            KPI("FOB", fmt.fmt_usd(f), sub=sub_f),
        ])

    c1, c2 = st.columns(2, gap="medium")
    with c1, guard("M3 por mes"):
        chart_title("Volumen embarcado por mes", "m³ por mes de ETD, según estructura de carga")
        d = per.dropna(subset=["etd"]).copy()
        d["mes"] = calc.month_start(d["etd"])
        d["estructura"] = d["estructura"].fillna("Sin dato")
        months = sorted(d["mes"].unique())
        fig = go.Figure()
        cmap = {"Consolidado": settings.SERIES[0], "Monoproveedor": settings.SERIES[1], "Sin dato": settings.SERIES_OTHER}
        for est in ["Consolidado", "Monoproveedor", "Sin dato"]:
            s = d[d["estructura"] == est].groupby("mes")["m3"].sum().reindex(months).fillna(0)
            if s.sum() == 0:
                continue
            fig.add_bar(x=month_labels(pd.Series(months)), y=s.values, name=est,
                        marker=dict(color=cmap[est], cornerradius=3),
                        hovertemplate=f"%{{x}} · {est}: %{{y:,.0f}} m³<extra></extra>")
        fig.update_layout(barmode="stack")
        charts.theme(fig, y_title="m³")
        charts.show(fig, key="hi_m3")

    with c2, guard("Comparación interanual"):
        chart_title("Embarques por mes: este año vs anterior", "Mismo mes, año calendario")
        y = end.year
        d = full.copy()
        d["anio"], d["m"] = d["etd"].dt.year, d["etd"].dt.month
        fig = go.Figure()
        for i, yr in enumerate([y - 1, y]):
            s = d[d["anio"] == yr].groupby("m").size().reindex(range(1, 13))
            if yr == y:
                s = s[s.index <= (end.month if end.year == y else 12)]
            fig.add_scatter(x=[fmt.MESES[m - 1] for m in s.index], y=s.values, name=str(yr),
                            mode="lines+markers", line=dict(color=settings.SERIES[1 - i] if i == 0 else settings.SERIES[0],
                                                            width=2, dash="dot" if yr != y else None),
                            marker=dict(size=8), hovertemplate=f"{yr} · %{{x}}: %{{y}} embarques<extra></extra>")
        charts.theme(fig, y_title="embarques")
        charts.show(fig, key="hi_yoy")

    section("Detalle mensual", "Δ% vs mes anterior y vs mismo mes del año anterior (en m³).")
    with guard("Tabla mensual"):
        allm = monthly(full, {"embarques": ("embarque", "count"), "contenedores": ("contenedores", "sum"),
                              "m3": ("m3", "sum"), "fob": ("fob_simi", "sum"),
                              "consolidacion": ("dias_consolidacion", "median")})
        allm["d_mes"] = allm["m3"].pct_change(fill_method=None)
        prev_year = allm.set_index("mes")["m3"]
        allm["d_anio"] = [calc.pct_change(v, prev_year.get(m - pd.DateOffset(years=1), np.nan))
                          for m, v in zip(allm["mes"], allm["m3"])]
        t = allm[(allm["mes"] >= start.to_period("M").to_timestamp()) & (allm["mes"] <= end)].iloc[::-1].copy()
        t["mes_txt"] = t["mes"].map(lambda m: fmt.fmt_month(m, long=True))
        data_table(t, [
            ColSpec("mes_txt", "Mes ETD"), ColSpec("embarques", "Embarques", "int"),
            ColSpec("contenedores", "Contenedores", "int"), ColSpec("m3", "M3", "int"),
            ColSpec("d_mes", "Δ% vs mes ant.", "pct"), ColSpec("d_anio", "Δ% vs año ant.", "pct"),
            ColSpec("fob", "FOB (USD)", "usd"), ColSpec("consolidacion", "Consolidación mediana (d)", "days"),
        ], key="hi_mensual", filename="historico_mensual", search=False)

    aer = bundle.get("aereos")
    if aer is not None:
        section("Aéreo embarcado", "Seguimiento Aéreos · mismo período.")
        with guard("Histórico aéreo"):
            a = filtered(bundle, "aereos", filters)
            a = a[a["etd"] <= today()]
            if a.empty:
                empty()
            else:
                g = monthly(a, {"embarques": ("embarque", "count"), "m3": ("m3", "sum"),
                                "chargeable": ("chargeable", "sum"), "fob": ("fob", "sum"),
                                "total": ("dias_total_aereo", "median")}).iloc[::-1]
                g["mes_txt"] = g["mes"].map(lambda m: fmt.fmt_month(m, long=True))
                data_table(g, [
                    ColSpec("mes_txt", "Mes ETD"), ColSpec("embarques", "Embarques", "int"),
                    ColSpec("m3", "M3", "num"), ColSpec("chargeable", "Chargeable (kg)", "int"),
                    ColSpec("fob", "FOB (USD)", "usd"), ColSpec("total", "Packeo→Caldas mediana (d)", "days"),
                ], key="hi_aereo", filename="historico_aereo", search=False)

    if aer is not None:
        from views import aereos
        aereos.render_historico(bundle, filters)
