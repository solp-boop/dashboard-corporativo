import pandas as pd

from utils import proyeccion as pr


def test_mono_por_mes_y_semana():
    ts = pd.Timestamp
    d = pd.DataFrame({
        "fuente": ["Reservado", "Por reservar", "Por reservar", "Embarcado", "Por reservar", "Por reservar"],
        "id": ["1", "2", "3", "4", "5", "6"], "embarque": ["FCL 1", None, None, "FCL 9", None, None],
        "etd": [ts("2026-11-03"), ts("2026-11-05"), ts("2026-12-10"), ts("2026-11-04"), ts("2026-11-05"), pd.NaT],
        "eta": pd.NaT, "contenedores": [2.0, 1.5, 0.5, 1.0, 3.0, 1.0], "m3": [120.0, 90, 30, 60, 180, 60],
        "fob": 0.0, "estructura": ["Monoproveedor"] * 4 + ["Consolidado", "Monoproveedor"],
        "medio": ["Marítimo"] * 6, "proveedor": ["P1", "P2", "P2", "P1", "P3", "P4"],
        "etd_ok": [True, False, False, False, False, False],
    })
    hoy = ts("2026-10-29")
    m = pr.mono_por_periodo(d, hoy, "mes").set_index("periodo")
    # por reservar: m³ / 68 (40 HQ) hacia arriba, por proveedor y ETD (90 m³ → 2; 30 m³ → 1; 60 m³ → 1)
    assert m.loc[ts("2026-11-01"), "reservados"] == 2 and m.loc[ts("2026-11-01"), "por_reservar"] == 2
    assert m.loc[ts("2026-11-01"), "confirmados"] == 2 and m.loc[ts("2026-11-01"), "sin_confirmar"] == 0
    assert m.loc[ts("2026-12-01"), "total"] == 1
    tot = m.iloc[-1]
    assert tot["so"] == 4                                # sin el consolidado ni el embarcado
    assert tot["total"] == m.iloc[:-1]["total"].sum()
    w = pr.mono_por_periodo(d, hoy, "semana").set_index("periodo")
    assert w.loc[ts("2026-11-02"), "total"] == 4          # semana del lunes 02/11: 2 reservados + 2 estimados
    assert pr.etiqueta_semana(ts("2026-10-26"), hoy) == "Sem 26/10 – 01/11*"
