import pandas as pd

from utils.salud import sin_so_esperado


def test_sin_so_esperado_por_empresa_o_tipo_aereo():
    df = pd.DataFrame({"empresa": ["RC Online", "Bidcom SRL", "Bidcom SRL", "Aeropix", "Bidcom SRL", None],
                       "tipo_envio_aereo": [None, "DJI RCONLINE", "DJI BAYNAL", None, "DJI", "Aeropix"]})
    assert sin_so_esperado(df).tolist() == [True, True, True, True, False, True]


def test_embarque_provisorio():
    from utils.salud import provisorio
    s = pd.Series(["AIR XXX", "AIR xxxxx", "FCL 2600", "AIR 140", "XXX", None, "AIR X1"])
    assert provisorio(s).tolist() == [True, True, False, False, True, False, False]


def test_sin_so_esperado_por_destino():
    df = pd.DataFrame({"empresa": ["Bidcom SRL"] * 4, "tipo_envio_aereo": [None] * 4,
                       "destino": ["Mexico", "Uruguay", "Argentina", None]})
    assert sin_so_esperado(df).tolist() == [True, True, False, False]


def test_destino_excluido_y_casos():
    from utils import salud
    df = pd.DataFrame({"embarque": ["FCL 1", "FCL 2", "FCL 3", "FCL 4"], "destino": ["México", "Uruguay", "Argentina", None],
                       "etd": pd.to_datetime(["2026-09-01"] * 4)})
    assert salud.destino_excluido(df).tolist() == [True, True, False, False]
    assert salud._casos(df, "Reservas", "x")["registro"].tolist() == ["FCL 3", "FCL 4"]


def test_errores_de_formula_sin_shipper():
    from types import SimpleNamespace
    from utils import salud
    q = SimpleNamespace(error_cells={"Shipper": (3, "#N/A", ""), "ETD": (1, "#N/A", ""), "ETD estimada": (1, "#N/A", ""), "ETA": (2, "#REF!", "")}, invalid_values={},
                        out_of_range={}, issue_rows={}, tab="Reservas", title="Reservas")
    b = SimpleNamespace(quality={"reservas": q}, get=lambda k: None)
    f = salud.formato(b)
    assert list(f["campo"]) == ["ETD estimada", "ETA"]
