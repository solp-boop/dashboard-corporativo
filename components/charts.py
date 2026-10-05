"""Gráficos Plotly con un estilo único.

Reglas: un solo eje Y por gráfico, máximo 4 series (resto en "Otros"),
colores por entidad en orden fijo, semáforo solo para cumplimiento,
tooltips con formato es-AR y sin decimales innecesarios.
"""
from __future__ import annotations

import plotly.graph_objects as go
import streamlit as st

from config import settings

C = settings.COLORS
STATUS_COLORS = {
    "Dentro de SLA": C["green"],
    "Atención": C["amber"],
    "Fuera de SLA": C["red"],
}
FONT = "Inter, 'Segoe UI', system-ui, -apple-system, sans-serif"
PLOTLY_CONFIG = {"displayModeBar": False, "responsive": True, "locale": "es"}


def color_map(categories: list[str], other_label: str = "Otros") -> dict[str, str]:
    """Color fijo por entidad según el orden recibido (no por ranking dinámico)."""
    cmap = {}
    for i, c in enumerate(categories):
        cmap[c] = settings.SERIES[i] if i < len(settings.SERIES) else settings.SERIES_OTHER
    cmap[other_label] = settings.SERIES_OTHER
    return cmap


def theme(fig: go.Figure, height: int = 340, y_title: str = "", x_title: str = "",
          y_suffix: str = "", y_tickformat: str = ",.0f", legend: bool | None = None,
          horizontal: bool = False) -> go.Figure:
    fig.update_layout(
        height=height,
        margin=dict(l=8, r=12, t=28, b=8),
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        font=dict(family=FONT, size=12, color=C["text"]),
        separators=",.",
        hoverlabel=dict(bgcolor="white", bordercolor=C["grey_light"], font=dict(family=FONT, size=12)),
        legend=dict(orientation="h", yanchor="bottom", y=1.0, xanchor="left", x=0,
                    font=dict(size=11), title_text=""),
        bargap=0.28,
        bargroupgap=0.06,
        showlegend=legend if legend is not None else None,
        hovermode="x unified" if not horizontal else "closest",
    )
    value_axis = dict(
        title=dict(text=y_title, font=dict(size=11, color=C["slate"])),
        gridcolor="#EEF1F4", zeroline=False, tickformat=y_tickformat, ticksuffix=y_suffix,
        tickfont=dict(size=11, color=C["slate"]), rangemode="tozero", automargin=True,
    )
    cat_axis = dict(
        title=dict(text=x_title, font=dict(size=11, color=C["slate"])),
        showgrid=False, linecolor=C["grey_light"], tickfont=dict(size=11, color=C["slate"]),
        automargin=True,
    )
    if horizontal:
        fig.update_xaxes(**value_axis)
        fig.update_yaxes(**cat_axis)
    else:
        fig.update_yaxes(**value_axis)
        fig.update_xaxes(**cat_axis)
    fig.update_traces(selector=dict(type="bar"), marker_line_width=0)
    return fig


def show(fig: go.Figure, key: str | None = None) -> None:
    st.plotly_chart(fig, theme=None, config=PLOTLY_CONFIG, key=key)


def hbar(labels, values, text=None, color=None, hover=None, height=None, x_title="",
         x_suffix="", ref_value: float | None = None, ref_label: str = "") -> go.Figure:
    """Barras horizontales ordenadas (la más grande arriba)."""
    fig = go.Figure(go.Bar(
        y=list(labels), x=list(values), orientation="h",
        marker=dict(color=color or settings.SERIES[0], cornerradius=4),
        text=text, textposition="outside", cliponaxis=False,
        hovertemplate=hover or "%{y}: %{x:,.0f}<extra></extra>",
    ))
    h = height or max(220, 30 * len(list(labels)) + 70)
    theme(fig, height=h, y_title=x_title, y_suffix=x_suffix, horizontal=True, legend=False)
    fig.update_yaxes(autorange="reversed")
    vals = [v for v in values if v == v]
    top = max(vals + ([ref_value] if ref_value is not None and ref_value == ref_value else []), default=0)
    if top > 0:
        # Espacio a la derecha para las etiquetas de texto.
        fig.update_xaxes(range=[0, top * 1.3])
    if ref_value is not None and ref_value == ref_value:
        fig.add_vline(x=ref_value, line=dict(color=C["slate"], width=1.5, dash="dash"),
                      annotation_text=ref_label, annotation_position="top",
                      annotation_font=dict(size=11, color=C["slate"]))
    return fig
