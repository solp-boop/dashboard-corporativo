import pandas as pd

from utils.salud import sin_so_esperado


def test_sin_so_esperado_por_empresa_o_tipo_aereo():
    df = pd.DataFrame({"empresa": ["RC Online", "Bidcom SRL", "Bidcom SRL", "Aeropix", "Bidcom SRL", None],
                       "tipo_envio_aereo": [None, "DJI RCONLINE", "DJI BAYNAL", None, "DJI", "Aeropix"]})
    assert sin_so_esperado(df).tolist() == [True, True, True, True, False, True]
