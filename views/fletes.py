"""Fletes y cotizaciones (planilla «Cotización fletes internacionales»)."""
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
from utils import calculations as calc
from utils import formatting as fmt
from views._common import ctx, filtered, month_labels, today

TIPOS = ["40ST/40HQ", "20ST", "40NOR"]


def best_by_forwarder(d: pd.DataFrame) -> pd.DataFrame:
    """Mejor tarifa de cada forwarder (con su POL y línea)."""
    idx = d.groupby("forwarder")["flete"].idxmin()
    return d.loc[idx].sort_values("flete")


def market(d: pd.DataFrame) -> tuple[float, float, str]:
    """(promedio de mercado, mejor tarifa, forwarder de la mejor tarifa).

    El promedio se calcula sobre la mejor tarifa de cada forwarder, para que un
    agente con muchas líneas cotizadas no pese más que otro.
    """
    if d.empty:
        return np.nan, np.nan, ""
    best = best_by_forwarder(d)
    return float(best["flete"].mean()), float(best["flete"].iloc[0]), str(best["forwarder"].iloc[0])


def render() -> None:
    bundle, filters = ctx()
    base = require(bundle, "cotizaciones")
    if base is None:
        return
    # El período no aplica a las vigentes: se usa la validez de cada cotización.
    df = filtered(bundle, "cotizaciones", filters, use_period=False)
    filter_notes(base, filters.without_period(), "Cotizaciones")
    st.caption("Filtros que aplican: puerto (POL) y forwarder. El período se usa solo en la evolución histórica.")

    tipo = st.segmented_control("Tipo de contenedor", TIPOS, default=TIPOS[0], key="fl_tipo") or TIPOS[0]
    t = today()
    d_tipo = df[df["tipo_ctnr"] == tipo]
    vig = d_tipo[(d_tipo["validez_desde"] <= t) & (d_tipo["validez_hasta"] >= t)]

    section(f"Cotizaciones vigentes hoy · {tipo}",
            f"Validez desde ≤ {t:%d/%m/%Y} ≤ validez hasta. Target = promedio de mercado − "
            f"{fmt.fmt_pct(settings.TARGET_DESCUENTO_FLETE)}.")
    with guard("KPIs de fletes"):
        prom, best, best_ffww = market(vig)
        target = prom * (1 - settings.TARGET_DESCUENTO_FLETE) if prom == prom else np.nan
        loc = df[(df["validez_desde"] <= t) & (df["validez_hasta"] >= t) & (df["locales_arg"] > 0)]
        loc_best = loc.groupby("forwarder")["locales_arg"].min().sort_values()
        kpi_row([
            KPI("Forwarders cotizando", fmt.fmt_int(vig["forwarder"].nunique()),
                sub=f"<b>{fmt.fmt_int(len(vig))}</b> tarifas vigentes"),
            KPI("Promedio de mercado", fmt.fmt_usd(prom, compact=False), sub="Mejor tarifa de cada forwarder"),
            KPI("Mejor tarifa", fmt.fmt_usd(best, compact=False), sub=f"<b>{best_ffww}</b>" if best_ffww else ""),
            KPI("Target", fmt.fmt_usd(target, compact=False),
                sub=(f"Mejor vs target: <b>{fmt.fmt_pct((best - target) / target, signed=True)}</b>"
                     if target == target and best == best else "")),
            KPI("Gastos locales ARG", fmt.fmt_usd(loc_best.mean() if len(loc_best) else np.nan, compact=False),
                sub=(f"Menor <b>{fmt.fmt_usd(loc_best.iloc[0], compact=False)}</b> ({loc_best.index[0]}) · "
                     f"mayor {fmt.fmt_usd(loc_best.iloc[-1], compact=False)}") if len(loc_best) else "Sin datos"),
        ])

    c1, c2 = st.columns(2, gap="medium")
    with c1, guard("Tarifa por forwarder"):
        chart_title("Mejor tarifa vigente por forwarder", f"{tipo} · USD por contenedor")
        if vig.empty:
            empty("No hay cotizaciones vigentes para este tipo de contenedor.")
        else:
            b = best_by_forwarder(vig)
            fig = charts.hbar(
                b["forwarder"], b["flete"], text=[fmt.fmt_usd(v, compact=False) for v in b["flete"]],
                x_title="USD", ref_value=target, ref_label="Target")
            fig.update_traces(customdata=np.stack([b["puerto"].fillna(""), b["linea"].fillna("")], axis=1),
                              hovertemplate="%{y}<br>USD %{x:,.0f}<br>POL: %{customdata[0]} · "
                                            "Línea: %{customdata[1]}<extra></extra>")
            fig.add_vline(x=prom, line=dict(color=settings.COLORS["grey"], width=1.5, dash="dot"),
                          annotation_text="Promedio", annotation_position="bottom",
                          annotation_font=dict(size=11, color=settings.COLORS["slate"]))
            charts.show(fig, key="fl_ffww")

    with c2, guard("Evolución mensual"):
        chart_title("Evolución mensual del mercado", f"{tipo} · mes de inicio de validez · últimos 12 meses")
        h = filtered(bundle, "cotizaciones", filters)
        h = h[h["tipo_ctnr"] == tipo].dropna(subset=["validez_desde"])
        h = h[h["validez_desde"] <= t]
        if h.empty:
            empty()
        else:
            h["mes"] = calc.month_start(h["validez_desde"])
            rows = []
            for mes, d in h.groupby("mes"):
                p, bst, _ = market(d)
                rows.append({"mes": mes, "prom": p, "mejor": bst, "n": d["forwarder"].nunique()})
            g = pd.DataFrame(rows).tail(12)
            g["target"] = g["prom"] * (1 - settings.TARGET_DESCUENTO_FLETE)
            x = month_labels(g["mes"])
            fig = go.Figure()
            fig.add_scatter(x=x, y=g["prom"], name="Promedio de mercado", mode="lines+markers",
                            line=dict(color=settings.SERIES[0], width=2), marker=dict(size=8),
                            customdata=g["n"], hovertemplate="Promedio: USD %{y:,.0f} (%{customdata} forwarders)<extra></extra>")
            fig.add_scatter(x=x, y=g["mejor"], name="Mejor oferta", mode="lines+markers",
                            line=dict(color=settings.SERIES[2], width=2), marker=dict(size=8),
                            hovertemplate="Mejor: USD %{y:,.0f}<extra></extra>")
            fig.add_scatter(x=x, y=g["target"], name="Target", mode="lines",
                            line=dict(color=settings.COLORS["slate"], width=1.5, dash="dash"),
                            hovertemplate="Target: USD %{y:,.0f}<extra></extra>")
            charts.theme(fig, y_title="USD")
            charts.show(fig, key="fl_mes")

    section("Tarifas vigentes")
    with guard("Tabla de tarifas"):
        data_table(vig.sort_values("flete"), [
            ColSpec("forwarder", "Forwarder"), ColSpec("agente", "Agente en origen"), ColSpec("puerto", "POL"),
            ColSpec("linea", "Línea"), ColSpec("servicio", "Servicio"), ColSpec("flete", "Flete (USD)", "usd"),
            ColSpec("locales_arg", "Locales ARG (USD)", "usd"), ColSpec("tt", "TT (d)", "days"),
            ColSpec("dias_libres", "Días libres"), ColSpec("transbordo", "Transbordo"),
            ColSpec("validez_desde", "Desde", "date"), ColSpec("validez_hasta", "Hasta", "date"),
            ColSpec("comentarios", "Comentarios", width="large"),
        ], key="fl_tabla", filename=f"cotizaciones_vigentes_{tipo.replace('/', '-')}")
