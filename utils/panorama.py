"""Panorama (nivel 1): los 8 indicadores para Dirección, con tendencia y estado contra objetivo.

Cada indicador devuelve un `Indicador` listo para mostrar. Sin Streamlit, para poder testearlo.
Tendencia: último mes cerrado contra el anterior (o trimestre, o año anterior, según el indicador).
"""
from __future__ import annotations

from dataclasses import dataclass

import numpy as np
import pandas as pd

from config import settings
from config.mappings import MODOS_MARITIMOS
from utils import calculations as calc
from utils import formatting as fmt


@dataclass
class Indicador:
    nombre: str
    valor: str
    unidad: str = ""
    sub: str = ""
    delta: str = ""            # "▼ 7 pp vs agosto"
    tono: str = ""             # good | bad | neutral (color de la tendencia)
    estado: str = ""           # ok | warn | bad (contra el objetivo); "" sin objetivo
    badge: str = ""
    ayuda: str = ""
    destino: str = ""          # url_path de la página de detalle


def _meses(t: pd.Timestamp) -> tuple[pd.Timestamp, pd.Timestamp]:
    last = t.to_period("M").to_timestamp() - pd.offsets.MonthBegin(1)
    return last, last - pd.offsets.MonthBegin(1)


def _mes(m: pd.Timestamp) -> str:
    return fmt.fmt_month(m, long=True).split()[0].lower()


def _flecha(diff: float) -> str:
    return "▲" if diff > 0 else ("▼" if diff < 0 else "=")


def _tono(diff: float, mejor_si_baja: bool) -> str:
    if diff != diff or diff == 0:
        return "neutral"
    return "good" if (diff < 0) == mejor_si_baja else "bad"


def _estado_pct(pct: float, objetivo: float) -> tuple[str, str]:
    """Mismo criterio que el resto del tablero: verde desde el objetivo, ámbar desde el mínimo, rojo debajo."""
    if pct != pct:
        return "", ""
    if pct >= objetivo:
        return "ok", "En objetivo"
    if pct >= settings.CUMPLIMIENTO_MINIMO:
        return "warn", "Cerca"
    return "bad", "Bajo objetivo"


# ---------------------------------------------------------------------------
# Tiempos
# ---------------------------------------------------------------------------
def sla_consolidacion(z: pd.DataFrame, z_all: pd.DataFrame, t: pd.Timestamp) -> Indicador:
    """z = marítimos zarpados del período; z_all = todos (sin período) para la tendencia mensual."""
    obj = settings.CUMPLIMIENTO_OBJETIVO
    pct, n = calc.cumplimiento(z["dias_consolidacion"], z["sla_consolidacion"])
    last, prev = _meses(t)
    mes = calc.month_start(z_all["etd"])
    p1, n1 = calc.cumplimiento(z_all.loc[mes == last, "dias_consolidacion"], z_all.loc[mes == last, "sla_consolidacion"])
    p0, n0 = calc.cumplimiento(z_all.loc[mes == prev, "dias_consolidacion"], z_all.loc[mes == prev, "sla_consolidacion"])
    if n1 < settings.MIN_SAMPLE:
        p1 = np.nan
    if n0 < settings.MIN_SAMPLE:
        p0 = np.nan
    ok = n >= settings.MIN_SAMPLE
    estado, badge = _estado_pct(pct, obj) if ok else ("", "")
    d = (p1 - p0) * 100 if p1 == p1 and p0 == p0 else np.nan
    return Indicador(
        "SLA de consolidación · marítimo", fmt.fmt_pct(pct) if ok else "—", estado=estado, badge=badge,
        sub=f"{_mes(last)} {fmt.fmt_pct(p1)} · objetivo {fmt.fmt_pct(obj)}" if p1 == p1 else f"objetivo {fmt.fmt_pct(obj)}",
        delta=f"{_flecha(d)} {fmt.fmt_num(abs(d), 0)} pp {_mes(last)} vs {_mes(prev)}" if d == d else "",
        tono=_tono(d, mejor_si_baja=False),
        ayuda=("% de embarques marítimos del período con consolidación (packeo → ETD) dentro de su SLA: "
               f"monoproveedor según la ETD ({calc.sla_mono_txt()}), consolidado según el puerto. "
               "La flecha compara el último mes cerrado con el anterior."),
        destino="sla")


