"""Tests de la capa de datos: conversión, normalización, carga y columnas faltantes."""
from __future__ import annotations

import datetime as dt

import numpy as np
import pandas as pd
import pytest

from services.data_loader import build_bundle, resolve_columns
from config.schema import RESERVAS as RESERVAS_SCHEMA
from utils import data_cleaning as dc
from tests.fakes import RESERVAS, FakeSource, tablero

ONLY_RES = {"reservas": ("tablero", "Reservas"), "validaciones": ("tablero", "Validaciones")}


# --------------------------------------------------------------------- fechas
@pytest.mark.parametrize("raw,expected", [
    ("16/09/2026", "2026-09-16"),
    ("9/9/2026", "2026-09-09"),
    ("30/8/26", "2026-08-30"),
    ("23/11//2024", "2024-11-23"),
    ("2026-04-29", "2026-04-29"),
    ("Wed Apr 29 2026 00:00:00 GMT-0300 (hora estándar de Argentina)", "2026-04-29"),
    (46295, "2026-09-30"),                       # número de serie de Sheets
    (dt.datetime(2026, 1, 5, 13, 0), "2026-01-05"),
])
def test_parse_dates_ok(raw, expected):
    s, stats = dc.parse_dates(pd.Series([raw], dtype=object))
    assert s.iloc[0] == pd.Timestamp(expected)
    assert stats.invalid == 0


@pytest.mark.parametrize("raw", ["Pendiente", "SI", "No aplica", "#N/A", "#¡VALOR!", "-", "", None, "*"])
def test_parse_dates_textos(raw):
    s, _ = dc.parse_dates(pd.Series([raw], dtype=object))
    assert pd.isna(s.iloc[0])


def test_parse_dates_fuera_de_rango_se_cuentan():
    s, stats = dc.parse_dates(pd.Series(["01/01/1900", "05/05/0202", "31/12/1969"], dtype=object))
    assert s.isna().all()
    assert stats.out_of_range == 3


# --------------------------------------------------------------------- números
@pytest.mark.parametrize("raw,expected", [
    ("USD30.400,00", 30400.0),
    ("USD 1.030,00", 1030.0),
    ("$ 812", 812.0),
    ("0,10", 0.10),
    ("1.234,5", 1234.5),
    ("1,234.5", 1234.5),
    ("8.100", 8100.0),
    ("61.84", 61.84),
    ("11,11%", 0.1111),
    ("(500)", -500.0),
    (42, 42.0),
    (3.5, 3.5),
])
def test_parse_numbers(raw, expected):
    s, _ = dc.parse_numbers(pd.Series([raw], dtype=object))
    assert s.iloc[0] == pytest.approx(expected)


@pytest.mark.parametrize("raw", ["#REF!", "N/A", "Sin dato", "abc", "", None, True])
def test_parse_numbers_invalidos(raw):
    s, _ = dc.parse_numbers(pd.Series([raw], dtype=object))
    assert np.isnan(s.iloc[0])


def test_flags():
    s = dc.parse_flags(pd.Series(["Ok", "SI", "sí", "NO", "", None, "quizás"], dtype=object))
    assert list(s.astype(object).where(s.notna(), None)) == [True, True, True, False, None, None, None]


def test_fold_y_alias():
    assert dc.fold("  Shanghái ") == "shanghai"
    assert dc.fold("Cotizacion agente? ") == dc.fold("Cotización Agente")
    s = dc.apply_aliases(pd.Series(["Zhonshan", "40ST", "Courrier", " Delfin  Group "], dtype=object),
                         {"zhonshan": "Zhongshan", "40st": "40 ST", "courrier": "Courier"})
    assert list(s) == ["Zhongshan", "40 ST", "Courier", "Delfin Group"]


def test_canonical_spelling_elige_la_mas_frecuente():
    canon = dc.canonical_spelling([pd.Series(["Hong Kong", "Hong Kong", "HONG KONG"], dtype=object)])
    assert canon["hong kong"] == "Hong Kong"


# --------------------------------------------------------------------- encabezados
def test_resolve_columns_tolerante_a_espacios_y_acentos():
    headers = [" embarque ", "ETD", "Fecha de Instruccion", "Empresa"]
    found, miss_req, miss_opt = resolve_columns(RESERVAS_SCHEMA, headers)
    assert found["embarque"] == 0 and found["f_instruccion"] == 2
    assert miss_req == []
    assert "Forwarder" in miss_opt


