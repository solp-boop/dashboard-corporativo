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
    assert prom == pytest.approx((6000 + 5800 + 7000) / 3)


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
    # mercado sept 40ST/40HQ = promedio de la mejor de cada forwarder con validez que empieza en sept: A 6000, B 5800, C 7000
    assert out.loc[0, "mercado_mes"] == pytest.approx(6266.67, rel=1e-3)
    assert out.loc[0, "vs_mercado"] == pytest.approx(5940 / 6266.67 - 1, rel=1e-3)
    assert np.isnan(out.loc[1, "vs_mercado"])
