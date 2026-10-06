"""Tests de fletes: mercado, pagado vs mercado y recomendación de forwarder."""
from __future__ import annotations

import numpy as np
import pandas as pd
import pytest

from utils import freight

HOY = pd.Timestamp("2026-09-30")


def cot():
    rows = [
        # forwarder, flete, locales, pol, tipo, desde, hasta
        ("A", 6000, 800, "Ningbo", "40ST/40HQ", "2026-09-15", "2026-10-15"),
        ("A", 6500, 800, "Shanghai", "40ST/40HQ", "2026-09-15", "2026-10-15"),
        ("B", 5800, np.nan, "Ningbo", "40ST/40HQ", "2026-09-20", "2026-10-05"),
        ("C", 7000, 700, "Ningbo", "40ST/40HQ", "2026-09-01", "2026-10-31"),
        ("C", 4000, 700, "Ningbo", "20ST", "2026-09-01", "2026-10-31"),
        ("D", 3000, 700, "Ningbo", "40ST/40HQ", "2026-08-01", "2026-08-15"),  # vencida
    ]
    d = pd.DataFrame(rows, columns=["forwarder", "flete", "locales_arg", "puerto", "tipo_ctnr",
                                    "validez_desde", "validez_hasta"])
    d["validez_desde"] = pd.to_datetime(d["validez_desde"])
    d["validez_hasta"] = pd.to_datetime(d["validez_hasta"])
    d["destino"] = "Argentina"
    return d


def hist():
    n = 10
    etd = pd.date_range("2026-03-01", periods=n, freq="15D")
    base = dict(etd=etd, dias_consolidacion=[20] * n, sla_consolidacion=[25] * n,
                resultado_validacion=["Validado"] * n)
    a = pd.DataFrame({**base, "forwarder": "A", "desvio_etd": [0] * n, "dias_agente": [20] * n})
    b = pd.DataFrame({**base, "forwarder": "B", "desvio_etd": [10] * n, "dias_agente": [40] * n})
    return pd.concat([a, b], ignore_index=True)


def test_vigentes_excluye_vencidas():
    v = freight.vigentes(cot(), HOY, "40ST/40HQ")
    assert set(v["forwarder"]) == {"A", "B", "C"}


def test_mercado_usa_mejor_tarifa_por_forwarder():
    prom, mejor, ffww = freight.market(freight.vigentes(cot(), HOY, "40ST/40HQ"))
    assert mejor == 5800 and ffww == "B"
    assert prom == pytest.approx(6000)  # mediana de 5800, 6000, 7000


def test_recomendacion_combina_precio_y_servicio():
    rec = freight.recommend(cot(), hist(), HOY, "40ST/40HQ", "Ningbo", peso_precio=0.7)
    op = rec.opciones
    # B es la más barata en flete, pero no trae locales (se estiman) y tiene mal servicio.
    b = op.set_index("forwarder").loc["B"]
    assert bool(b["locales_estimados"]) and b["locales_calc"] == 750   # mediana de 800 y 700
    assert op.iloc[0]["forwarder"] == "A"
    # C sin historial: servicio neutro
    c = op.set_index("forwarder").loc["C"]
    assert c["historial"] == "Sin historial suficiente" and c["score_servicio"] == 0.5
    assert list(op["ranking"]) == [1, 2, 3]


def test_prioridad_precio_puede_cambiar_el_ganador():
    rec = freight.recommend(cot(), hist(), HOY, "40ST/40HQ", "Ningbo", peso_precio=1.0)
    assert rec.opciones.iloc[0]["forwarder"] == "B"      # solo precio: la más barata


def test_sin_vigentes_devuelve_vacio():
    rec = freight.recommend(cot(), hist(), pd.Timestamp("2025-01-01"), "40ST/40HQ")
    assert rec.opciones.empty


def test_pagado_vs_mercado():
    h = pd.DataFrame({"etd": pd.to_datetime(["2026-09-20", "2026-09-25"]), "tipo_ctnr": ["40ST/40HQ", None],
                      "flete_por_ctnr": [5940.0, 3000.0], "destino": ["Argentina", "Argentina"]})
    out = freight.add_market_reference(h, cot())
    # mercado sept 40ST/40HQ = mediana de la mejor de cada forwarder con validez que empieza en sept: A 6000, B 5800, C 7000
    assert out.loc[0, "mercado_mes"] == pytest.approx(6000)
    assert out.loc[0, "vs_mercado"] == pytest.approx(5940 / 6000 - 1)
    assert np.isnan(out.loc[1, "vs_mercado"])


