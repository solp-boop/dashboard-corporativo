"""Fase 1: salud de datos, bandeja de acción y panorama."""
from __future__ import annotations

from types import SimpleNamespace

import numpy as np
import pandas as pd

from utils import bandeja, panorama, salud

HOY = pd.Timestamp("2026-10-07")
ts = pd.Timestamp


def _bundle(**frames):
    data = {k: v for k, v in frames.items()}
    return SimpleNamespace(get=data.get, quality={}, source_modified={})


def _res(**kw):
    base = dict(embarque=["FCL 1"], responsable=["Sofi"], forwarder=["NIP"], etd=[ts("2026-10-20")],
                eta=[ts("2026-11-30")], f_packeo_min=[ts("2026-10-01")], estructura=["Consolidado"],
                modo=["Marítimo"], grupo_modo=["Marítimo"], etd_ok=[False], draft_bl=["SI"], pl_final=["SI"],
                f_instruccion=[ts("2026-09-20")], estado_consolidacion=["Dentro de SLA"],
                dias_consolidacion=[19.0], sla_consolidacion=[25.0], tipo_demora=[None])
    base.update(kw)
    return pd.DataFrame(base)


# ---------------------------------------------------------------- salud
def test_salud_llego_y_sigue_en_reservas_y_fechas_ilogicas():
    res = _res(embarque=["FCL 1", "FCL 2"], responsable=["Sofi", "Sol"], forwarder=["NIP", "NIP"],
               etd=[ts("2026-09-01"), ts("2026-10-20")], eta=[ts("2026-10-01"), ts("2026-10-10")],
               f_packeo_min=[ts("2026-09-10"), ts("2026-10-01")], estructura=["Consolidado"] * 2,
               modo=["Marítimo"] * 2, grupo_modo=["Marítimo"] * 2, etd_ok=[True] * 2, draft_bl=["SI"] * 2,
               pl_final=["SI"] * 2, f_instruccion=[None] * 2, estado_consolidacion=[None] * 2,
               dias_consolidacion=[np.nan] * 2, sla_consolidacion=[25.0] * 2, tipo_demora=[None] * 2)
    c = {x.clave: x for x in salud.controles(_bundle(reservas=res), HOY)}
    assert c["llego_en_reservas"].n == 1                      # FCL 1: ETA 01/10 ya pasó
    assert c["packeo_post_etd"].n == 1                        # FCL 1: packeo 10/09 después de la ETD 01/09
    assert c["eta_antes_etd"].n == 1                          # FCL 2: ETA 10/10 antes de la ETD 20/10
    assert c["packeo_post_etd"].severidad == "bad"


def test_salud_criticos_ignora_air_de_reservas():
    res = _res(embarque=["FCL 1", "AIR 9"], responsable=["Sofi", "Sofi"], forwarder=[None, None],
               etd=[ts("2026-10-20")] * 2, eta=[ts("2026-11-30")] * 2, f_packeo_min=[ts("2026-10-01")] * 2,
               estructura=["Consolidado", None], modo=["Marítimo", "Aéreo"], grupo_modo=["Marítimo", "Aéreo"],
               etd_ok=[False] * 2, draft_bl=["SI"] * 2, pl_final=["SI"] * 2, f_instruccion=[None] * 2,
               estado_consolidacion=[None] * 2, dias_consolidacion=[np.nan] * 2, sla_consolidacion=[25.0] * 2,
               tipo_demora=[None] * 2)
    c = {x.clave: x for x in salud.controles(_bundle(reservas=res), HOY)}
    assert c["criticos"].casos["registro"].tolist() == ["FCL 1"]


def test_salud_dias_habiles_sin_edicion():
    # editado el lunes 05/10 a la mañana: el jueves 08/10 van 2 días hábiles completos (mar y mié)
    assert salud._dias_habiles(ts("2026-10-05 09:00"), ts("2026-10-08")) == 2
    assert salud._dias_habiles(ts("2026-10-07 09:00"), ts("2026-10-07")) == 0


def test_salud_resumen():
    ok = salud.Control("a", "A", "", "", "")
    roto = salud.Control("b", "B", "", "", "", "bad", pd.DataFrame({"registro": ["x"]}))
    assert salud.resumen([ok]) == ("ok", 0, 0)
    assert salud.resumen([ok, roto]) == ("bad", 1, 1)


