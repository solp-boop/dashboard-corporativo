"""Dashboard Ejecutivo · Comercio Exterior / Logística Internacional.

Punto de entrada. Ejecutar con:  streamlit run streamlit_app.py
"""
from __future__ import annotations

import streamlit as st

st.set_page_config(
    page_title="Dashboard Ejecutivo · Comex",
    page_icon="🚢",
    layout="wide",
    initial_sidebar_state="expanded",
)

from components.filters import render_filters  # noqa: E402
from components.layout import guard, load_css, page_header  # noqa: E402
from services.data_loader import SourceError, clear_cache, get_data  # noqa: E402
from utils.logger import get_logger  # noqa: E402
from views import (  # noqa: E402
    aereos, agentes, alertas, buscar, calidad, cotizaciones, embarques, fletes_pagados, historico, lead_times, pipeline,
    resumen,
)

log = get_logger("app")
load_css()

PAGES = {
    "General": [
        st.Page(resumen.render, title="Resumen ejecutivo", icon=":material/dashboard:",
                url_path="resumen", default=True),
    ],
    "Alertas": [
        st.Page(alertas.render, title="Alertas", icon=":material/notifications:", url_path="alertas"),
    ],
    "Operación": [
        st.Page(pipeline.render, title="Pipeline de origen", icon=":material/inventory_2:", url_path="pipeline"),
        st.Page(embarques.render, title="Embarques en curso", icon=":material/directions_boat:", url_path="embarques"),
        st.Page(aereos.render, title="Aéreos", icon=":material/flight:", url_path="aereos"),
    ],
    "Desempeño": [
        st.Page(lead_times.render, title="Lead times y SLA", icon=":material/timer:", url_path="sla"),
        st.Page(agentes.render, title="Agentes y analistas", icon=":material/groups:", url_path="agentes"),
        st.Page(historico.render, title="Histórico", icon=":material/insights:", url_path="historico"),
    ],
    "Fletes": [
        st.Page(fletes_pagados.render, title="Fletes y gastos pagados", icon=":material/payments:",
                url_path="fletes"),
        st.Page(cotizaciones.render, title="Cotizaciones", icon=":material/request_quote:",
                url_path="cotizaciones"),
    ],
    "Herramientas": [
        st.Page(buscar.render, title="Buscar SO / embarque", icon=":material/search:", url_path="buscar"),
        st.Page(calidad.render, title="Calidad de datos", icon=":material/fact_check:", url_path="calidad"),
    ],
}

pg = st.navigation(PAGES, position="sidebar")

with st.sidebar:
    st.markdown('<div class="side-brand">BIDCOM · Comex</div>'
                '<div class="side-sub">Logística internacional</div>', unsafe_allow_html=True)
    if st.button("↻  Actualizar datos", width="stretch", type="primary",
                 help="Vuelve a consultar la planilla (los datos se refrescan solos cada 10 minutos)."):
        clear_cache()
        st.rerun()

try:
    bundle = get_data()
except SourceError as exc:
    page_header(pg.title, None, None)
    st.error(f"No se pudieron cargar los datos. {exc}")
    st.caption("Probá con «Actualizar datos». Si el problema sigue, revisá la configuración de "
               "credenciales (ver README).")
    st.stop()

with st.sidebar:
    filters = render_filters(bundle)
    if bundle.errors:
        with st.expander("Avisos de la carga", expanded=False):
            for e in bundle.errors:
                st.caption(f"• {e}")

page_header(pg.title, bundle, filters)
with guard(pg.title):  # red de seguridad: un error inesperado nunca muestra un traceback
    pg.run()
