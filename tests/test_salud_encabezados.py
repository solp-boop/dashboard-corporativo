import pandas as pd

from services.data_loader import DatasetQuality
from utils import salud


class B:
    def __init__(self, quality):
        self.quality = quality


def test_titulos_rotos_faltantes_y_repetidos():
    q = {"planif": DatasetQuality("planif", "Planificación", tab="Planif cargas",
                                  headers=["SO", "#REF!", "Embarque", "ETD", "embarque", None, "#N/A"],
                                  missing_required=["Fecha de Instruccion"], missing_optional=["Marca", "Prioridad"]),
         "aereos": DatasetQuality("aereos", "Seguimiento Aéreos", message="No se encontró la solapa 'SEGUIMIENTO AEREOS'.")}
    c = salud._encabezados(B(q))
    det = dict(zip(c.casos["registro"], c.casos["detalle"]))
    assert "error" in det["Columna B"] and "#N/A" in det["Columna G"]
    assert "obligatoria" in det["Columna «Fecha de Instruccion»"] and "Columna «Marca»" in det
    assert "Columna «Prioridad»" not in det                       # columna futura: no se avisa
    assert "Columnas C, E" in det and c.estado == "Roto"
    assert any(c.casos["registro"] == "Solapa")
