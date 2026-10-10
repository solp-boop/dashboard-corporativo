"""Tiempos de consolidación de SKU nuevos y top ranking contra el objetivo de −15 %.

Por trimestre del año: Q1 es la base; el objetivo es bajar la mediana un 15 % y se
compara el último trimestre cerrado contra la base.

Unidad: SO (Embarques Historicos tiene una fila por SO × producto; se cuentan SO
distintas). Tiempo: columna "Tiempo de consolidacion" de Embarques Historicos.
Estructura (mono / consolidado): la del embarque en Reservas Históricas.

Sin Streamlit, para poder testearlo.
"""
from __future__ import annotations

import numpy as np
import pandas as pd

from config import settings
from utils import calculations as calc

GRUPOS = {"es_nuevo": "SKU nuevos", "es_top": f"Top ranking (1–{settings.TOP_RANKING_MAX})"}
ESTRUCTURAS = ["Consolidado", "Monoproveedor"]


def base_lines(eh: pd.DataFrame, today: pd.Timestamp) -> pd.DataFrame:
    """Líneas marítimas ya zarpadas con tiempo de consolidación y estructura."""
    d = eh[eh["maritimo"] & eh["etd"].notna() & (eh["etd"] <= today)
           & eh["tiempo_consolidacion"].notna() & eh["estructura"].isin(ESTRUCTURAS)].copy()
    d = _solo_destino(d)
    d["mes"] = calc.month_start(d["etd"])
    return d


def _solo_destino(d: pd.DataFrame) -> pd.DataFrame:
    if d.empty:
        return d
    if settings.PRODUCTOS_DESTINO and "destino" in d:
        from utils.data_cleaning import fold
        return d[d["destino"].map(lambda v: fold(v) == fold(settings.PRODUCTOS_DESTINO) if isinstance(v, str) else False)]
    return d


EXCLUIDOS = ("muestra", "repuesto")   # tipos de negocio que no entran en el universo de time to market


def tipos_aereos(aereos: pd.DataFrame | None, hist: pd.DataFrame | None = None) -> dict:
    """Embarque (id_key) → tipo de negocio aéreo: Seguimiento Aéreos y, si no está, «Tipo de envio aereo» de Históricas."""
    from utils.data_cleaning import id_key
    out = {}
    if hist is not None and len(hist) and "tipo_envio_aereo" in hist:
        h = hist.dropna(subset=["tipo_envio_aereo"])
        out.update(dict(zip(id_key(h["embarque"]), h["tipo_envio_aereo"])))
    if aereos is not None and len(aereos) and "tipo_negocio" in aereos:
        a = aereos.dropna(subset=["tipo_negocio"])
        out.update(dict(zip(id_key(a["embarque"]), a["tipo_negocio"])))   # Seguimiento Aéreos manda
    return out


def muestras(aereos: pd.DataFrame | None, planif: pd.DataFrame | None, hist: pd.DataFrame | None = None) -> tuple[set, set]:
    """(embarques, SO) a excluir: muestras y repuestos.

    Aéreos con tipo MUESTRAS / REPUESTOS (Seguimiento Aéreos o «Tipo de envio aereo» de Históricas) y SO
    «Muestras» / «Repuestos» en Planificación.
    """
    from utils.data_cleaning import fold, id_key

    def es_excluido(v) -> bool:
        return isinstance(v, str) and any(k in fold(v) for k in EXCLUIDOS)

    embs, sos = set(), set()
    embs = {k for k, v in tipos_aereos(aereos, hist).items() if es_excluido(v)}
    if aereos is not None and len(aereos):
        col = aereos["tipo_sla"] if "tipo_sla" in aereos else None
        if col is not None:
            embs |= set(id_key(aereos.loc[col.map(es_excluido), "embarque"].dropna()))
    if planif is not None and len(planif) and "tipo_negocio" in planif:
        sos = set(planif.loc[planif["tipo_negocio"].map(es_excluido), "so"].dropna().astype(str))
    return embs, sos


MEDIOS = {"todos": "Todos", "Marítimo": "Marítimo (FCL)", "Aéreo": "Aéreo (AIR)"}


