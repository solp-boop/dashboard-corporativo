"""Motor de costos: comparabilidad, oportunidades, adherencia, selección, alertas y helpers de costos."""
import numpy as np
import pandas as pd

from utils import costos as cs
from utils import oportunidades as op

HOY = pd.Timestamp("2026-10-11")


def _cot(rows):
    base = {"destino": "Argentina", "validez_desde": pd.Timestamp("2026-10-01"),
            "validez_hasta": pd.Timestamp("2026-10-31"), "servicio": "Directo", "transbordo": None, "tt": 40,
            "pagadero": "Origen"}
    return pd.DataFrame([{**base, **r} for r in rows])


def _hist(rows):
    base = {"destino": "Argentina", "contenedores": 1, "etd": HOY - pd.Timedelta(days=10), "responsable": "Ana"}
    d = pd.DataFrame([{**base, **r} for r in rows])
    d["embarque"] = [f"FCL {i}" for i in range(len(d))]
    if "flete_por_ctnr" in d:
        d["flete_pagado"] = d["flete_por_ctnr"] * d["contenedores"]
    return d


def test_servicio_y_comparable():
    assert op.servicio({"servicio": "Directo"}) == "Directo"
    assert op.servicio({"servicio": "Via Busan"}) == "Trasbordo"
    assert op.servicio({"servicio": "A confirmar"}) == "A confirmar"
    c = op.preparar(_cot([{"forwarder": "A", "puerto": "Ningbo", "tipo_ctnr": "20ST", "flete": 1000},
                          {"forwarder": "B", "puerto": "Ningbo", "tipo_ctnr": "20ST", "flete": 900,
                           "servicio": "Trasbordo"},
                          {"forwarder": "C", "puerto": "Ningbo", "tipo_ctnr": "20ST", "flete": 900, "tt": 60},
                          {"forwarder": "D", "puerto": "Ningbo", "tipo_ctnr": "20ST", "flete": 900, "pagadero": np.nan}]))
    a = c.iloc[0]
    assert op.comparable(a, c.iloc[1])[0] is False          # directo vs trasbordo
    assert op.comparable(a, c.iloc[2])[0] is False          # tránsito fuera de tolerancia
    assert op.comparable(a, c.iloc[3]) == (True, "")        # pagadero vacío no descarta


def test_oportunidad_inmediata_con_objetivo_y_ahorro():
    h = _hist([{"forwarder": "A", "puerto": "Ningbo", "tipo_ctnr": "40ST/40HQ", "flete_por_ctnr": 5700,
                "contenedores": 10}])
    c = _cot([{"forwarder": "A", "puerto": "Ningbo", "tipo_ctnr": "40ST/40HQ", "flete": 5700},
              {"forwarder": "B", "puerto": "Ningbo", "tipo_ctnr": "40ST/40HQ", "flete": 4800},
              {"forwarder": "C", "puerto": "Ningbo", "tipo_ctnr": "40ST/40HQ", "flete": 4000, "servicio": "Trasbordo"}])
    o = op.oportunidades(h, c, HOY, dias=60)
    r = o.iloc[0]
    assert r["tipo"] == "Inmediata" and r["mejor_agente"] == "B" and r["objetivo"] == 4800
    assert r["dif_usd"] == 900 and abs(r["ahorro_mes"] - 900 * 10 / 2) < 1e-6
    assert r["menor_no_comparable"] == 4000                  # la de C no es comparable (trasbordo)


def test_diferencia_chica_es_seguimiento_y_sin_tarifa_es_investigar():
    h = _hist([{"forwarder": "A", "puerto": "Ningbo", "tipo_ctnr": "20ST", "flete_por_ctnr": 1000, "contenedores": 5},
               {"forwarder": "A", "puerto": "Xiamen", "tipo_ctnr": "20ST", "flete_por_ctnr": 1000, "contenedores": 25}])
    c = _cot([{"forwarder": "A", "puerto": "Ningbo", "tipo_ctnr": "20ST", "flete": 1000},
              {"forwarder": "B", "puerto": "Ningbo", "tipo_ctnr": "20ST", "flete": 980},
              {"forwarder": "B", "puerto": "Xiamen", "tipo_ctnr": "20ST", "flete": 900}])
    o = op.oportunidades(h, c, HOY, dias=60).set_index("puerto")
    assert o.loc["Ningbo", "tipo"] == "Seguimiento"          # USD 20 < umbral
    assert o.loc["Xiamen", "tipo"] == "Investigar" and o.loc["Xiamen", "prioridad"] == "Alta"


