"""Operación en curso (nivel 2): lo que está en tránsito.
El desempeño de analistas y agentes pasó a su propia página (views/equipo.py).

«Lo que viene» y «Embarcado» se sacaron porque repetían Panorama («Nuestro año» y la proyección por Planif cargas).
Las páginas pipeline.py e historico.py siguen en el repo por si se quieren volver a mostrar.
"""
from __future__ import annotations

from views import embarques


def render() -> None:
    embarques.render()
