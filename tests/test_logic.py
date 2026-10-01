"""Tests de filtros, cálculos, formato y buscador."""
from __future__ import annotations

import datetime as dt

import numpy as np
import pandas as pd
import pytest

from utils import calculations as calc
from utils import formatting as fmt
from utils.filters import (FilterState, apply_filters, build_dimensions, dependent_options,
                           not_applicable, undated_count)


@pytest.fixture
def datasets():
    a = pd.DataFrame({
        "empresa": ["A", "A", "B", "B"], "destino": ["Argentina", "México", "Argentina", "Argentina"],
        "puerto": ["Ningbo", "Shenzhen", "Ningbo", "Qingdao"], "forwarder": ["F1", "F2", "F1", "F3"],
        "fecha_ref": pd.to_datetime(["2026-01-10", "2026-02-10", "2026-03-10", None]),
    })
    b = pd.DataFrame({  # dataset sin empresa ni forwarder (como Planif cargas)
        "destino": ["Argentina", "Uruguay"], "puerto": ["Yantian", "Ningbo"],
        "fecha_ref": pd.to_datetime(["2026-01-01", "2026-05-01"]),
    })
    return {"a": a, "b": b}


def test_apply_filters_combina_periodo_y_selecciones(datasets):
    a = datasets["a"]
    f = FilterState(dt.date(2026, 1, 1), dt.date(2026, 2, 28), {"empresa": ["A"]})
    out = apply_filters(a, f)
    assert list(out["puerto"]) == ["Ningbo", "Shenzhen"]
    assert out is not a                       # siempre copia


def test_apply_filters_sin_filtros_devuelve_todo(datasets):
    assert len(apply_filters(datasets["a"], FilterState())) == 4


def test_filtro_no_aplicable_se_ignora_y_se_informa(datasets):
    b = datasets["b"]
    f = FilterState(selections={"empresa": ["A"], "puerto": ["Ningbo"]})
    out = apply_filters(b, f)
    assert list(out["puerto"]) == ["Ningbo"]
    assert not_applicable(b, f) == ["Empresa"]


def test_registros_sin_fecha_con_periodo(datasets):
    f = FilterState(dt.date(2026, 1, 1), None, {})
    assert undated_count(datasets["a"], f) == 1
    assert len(apply_filters(datasets["a"], f)) == 3


def test_filtros_dependientes(datasets):
    dims = build_dimensions(datasets)
    f = FilterState(selections={"empresa": ["A"]})
    # Con empresa A: destinos de A + los de datasets sin empresa (b)
    assert dependent_options(dims, f, "destino") == ["Argentina", "México", "Uruguay"]
    f2 = FilterState(selections={"empresa": ["B"]})
    assert dependent_options(dims, f2, "forwarder") == ["F1", "F3"]
    # Un filtro nunca restringe sus propias opciones ni las anteriores
    assert dependent_options(dims, f2, "empresa") == ["A", "B"]


def test_filtros_dependientes_respetan_periodo(datasets):
    f = FilterState(dt.date(2026, 3, 1), None, {})
    dims = build_dimensions(datasets, f)
    assert dependent_options(dims, f, "empresa") == ["B"]


def test_describe_usa_mediana_y_percentiles():
    s = calc.describe(pd.Series([1, 2, 3, 4, 100, np.nan]))
    assert s.median == 3 and s.n == 5 and s.total == 6
    assert s.p25 == 2 and s.p75 == 4
    assert s.enough


def test_describe_muestra_chica():
    s = calc.describe(pd.Series([10, np.nan, np.nan, np.nan]))
    assert not s.enough and s.low_coverage


def test_semaforo():
    out = calc.semaforo(pd.Series([10, 11, 13, np.nan]), pd.Series([10, 10, 10, 10]))
    assert list(out.where(out.notna(), None)) == ["Dentro de SLA", "Atención", "Fuera de SLA", None]


def test_days_between_descarta_fuera_de_rango():
    d, bad = calc.days_between(pd.Series(pd.to_datetime(["2026-02-01", "2026-02-01"])),
                               pd.Series(pd.to_datetime(["2026-01-01", "1900-01-01"])), "dias_consolidacion")
    assert d.iloc[0] == 31 and np.isnan(d.iloc[1]) and bad == 1


def test_cumplimiento():
    pct, n = calc.cumplimiento(pd.Series([5, 10, 30, np.nan]), pd.Series([7, 7, 25, 25]))
    assert n == 3 and pct == pytest.approx(1 / 3)


