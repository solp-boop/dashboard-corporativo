"""Operación en curso (nivel 2): lo que está en tránsito, lo que viene, lo que se embarcó y la carga del equipo.

Reúne lo que antes eran las páginas Embarques en curso, Pipeline de origen, Histórico, Analistas y Agentes,
y el bloque «Nuestro año» del Resumen.
"""
from __future__ import annotations

import streamlit as st

from components.layout import guard
from views import agentes, analistas, embarques, historico, pipeline, resumen
from views._common import ctx


def render() -> None:
    tab_curso, tab_viene, tab_emb, tab_equipo = st.tabs(
        ["En curso", "Lo que viene", "Embarcado", "Equipo y agentes"])
    with tab_curso:
        embarques.render()
    with tab_viene:
        pipeline.render()
    with tab_emb:
        bundle, filters = ctx()
        with guard("Nuestro año"):
            resumen.render_anio(bundle, filters, numerado=False)
        with st.expander("Comparación con el año anterior y aéreos históricos"):
            historico.render()
    with tab_equipo:
        with guard("Analistas"):
            analistas.render()
        with st.expander("Agentes: instrucción → ETD, desvío de ETD y certificación por forwarder"):
            agentes.render()
