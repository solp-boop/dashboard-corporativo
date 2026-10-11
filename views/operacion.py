"""Operación en curso (nivel 2): lo que está en tránsito y la carga del equipo.

«Lo que viene» y «Embarcado» se sacaron porque repetían Panorama («Nuestro año» y la proyección por Planif cargas).
Las páginas pipeline.py e historico.py siguen en el repo por si se quieren volver a mostrar.
"""
from __future__ import annotations

import streamlit as st

from components.layout import guard
from views import agentes, analistas, embarques


def render() -> None:
    tab_curso, tab_equipo = st.tabs(["En curso", "Equipo y agentes"])
    with tab_curso:
        embarques.render()
    with tab_equipo:
        with guard("Analistas"):
            analistas.render()
        with st.expander("Agentes: instrucción → ETD, desvío de ETD y certificación por forwarder"):
            agentes.render()
