"""Visualizaciones de SLA: gráfico mensual con mes en curso parcial y tabla de cierre."""
from __future__ import annotations

import html

import pandas as pd
import plotly.graph_objects as go
import streamlit as st

from components import charts
from config import settings
from utils import formatting as fmt
from utils.sla import Celda, Cierre

STATUS = {"ok": settings.COLORS["green"], "warn": settings.COLORS["amber"], "bad": settings.COLORS["red"]}


def compliance_chart(monthly: pd.DataFrame, today: pd.Timestamp, key: str, height: int = 300) -> None:
    """Barras de % dentro del SLA por mes; el mes en curso va claro y rayado ('parcial')."""
    if monthly.empty:
        st.markdown('<div class="empty">Sin embarques con datos suficientes.</div>', unsafe_allow_html=True)
        return
    this_month = today.to_period("M").to_timestamp()
    m = monthly.sort_values("mes").tail(13)
    labels = [fmt.fmt_month(x) + (" (parcial)" if x == this_month else "") for x in m["mes"]]
    partial = [x == this_month for x in m["mes"]]
    colors = [settings.SERIES[1] if p else settings.SERIES[0] for p in partial]
    fig = go.Figure(go.Bar(
        x=labels, y=m["pct"] * 100,
        marker=dict(color=colors, cornerradius=4,
                    pattern=dict(shape=["/" if p else "" for p in partial], fgcolor="white", size=6)),
        text=[fmt.fmt_pct(v) for v in m["pct"]], textposition="outside", cliponaxis=False,
        customdata=m["n"],
        hovertemplate="%{x}<br>Dentro del SLA: %{y:.0f} %<br>Embarques: %{customdata}<extra></extra>",
    ))
    if settings.CUMPLIMIENTO_OBJETIVO is not None:
        fig.add_hline(y=settings.CUMPLIMIENTO_OBJETIVO * 100,
                      line=dict(color=settings.COLORS["slate"], width=1.2, dash="dash"),
                      annotation_text=f"Objetivo {fmt.fmt_pct(settings.CUMPLIMIENTO_OBJETIVO)}",
                      annotation_position="top left",
                      annotation_font=dict(size=11, color=settings.COLORS["slate"]))
    charts.theme(fig, height=height, y_suffix=" %", legend=False)
    fig.update_yaxes(range=[0, 110])
    charts.show(fig, key=key)


def _fmt_celda(c: Celda) -> str:
    if c.valor != c.valor:
        return '<td class="na">—</td>'
    v = fmt.fmt_pct(c.valor) if c.tipo == "pct" else f"{fmt.fmt_int(c.valor)} d"
    dot = f'<i class="dot {c.estado}"></i>' if c.estado else ""
    small = (f'<span class="n">n={c.n}</span>' if c.n < settings.MIN_SAMPLE
             else f'<span class="n">n={fmt.fmt_int(c.n)}</span>')
    return f"<td>{dot}{html.escape(v)}{small}</td>"


def scorecard_table(sc: Cierre) -> None:
    head = "".join(f"<th>{html.escape(c)}</th>" for c in ["Indicador"] + sc.columnas)
    rows = []
    for label, cells in sc.filas:
        tds = []
        for c in cells:
            tds.append(f'<td class="var">{html.escape(c)}</td>' if isinstance(c, str) else _fmt_celda(c))
        rows.append(f"<tr><th class='rowh'>{html.escape(label)}</th>{''.join(tds)}</tr>")
    st.markdown(f'<div class="scorecard"><table><thead><tr>{head}</tr></thead>'
                f'<tbody>{"".join(rows)}</tbody></table></div>', unsafe_allow_html=True)
    obj = (f"cumplimiento contra el objetivo de {fmt.fmt_pct(settings.CUMPLIMIENTO_OBJETIVO)}"
           if settings.CUMPLIMIENTO_OBJETIVO is not None else "cumplimiento sin objetivo definido")
    st.caption(f"Semáforo: tiempos contra su SLA; {obj}. Sin color cuando hay menos de "
               f"{settings.MIN_SAMPLE} embarques (n). «Proyectado» suma a lo ya zarpado las Reservas con ETD en el mes.")
