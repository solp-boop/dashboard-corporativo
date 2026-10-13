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


def test_performance_fletes_como_el_reporte_del_equipo():
    import numpy as np
    h = pd.DataFrame({
        "embarque": ["E1", "E2", "E3", "E4"], "modo": ["Marítimo FCL"] * 4,
        "etd": pd.to_datetime(["2026-08-05", "2026-08-10", "2026-08-20", "2026-08-25"]),
        "tipo_ctnr": ["40ST/40HQ", "40ST/40HQ", "40ST/40HQ", "20ST"],
        "flete_pagado": [5000.0, 6000.0, 0.0, 5600.0], "flete_por_ctnr": [5000.0, 6000.0, np.nan, 5600.0],
        "flete_certificado": [3000.0, 3600.0, np.nan, 3360.0]})
    cot = pd.DataFrame({"flete": [6000.0, 6200.0, 9999.0, 5900.0], "tipo_ctnr": ["40ST/40HQ", "40ST/40HQ", "40ST/40HQ", "20ST"],
                        "validez_desde": pd.to_datetime(["2026-08-01", "2026-08-16", "2026-08-16", "2026-08-01"]),
                        "destino": ["Argentina", "Argentina", "Brasil", "Argentina"]})
    r = cs.performance_fletes(h, cot).set_index("tipo")
    assert r.loc["40ST/40HQ", "embarques"] == 3 and r.loc["40ST/40HQ", "pagado"] == 5500   # sin flete: cuenta, no entra en la mediana
    assert r.loc["40ST/40HQ", "negociado"] == 6100                                            # solo Argentina
    assert round(r.loc["40ST/40HQ", "variacion"], 4) == round(5500 / 6100 - 1, 4)
    assert r.loc["20ST", "certificacion"] == 0.6 and r.loc["TOTAL", "embarques"] == 4