def _mediana_mes(df: pd.DataFrame, col: str, t: pd.Timestamp) -> tuple[float, float, int]:
    last, prev = _meses(t)
    mes = calc.month_start(df["etd"])
    a, b = df.loc[mes == last, col].dropna(), df.loc[mes == prev, col].dropna()
    ok = settings.MIN_SAMPLE
    return (float(a.median()) if len(a) >= ok else np.nan, float(b.median()) if len(b) >= ok else np.nan, len(a))


def punta_aereo(a: pd.DataFrame, a_all: pd.DataFrame, t: pd.Timestamp) -> Indicador:
    """a / a_all = aéreos zarpados con «Total» (air_zarpados), del período / sin período."""
    obj = settings.CUMPLIMIENTO_OBJETIVO
    v = a["dias_aereo"].dropna()
    vig = a[a["sla_vigente"] & a["sla_aereo"].notna()] if "sla_vigente" in a else a.iloc[0:0]
    pct, n = calc.cumplimiento(vig["dias_aereo"], vig["sla_aereo"])
    m1, m0, _ = _mediana_mes(a_all, "dias_aereo", t)
    last, prev = _meses(t)
    d = m1 - m0 if m1 == m1 and m0 == m0 else np.nan
    estado, badge = _estado_pct(pct, obj) if n >= settings.MIN_SAMPLE else ("", "")
    return Indicador(
        "Punta a punta · aéreo", fmt.fmt_int(v.median()) if len(v) >= settings.MIN_SAMPLE else "—", "d",
        estado=estado, badge=badge,
        sub=(f"{fmt.fmt_pct(pct)} dentro del SLA de su tipo ({fmt.fmt_int(n)} embarques)"
             if n >= settings.MIN_SAMPLE else "Pocos embarques con SLA vigente"),
        delta=f"{_flecha(d)} {fmt.fmt_int(abs(d))} d {_mes(last)} vs {_mes(prev)}" if d == d else "",
        tono=_tono(d, mejor_si_baja=True),
        ayuda=("Mediana de packeo mínimo → ETA Caldas (columna «Total» de Seguimiento Aéreos). El estado compara el % "
               f"de embarques dentro del SLA de su tipo (vigente desde el {settings.SLA_AEREO_DESDE:%d/%m/%Y}) con el "
               f"objetivo de {fmt.fmt_pct(obj)}. La flecha compara la mediana del último mes cerrado con la del anterior."),
        destino="sla")


def punta_maritimo(z: pd.DataFrame, z_all: pd.DataFrame, t: pd.Timestamp) -> Indicador:
    obj = settings.CUMPLIMIENTO_OBJETIVO
    v = z["dias_total"].dropna()
    pct, n = calc.cumplimiento(z["dias_total"], z["sla_total"])
    m1, m0, _ = _mediana_mes(z_all, "dias_total", t)
    last, prev = _meses(t)
    d = m1 - m0 if m1 == m1 and m0 == m0 else np.nan
    estado, badge = _estado_pct(pct, obj) if n >= settings.MIN_SAMPLE else ("", "")
    return Indicador(
        "Punta a punta · marítimo", fmt.fmt_int(v.median()) if len(v) >= settings.MIN_SAMPLE else "—", "d",
        estado=estado, badge=badge,
        sub=f"{fmt.fmt_pct(pct)} dentro del SLA total del puerto" if n else "",
        delta=f"{_flecha(d)} {fmt.fmt_int(abs(d))} d {_mes(last)} vs {_mes(prev)}" if d == d else "",
        tono=_tono(d, mejor_si_baja=True),
        ayuda=("Mediana de fin de producción → ETA, solo embarques que ya llegaron. El estado compara el % dentro del SLA total de cada puerto "
               f"(Validaciones) con el objetivo de {fmt.fmt_pct(obj)}."),
        destino="sla")


