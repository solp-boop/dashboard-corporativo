"""Agentes (forwarders) y analistas: quién demora y dónde intervenir."""
from __future__ import annotations

import numpy as np
import pandas as pd
import plotly.graph_objects as go
import streamlit as st

from components import charts
from components.kpi_cards import KPI, kpi_row, status_for
from components.layout import chart_title, empty, filter_notes, guard, require, section
from components.tables import ColSpec, data_table
from config import settings
from config.mappings import MODOS_MARITIMOS
from utils import calculations as calc
from utils import formatting as fmt
from views._common import ctx, filtered, month_labels, stat_sub, today


def _group(df: pd.DataFrame, by: str) -> pd.DataFrame:
    rows = []
    for key, d in df.groupby(by):
        pct, n = calc.cumplimiento(d["dias_consolidacion"], d["sla_consolidacion"])
        pagado = d.loc[d["flete_pagado"] > 0, "flete_pagado"].sum()
        cert = d.loc[d["flete_pagado"] > 0, "flete_certificado"].sum()
        rows.append({
            by: key, "embarques": len(d), "contenedores": d["contenedores"].sum(), "m3": d["m3"].sum(),
            "agente": d["dias_agente"].median(), "n_agente": int(d["dias_agente"].notna().sum()),
            "consolidacion": d["dias_consolidacion"].median(), "cumple": pct if n else np.nan,
            "desvio": d["desvio_etd"].median(),
            "in_advance": (d["booking"] == "In advance").mean() if d["booking"].notna().any() else np.nan,
            "certificacion": cert / pagado if pagado else np.nan,
        })
    return pd.DataFrame(rows).sort_values("embarques", ascending=False) if rows else pd.DataFrame()


