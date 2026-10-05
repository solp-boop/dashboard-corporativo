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


def cert_status(pct: float) -> tuple[str, str]:
    """Flete certificado (lo certificado por fuera): bien hasta el máximo, mal por encima."""
    from config import settings

    if pct is None or pct != pct:
        return "", ""
    mx = settings.KPI_CERTIFICACION_MAX
    if pct <= mx:
        return "ok", "En objetivo"
    if pct <= mx * (1 + settings.SLA_WARNING_TOLERANCE):
        return "warn", "Atención"
    return "bad", "Sobre el máximo"


def cert_sub() -> str:
    from config import settings
    return f"Máximo ≤ {fmt_pct_local(settings.KPI_CERTIFICACION_MAX)} · menos es mejor"


def fmt_pct_local(v: float) -> str:
    from utils import formatting as fmt
    return fmt.fmt_pct(v)


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
