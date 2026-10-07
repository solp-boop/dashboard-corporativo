"""Aéreos y courier (Seguimiento Aéreos).

- render_en_curso: lo activo, en la pestaña Aéreo de «Embarques en curso».
- render_historico: tiempos por mes, tramos y tipo de negocio, en «Histórico».
"""
from __future__ import annotations

import numpy as np
import pandas as pd
import plotly.graph_objects as go
import streamlit as st

from components import charts
from components.kpi_cards import KPI, kpi_row
from components.layout import chart_title, coverage, empty, guard, require, section
from components.tables import ColSpec, data_table
from config import settings
from utils import calculations as calc
from utils import formatting as fmt
from views._common import ctx, filtered, month_labels, sla_por_grupo, today

TRAMOS = [
    ("dias_packeo_wh", "Packeo → WH"),
    ("dias_wh_etd", "WH → ETD"),
    ("dias_etd_eta", "ETD → ETA"),
    ("dias_eta_caldas", "ETA → Caldas"),
]


def riesgo_aereo(act: pd.DataFrame, today: pd.Timestamp) -> pd.DataFrame:
    """Aéreos activos proyectados fuera del SLA de su tipo y todavía sin ETD OK FFWW."""
    r = riesgo(act, today)
    return r[r["estado_sla"].isin([calc.SEMAFORO_WARN, calc.SEMAFORO_BAD]) & ~r["etd_ok"].fillna(False).astype(bool)]


def riesgo(act: pd.DataFrame, today: pd.Timestamp) -> pd.DataFrame:
    """Aéreos activos con su tiempo total proyectado (packeo mínimo → ETA Caldas) contra el SLA de su tipo.

    Proyección: «Total» si ya está cargado; si no, ETA Caldas; si no, ETA + mediana ETA→Caldas;
    si no, ETD + mediana ETD→Caldas; si no, hoy. Siempre desde F.Packeo Min.
    """
    d = act.copy()
    med_eta_cal = d["dias_eta_caldas"].median() if "dias_eta_caldas" in d else np.nan
    med_etd_cal = (d["dias_etd_eta"] + d["dias_eta_caldas"]).median() if "dias_etd_eta" in d else np.nan
    fin = d["eta_caldas"].copy()
    if med_eta_cal == med_eta_cal:
        fin = fin.fillna(d["eta"] + pd.to_timedelta(med_eta_cal, unit="D"))
    if med_etd_cal == med_etd_cal:
        fin = fin.fillna(d["etd"] + pd.to_timedelta(med_etd_cal, unit="D"))
    fin = fin.fillna(today)
    proy = (fin - d["f_packeo_min"]).dt.days.astype(float)
    d["dias_proyectados"] = d["dias_aereo"].fillna(proy) if "dias_aereo" in d else proy
    d["estado_sla"] = calc.semaforo(d["dias_proyectados"], d["sla_aereo"])
    return d


def render_en_curso(bundle=None, filters=None) -> None:
    if bundle is None:
        bundle, filters = ctx()
    if require(bundle, "aereos") is None:
        return
    todos = filtered(bundle, "aereos", filters, use_period=False)
    act = todos[todos["activo"]]

    section("Aéreos en gestión", "Seguimiento Aéreos: todo lo que no está ENTREGADO. Los tiempos por mes y por tramo están en "
            "Histórico.")
    if act.empty:
        empty("No hay aéreos activos.")
        return
    t = today()
    r = riesgo(act, t)
    en_riesgo = r[r["estado_sla"].isin([calc.SEMAFORO_WARN, calc.SEMAFORO_BAD]) & ~r["etd_ok"].fillna(False).astype(bool)]
    with guard("KPIs aéreos"):
        kpi_row([
            KPI("Aéreos activos", fmt.fmt_int(len(act))),
            KPI("Volumen activo", fmt.fmt_num(act["m3"].sum(), 0), unit="m³",
                sub=f"<b>{fmt.fmt_int(act['unidades'].sum())}</b> unidades"),
            KPI("FOB activo", fmt.fmt_usd(act["fob"].sum())),
            KPI("Chargeable weight", fmt.fmt_int(act["chargeable"].sum()), unit="kg"),
            KPI("En riesgo", fmt.fmt_int(len(en_riesgo)), status="bad" if len(en_riesgo) else "ok",
                sub="fuera del SLA de su tipo, sin ETD OK · detalle en la Bandeja de acción"),
        ])

    section("Operaciones por tipo de negocio",
            "Aéreos en curso por tipo de negocio y estadio, y cuántos están dentro o fuera del SLA de su tipo "
            "(tiempo total proyectado). Seguimiento Aéreos no tiene responsable de la carga, por eso se abre por "
            "tipo de negocio.")
    with guard("Operaciones por tipo de negocio"):
        r2 = r.assign(tipo_negocio=r["tipo_sla"].where(r["tipo_sla"].notna(), r["tipo_negocio"]))
        estadios = r2["estadio"].value_counts().index.tolist()
        chart_title("Por estadio")
        st.markdown(sla_por_grupo(r2, "tipo_negocio", "estado_sla", "Tipo de negocio",
                                  extra=estadios, extra_col="estadio", extra_label="Estadio", sla=False),
                    unsafe_allow_html=True)
        chart_title("Dentro / fuera del SLA de su tipo", "Tiempo total proyectado · Fuera = Atención + Fuera de SLA")
        st.markdown(sla_por_grupo(r2, "tipo_negocio", "estado_sla", "Tipo de negocio"), unsafe_allow_html=True)


def render_historico(bundle, filters) -> None:
    """Tiempos de los aéreos con ETD en el período: total por mes, tramos y tipo de negocio."""
    base = require(bundle, "aereos")
    if base is None:
        return
    df = filtered(bundle, "aereos", filters)
    df = df[df["etd"] <= today()]
    section("Aéreos · tiempos", "Seguimiento Aéreos · aéreos con ETD en el período.")
    if df.empty:
        empty()
        return
    tot = calc.describe(df["dias_total_aereo"])
    coverage(tot.n, len(df), "embarques con fecha de packeo y ETA Caldas válidas")
    with guard("Tiempos por tramo"):
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

    section("Aéreos · ¿en qué tramo se demora?", "Mediana de cada tramo por mes de ETD (días). "
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

    section("Aéreos · participación por tipo de negocio")
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
