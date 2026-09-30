"""Tarjetas KPI: nombre, valor principal y, cuando aplica, referencia/SLA."""
from __future__ import annotations

from dataclasses import dataclass

import streamlit as st

from components.layout import esc


@dataclass
class KPI:
    label: str
    value: str
    unit: str = ""
    sub: str = ""            # texto secundario (puede traer <b>…</b> ya escapado)
    status: str = ""         # "", "ok", "warn", "bad"
    badge: str = ""          # texto corto del estado (ej. "Fuera de SLA")
    help: str = ""           # tooltip nativo


def kpi_row(kpis: list[KPI], columns: int | None = None) -> None:
    n = columns or max(1, len(kpis))
    cards = []
    for k in kpis:
        badge = f'<span class="badge {k.status or "info"}">{esc(k.badge)}</span>' if k.badge else ""
        unit = f'<span class="unit">{esc(k.unit)}</span>' if k.unit else ""
        sub = f'<div class="sub">{k.sub}</div>' if k.sub else ""
        title = f' title="{esc(k.help)}"' if k.help else ""
        cards.append(
            f'<div class="kpi {k.status}"{title}><div class="label">{esc(k.label)}</div>'
            f'<div class="value">{esc(k.value)}{unit}{badge}</div>{sub}</div>'
        )
    st.markdown(
        f'<div class="kpi-grid" style="grid-template-columns: repeat({n}, minmax(0, 1fr));">'
        + "".join(cards) + "</div>",
        unsafe_allow_html=True,
    )


def status_for(value: float, sla: float, higher_is_better: bool = False) -> tuple[str, str]:
    """Estado del semáforo para un valor contra su SLA."""
    from config import settings

    if value is None or sla is None or value != value or sla != sla:
        return "", ""
    tol = settings.SLA_WARNING_TOLERANCE
    if higher_is_better:
        if value >= sla:
            return "ok", "En objetivo"
        if value >= sla * (1 - tol):
            return "warn", "Atención"
        return "bad", "Bajo objetivo"
    if value <= sla:
        return "ok", "Dentro de SLA"
    if value <= sla * (1 + tol):
        return "warn", "Atención"
    return "bad", "Fuera de SLA"
