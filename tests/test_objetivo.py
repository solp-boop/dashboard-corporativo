"""Objetivo −15 % contra el año anterior: por estructura, mes a mes, acumulado y total ponderado."""
import pandas as pd

from utils import objetivo

HOY = pd.Timestamp("2026-03-15")


def _d(rows):
    return pd.DataFrame([{"etd": pd.Timestamp(f), "estructura": e, "valor": v} for f, e, v in rows])


def test_mes_a_mes_acumulado_y_total_ponderado():
    rows = []
    # Enero: conso 30 → 24 (−20 %, cumple); mono 20 → 19 (−5 %)
    rows += [("2025-01-10", "Consolidado", 30)] * 5 + [("2026-01-10", "Consolidado", 24)] * 6
    rows += [("2025-01-10", "Monoproveedor", 20)] * 5 + [("2026-01-10", "Monoproveedor", 19)] * 2
    # Febrero: conso 30 → 33 (sube)
    rows += [("2025-02-10", "Consolidado", 30)] * 5 + [("2026-02-10", "Consolidado", 33)] * 6
    # Marzo (en curso): no se califica
    rows += [("2025-03-10", "Consolidado", 30)] * 5 + [("2026-03-10", "Consolidado", 10)] * 5
    r = objetivo.vs_anio_anterior(_d(rows), HOY)
    m = r["mensual"].set_index(["estructura", "mes"])
    assert m.loc[("Consolidado", 1), "objetivo"] == 25.5
    assert m.loc[("Consolidado", 1), "estado"] == "Cumple"
    assert m.loc[("Monoproveedor", 1), "estado"] == "Muestra chica"      # 2 casos en 2026
    assert m.loc[("Consolidado", 2), "estado"] == "No reduce"
    assert m.loc[("Consolidado", 3), "estado"] == "En curso"
    ac = r["acumulado"].set_index("estructura")
    assert r["ult_mes"] == 2
    assert ac.loc["Consolidado", "ant"] == 30 and ac.loc["Consolidado", "n_act"] == 12   # ene + feb, sin marzo
    # Total = variaciones ponderadas por el volumen 2026 (conso 12, mono 2)
    v_c, v_m = ac.loc["Consolidado", "var"], ac.loc["Monoproveedor", "var"]
    assert abs(r["total"]["var"] - (v_c * 12 + v_m * 2) / 14) < 1e-9


def test_la_mezcla_no_mueve_el_total():
    # Ninguna estructura mejora, pero en 2026 hay muchos más mono (más rápidos): la mediana total bajaría.
    rows = [("2025-01-10", "Consolidado", 30)] * 10 + [("2025-01-10", "Monoproveedor", 15)] * 2
    rows += [("2026-01-10", "Consolidado", 30)] * 2 + [("2026-01-10", "Monoproveedor", 15)] * 10
    r = objetivo.vs_anio_anterior(_d(rows), pd.Timestamp("2026-02-10"))
    assert r["total"]["var"] == 0 and r["total"]["estado"] == "No reduce"


def test_objetivo_por_fila_y_sin_datos():
    rows = [("2025-01-10", "Consolidado", 30)] * 5 + [("2026-01-10", "Consolidado", 20)] * 5
    d = _d(rows)
    r = objetivo.vs_anio_anterior(d, HOY)
    obj = objetivo.objetivo_por_fila(d[d["etd"].dt.year == 2026], r)
    assert (obj == 25.5).all()
    vacio = objetivo.vs_anio_anterior(pd.DataFrame(columns=["etd", "estructura", "valor"]), HOY)
    assert vacio["mensual"].empty and vacio["total"]["var"] != vacio["total"]["var"]