def test_adherencia_por_etd_contra_la_mas_alta():
    h = _hist([{"forwarder": "A", "puerto": "Ningbo", "tipo_ctnr": "20ST", "flete_por_ctnr": 1100},
               {"forwarder": "A", "puerto": "Ningbo", "tipo_ctnr": "20ST", "flete_por_ctnr": 1300, "contenedores": 2}])
    c = _cot([{"forwarder": "A", "puerto": "Ningbo", "tipo_ctnr": "20ST", "flete": 1000},
              {"forwarder": "A", "puerto": "Ningbo", "tipo_ctnr": "20ST", "flete": 1100}])
    a = op.adherencia(h, c)
    assert a["pago_mas"].sum() == 1 and a["exceso"].sum() == 400
    # fuera de vigencia a la ETD: no se compara
    assert op.adherencia(h.assign(etd=pd.Timestamp("2026-09-01")), c).empty


def test_por_seleccion_usa_otros_agentes():
    h = _hist([{"forwarder": "A", "puerto": "Ningbo", "tipo_ctnr": "20ST", "flete_por_ctnr": 1000, "contenedores": 2}])
    c = _cot([{"forwarder": "B", "puerto": "Ningbo", "tipo_ctnr": "20ST", "flete": 1100},
              {"forwarder": "C", "puerto": "Ningbo", "tipo_ctnr": "20ST", "flete": 1300},
              {"forwarder": "A", "puerto": "Ningbo", "tipo_ctnr": "20ST", "flete": 500}])
    s = op.por_seleccion(h, c)
    assert s.iloc[0]["alternativa"] == 1200 and s.iloc[0]["ahorro"] == 400


def test_alertas_y_top_acciones():
    h = _hist([{"forwarder": "A", "puerto": "Ningbo", "tipo_ctnr": "40ST/40HQ", "flete_por_ctnr": 5700,
                "contenedores": 10}])
    c = _cot([{"forwarder": "A", "puerto": "Ningbo", "tipo_ctnr": "40ST/40HQ", "flete": 5000,
               "validez_hasta": HOY + pd.Timedelta(days=2)},
              {"forwarder": "B", "puerto": "Ningbo", "tipo_ctnr": "40ST/40HQ", "flete": 4000}])
    o = op.oportunidades(h, c, HOY, dias=60)
    adh = op.adherencia(h, c)
    al = op.alertas(h, c, HOY, o, adh)
    sit = set(al["situacion"])
    assert {"Pagamos más de lo cotizado", "Tarifa por vencer", "Dependencia de un agente"} <= sit
    top = op.top_acciones(o, al)
    assert len(top) <= 4 and top.iloc[0]["titulo"].startswith(("Renegociar", "Reclamar"))


def test_puente_suma_exacto():
    prev = pd.DataFrame({"tipo_ctnr": ["20ST", "40ST/40HQ"], "contenedores": [10, 10],
                         "flete_pagado": [10000, 20000]})
    cur = pd.DataFrame({"tipo_ctnr": ["20ST", "40ST/40HQ", "40NOR"], "contenedores": [5, 20, 5],
                        "flete_pagado": [6000, 50000, 7500]})
    r = cs.puente(prev, cur)
    assert abs(r["residuo"]) < 1e-6
    assert abs(r["base"] + r["volumen"] + r["mezcla"] + r["precio"] - r["final"]) < 1e-6
    assert r["volumen"] == (30 - 20) * 1500


def test_equipos_espacio_vacio_imo():
    h = pd.DataFrame({"embarque": ["a", "b", "c", "d"], "tipo_ctnr": ["20ST", "40ST/40HQ", "40ST/40HQ", "40ST/40HQ"],
                      "contenedores": [1, 1, 1, 1], "m3": [30, 34, 68, 60], "capacidad": [30, 68, 68, 68],
                      "flete_por_ctnr": [3000, 4000, 4000, 5000], "flete_pagado": [3000, 4000, 4000, 5000],
                      "puerto": "Ningbo", "etd": pd.Timestamp("2026-09-10"), "dg": [False, False, False, True]})
    e = cs.equipos(h).set_index("equipo")
    assert e.loc["20 ST", "flete_m3"] == 100
    ev = cs.espacio_vacio(h, 0.7)
    assert ev["bajos"] == 1 and ev["usd_vacio"] == 2000
    imo = cs.imo_sobrecosto(h)
    assert imo["n_celdas"] == 1 and imo["dif_med"] == 1000
