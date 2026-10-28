import pandas as pd

from utils import tiempos_mes as tm


def test_tramos_entregados_meses_y_crudos():
    ts = pd.Timestamp
    d = pd.DataFrame({
        "etd": [ts("2026-03-10"), ts("2026-03-20"), ts("2026-05-05")],
        "f_packeo_min": [ts("2026-03-01"), ts("2026-03-15"), pd.NaT],
        "f_ingreso_wh": [ts("2026-03-04"), ts("2026-03-12"), ts("2026-05-01")],   # 2º: WH antes del packeo
        "eta": [ts("2026-03-12"), ts("2026-03-25"), ts("2026-05-08")],
        "eta_caldas": [ts("2026-03-15"), ts("2026-03-28"), ts("2026-05-12")],
        "dias_aereo": [14.0, 13.0, None],
    })
    t = tm.tramos_entregados(d, ts("2026-05-20"))
    assert t["mes"].iloc[:5].tolist() == [ts(f"2026-0{m}-01") for m in range(1, 6)]
    assert t["n"].tolist() == [0, 0, 2, 0, 1, 3]
    mar = t.iloc[2]
    assert mar["dias_packeo_wh"] == 0.0            # mediana de 3 y −3 (el negativo no se recorta)
    may = t.iloc[4]
    assert pd.isna(may["dias_packeo_wh"]) and may["dias_wh_etd"] == 4 and pd.isna(may["dias_aereo"])
    assert t.iloc[-1]["n"] == 3 and pd.isna(t.iloc[-1]["mes"])
    assert mar["etapa"] in [lbl for _, lbl in tm.TRAMOS_ENTREGADOS]