def time_to_market(summ: pd.DataFrame) -> Indicador:
    """summ = productos.objetivo_universo(...): fila «Todas las SO»."""
    ayuda = ("Mediana de días de consolidación por SO (todas las SO, marítimas y aéreas, sin muestras ni repuestos). "
             f"Objetivo: bajar un {fmt.fmt_pct(settings.REDUCCION_OBJETIVO)} contra Q1.")
    r = summ[summ["grupo"] == "Todas las SO"] if len(summ) else summ
    if r.empty or r.iloc[0]["actual"] != r.iloc[0]["actual"]:
        return Indicador("Time to market", "—", ayuda=ayuda, destino="sla")
    r = r.iloc[0]
    var = r["variacion"]
    estado = {"Cumple": "ok", "Reduce, sin llegar": "warn", "No reduce": "bad"}.get(r["estado"], "")
    return Indicador(
        "Time to market", fmt.fmt_int(r["actual"]), "d", estado=estado, badge=r["estado"],
        sub=f"{r['actual_q']} vs {r['base_q']} ({fmt.fmt_int(r['base'])} d) · objetivo "
            f"−{fmt.fmt_pct(settings.REDUCCION_OBJETIVO)}",
        delta=f"{_flecha(var)} {fmt.fmt_pct(abs(var))} {r['actual_q']} vs {r['base_q']}" if var == var else "",
        tono=_tono(var, mejor_si_baja=True), ayuda=ayuda, destino="sla")


# ---------------------------------------------------------------------------
# Volumen y costos
# ---------------------------------------------------------------------------
def volumen(h: pd.DataFrame, h_prev: pd.DataFrame | None) -> Indicador:
    """h = embarques zarpados del período (todos los modos); h_prev = mismo período del año anterior
    (None si el período no tiene inicio y la comparación no tiene sentido)."""
    n = h["embarque"].nunique()
    n0 = h_prev["embarque"].nunique() if h_prev is not None and len(h_prev) else 0
    d = (n - n0) / n0 if n0 else np.nan
    return Indicador(
        "Volumen gestionado", fmt.fmt_int(n), "emb.",
        sub=f"{fmt.fmt_int(h['m3'].sum())} m³ · {fmt.fmt_usd(h['fob_simi'].sum())} FOB",
        delta=f"{_flecha(d)} {fmt.fmt_pct(abs(d))} vs mismo período del año anterior" if d == d else "",
        tono="neutral",
        ayuda="Embarques zarpados en el período (todos los modos), con su volumen y FOB SIMI. Se compara con la "
              "misma ventana de fechas del año anterior.",
        destino="embarques")


def _costo_fila(d: pd.DataFrame) -> pd.Series:
    return (d["flete_pagado"].clip(lower=0).fillna(0) + d["gastos_origen"].clip(lower=0).fillna(0)
            + d["gastos_locales"].clip(lower=0).fillna(0))


def _incidencia(d: pd.DataFrame) -> float:
    if not len(d) or "fob" not in d:
        return np.nan
    ok = d["fob"] > 0
    fob = float(d.loc[ok, "fob"].sum())
    return float(_costo_fila(d[ok]).sum()) / fob if fob else np.nan


def costo(pagos: pd.DataFrame, pagos_all: pd.DataFrame, t: pd.Timestamp) -> Indicador:
    """pagos = marítimos + aéreos zarpados con flete pagado (período); pagos_all = sin período."""
    total = float(_costo_fila(pagos).sum()) if len(pagos) else 0.0
    inc = _incidencia(pagos)
    last, prev = _meses(t)
    mes = calc.month_start(pagos_all["etd"]) if len(pagos_all) else pd.Series(dtype="datetime64[ns]")
    i1 = _incidencia(pagos_all[mes == last]) if len(pagos_all) else np.nan
    i0 = _incidencia(pagos_all[mes == prev]) if len(pagos_all) else np.nan
    d = (i1 - i0) * 100 if i1 == i1 and i0 == i0 else np.nan
    return Indicador(
        "Costo logístico pagado", fmt.fmt_usd(total),
        sub=f"{fmt.fmt_pct(inc, 1)} del FOB · {_mes(last)} {fmt.fmt_pct(i1, 1)}",
        delta=f"{_flecha(d)} {fmt.fmt_num(abs(d), 1)} pp de incidencia {_mes(last)} vs {_mes(prev)}" if d == d else "",
        tono=_tono(d, mejor_si_baja=True),
        ayuda="Flete + gastos en origen + gastos locales, marítimo y aéreo. Incidencia = costo / FOB, solo embarques "
              "con FOB cargado. La flecha compara la incidencia del último mes cerrado con la del anterior.",
        destino="fletes")


