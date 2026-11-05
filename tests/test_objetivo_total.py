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


def test_destino_oficial_emb_hist_o_reservas_historicas():
    from utils.productos import _solo_destino
    d = pd.DataFrame({"embarque": ["FCL 1", "FCL 2", "FCL 3", "FCL 4", "FCL 5", "FCL 6"],
                      "destino": ["Argentina", None, "", "Uruguay", None, "argentina"]})
    hist = pd.DataFrame({"embarque": ["FCL 2", "FCL 3", "FCL 4"], "destino": ["Argentina", "Uruguay", "Argentina"]})
    # FCL 2 toma Argentina de Históricas; FCL 3 dice Uruguay; FCL 4 manda Emb Hist (Uruguay); FCL 5 sin destino: afuera
    assert _solo_destino(d, hist).index.tolist() == [0, 1, 5]


def test_tiempo_oficial_recalculado():
    from services.data_loader import prepare_emb_hist
    ts = pd.Timestamp
    eh = pd.DataFrame({"embarque": ["FCL 1"] * 4, "so": ["S1", "S2", "S3", "S4"],
                       "etd": [ts("2026-03-20")] * 4,
                       "fin_produccion": [ts("2026-03-01"), pd.NaT, pd.NaT, ts("2026-03-25")],
                       "f_packeo_act": [ts("2026-02-01"), ts("2026-03-10"), pd.NaT, pd.NaT],
                       "tiempo_consolidacion": [99.0, 99.0, 0.0, 5.0],
                       "sku_nuevo": None, "ranking": None, "estructura_eh": "CONSOLIDADO"})
    prepare_emb_hist(eh, None)
    t = eh["tiempo_consolidacion"].tolist()
    assert t[0] == 19 and t[1] == 10            # fin de producción; si falta, packeo actualizada
    assert t[2] == 0                            # sin fechas: la columna de la planilla (0 cuenta)
    assert pd.isna(t[3])                        # negativo: afuera
