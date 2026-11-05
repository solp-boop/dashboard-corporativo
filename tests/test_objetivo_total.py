import pandas as pd

from utils import objetivo


def test_total_mono_mas_conso_sin_separar():
    ts = pd.Timestamp
    d = pd.DataFrame({
        "etd": [ts("2025-03-05"), ts("2025-03-10"), ts("2025-03-12"), ts("2026-03-05"), ts("2026-03-09"),
                ts("2026-03-20")],
        "valor": [10.0, 30.0, 50.0, 8.0, 20.0, 40.0],
        "estructura": ["Monoproveedor", "Consolidado", "Consolidado", "Monoproveedor", "Consolidado", "Consolidado"],
    })
    r = objetivo.vs_anio_anterior(d, ts("2026-05-10"))
    m = r["mensual"].set_index(["estructura", "mes"])
    assert m.loc[("Total", 3), "ant"] == 30 and m.loc[("Total", 3), "act"] == 20     # mediana de las 3 SO de cada año
    assert m.loc[("Total", 3), "n_ant"] == 3
    # el total ponderado sigue saliendo solo de mono y conso
    assert set(r["total"]["pesos"]) <= {"Monoproveedor", "Consolidado"}
    assert r["total"]["n_ant"] == 3
