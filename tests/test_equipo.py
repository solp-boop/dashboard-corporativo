import numpy as np
import pandas as pd

from utils import equipo as eq


def _h():
    d = pd.to_datetime
    return pd.DataFrame({
        "embarque": ["E1", "E2", "E3", "E4", "E4"],
        "modo": ["Marítimo FCL"] * 5, "etd": d(["2026-09-10", "2026-09-20", "2026-09-25", "2026-09-28", "2026-09-28"]),
        "f_packeo_min": d(["2026-09-01", "2026-09-01", "2026-09-05", "2026-09-10", "2026-09-10"]),
        "f_packeo_max": d(["2026-09-01", "2026-09-05", None, "2026-09-12", "2026-09-12"]),
        "f_instruccion": d(["2026-08-25", "2026-09-08", "2026-09-01", None, None]),
        "dias_consolidacion": [9, 19, 20, 18, 18], "cumple_consolidacion": [True, False, False, None, None],
        "dias_agente": [16, 12, 24, np.nan, np.nan], "desvio_etd": [2, 10, np.nan, 1, 1],
        "estructura": ["Monoproveedor", "Consolidado", "Consolidado", "Consolidado", "Consolidado"],
        "booking": ["In advance", "Spot", None, "In advance", "In advance"],
        "tipo_demora": [None, "Proveedor + Agente", None, None, None],
        "responsable": ["Ana", "Ana", "Beto", "Beto", "Beto"], "forwarder": ["F1", "F1", "F2", "F2", "F2"],
        "contenedores": [1, 2, 1, 1, 1], "flete_pagado": [100, 0, 0, 0, 0], "flete_certificado": [60, 0, 0, 0, 0],
    })


def test_zarpados_listo_y_tardia():
    z = eq.zarpados(_h(), pd.Timestamp("2026-10-01"))
    assert len(z) == 4                                                 # embarque único
    e2 = z[z["embarque"] == "E2"].iloc[0]
    assert e2["dias_listo_etd"] == 12 and bool(e2["_tarde"]) and e2["dias_atraso_instr"] == 3  # último packeo 05/09
    e3 = z[z["embarque"] == "E3"].iloc[0]
    assert e3["dias_listo_etd"] == 20 and not bool(e3["_tarde"])        # sin packeo máx: usa el mínimo
    assert pd.isna(z[z["embarque"] == "E4"].iloc[0]["_tarde"])          # sin instrucción: no se juzga
    assert eq.origen_causa("Proveedor + Agente") == "Agente" and eq.origen_causa(None) == ""
    assert eq.origen_causa("Congestión en puerto de origen") == "Naviera / puerto / clima"


def test_analistas_agentes_y_salud():
    t = pd.Timestamp("2026-10-01")
    z = eq.zarpados(_h(), t)
    act = pd.DataFrame({"embarque": ["A1", "A2", "A3"], "responsable": ["Ana", "Ana", "Beto"],
                        "forwarder": ["F1", "F1", "F2"], "etd": pd.to_datetime(["2026-10-03", "2026-10-20", None]),
                        "etd_ok": [False, True, None]})
    casos = pd.DataFrame({"embarque": ["A1", "A1", "E2"], "responsable": ["Ana", "Ana", "Ana"],
                          "prioridad": ["Alta", "Media", "Baja"], "quien": ["Agente", "Analista", "Analista"]})
    an = eq.por_analista(z, act, casos).set_index("analista")
    assert an.loc["Ana", "activos"] == 2 and an.loc["Ana", "casos"] == 2 and an.loc["Ana", "casos_alta"] == 1
    assert an.loc["Ana", "casos_analista"] == 2 and an.loc["Ana", "pct_tarde"] == 0.5
    assert an.loc["Ana", "fuera_ext"] == 1 and an.loc["Beto", "fuera_sin_causa"] == 1
    ag = eq.por_agente(z, act).set_index("agente")
    assert ag.loc["F1", "demoras_agente"] == 1 and ag.loc["F1", "certificacion"] == 0.6
    assert ag.loc["F1", "revisar"] == "Muestra chica"
    s = eq.salud(z, act, casos, t)
    comp = {c[0]: c for c in s["componentes"]}
    assert comp["Cumplimiento SLA consolidación"][1] == 1 / 3
    assert comp["Activos con caso de prioridad alta"][1] == 1 / 3 and s["general"] == "bad"
    assert eq.semaforo(0.05, (0.1, 0.2)) == "ok" and eq.semaforo(0.45, (0.5, 0.4), True) == "warn"


def test_zarpados_en_reservas_y_aereos_por_analista():
    import pandas as pd
    from utils import equipo as eq
    ts = pd.Timestamp
    hoy = ts("2026-11-02")
    res = pd.DataFrame({"embarque": ["FCL 1", "FCL 2", "FCL 3", "AIR 9"], "etd": [ts("2026-11-01"), ts("2026-11-10"),
                        ts("2026-10-30"), ts("2026-10-30")], "responsable": ["Lu"] * 4,
                        "dias_consolidacion": [10.0, 5.0, 30.0, 3.0], "sla_cons_puerto": [25.0, 25.0, 25.0, 25.0],
                        "sla_consolidacion": [25.0] * 4})
    hist = pd.DataFrame({"embarque": ["FCL 3", "AIR 50"], "responsable": ["Lu", "Azul"]})
    rz = eq.zarpados_en_reservas(res, hist, hoy)
    assert list(rz["embarque"]) == ["FCL 1"]          # FCL 2 no salió, FCL 3 ya está en Históricas, AIR afuera
    assert bool(rz["cumple_consolidacion"].iloc[0])
    aer = pd.DataFrame({"embarque": ["AIR 50", "AIR 51"], "etd": [ts("2026-10-01"), ts("2026-10-05")],
                        "estadio": ["ENTREGADO", "EN TRANSITO"], "dias_aereo": [20.0, 10.0],
                        "sla_aereo": [25.0, 25.0], "sla_vigente": [True, True]})
    a = eq.aereos_por_analista(aer, hist, res, hoy)
    assert list(a["embarque"]) == ["AIR 50"] and a["responsable"].iloc[0] == "Azul"
    an = eq.por_analista(pd.DataFrame(), None, None, None, a).set_index("analista")
    assert an.loc["Azul", "aereos"] == 1 and an.loc["Azul", "cumple_aereo"] == 1.0