# ---------------------------------------------------------------- bandeja
def test_bandeja_reglas_en_curso():
    res = _res(embarque=["FCL 1", "FCL 2", "FCL 3", "FCL 4"], responsable=["Sofi"] * 4, forwarder=["NIP"] * 4,
               etd=[ts("2026-10-09"), ts("2026-10-01"), ts("2026-10-25"), ts("2026-10-04")],
               eta=[ts("2026-11-30")] * 4, f_packeo_min=[ts("2026-09-01")] * 4, estructura=["Consolidado"] * 4,
               modo=["Marítimo"] * 4, grupo_modo=["Marítimo"] * 4, etd_ok=[False, True, False, False],
               draft_bl=["SI", "NO", "SI", "NO"], pl_final=["SI"] * 4, f_instruccion=[None] * 4,
               estado_consolidacion=["Dentro de SLA", "Dentro de SLA", "Fuera de SLA", "Fuera de SLA"],
               dias_consolidacion=[8.0, 30.0, 54.0, 33.0], sla_consolidacion=[25.0] * 4, tipo_demora=[None] * 4)
    df = bandeja.armar(bandeja.casos_en_curso(res, HOY))
    sit = dict(zip(df["embarque"] + "|" + df["tipo"], df["prioridad"]))
    assert sit["FCL 1|" + bandeja.TIPOS["forwarder"]] == "Alta"        # sale en 2 días sin confirmar
    assert sit["FCL 2|" + bandeja.TIPOS["forwarder"]] == "Alta"        # zarpó hace 6 días sin Draft BL
    assert sit["FCL 3|" + bandeja.TIPOS["sla"]] == "Alta"              # packeo hace 36 d > SLA 25: ya pasado
    assert "FCL 4|" + bandeja.TIPOS["forwarder"] not in sit            # zarpó hace 3 días: todavía no se reclama
    assert "FCL 4|" + bandeja.TIPOS["sla"] not in sit                  # ya zarpó: no es riesgo accionable
    fila = df[(df["embarque"] == "FCL 3")].iloc[0]
    assert fila["excedido"] == 29 and fila["accion"].startswith("Adelantar")  # packeo ya hecho


def test_bandeja_enriquece_so_y_proveedor():
    df = bandeja.armar([pd.DataFrame({"embarque": ["FCL 7"], "tipo": ["x"], "prioridad": ["Media"]})])
    eh = pd.DataFrame({"embarque": ["fcl 7", "FCL 7"], "so": ["SO-2", "SO-1"], "proveedor": ["Acme", "Acme"]})
    out = bandeja.enriquecer(df, None, eh)
    assert out.iloc[0]["so"] == "SO-1, SO-2" and out.iloc[0]["proveedor"] == "Acme"


# ---------------------------------------------------------------- panorama
def test_panorama_sla_tendencia_y_estado():
    filas = []
    for mes, ok in ((ts("2026-08-10"), 6), (ts("2026-09-10"), 3)):
        for i in range(6):
            filas.append({"etd": mes, "dias_consolidacion": 10.0 if i < ok else 40.0, "sla_consolidacion": 25.0})
    z = pd.DataFrame(filas)
    ind = panorama.sla_consolidacion(z, z, HOY)
    assert ind.valor == "75 %" and ind.estado == "ok"
    assert ind.delta.startswith("▼ 50 pp") and ind.tono == "bad"


def test_panorama_sin_muestra_no_muestra_tendencia():
    z = pd.DataFrame({"etd": [ts("2026-09-10"), ts("2026-08-10")], "dias_consolidacion": [10.0, 40.0],
                      "sla_consolidacion": [25.0, 25.0]})
    assert panorama.sla_consolidacion(z, z, HOY).delta == ""


def test_panorama_volumen_sin_comparacion_si_no_hay_inicio():
    h = pd.DataFrame({"embarque": ["A", "B"], "m3": [10.0, 5.0], "fob_simi": [100.0, 50.0]})
    assert panorama.volumen(h, None).delta == ""
    prev = pd.DataFrame({"embarque": ["X"], "m3": [1.0], "fob_simi": [1.0]})
    assert panorama.volumen(h, prev).delta.startswith("▲ 100 %")


def test_panorama_vs_mercado_estado():
    assert panorama.vs_mercado(-0.02, 20, np.nan, np.nan, HOY).estado == "ok"
    assert panorama.vs_mercado(0.07, 20, 0.05, 0.10, HOY).estado == "bad"
    assert panorama.vs_mercado(0.07, 20, 0.05, 0.10, HOY).tono == "good"     # bajó 5 pp: mejora