def test_sla_scorecard_y_proyectado():
    from utils import sla

    hoy = pd.Timestamp("2026-10-15")
    base = dict(modo="Marítimo FCL", sla_consolidacion=25.0, sla_total=75.0, dias_total=70.0)
    hist = pd.DataFrame([
        {**base, "embarque": "FCL 1", "etd": pd.Timestamp("2026-08-10"), "dias_consolidacion": 20, "estructura": "Consolidado"},
        {**base, "embarque": "FCL 2", "etd": pd.Timestamp("2026-09-10"), "dias_consolidacion": 30, "estructura": "Consolidado"},
        {**base, "embarque": "FCL 3", "etd": pd.Timestamp("2026-10-05"), "dias_consolidacion": 10, "estructura": "Consolidado"},
    ])
    res = pd.DataFrame([
        {**base, "embarque": "FCL 3", "etd": pd.Timestamp("2026-10-05"), "dias_consolidacion": 99,
         "estructura": "Consolidado", "responsable": "Sol"},  # ya zarpó: no se duplica
        {**base, "embarque": "FCL 4", "etd": pd.Timestamp("2026-10-25"), "dias_consolidacion": 40,
         "estructura": "Consolidado", "responsable": "Sol"},
        {**base, "embarque": "FCL 5", "etd": pd.Timestamp("2026-10-26"), "dias_consolidacion": 5,
         "estructura": "Consolidado", "responsable": None},   # sin responsable: no cuenta
    ])
    proj = sla.projected_month(hist, res, pd.Timestamp("2026-10-01"), hoy)
    assert sorted(proj["embarque"]) == ["FCL 3", "FCL 4"]
    sc = sla.scorecard(hist, res, hist, hoy, lambda m: m.strftime("%b"))
    cumpl = dict(sc.filas)["Cumplimiento SLA consolidación"]
    assert cumpl[1].valor == 1.0 and cumpl[2].valor == 0.0          # agosto 100 %, septiembre 0 %
    assert cumpl[3].startswith("▼")                                   # variación
    assert cumpl[4].n == 1 and cumpl[5].n == 2                        # octubre zarpados / proyectado
    m = sla.monthly_compliance(hist)
    assert list(m["n"]) == [1, 1, 1]


def test_productos_resumen_objetivo():
    from utils import productos

    hoy = pd.Timestamp("2026-10-01")
    rows = []
    for mes, t in [("2026-01-10", 20), ("2026-02-10", 20), ("2026-03-10", 20),
                   ("2026-07-10", 16), ("2026-08-10", 16), ("2026-09-10", 16)]:
        for i in range(6):
            rows.append({"so": f"SO-{mes}-{i}", "embarque": "FCL 1", "etd": pd.Timestamp(mes),
                         "tiempo_consolidacion": t, "estructura": "Consolidado", "maritimo": True,
                         "es_nuevo": True, "es_top": False})
    d = productos.base_lines(pd.DataFrame(rows), hoy)
    s = productos.summary(d, hoy).set_index(["grupo", "estructura"])
    r = s.loc[("SKU nuevos", "Consolidado")]
    assert r["base"] == 20 and r["actual"] == 16 and r["objetivo"] == 17
    assert r["variacion"] == pytest.approx(-0.20) and r["estado"] == "Cumple"


def test_sla_aereo_por_tipo():
    from services.data_loader import DatasetQuality, add_air_sla

    a = pd.DataFrame({"tipo_negocio": ["DJI", "DJI RCONLINE", "Marcas", "Defectuosos"],
                      "total_dias": [20.0, 30.0, 16.0, 10.0],
                      "etd": pd.to_datetime(["2026-08-05", "2026-08-05", "2026-07-01", "2026-08-05"])})
    out = add_air_sla(a, DatasetQuality("aereos", "Aéreos"))
    assert list(out["sla_aereo"].fillna(0)) == [24, 24, 16, 0]
    assert list(out["sla_vigente"]) == [True, True, False, True]
    assert list(out["estado_aereo"].fillna("")) == ["Dentro de SLA", "Fuera de SLA", "Dentro de SLA", ""]


def test_ahorro_40nor():
    h = pd.DataFrame({
        "embarque": ["A", "B", "C", "N1", "N2"], "etd": pd.to_datetime(["2026-09-05"] * 5),
        "tipo_ctnr": ["40ST/40HQ", "40ST/40HQ", "40ST/40HQ", "40NOR", "40NOR"],
        "flete_por_ctnr": [8000.0, 8200.0, 9000.0, 6000.0, 7000.0], "contenedores": [1, 1, 1, 2, 1],
        "capacidad": [68.0, 68.0, 68.0, 60.0, 60.0], "m3": [60.0, 60.0, 60.0, 100.0, 50.0],
    })
    nor = freight.nor_savings(h)
    assert list(nor["ref_hq"]) == [8200.0, 8200.0]
    assert list(nor["ahorro"]) == [4400.0, 1200.0]


def test_vs_mercado_ponderado_pondera_por_contenedores():
    import numpy as np
    import pandas as pd
    from utils import freight
    h = pd.DataFrame({"mercado_mes": [1000.0, 2000.0, np.nan], "flete_por_ctnr": [1100.0, 2000.0, 5000.0],
                      "contenedores": [1, 3, 2]})
    pct, n = freight.vs_mercado_ponderado(h)
    assert n == 2
    assert abs(pct - (7100 - 7000) / 7000) < 1e-9
