"""Embarques en curso, marítimos y aéreos: qué zarpa, qué falta confirmar y con qué agente."""
from __future__ import annotations

import numpy as np
import pandas as pd
import plotly.graph_objects as go
import streamlit as st

from components import charts
from components.kpi_cards import KPI, kpi_row, status_for
from components.layout import chart_title, coverage, empty, guard, section, semaforo_legend
from components.tables import ColSpec, data_table
from config import settings
from utils import calculations as calc
from utils import formatting as fmt
from views import aereos
from views._common import ctx, en_curso, kpis_en_curso, stat_sub, today


def render() -> None:
    bundle, filters = ctx()
    df, info = en_curso(bundle, filters)
    if df.empty:
        empty()
        return

    t = today()
    week_start = t - pd.Timedelta(days=t.weekday())
    mar = df[df["grupo_modo"] == "Marítimo"]

    section("¿Cómo estamos hoy?")
    with guard("KPIs de embarques en curso"):
        kpis_en_curso(df, info)
        mono_n = int((mar["estructura"] == "Monoproveedor").sum())
        cons_n = int((mar["estructura"] == "Consolidado").sum())
        adv = mar["booking"].value_counts()
        st.caption(f"Marítimo: {fmt.fmt_int(mono_n)} monoproveedor / {fmt.fmt_int(cons_n)} consolidado · "
                   f"in advance {fmt.fmt_int(adv.get('In advance', 0))} / spot {fmt.fmt_int(adv.get('Spot', 0))}.")

    section("Próximas semanas", "Marítimos y aéreos en curso.")
    c1, c2 = st.columns(2, gap="medium")
    with c1, guard("ETD por semana"):
        chart_title("Volumen a zarpar por semana", "m³ por semana de ETD · próximas 8 semanas")
        horizon = df[(df["etd"] >= week_start) & (df["etd"] < week_start + pd.Timedelta(weeks=8))].copy()
        if horizon.empty:
            empty("No hay ETD en las próximas 8 semanas.")
        else:
            horizon["semana"] = calc.week_start(horizon["etd"])
            weeks = pd.date_range(week_start, periods=8, freq="7D")
            labels = [f"{w:%d/%m}" for w in weeks]
            fig = go.Figure()
            for flag, name, color in ((True, "ETD confirmado", settings.SERIES[0]),
                                      (False, "Sin confirmar", settings.SERIES[1])):
                s = horizon[horizon["etd_ok"] == flag].groupby("semana")["m3"].sum().reindex(weeks).fillna(0)
                n = horizon[horizon["etd_ok"] == flag].groupby("semana").size().reindex(weeks).fillna(0)
                fig.add_bar(x=labels, y=s.values, name=name, marker=dict(color=color, cornerradius=3),
                            customdata=n.values,
                            hovertemplate=f"Semana del %{{x}} · {name}: %{{y:,.0f}} m³ (%{{customdata}} emb.)<extra></extra>")
            fig.update_layout(barmode="stack")
            charts.theme(fig, y_title="m³", x_title="Semana (lunes)")
            charts.show(fig, key="emb_semana")

    with c2, guard("Pendientes por forwarder"):
        chart_title("ETD pendiente de confirmar, por forwarder", "Embarques en curso sin «ETD OK FFWW»")
        pend = df[~df["etd_ok"]]
        g = pend.groupby("forwarder").size().sort_values(ascending=False)
        if g.empty:
            empty("Todos los embarques tienen el ETD confirmado.")
        else:
            total = len(pend)
            fig = charts.hbar(g.index, g.values,
                              text=[f"{v} · {fmt.fmt_pct(v / total)}" for v in g.values],
                              hover="%{y}: %{x} embarques<extra></extra>", x_title="embarques")
            charts.show(fig, key="emb_pend_ffww")

    tab_mar, tab_aer = st.tabs(["Marítimo", "Aéreo"])
    with tab_mar:
        section("Consolidación de los embarques en curso",
                "ETD (confirmado o previsto) − fecha de packeo mínima. Mediana contra SLA.")
        with guard("Consolidación en curso"):
            cards = []
            for est, sla in (("Monoproveedor", settings.SLA_CONSOLIDACION_MONO), ("Consolidado", None)):
                sub = mar[mar["estructura"] == est]
                s = calc.describe(sub["dias_consolidacion"])
                sla_v = sla if sla is not None else (float(sub["sla_consolidacion"].median()) if len(sub) else np.nan)
                stt, badge = status_for(s.median, sla_v) if s.enough else ("", "")
                cards.append(KPI(est, fmt.fmt_int(s.median) if s.enough else "—", unit="d", status=stt, badge=badge,
                                 sub=f"SLA {fmt.fmt_int(sla_v)} d · " + stat_sub(s)))
            for bk in ("In advance", "Spot"):
                sub = mar[mar["booking"] == bk]
                s = calc.describe(sub["dias_consolidacion"])
                stt, badge = status_for(s.median, settings.REF_CONSOLIDACION_BOOKING) if s.enough else ("", "")
                cards.append(KPI(bk, fmt.fmt_int(s.median) if s.enough else "—", unit="d", status=stt, badge=badge,
                                 sub=f"Ref. {settings.REF_CONSOLIDACION_BOOKING} d · " + stat_sub(s)))
            kpi_row(cards)
            coverage(int(mar["dias_consolidacion"].notna().sum()), len(mar), "embarques marítimos",
                     "sin fecha de packeo o con fechas inconsistentes no se consideran")
    with tab_aer:
        aereos.render(bundle, filters)

    section("Detalle de embarques", "Ordenado por ETD. El semáforo compara la consolidación con su SLA.")
    with guard("Tabla de embarques"):
        semaforo_legend()
        tbl = df.sort_values("etd")
        data_table(tbl, [
            ColSpec("embarque", "Embarque"), ColSpec("grupo_modo", "Modo"), ColSpec("estadio", "Estadio (aéreo)"),
            ColSpec("empresa", "Empresa"), ColSpec("puerto", "Puerto"),
            ColSpec("forwarder", "Forwarder"), ColSpec("tipo_carga", "Tipo carga"),
            ColSpec("estructura", "Estructura"), ColSpec("booking", "Booking"),
            ColSpec("contenedores", "Cont.", "int"), ColSpec("m3", "M3", "num"), ColSpec("fob", "FOB (USD)", "usd"),
            ColSpec("f_packeo_min", "Packeo mín.", "date"), ColSpec("f_instruccion", "Instrucción", "date"),
            ColSpec("etd", "ETD", "date"), ColSpec("eta", "ETA", "date"), ColSpec("etd_ok", "ETD OK", "bool"),
            ColSpec("tipo_negocio", "Tipo de negocio (aéreo)"), ColSpec("eta_caldas", "ETA Caldas", "date"),
            ColSpec("chargeable", "Chargeable (kg)", "int"), ColSpec("guia", "Guía"),
            ColSpec("draft_bl", "Draft BL"), ColSpec("pl_final", "PL final"), ColSpec("fotos", "Fotos"),
            ColSpec("dias_consolidacion", "Consolidación (d)", "days"),
            ColSpec("sla_consolidacion", "SLA (d)", "days"),
            ColSpec("estado_consolidacion", "Estado", "status"),
            ColSpec("responsable", "Responsable"), ColSpec("tipo_demora", "Tipo de demora"),
            ColSpec("observaciones", "Observaciones", width="large"),
        ], key="emb_tabla", filename="embarques_en_curso")