def test_sla_zarpados_con_reservas():
    from utils import sla
    hist = pd.DataFrame({"embarque": ["FCL 1"], "modo": ["Marítimo FCL"], "etd": [ts("2026-09-01")]})
    res = pd.DataFrame({"embarque": ["FCL 1", "FCL 2", "FCL 3"], "modo": ["Marítimo FCL"] * 3,
                        "etd": [ts("2026-09-01"), ts("2026-09-20"), ts("2026-10-20")], "responsable": ["a"] * 3})
    z = sla.zarpados_con_reservas(hist, res, HOY)
    assert sorted(z["embarque"]) == ["FCL 1", "FCL 2"]      # FCL 1 una sola vez; FCL 3 todavía no zarpó


# ---------------------------------------------------------------- fase 2: diagnóstico
def test_diagnostico_contribucion_y_multiple():
    from utils import diagnostico as dg
    df = pd.DataFrame({
        "embarque": ["A", "B", "C", "D"], "dias": [30.0, 40.0, 10.0, 50.0], "sla": [25.0] * 4,
        "puerto": ["Ningbo", "Ningbo", "Shekou", None],
        "proveedores": [["P1"], ["P1", "P2"], ["P2"], []],
    })
    t = dg.explicar(df, "puerto", "dias", "sla")
    assert t.iloc[0]["grupo"] == "Ningbo" and t.iloc[0]["fuera"] == 2
    assert abs(t.iloc[0]["contrib"] - 2 / 3) < 1e-9
    assert t.iloc[-1]["grupo"] == dg.SIN_DATO                       # «Sin dato» siempre al final
    tp = dg.explicar(df, "proveedores", "dias", "sla").set_index("grupo")
    assert tp.loc["P1", "ops"] == 2 and tp.loc["P2", "ops"] == 2     # B cuenta en los dos proveedores
    assert list(dg.casos(df, "proveedores", "P2")["embarque"]) == ["B", "C"]
    assert list(dg.casos(df, "puerto", dg.SIN_DATO)["embarque"]) == ["D"]


def test_diagnostico_delta_vs_anterior():
    from utils import diagnostico as dg
    act = pd.DataFrame({"embarque": ["A", "B"], "dias": [20.0, 30.0], "sla": [25.0, 25.0], "puerto": ["X", "X"]})
    prev = pd.DataFrame({"embarque": ["C"], "dias": [15.0], "sla": [25.0], "puerto": ["X"]})
    t = dg.explicar(act, "puerto", "dias", "sla", prev=prev)
    assert t.iloc[0]["delta"] == 10


# ---------------------------------------------------------------- fase 3: captura y costos
def test_captura_por_negociacion_asigna_tarifa_vigente_y_parecida():
    from utils import captura as cap
    hist = pd.DataFrame({
        "embarque": ["A", "B", "C"], "forwarder": ["Delfin"] * 3, "puerto": ["Ningbo"] * 3,
        "tipo_ctnr": ["40ST/40HQ"] * 3, "contenedores": [2.0, 1.0, 1.0], "flete_por_ctnr": [1000.0, 2000.0, 1000.0],
        "f_instruccion": [ts("2026-05-05"), ts("2026-05-05"), ts("2026-07-01")], "etd": [ts("2026-05-20")] * 3,
    })
    neg = pd.DataFrame({"forwarder": ["DELFIN"], "puerto": ["ningbo"], "tipo_ctnr": ["40ST/40HQ"],
                        "validez_desde": [ts("2026-05-01")], "validez_hasta": [ts("2026-05-15")],
                        "flete_original": [1200.0], "flete_negociado": [1000.0], "rebaja": [200.0]})
    c = cap.por_negociacion(hist, neg)
    assert list(c["embarque"]) == ["A"]                # B pagó muy distinto; C fuera de vigencia
    assert c.iloc[0]["captura"] == 400.0               # 200 × 2 contenedores


