"""Tests de la app completa con el runner de Streamlit (AppTest).

Por defecto usan datos sintéticos. Para probar contra un export real de la
planilla, definí DASHBOARD_TEST_XLSX (y opcionalmente
DASHBOARD_TEST_COTIZACIONES_XLSX) con la ruta al .xlsx.
"""
from __future__ import annotations

import os
from pathlib import Path

import pytest
from streamlit.testing.v1 import AppTest

ROOT = Path(__file__).resolve().parent.parent
RUNNER = str(ROOT / "tests" / "page_runner.py")
PAGES = ["resumen", "alertas", "pipeline", "embarques", "aereos", "lead_times", "agentes", "fletes_pagados",
         "cotizaciones", "historico", "calidad", "buscar"]

REAL = os.environ.get("DASHBOARD_TEST_XLSX")
REAL_COT = os.environ.get("DASHBOARD_TEST_COTIZACIONES_XLSX")


@pytest.fixture(scope="session")
def local_files(tmp_path_factory):
    if REAL:
        files = {"tablero": REAL}
        if REAL_COT:
            files["cotizaciones"] = REAL_COT
        return files
    from tests.synthetic import write_synthetic

    return write_synthetic(tmp_path_factory.mktemp("data"))


def run_page(page: str, files: dict, setup=None) -> AppTest:
    at = AppTest.from_file(RUNNER, default_timeout=120)
    at.secrets["local_files"] = files
    at.secrets["test_page"] = page
    at.run()
    if setup:
        setup(at)
    return at


def assert_clean(at: AppTest):
    assert not at.exception, [e.value for e in at.exception]
    # guard() convierte errores en st.info con este texto: no debería aparecer ninguno
    bad = [i.value for i in at.info if "No se pudo" in i.value]
    assert not bad, bad


@pytest.mark.parametrize("page", PAGES)
def test_pagina_renderiza_sin_errores(page, local_files):
    at = run_page(page, local_files)
    assert_clean(at)


def test_filtros_dependientes_y_limpiar(local_files):
    at = run_page("embarques", local_files)
    empresa = at.sidebar.multiselect(key="f_empresa")
    puerto = at.sidebar.multiselect(key="f_puerto")
    all_ports = set(puerto.options)
    first = empresa.options[0]
    empresa.set_value([first]).run()
    assert_clean(at)
    ports_after = set(at.sidebar.multiselect(key="f_puerto").options)
    assert ports_after <= all_ports
    # Elegir un puerto y luego limpiar
    if ports_after:
        at.sidebar.multiselect(key="f_puerto").set_value([sorted(ports_after)[0]]).run()
        assert_clean(at)
    at.sidebar.button[0].click().run()          # "Limpiar filtros"
    assert at.sidebar.multiselect(key="f_empresa").value == []
    assert at.sidebar.multiselect(key="f_puerto").value == []
    assert_clean(at)


def test_periodo_personalizado_y_todo(local_files):
    at = run_page("lead_times", local_files)
    at.sidebar.selectbox(key="f_preset").set_value("Todo el histórico").run()
    assert_clean(at)
    at.sidebar.selectbox(key="f_preset").set_value("Personalizado").run()
    assert_clean(at)


def test_filtro_que_vacia_todo_no_rompe(local_files):
    def setup(at):
        at.sidebar.selectbox(key="f_preset").set_value("Próximos 90 días").run()
    for page in PAGES:
        at = run_page(page, local_files, setup)
        assert_clean(at)


def test_buscador(local_files):
    at = run_page("buscar", local_files)
    at.text_input(key="search_q").input("2679").run()
    assert_clean(at)
    assert any("embarque" in m.value and "SO" in m.value for m in at.markdown)
    at.text_input(key="search_q").input("zzzz-no-existe").run()
    assert_clean(at)


def test_cache_no_consulta_la_fuente_al_filtrar(monkeypatch):
    """Los filtros trabajan en memoria: la planilla se lee una sola vez hasta 'Actualizar datos'."""
    from services import data_loader
    from tests.fakes import FakeSource, tablero

    src = FakeSource(tablero())
    monkeypatch.setattr(data_loader, "make_source", lambda: src)
    monkeypatch.setattr(data_loader.settings, "DATASET_SOURCES",
                        {"reservas": ("tablero", "Reservas"), "validaciones": ("tablero", "Validaciones")})
    data_loader.clear_cache()

    at = AppTest.from_file(RUNNER, default_timeout=60)
    at.secrets["test_page"] = "embarques"
    at.run()
    assert_clean(at)
    calls_after_load = src.calls
    assert calls_after_load > 0
    for opts in (["Bidcom SRL"], [], ["Foretec SRL"]):
        at.sidebar.multiselect(key="f_empresa").set_value(opts).run()
        assert_clean(at)
    at.sidebar.selectbox(key="f_preset").set_value("Todo el histórico").run()
    assert src.calls == calls_after_load        # ninguna consulta nueva

    data_loader.clear_cache()                   # botón "Actualizar datos"
    at.run()
    assert src.calls > calls_after_load
    data_loader.clear_cache()


def test_fuente_caida_muestra_mensaje_amable(monkeypatch):
    from services import data_loader
    from tests.fakes import FakeSource, tablero

    src = FakeSource(tablero(), fail={"tablero"})
    monkeypatch.setattr(data_loader, "make_source", lambda: src)
    data_loader.clear_cache()
    data_loader._last_good().clear()
    at = AppTest.from_file(str(ROOT / "streamlit_app.py"), default_timeout=60)
    at.run()
    assert not at.exception
    assert any("No se pudieron cargar los datos" in e.value for e in at.error)
    data_loader.clear_cache()


def test_fuente_caida_usa_ultima_carga_valida(monkeypatch):
    from services import data_loader
    from tests.fakes import FakeSource, tablero

    ok = FakeSource(tablero())
    monkeypatch.setattr(data_loader.settings, "DATASET_SOURCES",
                        {"reservas": ("tablero", "Reservas"), "validaciones": ("tablero", "Validaciones")})
    monkeypatch.setattr(data_loader, "make_source", lambda: ok)
    data_loader.clear_cache()
    at = AppTest.from_file(str(ROOT / "streamlit_app.py"), default_timeout=60)
    at.run()
    assert not at.exception
    monkeypatch.setattr(data_loader, "make_source", lambda: FakeSource(tablero(), fail={"tablero"}))
    data_loader.clear_cache()
    at.run()
    assert not at.exception
    assert any("últimos datos cargados" in w.value for w in at.warning)
    data_loader.clear_cache()