@pytest.mark.parametrize("fn,val,exp", [
    (fmt.fmt_int, 17306.4, "17.306"),
    (fmt.fmt_num, 1234.56, "1.234,6"),
    (fmt.fmt_num, 12.0, "12"),
    (fmt.fmt_usd, 18_200_000, "USD 18,2 M"),
    (fmt.fmt_usd, 812, "USD 812"),
    (fmt.fmt_usd, 45_300, "USD 45 K"),
    (fmt.fmt_pct, 0.525, "52 %"),
    (fmt.fmt_days, 23.6, "24 d"),
    (fmt.fmt_int, np.nan, "—"),
])
def test_formato(fn, val, exp):
    assert fn(val) == exp


def test_buscador_coincidencia_tolerante():
    from views.buscar import matches

    s = pd.Series(["SO-38529", "SO-385290", "FCL 2679", "FCL 26790", "AIR 199", None], dtype=object)
    assert list(matches(s, "38529")) == [True, False, False, False, False, False]
    assert list(matches(s, "so38529")) == [True, False, False, False, False, False]
    assert list(matches(s, "SO-38529")) == [True, False, False, False, False, False]
    assert list(matches(s, "2679")) == [False, False, True, False, False, False]
    assert list(matches(s, "fcl 2679")) == [False, False, True, False, False, False]
    assert list(matches(s, "air")) == [False, False, False, False, True, False]


def test_exportacion_excel_y_csv_respetan_filas():
    import io

    from components.tables import ColSpec, _display_frame, _search, to_csv, to_excel

    df = pd.DataFrame({"embarque": ["FCL 1", "FCL 2", "FCL 3"], "m3": [1.5, 2.25, None],
                       "etd": pd.to_datetime(["2026-09-01", None, "2026-10-01"]),
                       "estado": ["Dentro de SLA", "Fuera de SLA", None]})
    disp, _ = _display_frame(df, [ColSpec("embarque", "Embarque"), ColSpec("m3", "M3", "num"),
                                  ColSpec("etd", "ETD", "date"), ColSpec("estado", "Estado", "status")])
    shown = _search(disp, "fcl 2")
    assert list(shown["Embarque"]) == ["FCL 2"]
    x = pd.read_excel(io.BytesIO(to_excel(shown)))
    assert list(x["Embarque"]) == ["FCL 2"] and x.loc[0, "Estado"].endswith("Fuera de SLA")
    csv = to_csv(disp).decode("utf-8-sig")
    assert csv.splitlines()[0] == "Embarque;M3;ETD;Estado"
    assert "FCL 1;1,5;01/09/2026" in csv


def test_en_curso_reglas():
    """Reservas con responsable (sin AIR) + aéreos no entregados; el período no filtra."""
    import datetime as dt

    from services.data_loader import DataBundle
    from views._common import en_curso

    res = pd.DataFrame({
        "embarque": ["FCL 1", "FCL 2", "AIR 9", "TRUCK 1"], "responsable": ["Sol", None, "Sofi", "David"],
        "modo": ["Marítimo FCL", "Marítimo FCL", "Aéreo", "Terrestre"], "etd_ok": [True, False, True, False],
        "etd": pd.to_datetime(["2020-01-01", "2026-10-02", "2026-10-02", None]),
        "contenedores": [2, 1, None, 1], "m3": [60, 30, 1, 5], "fob": [1, 1, 1, 1], "fecha_ref": pd.NaT,
    })
    aer = pd.DataFrame({
        "embarque": ["AIR 1", "AIR 2", "AIR 3"], "estadio": ["ENTREGADO", "EN ORIGEN", "NACIONALIZADO"],
        "modo": ["Aéreo"] * 3, "etd_ok": [True, False, True], "etd": pd.to_datetime(["2026-09-01"] * 3),
        "m3": [1, 2, 3], "fob": [1, 1, 1], "fecha_ref": pd.NaT,
    })
    b = DataBundle(datasets={"reservas": res, "aereos": aer}, sla_puertos=pd.DataFrame(), quality={},
                   errors=[], loaded_at=dt.datetime.now(), source_name="test")
    df, info = en_curso(b, FilterState(dt.date(2026, 1, 1), None, {}))
    assert sorted(df["embarque"]) == ["AIR 2", "AIR 3", "FCL 1", "TRUCK 1"]
    assert info == {"sin_responsable": 1, "air_en_reservas": 1, "aereos_entregados": 1}
    assert df.set_index("embarque")["grupo_modo"].to_dict() == {
        "FCL 1": "Marítimo", "TRUCK 1": "Camión", "AIR 2": "Aéreo", "AIR 3": "Aéreo"}