def test_captura_oportunidades_y_mensual():
    from utils import captura as cap
    h = pd.DataFrame({"embarque": ["A", "B"], "forwarder": ["X", "X"], "puerto": ["P", "P"], "tipo_ctnr": ["20ST"] * 2,
                      "contenedores": [1.0, 2.0], "flete_por_ctnr": [1200.0, 900.0], "mercado_mes": [1000.0, 1000.0]})
    op = cap.oportunidades(h)
    assert op.iloc[0]["en_juego"] == 200.0             # solo A pagó por encima
    nor = pd.DataFrame({"mes": [ts("2026-05-01")], "ahorro": [50.0], "contenedores": [1.0]})
    neg = pd.DataFrame({"mes": [ts("2026-05-01"), ts("2026-06-01")], "captura": [10.0, 20.0], "contenedores": [1, 1]})
    g = cap.mensual(neg, nor)
    assert list(g["total"]) == [60.0, 20.0] and g["acumulado"].iloc[-1] == 80.0


def test_costos_por_dimension():
    from utils import costos as cs
    d = pd.DataFrame({"embarque": ["A", "B", "C"], "forwarder": ["X", "X", "Y"], "costo": [100.0, 300.0, 100.0],
                      "flete_por_ctnr": [50.0, 70.0, 40.0], "mercado_mes": [60.0, 60.0, np.nan],
                      "contenedores": [1.0, 1.0, 1.0], "fob": [1000.0, 1000.0, 0.0]})
    t = cs.por_dimension(d, "forwarder")
    assert t.iloc[0]["grupo"] == "X" and abs(t.iloc[0]["pct_gasto"] - 0.8) < 1e-9
    assert abs(t.iloc[0]["incidencia"] - 0.2) < 1e-9 and abs(t.iloc[0]["vs_mercado"] - 0.0) < 1e-9


def test_captura_no_cuenta_si_pago_la_tarifa_original():
    from utils import captura as cap
    hist = pd.DataFrame({"embarque": ["A"], "forwarder": ["Delfin"], "puerto": ["Ningbo"], "tipo_ctnr": ["20ST"],
                         "contenedores": [1.0], "flete_por_ctnr": [5400.0], "f_instruccion": [ts("2026-05-05")],
                         "etd": [ts("2026-05-20")]})
    neg = pd.DataFrame({"forwarder": ["Delfin"], "puerto": ["Ningbo"], "tipo_ctnr": ["20ST"],
                        "validez_desde": [ts("2026-05-01")], "validez_hasta": [ts("2026-05-15")],
                        "flete_original": [5170.0], "flete_negociado": [4700.0], "rebaja": [470.0]})
    assert cap.por_negociacion(hist, neg).empty


def test_proyeccion_sin_doble_conteo():
    from utils import proyeccion as pr
    hoy = ts("2026-10-07")
    res = pd.DataFrame({"embarque": ["FCL 1", "FCL 2"], "etd": [ts("2026-10-20"), ts("2026-09-01")],
                        "contenedores": [2.0, 1.0], "m3": [120.0, 60.0], "fob_real": [1000.0, 1.0],
                        "fob_simi": [900.0, 1.0], "estructura": ["Consolidado", "Mono"], "modo": ["Marítimo FCL"] * 2})
    planif = pd.DataFrame({"so": ["SO-1", "SO-2", "SO-3"], "embarque": ["FCL 1", None, None],
                           "etd": [ts("2026-10-20"), ts("2026-11-10"), ts("2026-11-15")], "m3": [120.0, 59.0, 59.0],
                           "fob_origen": [1000.0, 500.0, 500.0], "estructura": ["Consolidado", "Monoproveedor",
                                                                                 "Monoproveedor"], "modo": [None] * 3})
    d = pr.base(res, planif, None, None, hoy)
    t = pr.mensual(d, hoy).set_index("mes")
    assert t.loc[ts("2026-10-01"), "embarques"] == 1 and t.loc[ts("2026-10-01"), "so_por_reservar"] == 0
    assert t.loc[ts("2026-11-01"), "contenedores_est"] == 2 and t.loc[ts("2026-11-01"), "fob"] == 1000.0
    # FCL 2 (ETD pasada, sigue en Reservas) va a «Anterior», no se pierde.
    assert t.loc[pr.ANTERIOR, "m3"] == 60.0
    assert t.iloc[-1]["m3"] == 298.0
    # Ya en Históricas: no se cuenta.
    d2 = pr.base(res, planif, None, pd.DataFrame({"embarque": ["FCL 2"]}), hoy)
    assert pr.mensual(d2, hoy).iloc[-1]["m3"] == 238.0
