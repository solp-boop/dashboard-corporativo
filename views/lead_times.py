"""Lead times y SLA (Reservas Históricas, marítimo)."""
from __future__ import annotations

import numpy as np
import pandas as pd
import plotly.graph_objects as go
import streamlit as st

from components import charts
from components.kpi_cards import KPI, kpi_row, status_for
from components.layout import (chart_title, coverage, empty, filter_notes, guard, require, section,
                               semaforo_legend)
from components.tables import ColSpec, data_table
from config import settings
from config.mappings import MODOS_MARITIMOS
from utils import calculations as calc
from utils import formatting as fmt
from views._common import ctx, filtered, month_labels, stat_sub, today

ETAPAS = [
    ("dias_comex", "Comex: packeo → instrucción"),
    ("dias_agente", "Agente: instrucción → ETD"),
    ("dias_consolidacion", "Consolidación: packeo → ETD"),
    ("dias_tt", "Tránsito: ETD → ETA"),
    ("dias_total", "Total: fin de producción → ETA"),
]


def render() -> None:
    bundle, filters = ctx()
    base = require(bundle, "historicas")
    if base is None:
        return
    df = filtered(bundle, "historicas", filters)
    df = df[df["modo"].isin(MODOS_MARITIMOS) & (df["etd"] <= today())]
    filter_notes(base, filters, "Reservas Históricas")
    st.caption("Solo embarques marítimos ya zarpados. SLA de consolidación: "
               f"{settings.SLA_CONSOLIDACION_MONO} d monoproveedor; consolidado según el target por puerto "
               f"de Validaciones (por defecto {settings.SLA_CONSOLIDACION_DEFAULT} d).")
    if df.empty:
        empty()
        return

    section("Indicadores del período")
    with guard("KPIs de SLA"):
        cards = []
        pct, n = calc.cumplimiento(df["dias_consolidacion"], df["sla_consolidacion"])
        cards.append(KPI("Cumplimiento SLA",
                         fmt.fmt_pct(pct) if n >= settings.MIN_SAMPLE else "—",
                         sub=f"n={fmt.fmt_int(n)} embarques"))
        for est in ("Monoproveedor", "Consolidado"):
            sub = df[df["estructura"] == est]
            s = calc.describe(sub["dias_consolidacion"])
            sla = float(sub["sla_consolidacion"].median()) if len(sub) else np.nan
            p, pn = calc.cumplimiento(sub["dias_consolidacion"], sub["sla_consolidacion"])
            stt, badge = status_for(s.median, sla) if s.enough else ("", "")
            cards.append(KPI(f"Consolidación {est.lower()}", fmt.fmt_int(s.median) if s.enough else "—", unit="d",
                             status=stt, badge=badge,
                             sub=f"SLA {fmt.fmt_int(sla)} d · cumple <b>{fmt.fmt_pct(p)}</b> · " + stat_sub(s)))
        tt = calc.describe(df["dias_tt"])
        stt, badge = status_for(tt.median, float(df["sla_tt"].median())) if tt.enough else ("", "")
        cards.append(KPI("Tránsito ETD→ETA", fmt.fmt_int(tt.median) if tt.enough else "—", unit="d",
                         status=stt, badge=badge, sub=stat_sub(tt)))
        kpi_row(cards)
        coverage(int(df["dias_consolidacion"].notna().sum()), len(df), "embarques con consolidación calculable")

    c1, c2 = st.columns(2, gap="medium")
    with c1, guard("Cumplimiento mensual"):
        chart_title("Cumplimiento de SLA por mes", "% dentro de SLA de consolidación · mes de ETD")
        d = df.dropna(subset=["dias_consolidacion", "estructura"]).copy()
        d["mes"] = calc.month_start(d["etd"])
        d["ok"] = d["dias_consolidacion"] <= d["sla_consolidacion"]
        g = d.groupby(["mes", "estructura"]).agg(pct=("ok", "mean"), n=("ok", "size")).reset_index()
        months = sorted(g["mes"].unique())[-12:]
        if not months:
            empty()
        else:
            fig = go.Figure()
            for i, est in enumerate(["Monoproveedor", "Consolidado"]):
                s = g[g["estructura"] == est].set_index("mes").reindex(months)
                fig.add_bar(x=month_labels(pd.Series(months)), y=s["pct"] * 100, name=est,
                            marker=dict(color=settings.SERIES[i], cornerradius=3),
                            customdata=s["n"].fillna(0),
                            hovertemplate=f"%{{x}} · {est}: %{{y:.0f}} % (n=%{{customdata}})<extra></extra>")
            charts.theme(fig, y_suffix=" %")
            fig.update_yaxes(range=[0, 105])
            charts.show(fig, key="sla_mes")

    with c2, guard("Etapas"):
        chart_title("¿En qué etapa se va el tiempo?", "Mediana y rango P25–P75 por etapa (días)")
        rows = []
        for col, label in ETAPAS:
            s = calc.describe(df[col])
            if s.n:
                rows.append((label, s))
        if not rows:
            empty()
        else:
            labels = [r[0] for r in rows]
            med = [r[1].median for r in rows]
            fig = go.Figure(go.Bar(
                y=labels, x=med, orientation="h", marker=dict(color=settings.SERIES[0], cornerradius=4),
                error_x=dict(type="data", symmetric=False, array=[r[1].p75 - r[1].median for r in rows],
                             arrayminus=[r[1].median - r[1].p25 for r in rows],
                             color=settings.COLORS["slate"], thickness=1.2, width=4),
                text=[f"{fmt.fmt_int(v)} d" for v in med], textposition="inside",
                customdata=[[r[1].p25, r[1].p75, r[1].n] for r in rows],
                hovertemplate="%{y}<br>Mediana: %{x:.0f} d<br>P25–P75: %{customdata[0]:.0f}–%{customdata[1]:.0f} d"
                              "<br>n=%{customdata[2]}<extra></extra>",
            ))
            charts.theme(fig, height=320, y_title="días", horizontal=True, legend=False)
            fig.update_yaxes(autorange="reversed")
            charts.show(fig, key="sla_etapas")

    section("Tiempos por puerto de origen",
            f"Mediana real vs target de Validaciones · puertos con ≥ {settings.MIN_SAMPLE} embarques. "
            "El semáforo compara el total (fin de producción → ETA) con el target total.")
    with guard("Tabla por puerto"):
        semaforo_legend()
        g = df.groupby("puerto").agg(
            embarques=("embarque", "count"),
            cons=("dias_consolidacion", "median"), tt=("dias_tt", "median"), total=("dias_total", "median"),
            n_total=("dias_total", "count"),
            sla_cons=("sla_consolidacion", "median"), sla_tt=("sla_tt", "median"), sla_total=("sla_total", "median"),
            definido=("sla_puerto_definido", "max"),
        ).reset_index()
        g["cumple"] = df.groupby("puerto").apply(
            lambda d: calc.cumplimiento(d["dias_consolidacion"], d["sla_consolidacion"])[0],
            include_groups=False).reindex(g["puerto"]).values
        g = g[g["embarques"] >= settings.MIN_SAMPLE].sort_values("embarques", ascending=False)
        # SLA de consolidado del puerto (el de mono es fijo y se aclara arriba).
        sla_map = bundle.sla_puertos.set_index("puerto")["sla_consolidacion"] if not bundle.sla_puertos.empty else {}
        g["sla_cons"] = g["puerto"].map(sla_map).fillna(settings.SLA_CONSOLIDACION_DEFAULT)
        g["estado"] = calc.semaforo(g["total"], g["sla_total"])
        g["target"] = np.where(g["definido"], "Validaciones", "Por defecto")
        data_table(g, [
            ColSpec("puerto", "Puerto"), ColSpec("embarques", "Embarques", "int"),
            ColSpec("cons", "Consolidación (d)", "days"), ColSpec("sla_cons", "SLA consolidado (d)", "days"),
            ColSpec("cumple", "% cumple consol.", "pct"),
            ColSpec("tt", "Tránsito (d)", "days"), ColSpec("sla_tt", "Target tránsito (d)", "days"),
            ColSpec("total", "Total (d)", "days"), ColSpec("sla_total", "Target total (d)", "days"),
            ColSpec("estado", "Estado", "status"), ColSpec("target", "Origen del target"),
        ], key="sla_puertos", filename="tiempos_por_puerto", search=False)

    c1, c2 = st.columns(2, gap="medium")
    with c1, guard("Booking"):
        chart_title("Consolidación según modalidad de booking", f"Mediana · referencia {settings.REF_CONSOLIDACION_BOOKING} d")
        g = calc.median_by(df, "booking", "dias_consolidacion")
        if g.empty:
            empty()
        else:
            fig = charts.hbar(g["booking"], g["mediana"],
                              text=[f"{fmt.fmt_int(v)} d · n={n}" for v, n in zip(g["mediana"], g["n"])],
                              hover="%{y}: %{x:.0f} d<extra></extra>", x_title="días",
                              ref_value=settings.REF_CONSOLIDACION_BOOKING, ref_label="Referencia")
            charts.show(fig, key="sla_booking")

    with c2, guard("Causas de demora"):
        chart_title("Principales causas de demora", "Embarques con «Tipo de demora» informado")
        causes = df["tipo_demora"].dropna()
        if causes.empty:
            empty("No hay causas de demora cargadas en el período.")
        else:
            g = causes.value_counts()
            top = g.head(8)
            fig = charts.hbar(top.index, top.values, text=[str(v) for v in top.values],
                              hover="%{y}: %{x} embarques<extra></extra>", x_title="embarques")
            charts.show(fig, key="sla_causas")
            coverage(int(causes.size), len(df), "embarques con causa informada")

    section("Embarques fuera de SLA")
    with guard("Detalle fuera de SLA"):
        bad = df[df["estado_consolidacion"] == calc.SEMAFORO_BAD].sort_values("etd", ascending=False)
        data_table(bad, [
            ColSpec("embarque", "Embarque"), ColSpec("etd", "ETD", "date"), ColSpec("puerto", "Puerto"),
            ColSpec("forwarder", "Forwarder"), ColSpec("estructura", "Estructura"), ColSpec("booking", "Booking"),
            ColSpec("dias_comex", "Comex (d)", "days"), ColSpec("dias_agente", "Agente (d)", "days"),
            ColSpec("dias_consolidacion", "Consolidación (d)", "days"),
            ColSpec("sla_consolidacion", "SLA (d)", "days"), ColSpec("tipo_demora", "Tipo de demora"),
            ColSpec("responsable", "Responsable"), ColSpec("observaciones", "Observaciones", width="large"),
        ], key="sla_bad", filename="embarques_fuera_de_sla")