def base_universo(eh: pd.DataFrame, today: pd.Timestamp, aereos=None, planif=None, hist=None) -> pd.DataFrame:
    """Universo completo de SO (marítimas y aéreas) ya zarpadas, sin muestras ni repuestos, con tiempo válido.

    Columna «medio»: Marítimo (embarque FCL), Aéreo (AIR, sin DJI Baynal / RC Online / Aeropix) u Otro
    (el resto: AIR de esos tipos de negocio o embarques con otro código). Todas = Marítimo + Aéreo + Otro."""
    from utils.data_cleaning import fold, id_key
    d = eh[eh["etd"].notna() & (eh["etd"] <= today) & eh["tiempo_consolidacion"].notna()].copy()
    d = _solo_destino(d)
    embs, sos = muestras(aereos, planif, hist)
    d = d[~id_key(d["embarque"]).isin(embs) & ~d["so"].astype(str).isin(sos)]
    d["mes"] = calc.month_start(d["etd"])
    k = id_key(d["embarque"].astype(str))
    pref = d["embarque"].astype(str).str.strip().str.upper()
    tipos = tipos_aereos(aereos, hist)
    excl = [fold(x).replace(" ", "") for x in settings.TTM_TIPOS_AEREOS_EXCLUIR]
    tipo_excl = k.map(lambda e: isinstance(tipos.get(e), str)
                      and any(fold(tipos[e]).replace(" ", "").startswith(x) for x in excl))
    d["medio"] = np.select([pref.str.startswith("FCL"), pref.str.startswith("AIR") & ~tipo_excl],
                           ["Marítimo", "Aéreo"], "Otro")
    return d


def per_so(d: pd.DataFrame) -> pd.DataFrame:
    """Una fila por SO: mediana del tiempo de sus líneas (suele ser el mismo valor)."""
    return (d.groupby(["so", "mes", "estructura"], as_index=False)
              .agg(tiempo=("tiempo_consolidacion", "median")))


def monthly(d: pd.DataFrame, grupo: str) -> pd.DataFrame:
    g = per_so(d[d[grupo]])
    if g.empty:
        return pd.DataFrame(columns=["mes", "estructura", "so", "mediana"])
    return g.groupby(["mes", "estructura"], as_index=False).agg(so=("so", "nunique"), mediana=("tiempo", "median"))


def quarters(year: int) -> list[pd.Timestamp]:
    return [pd.Timestamp(year, m, 1) for m in (1, 4, 7, 10)]


def q_label(q: pd.Timestamp) -> str:
    return f"Q{(q.month - 1) // 3 + 1}"


def summary(d: pd.DataFrame, today: pd.Timestamp, grupos: dict | None = None,
            estructuras: list | None = None) -> pd.DataFrame:
    """Por grupo × estructura: mediana por trimestre del año, base, actual y objetivo.

    Base: Q1 del año (si no tiene al menos MIN_SAMPLE SO, el primer trimestre que sí, y se avisa).
    Actual: el último trimestre cerrado posterior a la base.
    Objetivo: base − 15 %. Variación = actual vs base.
    """
    year = today.year
    qs = quarters(year)
    this_q = today.to_period("Q").to_timestamp()
    rows = []
    for grupo, label in (grupos or GRUPOS).items():
        so = per_so(d[d[grupo].fillna(False).astype(bool)])
        so = so[so["mes"].dt.year == year].assign(q=lambda x: x["mes"].dt.to_period("Q").dt.to_timestamp())
        for est in (estructuras or ESTRUCTURAS):
            s = so[so["estructura"] == est]
            row = {"grupo": label, "estructura": est, "so_anio": int(s["so"].nunique()), "nota": ""}
            stats = {}
            for q in qs:
                t = s[s["q"] == q]["tiempo"]
                stats[q] = (float(t.median()) if len(t) else np.nan, int(len(t)))
                row[q_label(q)], row[q_label(q) + "_n"] = stats[q]
            row["anio"] = float(s["tiempo"].median()) if len(s) else np.nan
            row["anio_n"] = int(s["so"].nunique())
            con_datos = [q for q in qs if stats[q][1] >= settings.MIN_SAMPLE and q < this_q]
            base_q = qs[0] if stats[qs[0]][1] >= settings.MIN_SAMPLE else (con_datos[0] if con_datos else None)
            if base_q is not None and base_q != qs[0]:
                row["nota"] = f"{label}: sin datos suficientes en Q1, la base es {q_label(base_q)}."
            cerrados = [q for q in qs if base_q is not None and base_q < q < this_q and stats[q][1] > 0]
            act_q = cerrados[-1] if cerrados else None
            base_med, base_n = stats[base_q] if base_q is not None else (np.nan, 0)
            act_med, act_n = stats[act_q] if act_q is not None else (np.nan, 0)
            objetivo = base_med * (1 - settings.REDUCCION_OBJETIVO) if base_med == base_med else np.nan
            var = (act_med - base_med) / base_med if base_med and act_med == act_med else np.nan
            enough = base_n >= settings.MIN_SAMPLE and act_n >= settings.MIN_SAMPLE
            row.update({
                "base": base_med, "base_n": base_n, "base_q": q_label(base_q) if base_q is not None else "",
                "base_txt": q_label(base_q) if base_q is not None else "—",
                "actual": act_med, "actual_n": act_n, "actual_q": q_label(act_q) if act_q is not None else "",
                "actual_txt": q_label(act_q) if act_q is not None else "—",
                "objetivo": objetivo, "variacion": var,
                "estado": ("" if not enough or var != var else
                           "Cumple" if var <= -settings.REDUCCION_OBJETIVO else
                           "Reduce, sin llegar" if var < 0 else "No reduce"),
            })
            rows.append(row)
    return pd.DataFrame(rows)


