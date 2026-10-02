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


CHART_H = 420  # mismo alto para los dos gráficos de «Próximas semanas»


def render() -> None:
    bundle, filters = ctx()
    df, info = en_curso(bundle, filters)
    if df.empty:
        empty()
        return

    t = today()
    week_start = t - pd.Timedelta(days=t.weekday())
    es_air = df["embarque"].astype(str).str.strip().str.upper().str.startswith("AIR")
    mar = df[(df["grupo_modo"] == "Marítimo") & ~es_air]

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
        chart_title("Volumen a zarpar por semana", f"m³ por semana de ETD · próximas 8 semanas · total {fmt.fmt_int(df.loc[(df['etd'] >= week_start) & (df['etd'] < week_start + pd.Timedelta(weeks=8)), 'm3'].sum())} m³")
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
            tot = horizon.groupby("semana")["m3"].sum().reindex(weeks).fillna(0)
            fig.add_scatter(x=labels, y=tot.values, mode="text", showlegend=False, hoverinfo="skip",
                            text=[f"{fmt.fmt_int(v)} m³" if v else "" for v in tot.values],
                            textposition="top center", cliponaxis=False,
                            textfont=dict(size=11, color=settings.COLORS["slate"]))
            fig.update_layout(barmode="stack")
            charts.theme(fig, height=CHART_H, y_title="m³", x_title="Semana (lunes)")
            fig.update_yaxes(range=[0, float(tot.max()) * 1.18 if tot.max() else 1])
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
                              hover="%{y}: %{x} embarques<extra></extra>", x_title="embarques", height=CHART_H)
            charts.show(fig, key="emb_pend_ffww")

    tab_mar, tab_aer = st.tabs(["Marítimo", "Aéreo"])
    with tab_mar:
        section("Marítimos en gestión", "Reservas con «Responsable de la carga» (sin los AIR).")
        with guard("KPIs marítimos"):
            riesgo_mar = mar[mar["estado_consolidacion"].isin([calc.SEMAFORO_WARN, calc.SEMAFORO_BAD])
                             & ~mar["etd_ok"]]
            kpi_row([
                KPI("Marítimos activos", fmt.fmt_int(len(mar)),
                    sub=f"<b>{fmt.fmt_int((mar['estructura'] == 'Monoproveedor').sum())}</b> mono · "
                        f"{fmt.fmt_int((mar['estructura'] == 'Consolidado').sum())} consolidado"),
                KPI("Contenedores", fmt.fmt_int(mar["contenedores"].sum())),
                KPI("Volumen activo", fmt.fmt_int(mar["m3"].sum()), unit="m³"),
                KPI("FOB activo", fmt.fmt_usd(mar["fob"].sum())),
                KPI("En riesgo", fmt.fmt_int(len(riesgo_mar)), status="bad" if len(riesgo_mar) else "ok",
                    sub="consolidación fuera de SLA, sin ETD OK"),
            ])

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

        section("Detalle de embarques en riesgo",
                "Consolidación proyectada fuera del SLA (Atención o Fuera de SLA) y todavía sin «ETD OK FFWW»: "
                "donde aún hay margen de acción. Ordenado por ETD.")
        with guard("Marítimos en riesgo"):
            if riesgo_mar.empty:
                empty("No hay marítimos en riesgo.")
            else:
                semaforo_legend()
                data_table(riesgo_mar.sort_values("etd"), [
                    ColSpec("embarque", "Embarque"), ColSpec("forwarder", "Forwarder"), ColSpec("etd", "ETD", "date"),
                    ColSpec("responsable", "Responsable de la carga"),
                    ColSpec("dias_consolidacion", "Consolidación total (d)", "days"),
                    ColSpec("sla_consolidacion", "SLA (d)", "days"),
                    ColSpec("estado_consolidacion", "Estado", "status"),
                ], key="emb_riesgo", filename="maritimos_en_riesgo", search=False)
    with tab_aer:
        aereos.render_en_curso(bundle, filters)
