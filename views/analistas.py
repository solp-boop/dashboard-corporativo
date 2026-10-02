"""Analistas (responsable de la carga): carga actual y desempeño de lo zarpado."""
from __future__ import annotations

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
from views._common import ctx, en_curso, filtered, month_labels, today
from views.agentes import _group


def _carga_actual(res: pd.DataFrame) -> pd.DataFrame:
    t = today()
    week = res["etd"].between(t, t + pd.Timedelta(days=settings.ALERT_HORIZON_DAYS))
    d = res.assign(semana=week, pendiente=~res["etd_ok"], mar=res["grupo_modo"] == "Marítimo")
    d = d[d["responsable"].notna()]
    if d.empty:
        return pd.DataFrame()
    g = d.groupby("responsable").agg(
        embarques=("embarque", "count"), maritimos=("mar", "sum"),
        contenedores=("contenedores", "sum"),
        m3=("m3", "sum"), fob=("fob", "sum"), semana=("semana", "sum"), pendientes=("pendiente", "sum"),
    ).reset_index()
    return g.sort_values("embarques", ascending=False)


def render() -> None:
    bundle, filters = ctx()

    section("Carga actual", "Embarques en curso de Reservas por «Responsable de la carga». "
            "Seguimiento Aéreos no tiene esa columna, así que los aéreos no se asignan a un analista.")
    with guard("Carga actual"):
        res, _ = en_curso(bundle, filters)
        if not res.empty:
            res = res[res["grupo_modo"] != "Aéreo"]
        carga = _carga_actual(res) if not res.empty else pd.DataFrame()
        if carga.empty:
            empty("No hay embarques en curso con responsable asignado.")
        else:
            sin = int(res["responsable"].isna().sum())
            kpi_row([
                KPI("Analistas con carga", fmt.fmt_int(len(carga))),
                KPI("Embarques en curso", fmt.fmt_int(carga["embarques"].sum()),
                    sub=f"sin responsable: <b>{fmt.fmt_int(sin)}</b>" if sin else ""),
                KPI(f"Zarpan en {settings.ALERT_HORIZON_DAYS} días", fmt.fmt_int(carga["semana"].sum())),
                KPI("ETD sin confirmar", fmt.fmt_int(carga["pendientes"].sum())),
            ])
            data_table(carga, [
                ColSpec("responsable", "Responsable"), ColSpec("embarques", "Embarques", "int"),
                ColSpec("maritimos", "Marítimos", "int"), ColSpec("contenedores", "Cont.", "int"),
                ColSpec("m3", "M3", "int"), ColSpec("fob", "FOB (USD)", "usd"),
                ColSpec("semana", f"Zarpan {settings.ALERT_HORIZON_DAYS} d", "int"),
                ColSpec("pendientes", "ETD sin confirmar", "int"),
            ], key="an_carga", filename="analistas_carga_actual", search=False)

    base = require(bundle, "historicas")
    if base is None:
        return
    df = filtered(bundle, "historicas", filters)
    df = df[df["modo"].isin(MODOS_MARITIMOS) & (df["etd"] <= today())]
    section("Desempeño", "Embarques marítimos zarpados en el período, por responsable de la carga.")
    filter_notes(base, filters, "Reservas Históricas")
    if df.empty:
        empty()
        return
    by_resp = _group(df, "responsable")
    c1, c2 = st.columns([2, 3], gap="medium")
    with c1, guard("Tabla de analistas"):
        data_table(by_resp, [
            ColSpec("responsable", "Responsable"), ColSpec("embarques", "Embarques", "int"),
            ColSpec("consolidacion", "Consolidación (d)", "days"), ColSpec("cumple", "% SLA", "pct"),
            ColSpec("agente", "Instr.→ETD (d)", "days"),
        ], key="ag_resp", filename="analistas", search=False, caption="Medianas en días")
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