def render() -> None:
    bundle, filters = ctx()
    base = require(bundle, "historicas")
    if base is None:
        return
    df = filtered(bundle, "historicas", filters)
    df = df[df["modo"].isin(MODOS_MARITIMOS) & (df["etd"] <= today())]
    filter_notes(base, filters, "Reservas Históricas")
    if df.empty:
        empty()
        return

    section("Forwarders", "Embarques marítimos zarpados en el período.")
    with guard("KPIs de agentes"):
        ag = calc.describe(df["dias_agente"])
        des = calc.describe(df["desvio_etd"])
        pagado = df.loc[df["flete_pagado"] > 0, "flete_pagado"].sum()
        cert = df.loc[df["flete_pagado"] > 0, "flete_certificado"].sum()
        n_cert = int((df["flete_pagado"] > 0).sum())
        pct_cert = cert / pagado if pagado else np.nan
        stt, badge = (status_for(pct_cert, settings.KPI_CERTIFICACION_TARGET, higher_is_better=True)
                      if n_cert >= settings.MIN_SAMPLE else ("", ""))
        kpi_row([
            KPI("Embarques", fmt.fmt_int(len(df)), sub=f"<b>{fmt.fmt_int(df['contenedores'].sum())}</b> contenedores"),
            KPI("Instrucción → ETD (mediana)", fmt.fmt_int(ag.median) if ag.enough else "—", unit="d",
                sub=stat_sub(ag)),
            KPI("Desvío ETD real vs estimada", fmt.fmt_int(des.median) if des.enough else "—", unit="d",
                sub=stat_sub(des)),
            KPI("Flete certificado", fmt.fmt_pct(pct_cert) if n_cert >= settings.MIN_SAMPLE else "—",
                status=stt, badge=badge,
                sub=f"Objetivo ≥ {fmt.fmt_pct(settings.KPI_CERTIFICACION_TARGET)} · "
                    f"datos en <b>{fmt.fmt_int(n_cert)}</b> de {fmt.fmt_int(len(df))} embarques"),
        ])

    by_ffww = _group(df, "forwarder")
    c1, c2 = st.columns(2, gap="medium")
    with c1, guard("Instrucción a ETD por forwarder"):
        chart_title("Instrucción → ETD por forwarder",
                    f"Mediana en días · forwarders con ≥ {settings.MIN_SAMPLE} embarques con dato")
        g = by_ffww[by_ffww["n_agente"] >= settings.MIN_SAMPLE].sort_values("agente", ascending=False)
        if g.empty:
            empty()
        else:
            fig = charts.hbar(g["forwarder"], g["agente"],
                              text=[f"{fmt.fmt_int(v)} d · n={n}" for v, n in zip(g["agente"], g["n_agente"])],
                              hover="%{y}: %{x:.0f} d<extra></extra>", x_title="días",
                              ref_value=ag.median if ag.enough else None, ref_label="Mediana general")
            charts.show(fig, key="ag_instr_etd")
    with c2, guard("Cumplimiento por forwarder"):
        chart_title("Cumplimiento de SLA de consolidación por forwarder",
                    f"% de embarques dentro de SLA · ≥ {settings.MIN_SAMPLE} embarques")
        g = by_ffww[(by_ffww["embarques"] >= settings.MIN_SAMPLE) & by_ffww["cumple"].notna()] \
            .sort_values("cumple")
        if g.empty:
            empty()
        else:
            fig = charts.hbar(g["forwarder"], g["cumple"] * 100,
                              text=[fmt.fmt_pct(v) for v in g["cumple"]],
                              hover="%{y}: %{x:.0f} %<extra></extra>", x_title="%", x_suffix=" %")
            charts.show(fig, key="ag_cumple")

    with guard("Tabla de forwarders"):
        data_table(by_ffww, [
            ColSpec("forwarder", "Forwarder"), ColSpec("embarques", "Embarques", "int"),
            ColSpec("contenedores", "Cont.", "int"), ColSpec("m3", "M3", "int"),
            ColSpec("agente", "Instr.→ETD (d)", "days"), ColSpec("consolidacion", "Consolidación (d)", "days"),
            ColSpec("cumple", "% SLA consol.", "pct"), ColSpec("desvio", "Desvío ETD (d)", "days"),
            ColSpec("in_advance", "% in advance", "pct"), ColSpec("certificacion", "% flete certificado", "pct"),
        ], key="ag_ffww", filename="forwarders", search=False,
            caption="Medianas en días. Desvío ETD = ETD real − ETD estimada")

    section("Analistas (responsable de la carga)")
    by_resp = _group(df, "responsable")
    c1, c2 = st.columns([2, 3], gap="medium")
    with c1, guard("Tabla de analistas"):
        data_table(by_resp, [
            ColSpec("responsable", "Responsable"), ColSpec("embarques", "Embarques", "int"),
            ColSpec("consolidacion", "Consolidación (d)", "days"), ColSpec("cumple", "% SLA", "pct"),
            ColSpec("agente", "Instr.→ETD (d)", "days"),
        ], key="ag_resp", filename="analistas", search=False)
    with c2, guard("Evolución por analista"):
        chart_title("Embarques por mes y analista", "Mes de ETD · los 4 con más embarques; el resto en «Otros»")
        d = df.dropna(subset=["responsable"]).copy()
        if d.empty:
            empty()
        else:
            d["mes"] = calc.month_start(d["etd"])
            top = list(d["responsable"].value_counts().index[:4])
            d["grupo"] = d["responsable"].where(d["responsable"].isin(top), "Otros")
            months = sorted(d["mes"].unique())[-12:]
            cmap = charts.color_map(top)
            fig = go.Figure()
            for name in top + (["Otros"] if (d["grupo"] == "Otros").any() else []):
                s = d[d["grupo"] == name].groupby("mes").size().reindex(months).fillna(0)
                fig.add_scatter(x=month_labels(pd.Series(months)), y=s.values, name=name, mode="lines+markers",
                                line=dict(color=cmap[name], width=2), marker=dict(size=8),
                                hovertemplate=f"{name}: %{{y}} embarques<extra></extra>")
            charts.theme(fig, y_title="embarques")
            charts.show(fig, key="ag_resp_mes")
