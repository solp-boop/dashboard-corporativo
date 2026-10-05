"""Tests del conector de Google Sheets con la API simulada (sin red)."""
from __future__ import annotations

from services.google_sheets import GoogleSheetsSource, col_letter, find_tab


class FakeWorksheet:
    def __init__(self, title):
        self.title = title


class FakeBook:
    def __init__(self):
        self.requests = []

    def worksheets(self):
        return [FakeWorksheet("Reservas"), FakeWorksheet("Validaciones")]

    def values_batch_get(self, ranges, params=None):
        self.requests.append((list(ranges), params))
        data = {
            "'Reservas'!1:1": [["Embarque", "Empresa", "ETD"]],
            "'Reservas'!A:A": [["Embarque"], ["FCL 1"], ["FCL 2"]],
            "'Reservas'!C:C": [["ETD"], [46295], [], [46300]],   # fila 3 vacía, fila 4 extra
            "'Validaciones'": [["Puertos", "Consolidacion"], ["Ningbo", 25]],
        }
        return {"valueRanges": [{"range": r, "values": data.get(r, [])} for r in ranges]}


def make_source():
    src = GoogleSheetsSource.__new__(GoogleSheetsSource)
    src._books = {"tablero": FakeBook()}
    src._books_ids = {"tablero": "x"}
    return src


def test_col_letter():
    assert [col_letter(i) for i in (0, 25, 26, 51, 52)] == ["A", "Z", "AA", "AZ", "BA"]


def test_find_tab():
    assert find_tab(["Reservas Historicas", "Planif cargas"], "reservas históricas") == "Reservas Historicas"
    assert find_tab(["Cotizaciones Maritimos Negociad"], "Cotizaciones Maritimos Negociado") == \
        "Cotizaciones Maritimos Negociad"
    assert find_tab(["Otra"], "Reservas") is None


def test_lectura_por_columnas_en_una_sola_llamada():
    src = make_source()
    assert src.tab_titles("tablero") == ["Reservas", "Validaciones"]
    assert src.read_headers("tablero", ["Reservas"])["Reservas"] == ["Embarque", "Empresa", "ETD"]
    grids = src.read_tables("tablero", {"Reservas": [0, 2], "Validaciones": None})
    book = src._books["tablero"]
    assert len(book.requests) == 2                                 # headers + datos
    ranges, params = book.requests[-1]
    assert ranges == ["'Reservas'!A:A", "'Reservas'!C:C", "'Validaciones'"]
    assert params["valueRenderOption"] == "UNFORMATTED_VALUE"
    g = grids["Reservas"]
    assert g[0] == ["Embarque", None, "ETD"]
    assert g[1] == ["FCL 1", None, 46295]
    assert g[2] == ["FCL 2", None, None]
    assert g[3] == [None, None, 46300]
    assert grids["Validaciones"][1] == ["Ningbo", 25]


# ---------------------------------------------------------------- CSV público
import pytest

from services.google_sheets import PublicCsvSource, SourceError


class SimCsv(PublicCsvSource):
    def __init__(self, responses):
        super().__init__({"tablero": "SID"}, {"tablero": {"Reservas": 11, "Validaciones": 22}})
        self.responses = responses
        self.urls = []

    def _download(self, url):
        self.urls.append(url)
        r = self.responses[url.split("gid=")[1]]
        if isinstance(r, Exception):
            raise r
        return r


def test_csv_publico_lee_y_cachea():
    src = SimCsv({"11": 'Embarque,ETD\nFCL 1,"16/09/2026"\n', "22": "Puertos,Consolidacion\nNingbo,25\n"})
    assert src.tab_titles("tablero") == ["Reservas", "Validaciones"]
    assert src.read_headers("tablero", ["Reservas"])["Reservas"] == ["Embarque", "ETD"]
    grids = src.read_tables("tablero", {"Reservas": [0, 1], "Validaciones": None})
    assert grids["Reservas"][1] == ["FCL 1", "16/09/2026"]
    assert len(src.urls) == 2                      # cada solapa se descarga una sola vez
    assert "export?format=csv&gid=11" in src.urls[0] or "export?format=csv&gid=11" in src.urls[1]


def test_csv_publico_error_amable():
    src = SimCsv({"11": SourceError("Google rechazó la descarga de la planilla."), "22": ""})
    with pytest.raises(SourceError):
        src.read_headers("tablero", ["Reservas"])


def test_csv_publico_carga_completa_con_formato_argentino():
    from services.data_loader import build_bundle
    from tests.fakes import RESERVAS, VALIDACIONES
    import csv, io

    def to_csv(rows):
        buf = io.StringIO()
        csv.writer(buf).writerows(rows)
        return buf.getvalue()

    src = SimCsv({"11": to_csv(RESERVAS), "22": to_csv(VALIDACIONES)})
    b = build_bundle(src, {"reservas": ("tablero", "Reservas"), "validaciones": ("tablero", "Validaciones")})
    assert b.available("reservas")
    assert b.get("reservas").loc[1, "m3"] == 1234.5
    assert not b.sla_puertos.empty
