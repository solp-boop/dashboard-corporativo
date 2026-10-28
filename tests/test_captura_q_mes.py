import pandas as pd

from utils import captura as cap


def test_mes_por_trimestre():
    ts = pd.Timestamp
    neg = pd.DataFrame({"etd": [ts("2026-01-10"), ts("2026-04-05")], "captura": [100.0, 50.0]})
    nor = pd.DataFrame({"etd": [ts("2026-02-01"), ts("2026-02-20"), ts("2026-04-30")],
                        "ahorro": [1000.0, 500.0, 200.0], "contenedores": [1.0, 2.0, 1.0]})
    t = cap.mes_por_trimestre(neg, nor, 2026, ts("2026-04-15"))
    q1 = t[t["q"] == "Q1"]
    assert len(q1) == 4 and q1["subtotal"].tolist() == [False, False, False, True]
    assert q1.loc[q1["subtotal"], "nor"].item() == 1500 and q1.loc[q1["subtotal"], "nor_cont"].item() == 3
    assert q1.loc[q1["subtotal"], "total"].item() == 1600
    assert q1.loc[~q1["subtotal"], "acum_q"].tolist() == [100, 1600, 1600]
    q2 = t[t["q"] == "Q2"]
    assert len(q2) == 2 and q2.loc[q2["subtotal"], "total"].item() == 250   # solo abril (hasta el mes en curso)
    assert set(t["q"]) == {"Q1", "Q2"}
