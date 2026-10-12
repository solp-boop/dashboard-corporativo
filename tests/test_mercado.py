import pandas as pd

from utils import costos as cs


def test_mercado_mes_mediana_por_mes_y_variaciones():
    cot = pd.DataFrame({
        "flete": [1000, 2000, 3000, 1500, 9999, 4000, 500],
        "tipo_ctnr": ["40ST/40HQ", "40ST/40HQ", None, "40ST/40HQ", "20ST", "40ST/40HQ", "40ST/40HQ"],
        "validez_desde": pd.to_datetime(["2025-02-01", "2025-02-16", "2026-01-01", "2026-02-01", "2026-02-01",
                                         "2026-02-16", "2026-03-01"]),
    })
    m = cs.mercado_mes(cot, "40ST/40HQ", pd.Timestamp("2026-02-20"))
    assert list(m["mes"].dt.strftime("%Y-%m")) == ["2025-02", "2026-01", "2026-02"]   # marzo es futuro: no entra
    feb = m.iloc[-1]
    assert feb["mediana"] == 2750 and feb["n"] == 2                                   # 20ST no entra
    assert round(feb["var_mes"], 4) == round(2750 / 3000 - 1, 4)                     # sin tipo cuenta como 40ST/40HQ
    assert feb["anio_ant"] == 1500 and round(feb["var_anio"], 4) == round(2750 / 1500 - 1, 4)
    assert cs.mercado_mes(None, "40ST/40HQ", pd.Timestamp("2026-02-20")).empty
