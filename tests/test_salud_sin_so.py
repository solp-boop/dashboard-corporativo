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