# --------------------------------------------------------------------- carga completa
def test_bundle_reservas_normaliza_y_deduplica():
    b = build_bundle(FakeSource(tablero()), ONLY_RES)
    assert b.available("reservas")
    df = b.get("reservas")
    q = b.quality["reservas"]
    assert q.duplicates == 1            # FCL 1 repetido
    assert q.rows_filler == 2           # FCL 9 vacío + AIR PROYECCION
    assert list(df["embarque"]) == ["FCL 1", "FCL 2", "FCL 3"]
    # Categorías unificadas
    assert set(df["empresa"]) == {"Bidcom SRL", "Foretec SRL"}
    assert set(df["puerto"]) == {"Ningbo", "Shenzhen"}
    assert set(df["forwarder"]) == {"DELFIN GROUP", "NIP"}
    assert list(df["tipo_carga"]) == ["40 HQ", "40 ST", "Avión"]
    assert list(df["modo"]) == ["Marítimo FCL", "Marítimo FCL", "Aéreo"]
    # Números en formato argentino y FOB real con fallback a SIMI
    assert df.loc[1, "m3"] == pytest.approx(1234.5)
    assert df.loc[0, "fob"] == pytest.approx(10000)
    assert df.loc[1, "fob"] == pytest.approx(7500)
    # Flags y estructura
    assert list(df["etd_ok"]) == [True, False, False]
    assert list(df["estructura"].where(df["estructura"].notna(), None)) == ["Consolidado", "Monoproveedor", None]
    assert list(df["booking"].where(df["booking"].notna(), None)) == ["In advance", "Spot", None]


def test_bundle_recalcula_tiempos_y_sla():
    b = build_bundle(FakeSource(tablero()), ONLY_RES)
    df = b.get("reservas")
    r0 = df.iloc[0]
    assert r0["dias_consolidacion"] == 26          # 20/09 - 25/08
    assert r0["dias_tt"] == 46
    assert r0["sla_consolidacion"] == 25           # Ningbo en Validaciones
    assert r0["estado_consolidacion"] == "Atención"  # 26 d vs 25 d (+4 %)
    assert pd.isna(df.iloc[1]["dias_consolidacion"])  # ETD = #N/A
    assert df.iloc[1]["sla_consolidacion"] == 12   # monoproveedor sin ETD: SLA vigente hoy
    assert pd.isna(df.iloc[2]["dias_consolidacion"])  # packeo 1900 descartado
    assert b.quality["reservas"].out_of_range      # el 1900 quedó registrado


def test_sla_por_puerto_desde_validaciones():
    b = build_bundle(FakeSource(tablero()), ONLY_RES)
    sla = b.sla_puertos.set_index("puerto")
    assert sla.loc["Shenzhen", "sla_consolidacion"] == 30
    assert "Nantong" in sla.index                  # alias Nangtong -> Nantong


def test_columna_obligatoria_faltante_mensaje_claro():
    sin_etd = [[c for c in RESERVAS[0] if c != "ETD"]] + [r[:10] + r[11:] for r in RESERVAS[1:]]
    b = build_bundle(FakeSource(tablero(Reservas=sin_etd)), ONLY_RES)
    q = b.quality["reservas"]
    assert not b.available("reservas")
    assert "ETD" in q.missing_required
    assert "ETD" in q.message and "Reservas" in q.message


def test_columna_opcional_faltante_no_rompe():
    idx = RESERVAS[0].index("Forwarder")
    sin_ffww = [[c for i, c in enumerate(r) if i != idx] for r in RESERVAS]
    b = build_bundle(FakeSource(tablero(Reservas=sin_ffww)), ONLY_RES)
    assert b.available("reservas")
    assert "Forwarder" in b.quality["reservas"].missing_optional
    assert b.get("reservas")["forwarder"].isna().all()


def test_solapa_faltante_y_planilla_caida_no_rompen_el_resto():
    books = tablero()
    books["cotizaciones"] = {}
    src = FakeSource(books, fail={"cotizaciones"})
    ds = {**ONLY_RES, "historicas": ("tablero", "Reservas Historicas"),
          "cotizaciones": ("cotizaciones", "Cotizaciones Maritimos Negociado")}
    b = build_bundle(src, ds)
    assert b.available("reservas")
    assert not b.available("historicas")
    assert "No se encontró la solapa" in b.quality["historicas"].message
    assert not b.available("cotizaciones")
    assert any("cotizaciones" in e for e in b.errors)


def test_encabezados_con_typos_corregidos_siguen_funcionando():
    renamed = [list(RESERVAS[0])] + [list(r) for r in RESERVAS[1:]]
    renamed[0][renamed[0].index("Fecha de Instrucción")] = "FECHA DE INSTRUCCION "
    b = build_bundle(FakeSource(tablero(Reservas=renamed)), ONLY_RES)
    assert b.get("reservas")["f_instruccion"].notna().sum() == 2