def captura(nor: pd.DataFrame, nor_prev: pd.DataFrame | None, neg: pd.DataFrame | None = None,
            neg_prev: pd.DataFrame | None = None, hay_negociacion: bool = False) -> Indicador:
    """Ahorro capturado por la gestión: negociación de tarifas + uso de 40 NOR (utils.captura)."""
    from utils import captura as cap
    r = cap.resumen(neg, nor)
    v = r["total"]
    d = np.nan
    if nor_prev is not None:
        r0 = cap.resumen(neg_prev, nor_prev)
        d = v - r0["total"]
    neg_txt = (f"negociación <b>{fmt.fmt_usd(r['negociacion'])}</b>" if hay_negociacion
               else "negociación: falta la solapa sin negociar")
    return Indicador(
        "Captura acumulada", fmt.fmt_usd(v),
        sub=f"{neg_txt} · 40 NOR <b>{fmt.fmt_usd(r['nor'])}</b>",
        delta=(f"{_flecha(d)} {fmt.fmt_usd(abs(d))} vs mismo período del año anterior ({fmt.fmt_usd(r0['total'])})"
               if d == d else ""),
        tono=_tono(d, mejor_si_baja=False),
        ayuda="Lo que la gestión ahorró y se puede sumar: rebaja al negociar las tarifas (tarifa sin negociar − "
              "negociada, en los embarques que salieron con esa tarifa) + uso de 40 NOR en lugar de 40 ST/HQ "
              "(mediana pagada ese mes). No incluye la posición contra el mercado.",
        destino="fletes")


def vs_mercado(pct: float, n: int, pct_last: float, pct_prev: float, t: pd.Timestamp) -> Indicador:
    """pct_last / pct_prev = NaN cuando ese mes tiene pocos embarques comparados."""
    tol = settings.PAGADO_VS_MERCADO_TOLERANCIA
    if n < settings.MIN_SAMPLE or pct != pct:
        return Indicador("Pagado vs mercado", "—", sub="Sin cotizaciones para comparar", destino="fletes",
                         ayuda="Flete pagado por contenedor contra la mediana de mercado del mes (cotizaciones).")
    estado = "ok" if pct <= 0 else ("warn" if pct <= tol else "bad")
    last, prev = _meses(t)
    d = (pct_last - pct_prev) * 100 if pct_last == pct_last and pct_prev == pct_prev else np.nan
    return Indicador(
        "Pagado vs mercado", fmt.fmt_pct(pct, signed=True), estado=estado,
        badge={"ok": "Bajo mercado", "warn": "Algo encima", "bad": "Sobre mercado"}[estado],
        sub=f"{fmt.fmt_int(n)} embarques comparados con el mercado de su mes",
        delta=f"{_flecha(d)} {fmt.fmt_num(abs(d), 0)} pp {_mes(last)} vs {_mes(prev)}" if d == d else "",
        tono=_tono(d, mejor_si_baja=True),
        ayuda=("Flete pagado contra la mediana de mercado del mes (mejor tarifa de cada forwarder cotizada para ese "
               "tipo de contenedor y destino), ponderado por contenedores. Negativo = pagamos menos que el mercado. "
               f"Verde ≤ 0 %, ámbar hasta +{fmt.fmt_pct(tol)}, rojo por encima."),
        destino="fletes")


def ventana_anterior(start: pd.Timestamp, end: pd.Timestamp) -> tuple[pd.Timestamp, pd.Timestamp]:
    return start - pd.DateOffset(years=1), end - pd.DateOffset(years=1)


def maritimos(h: pd.DataFrame) -> pd.DataFrame:
    return h[h["modo"].isin(MODOS_MARITIMOS)]
