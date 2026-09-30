"""Fuente de datos en memoria para tests (imita la interfaz de GoogleSheetsSource)."""
from __future__ import annotations

import datetime as dt

from services.google_sheets import SourceError


class FakeSource:
    name = "Fake"

    def __init__(self, books: dict[str, dict[str, list[list]]], fail: set[str] | None = None):
        self.books = books
        self.fail = fail or set()
        self.calls = 0

    def _check(self, book):
        self.calls += 1
        if book in self.fail:
            raise SourceError(f"No se pudo conectar con la planilla '{book}'.")
        if book not in self.books:
            raise SourceError(f"No hay ID configurado para la planilla '{book}'.")

    def tab_titles(self, book):
        self._check(book)
        return list(self.books[book])

    def read_headers(self, book, tabs):
        self._check(book)
        return {t: self.books[book][t][0] for t in tabs}

    def read_tables(self, book, request):
        self._check(book)
        return {t: self.books[book][t] for t in request}

    def last_modified(self, book):
        return dt.datetime(2026, 9, 30, 12, 0, tzinfo=dt.timezone.utc)


RESERVAS = [
    ["Embarque", "Cant. Contenedores", "Empresa", "Destino", "Puerto / Aeropuerto", "Tipo Carga",
     "Forwarder", "Fecha de Instrucción", "Booked in Advance", "ETD OK FFWW", "ETD", "ETA",
     "F.Packeo Min", "M3", "Fob SIMI Total", "FOB Total Real", "Responsable de la carga",
     "¿ES MONOPROVEEDOR?", "DRAFT BL", "PACKING LIST FINAL", "Cotizacion agente? "],
    ["FCL 1", "1", "Bidcom SRL", "Argentina", "Ningbo", "40 HQ", "DELFIN GROUP", "01/09/2026",
     "Booked in Advance", "Ok", "20/09/2026", "05/11/2026", "25/08/2026", "60,5", "USD 10.000,00", "0",
     "Sol", "Consolidado", "SI", "SI", ""],
    ["FCL 2", "2", "bidcom srl ", "argentina", "NINGBO", "40ST", "Delfin Group", "Pendiente",
     "No Booked in Advance", "", "#N/A", "", "01/08/2026", "1.234,5", "5000", "7.500,00",
     "Sofi", "Monoproveedor", "NO", "incompleto", ""],
    ["FCL 3", "1", "Foretec SRL", "México", "Shenzhen", "Avion", "NIP", "10/09/2026",
     "", "", "15/10/2026", "20/10/2026", "01/01/1900", "3", "", "", "David", "FCL no figura en Planif Cargas",
     "", "", ""],
    ["FCL 1", "1", "Bidcom SRL", "Argentina", "Ningbo", "40 HQ", "DELFIN GROUP", "", "", "", "", "", "", "",
     "", "", "", "", "", "", ""],  # duplicado
    ["FCL 9", "", "", "", "", "", "", "", "", "", "", "", "", "0", "", "", "", "", "", "", ""],  # relleno
    ["AIR PROYECCION", "", "Bidcom SRL", "", "", "", "", "", "", "", "", "", "", "", "", "", "", "", "", "", ""],
    ["", "", "", "", "", "", "", "", "", "", "", "", "", "", "", "", "", "", "", "", ""],
]

VALIDACIONES = [
    ["Empresa", "Tipo de Embarque", "Puertos", "", "Puertos", "Consolidacion", "Transito ARG", "Total"],
    ["Bidcom srl", "20 ST", "Shenzhen", "", "Shenzhen", "30", "50", "80"],
    ["", "", "", "", "Ningbo", "25", "50", "75"],
    ["", "", "", "", "Nangtong", "25", "60", "85"],
]


def tablero(**overrides) -> dict:
    books = {"Reservas": RESERVAS, "Validaciones": VALIDACIONES}
    books.update(overrides)
    return {"tablero": books}
