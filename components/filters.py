"""Barra lateral de filtros globales (dependientes) + limpiar filtros."""
from __future__ import annotations

import datetime as dt

import streamlit as st

from services.data_loader import DataBundle
from utils.filters import FILTER_FIELDS, FilterState, build_dimensions, dependent_options

PRESETS = [
    "Desde inicio de año",
    "Últimos 12 meses",
    "Últimos 90 días",
    "Próximos 90 días",
    "Todo el histórico",
    "Personalizado",
]
DEFAULT_PRESET = PRESETS[0]
_STATE_KEY = "_filters"


def _preset_range(preset: str, today: dt.date) -> tuple[dt.date | None, dt.date | None]:
    if preset == "Desde inicio de año":
        return dt.date(today.year, 1, 1), None
    if preset == "Últimos 12 meses":
        return today - dt.timedelta(days=365), today
    if preset == "Últimos 90 días":
        return today - dt.timedelta(days=90), today
    if preset == "Próximos 90 días":
        return today, today + dt.timedelta(days=90)
    return None, None


def reset_filters() -> None:
    st.session_state["f_preset"] = DEFAULT_PRESET
    for f, _ in FILTER_FIELDS:
        st.session_state[f"f_{f}"] = []
    st.session_state.pop("f_range", None)


def render_filters(bundle: DataBundle) -> FilterState:
    today = dt.date.today()
    st.markdown('<div class="side-label">Período (fecha ETD)</div>', unsafe_allow_html=True)
    st.session_state.setdefault("f_preset", DEFAULT_PRESET)
    preset = st.selectbox("Período", PRESETS, key="f_preset", label_visibility="collapsed")
    start, end = _preset_range(preset, today)
    if preset == "Personalizado":
        st.session_state.setdefault("f_range", (dt.date(today.year, 1, 1), today))
        rng = st.date_input("Rango", key="f_range", format="DD/MM/YYYY",
                            label_visibility="collapsed")
        if isinstance(rng, (tuple, list)) and len(rng) == 2:
            start, end = rng
        elif isinstance(rng, (tuple, list)) and len(rng) == 1:
            start, end = rng[0], None

    state = FilterState(start=start, end=end, selections={})
    dims = build_dimensions(bundle.datasets, state)

    st.markdown('<div class="side-label">Filtros</div>', unsafe_allow_html=True)
    for field_name, label in FILTER_FIELDS:
        key = f"f_{field_name}"
        options = dependent_options(dims, state, field_name)
        # Si un filtro anterior cambió, se descartan selecciones incompatibles.
        current = [v for v in st.session_state.get(key, []) if v in options]
        st.session_state[key] = current
        chosen = st.multiselect(label, options, key=key, placeholder="Todos")
        state.selections[field_name] = list(chosen)

    st.button("Limpiar filtros", on_click=reset_filters, width="stretch", type="secondary")
    st.session_state[_STATE_KEY] = state
    return state


def current_filters() -> FilterState:
    return st.session_state.get(_STATE_KEY) or FilterState()
