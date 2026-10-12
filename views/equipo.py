"""Equipo y agentes (nivel 2): desempeño de los analistas (responsable de la carga) y de los forwarders.

Antes era una pestaña dentro de «Operación en curso» y los agentes estaban plegados. Período = el de la barra lateral
(por defecto, desde inicio de año).
"""
from __future__ import annotations

from components.layout import guard
from views import agentes, analistas


def render() -> None:
    with guard("Analistas"):
        analistas.render()
    with guard("Agentes"):
        agentes.render()