def mes_a_mes(d: pd.DataFrame, year: int) -> pd.DataFrame:
    """Por mes de ETD del año: SO, mínimo, mediana y máximo de consolidación (días por SO).

    Grupos (todas las SO, SKU nuevos, top ranking) × medio (todos, marítimo, aéreo).
    Columnas «{grupo}|{medio}|so», «|min», «|med», «|max» y, para conciliar, «otro|so» (SO que no son FCL ni AIR
    computables). Unidad = SO por envío (SO + embarque). La última fila (mes NaT) es el total del año.
    """
    x = d[d["mes"].dt.year == year].assign(todas=True)
    if "medio" not in x:
        x = x.assign(medio="Otro")
    grupos = {"todas": "Todas las SO", **GRUPOS}
    meses = sorted(x["mes"].unique())
    rows = []
    for mes in meses + [pd.NaT]:
        r = {"mes": mes}
        sub_m = x if pd.isna(mes) else x[x["mes"] == mes]
        for g in grupos:
            sg = sub_m[sub_m[g].fillna(False).astype(bool)]
            so_all = sg.groupby(["so", "embarque", "medio"], as_index=False).agg(tiempo=("tiempo_consolidacion", "median"))
            for m in MEDIOS:
                so = so_all if m == "todos" else so_all[so_all["medio"] == m]
                t = so["tiempo"]
                r[f"{g}|{m}|so"] = int(len(so))
                r[f"{g}|{m}|min"] = float(t.min()) if len(t) else np.nan
                r[f"{g}|{m}|med"] = float(t.median()) if len(t) else np.nan
                r[f"{g}|{m}|max"] = float(t.max()) if len(t) else np.nan
            r[f"{g}|otro|so"] = int((so_all["medio"] == "Otro").sum())
        rows.append(r)
    out = pd.DataFrame(rows)
    out.attrs["grupos"] = grupos
    out.attrs["medios"] = MEDIOS
    return out


GRUPOS_TODO = {"todas": "Todas las SO", **GRUPOS}


def objetivo_universo(du: pd.DataFrame, today: pd.Timestamp) -> pd.DataFrame:
    """Objetivo −15 % sobre el universo completo (base_universo), sin abrir por estructura.

    Una fila por grupo: todas las SO, SKU nuevos y top ranking.
    """
    d = du.assign(estructura="Total", todas=True)
    return summary(d, today, GRUPOS_TODO, ["Total"])


def mensual_universo(du: pd.DataFrame, year: int) -> pd.DataFrame:
    """Mediana mensual de días por SO de cada grupo (universo completo): columnas mes, grupo, so, mediana."""
    d = du[du["mes"].dt.year == year].assign(todas=True)
    rows = []
    for g, label in GRUPOS_TODO.items():
        so = (d[d[g].fillna(False).astype(bool)].groupby(["so", "mes"], as_index=False)
              .agg(tiempo=("tiempo_consolidacion", "median")))
        for mes, x in so.groupby("mes"):
            rows.append({"mes": mes, "grupo": label, "so": int(x["so"].nunique()), "mediana": float(x["tiempo"].median())})
    return pd.DataFrame(rows, columns=["mes", "grupo", "so", "mediana"])
