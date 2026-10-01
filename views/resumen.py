"""Resumen ejecutivo: ¿cómo estamos?, ¿cumplimos SLA?, ¿qué requiere atención?"""
from __future__ import annotations

import numpy as np
import pandas as pd
import plotly.graph_objects as go

from components import charts
from components.kpi_cards import KPI, kpi_row, status_for
from components.layout import chart_title, coverage, empty, filter_notes, guard, require, section
from components.tables import ColSpec, data_table
from config import settings
from config.mappings import MODOS_MARITIMOS
from utils import calculations as calc
from utils import formatting as fmt
from views._common import (ctx, en_curso, filtered, kpis_en_curso, month_labels, periodo_txt, stat_sub,
                           today)


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
            f"Embarques marítimos que zarparon {periodo} (período de la barra lateral). "
            "La segunda tarjeta muestra solo el último mes cerrado. "
            "Consolidación = ETD − fecha de packeo mínima; los tiempos son medianas.")
    hist_all = require(bundle, "historicas")
    if hist_all is not None:
        with guard("Cumplimiento de SLA"):
            hist = filtered(bundle, "historicas", filters)
            hist = hist[hist["modo"].isin(MODOS_MARITIMOS) & (hist["etd"] <= today())]
            tot = calc.describe(hist["dias_total"])
            pct, n_pct = calc.cumplimiento(hist["dias_consolidacion"], hist["sla_consolidacion"])

            last, prev = calc.last_closed_months(hist["etd"])
            m = calc.month_start(hist["etd"])
            p_last, _ = calc.cumplimiento(hist.loc[m == last, "dias_consolidacion"], hist.loc[m == last, "sla_consolidacion"])
            p_prev, _ = calc.cumplimiento(hist.loc[m == prev, "dias_consolidacion"], hist.loc[m == prev, "sla_consolidacion"])
            delta = (p_last - p_prev) if not (np.isnan(p_last) or np.isnan(p_prev)) else np.nan
            n_ok = int((hist["dias_consolidacion"] <= hist["sla_consolidacion"]).sum())
            cards = [KPI("Cumplimiento SLA · período",
                         fmt.fmt_pct(pct) if n_pct >= settings.MIN_SAMPLE else "—",
                         sub=f"<b>{fmt.fmt_int(n_ok)}</b> de {fmt.fmt_int(n_pct)} embarques dentro del SLA")]
            mes_last = fmt.fmt_month(last, long=True).split()[0]
            if np.isnan(p_last):
                cards.append(KPI(f"Cumplimiento SLA · {mes_last.lower()}", "—", sub="Sin embarques ese mes"))
            else:
                if np.isnan(delta):
                    comp = ""
                elif round(delta * 100) == 0:
                    comp = f"Igual que {fmt.fmt_month(prev, long=True).split()[0].lower()}"
                else:
                    comp = (f"{'▲' if delta > 0 else '▼'} {fmt.fmt_int(abs(delta * 100))} puntos vs "
                            f"{fmt.fmt_month(prev, long=True).split()[0].lower()} ({fmt.fmt_pct(p_prev)})")
                cards.append(KPI(f"Cumplimiento SLA · {mes_last.lower()}", fmt.fmt_pct(p_last),
                                 sub=f"Último mes cerrado<br>{comp}"))
            for est in ("Monoproveedor", "Consolidado"):
                sub = hist[hist["estructura"] == est]
                s = calc.describe(sub["dias_consolidacion"])
                sla_ref = float(sub["sla_consolidacion"].median()) if len(sub) else np.nan
                stt, badge = status_for(s.median, sla_ref) if s.enough else ("", "")
                cards.append(KPI(f"Consolidación {est.lower()}", fmt.fmt_int(s.median) if s.enough else "—",
                                 unit="d", status=stt, badge=badge,
                                 sub=f"SLA {fmt.fmt_int(sla_ref)} d · " + stat_sub(s)))
            sla_tot = float(hist["sla_total"].median()) if len(hist) else np.nan
            s_tot, b_tot = status_for(tot.median, sla_tot) if tot.enough else ("", "")
            cards.append(KPI("Fin de producción → ETA", fmt.fmt_int(tot.median) if tot.enough else "—",
                             unit="d", status=s_tot, badge=b_tot,
                             sub=f"Target {fmt.fmt_int(sla_tot)} d · " + stat_sub(tot)))
            kpi_row(cards)
            cons = calc.describe(hist["dias_consolidacion"])
            coverage(cons.n, len(hist), "embarques con fechas de packeo y ETD válidas",
                     f"fin de producción → ETA: {fmt.fmt_int(tot.n)} con fecha de fin de producción")

            c1, c2 = st_columns()
            with c1:
                chart_title("Cumplimiento de SLA de consolidación por mes",
                            "% de embarques con consolidación dentro del SLA (mes de ETD)")
                g = hist.dropna(subset=["dias_consolidacion"]).assign(mes=m)
                g = g.assign(ok=g["dias_consolidacion"] <= g["sla_consolidacion"]) \
                    .groupby("mes").agg(pct=("ok", "mean"), n=("ok", "size")).reset_index()
                g = g[g["n"] > 0].tail(12)
                if g.empty:
                    empty()
                else:
                    fig = go.Figure(go.Bar(
                        x=month_labels(g["mes"]), y=g["pct"] * 100,
                        marker=dict(color=settings.SERIES[0], cornerradius=4),
                        text=[fmt.fmt_pct(v) for v in g["pct"]], textposition="outside", cliponaxis=False,
                        customdata=g["n"],
                        hovertemplate="%{x}<br>Cumplimiento: %{y:.0f} %<br>Embarques: %{customdata}<extra></extra>",
                    ))
                    charts.theme(fig, y_suffix=" %", legend=False)
                    fig.update_yaxes(range=[0, 110])
                    charts.show(fig, key="res_sla_mes")
            with c2:
                chart_title("¿Dónde se demora la consolidación?",
                            f"Embarques consolidados · mediana por puerto vs SLA del puerto "
                            f"(≥ {settings.MIN_SAMPLE} embarques)")
                hc = hist[hist["estructura"] == "Consolidado"]
                by = calc.median_by(hc, "puerto", "dias_consolidacion", min_n=settings.MIN_SAMPLE)
                if by.empty:
                    empty()
                else:
                    sla_port = hc.groupby("puerto")["sla_consolidacion"].median()
                    by["sla"] = by["puerto"].map(sla_port)
                    by["estado"] = calc.semaforo(by["mediana"], by["sla"])
                    by = by.sort_values("mediana", ascending=False).head(10)
                    fig = charts.hbar(
                        by["puerto"], by["mediana"],
                        text=[f"{fmt.fmt_int(v)} d" for v in by["mediana"]],
                        color=[charts.STATUS_COLORS.get(e, settings.SERIES[0]) for e in by["estado"]],
                        hover=None, x_title="días", )
                    fig.update_traces(customdata=np.stack([by["n"], by["sla"], by["estado"].fillna("")], axis=1),
                                      hovertemplate="%{y}<br>Mediana: %{x:.0f} d<br>SLA: %{customdata[1]:.0f} d"
                                                    "<br>%{customdata[2]}<br>n=%{customdata[0]}<extra></extra>")
                    fig.update_traces(textposition="inside", insidetextanchor="end",
                                      textfont=dict(color="white"), selector=dict(type="bar"))
                    fig.add_trace(go.Scatter(x=by["sla"], y=by["puerto"], mode="markers", name="SLA",
                                             marker=dict(symbol="line-ns", size=18, line=dict(width=2.5, color=settings.COLORS["navy"])),
                                             hovertemplate="SLA: %{x:.0f} d<extra></extra>"))
                    fig.update_layout(showlegend=False)
                    charts.show(fig, key="res_sla_puerto")
                    from components.layout import semaforo_legend
                    semaforo_legend()

    # ------------------------------------------------------------------ aéreos
    section("Cumplimiento de SLA · aéreos")
    st_placeholder()

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


def st_columns():
    import streamlit as st

    return st.columns(2, gap="medium")


def st_placeholder():
    from components.layout import empty as _empty

    _empty("Espacio reservado para el SLA de aéreos: se arma con la definición que nos vas a pasar.")
