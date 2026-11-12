"""Equipo y agentes: indicadores de gestión de analistas (responsable de la carga) y forwarders.

Reglas (ver docs en la página):
- Unidad de análisis = embarque único. Las SO se cuentan aparte y se rotulan como SO.
- Histórico = marítimos zarpados (ETD ≤ hoy) del período elegido, de Reservas Históricas. Activo = en curso
  (Reservas con responsable + aéreos sin entregar), sin filtro de período.
- Tiempos por mediana (y P25–P75 para dispersión), siempre con su n. Un dato faltante no cuenta como incumplimiento.
- Se separa lo que controla cada uno:
  · Bidcom / analista: instruir a tiempo. Instrucción tardía = la instrucción salió después de que la carga
    estaba lista (último packeo: en un consolidado se espera a todos los proveedores) y la carga esperó.
  · Agente: «listo → ETD» = días desde que la carga está lista E instruida (la mayor de packeo e instrucción) hasta
    la ETD. Es la parte del tiempo que depende del forwarder (booking, espacio, salida).
  · Consolidación total packeo → ETD contra SLA = resultado del proceso (incluye proveedor, naviera y puerto).
- «Tipo de demora» atribuye el desvío; sin causa cargada no se atribuye a nadie.
"""
from __future__ import annotations

import numpy as np
import pandas as pd

from config import settings
from utils.data_cleaning import fold

# Causas de «Tipo de demora» → quién la origina. Una causa con varias partes («Proveedor + Agente») cuenta para
# cada una. Lo que no se reconoce queda como «Otra».
CAUSAS = {
    "Agente": ("agente", "forwarder"),
    "Proveedor": ("proveedor", "fabrica", "fábrica"),
    "Naviera / puerto / clima": ("maritima", "marítima", "naviera", "congestion", "puerto", "climat", "clima",
                                 "feriado", "dg", "imo", "aduana"),
    "Bidcom": ("falta de pago", "pago", "category", "comex", "bidcom"),
}


def origen_causa(v) -> str:
    """Primera parte reconocida de «Tipo de demora» (orden de CAUSAS). Vacío si no hay causa."""
    s = fold(v)
    if not s:
        return ""
    for nombre, claves in CAUSAS.items():
        if any(fold(k) in s for k in claves):
            return nombre
    return "Otra"


def excluido(nombre) -> bool:
    """Analista que ya no está en el equipo (settings.EQ_ANALISTAS_EXCLUIDOS)."""
    return fold(nombre) in {fold(x) for x in settings.EQ_ANALISTAS_EXCLUIDOS}


def _med(s: pd.Series) -> float:
    s = s.dropna()
    return float(s.median()) if len(s) else np.nan


def _pct(mask: pd.Series) -> float:
    m = mask.dropna()
    return float(m.astype(bool).mean()) if len(m) else np.nan


def zarpados_en_reservas(res: pd.DataFrame | None, hist: pd.DataFrame | None, today: pd.Timestamp) -> pd.DataFrame:
    """Embarques que ya zarparon (ETD ≤ hoy) pero siguen en Reservas porque todavía no llegaron. Se miden con el SLA
    de consolidación de su puerto (en curso se usa el tope fijo; una vez zarpado corresponde el del puerto)."""
    from utils.data_cleaning import id_key
    if res is None or res.empty:
        return pd.DataFrame()
    r = res[res["etd"].notna() & (res["etd"] <= today)]
    r = r[~r["embarque"].map(lambda v: fold(v).startswith("air"))]
    if hist is not None and len(hist):
        r = r[~id_key(r["embarque"]).isin(set(id_key(hist["embarque"])))]
    if r.empty:
        return r
    r = r.copy()
    if "sla_cons_puerto" in r:
        r["sla_consolidacion"] = r["sla_cons_puerto"]
        r["cumple_consolidacion"] = (r["dias_consolidacion"] <= r["sla_consolidacion"]).where(
            r["dias_consolidacion"].notna())
    return r


def aereos_por_analista(aer: pd.DataFrame | None, hist: pd.DataFrame | None, res: pd.DataFrame | None,
                        today: pd.Timestamp) -> pd.DataFrame:
    """Aéreos entregados (Seguimiento Aéreos) con el analista de «Responsable de la carga» de Reservas Históricas o
    Reservas (Seguimiento Aéreos no tiene responsable). Columnas: embarque, responsable, etd, dias_aereo, sla_vig."""
    from utils.data_cleaning import id_key
    cols = ["embarque", "responsable", "etd", "dias_aereo", "sla_vig"]
    if aer is None or aer.empty:
        return pd.DataFrame(columns=cols)
    a = aer[aer["etd"].notna() & (aer["etd"] <= today)]
    if "estadio" in a:
        a = a[a["estadio"].map(lambda v: fold(v).upper() == "ENTREGADO" if isinstance(v, str) else False)]
    a = a.assign(responsable=id_key(a["embarque"]).map(responsables(hist, res)))
    vig = a["sla_vigente"].fillna(False).astype(bool) if "sla_vigente" in a else pd.Series(True, index=a.index)
    a = a.assign(sla_vig=a["sla_aereo"].where(vig) if "sla_aereo" in a else np.nan)
    return a[[c for c in cols if c in a]]


def responsables(hist: pd.DataFrame | None, res: pd.DataFrame | None) -> dict:
    """id de embarque → «Responsable de la carga» (Reservas manda sobre Históricas)."""
    from utils.data_cleaning import id_key
    out = {}
    for d in (hist, res):
        if d is not None and len(d) and "responsable" in d:
            x = d.dropna(subset=["responsable"])
            out.update(dict(zip(id_key(x["embarque"]), x["responsable"])))
    return out


def zarpados(h: pd.DataFrame | None, today: pd.Timestamp) -> pd.DataFrame:
    """Marítimos zarpados (una fila por embarque) con columnas auxiliares para los indicadores."""
    from config.mappings import MODOS_MARITIMOS
    if h is None or h.empty:
        return pd.DataFrame()
    d = h[h["modo"].isin(MODOS_MARITIMOS) & (h["etd"] <= today)].drop_duplicates("embarque")
    causa = d["tipo_demora"].map(origen_causa) if "tipo_demora" in d else pd.Series("", index=d.index)
    fuera = d["cumple_consolidacion"].eq(False)
    # Carga lista = último packeo (en un consolidado se espera a todos los proveedores; si falta, el primero).
    lista = d["f_packeo_max"].fillna(d["f_packeo_min"]) if "f_packeo_max" in d else d["f_packeo_min"]
    listo = pd.concat([lista, d["f_instruccion"]], axis=1).max(axis=1, skipna=False)
    atraso = (d["f_instruccion"] - lista).dt.days
    return d.assign(
        dias_listo_etd=(d["etd"] - listo).dt.days, dias_atraso_instr=atraso,
        _tarde=(atraso > 0).where(atraso.notna()),
        _causa=causa, _fuera=fuera,
        _desvio_alto=(d["desvio_etd"] > settings.EQ_DESVIO_DIAS).where(d["desvio_etd"].notna()),
        _conso=d["estructura"].eq("Consolidado").where(d["estructura"].notna()) if "estructura" in d else np.nan,
        _advance=d["booking"].eq("In advance").where(d["booking"].notna()) if "booking" in d else np.nan,
        mes=d["etd"].dt.to_period("M").dt.to_timestamp())


def _comun(g: pd.DataFrame) -> dict:
    n_c = int(g["cumple_consolidacion"].notna().sum())
    fuera = g[g["_fuera"]]
    return {
        "embarques": int(len(g)), "contenedores": float(g["contenedores"].sum()),
        "pct_conso": _pct(g["_conso"]),
        "cumple": _pct(g["cumple_consolidacion"]) if n_c else np.nan, "n_cumple": n_c,
        "fuera": int(len(fuera)), "fuera_sin_causa": int((fuera["_causa"] == "").sum()),
        "med_consol": _med(g["dias_consolidacion"]),
    }


def por_analista(z: pd.DataFrame, act: pd.DataFrame | None, casos: pd.DataFrame | None,
                 so_por_emb: pd.Series | None = None, aer: pd.DataFrame | None = None) -> pd.DataFrame:
    """Una fila por analista. Productividad (activos, zarpados, SO, contenedores), eficiencia controlable
    (packeo → instrucción), resultado (cumplimiento SLA) y calidad de seguimiento (casos abiertos)."""
    nombres = set()
    if len(z):
        nombres |= set(z["responsable"].dropna())
    if act is not None and len(act):
        nombres |= set(act["responsable"].dropna())
    if aer is not None and len(aer):
        nombres |= set(aer["responsable"].dropna())
    rows = []
    for a in sorted(x for x in nombres if not excluido(x)):
        g = z[z["responsable"] == a] if len(z) else z
        r = {"analista": a, **(_comun(g) if len(g) else {"embarques": 0})}
        r["pct_tarde"] = _pct(g["_tarde"]) if len(g) else np.nan
        r["n_tarde_base"] = int(g["_tarde"].notna().sum()) if len(g) else 0
        r["med_atraso"] = _med(g.loc[g["_tarde"].eq(True), "dias_atraso_instr"]) if len(g) else np.nan
        r["so"] = int(so_por_emb.reindex(g["embarque"]).fillna(0).sum()) if so_por_emb is not None and len(g) else np.nan
        r["fuera_ext"] = int(g["_fuera"][g["_causa"].isin(["Proveedor", "Naviera / puerto / clima", "Agente"])].sum()) \
            if len(g) else 0
        aa = act[act["responsable"] == a] if act is not None and len(act) else pd.DataFrame()
        r["activos"] = int(aa["embarque"].nunique()) if len(aa) else 0
        cc = casos[casos["responsable"] == a] if casos is not None and len(casos) else pd.DataFrame()
        r["casos_alta"] = int(cc.loc[cc["prioridad"] == "Alta", "embarque"].nunique()) if len(cc) else 0
        r["casos"] = int(cc["embarque"].nunique()) if len(cc) else 0
        quien = cc["quien"] if len(cc) and "quien" in cc else pd.Series(dtype=object)
        r["casos_analista"] = int(cc.loc[quien == "Analista", "embarque"].nunique()) if len(cc) else 0
        ga = aer[aer["responsable"] == a] if aer is not None and len(aer) else pd.DataFrame()
        r["aereos"] = int(ga["embarque"].nunique()) if len(ga) else 0
        con_tot = ga[ga["dias_aereo"].notna()] if len(ga) else ga
        r["med_aereo"] = _med(con_tot["dias_aereo"]) if len(con_tot) else np.nan
        c_sla = con_tot[con_tot["sla_vig"].notna()] if len(con_tot) else con_tot
        r["n_sla_aereo"] = int(len(c_sla))
        r["cumple_aereo"] = float((c_sla["dias_aereo"] <= c_sla["sla_vig"]).mean()) if len(c_sla) else np.nan
        rows.append(r)
    t = pd.DataFrame(rows)
    if t.empty:
        return t
    tot_act = t["activos"].sum()
    t["pct_activos"] = t["activos"] / tot_act if tot_act else np.nan
    return t.sort_values(["activos", "embarques"], ascending=False).reset_index(drop=True)


def por_agente(z: pd.DataFrame, act: pd.DataFrame | None, z_prev: pd.DataFrame | None = None) -> pd.DataFrame:
    """Una fila por forwarder: volumen, tiempos (instrucción → ETD con P25–P75), cumplimiento de SLA, confiabilidad
    (desvío de ETD, booking in advance, ETD confirmado en los activos) y demoras atribuidas al agente."""
    if z is None or z.empty:
        return pd.DataFrame()
    rows = []
    total = len(z)
    for f, g in z.groupby("forwarder"):
        q = g["dias_listo_etd"].dropna()
        r = {"agente": f, **_comun(g), "share": len(g) / total,
             "med_listo_etd": _med(q), "n_listo_etd": int(len(q)), "med_instr_etd": _med(g["dias_agente"]),
             "p25": float(q.quantile(.25)) if len(q) else np.nan, "p75": float(q.quantile(.75)) if len(q) else np.nan,
             "med_desvio": _med(g["desvio_etd"]), "n_desvio": int(g["desvio_etd"].notna().sum()),
             "pct_desvio_alto": _pct(g["_desvio_alto"]), "pct_advance": _pct(g["_advance"]),
             "demoras_agente": int((g["_causa"] == "Agente").sum())}
        r["dispersion"] = r["p75"] - r["p25"] if r["n_listo_etd"] else np.nan
        pag = g.loc[g["flete_pagado"] > 0, "flete_pagado"].sum() if "flete_pagado" in g else 0
        cert = g.loc[g["flete_pagado"] > 0, "flete_certificado"].sum() if "flete_certificado" in g else 0
        r["certificacion"] = cert / pag if pag else np.nan
        if z_prev is not None and len(z_prev):
            gp = z_prev[z_prev["forwarder"] == f]
            n_p = int(gp["cumple_consolidacion"].notna().sum())
            r["cumple_prev"] = _pct(gp["cumple_consolidacion"]) if n_p >= settings.MIN_SAMPLE else np.nan
        aa = act[act["forwarder"] == f] if act is not None and len(act) else pd.DataFrame()
        r["activos"] = int(aa["embarque"].nunique()) if len(aa) else 0
        r["pct_etd_ok"] = _pct(aa["etd_ok"].fillna(False)) if len(aa) and "etd_ok" in aa else np.nan
        rows.append(r)
    t = pd.DataFrame(rows)
    if "cumple_prev" not in t:
        t["cumple_prev"] = np.nan
    t["delta_cumple"] = t["cumple"] - t["cumple_prev"]
    t["revisar"] = [_motivo_revision(r, z) for _, r in t.iterrows()]
    return t.sort_values("embarques", ascending=False).reset_index(drop=True)


def _motivo_revision(r, z: pd.DataFrame) -> str:
    """Por qué un agente requiere seguimiento (solo con muestra suficiente). Vacío = sin observaciones."""
    if r["embarques"] < settings.MIN_SAMPLE:
        return "Muestra chica"
    motivos = []
    obj = settings.CUMPLIMIENTO_OBJETIVO
    if r["n_cumple"] >= settings.MIN_SAMPLE and r["cumple"] == r["cumple"] and r["cumple"] < obj - settings.EQ_MARGEN_PP:
        motivos.append(f"cumplimiento {r['cumple']:.0%} (objetivo {obj:.0%})")
    if r["delta_cumple"] == r["delta_cumple"] and r["delta_cumple"] <= -settings.EQ_DETERIORO_PP:
        motivos.append(f"cumplimiento bajó {abs(r['delta_cumple']) * 100:.0f} pp vs período anterior")
    equipo = _med(z["dias_listo_etd"])
    if r["n_listo_etd"] >= settings.MIN_SAMPLE and equipo == equipo and \
            r["med_listo_etd"] > equipo * (1 + settings.EQ_LENTO_PCT):
        motivos.append(f"listo → ETD {r['med_listo_etd']:.0f} d vs {equipo:.0f} d del total")
    if r["n_desvio"] >= settings.MIN_SAMPLE and r["pct_desvio_alto"] == r["pct_desvio_alto"] and \
            r["pct_desvio_alto"] > settings.EQ_SALUD["desvio"][1]:
        motivos.append(f"{r['pct_desvio_alto']:.0%} sale > {settings.EQ_DESVIO_DIAS} d después de lo estimado")
    if r["demoras_agente"] >= 3:
        motivos.append(f"{r['demoras_agente']} demoras con el agente involucrado")
    return " · ".join(motivos)


def quien_resuelve(tipo: str, accion: str = "") -> str:
    """Quién tiene que intervenir en un caso de la Bandeja de acción."""
    from utils import bandeja
    a = fold(accion)
    if tipo in (bandeja.TIPOS["forwarder"], bandeja.TIPOS["ajuste"]):
        return "Agente"
    if tipo == bandeja.TIPOS["sla"]:
        return "Proveedor / category" if "proveedor" in a or "packeo" in a else "Agente"
    return "Analista"


def semaforo(valor: float, umbrales: tuple[float, float], mayor_es_mejor: bool = False) -> str:
    """ok / warn / bad. umbrales = (límite verde, límite amarillo)."""
    if valor != valor:
        return ""
    v, a = umbrales
    if mayor_es_mejor:
        return "ok" if valor >= v else "warn" if valor >= a else "bad"
    return "ok" if valor <= v else "warn" if valor <= a else "bad"


def salud(z: pd.DataFrame, act: pd.DataFrame | None, casos: pd.DataFrame | None, today: pd.Timestamp) -> dict:
    """Salud operativa = el peor de cuatro componentes medibles, cada uno con su semáforo (umbrales en settings)."""
    s = settings.EQ_SALUD
    comp = []
    cum = _pct(z["cumple_consolidacion"]) if len(z) else np.nan
    n_cum = int(z["cumple_consolidacion"].notna().sum()) if len(z) else 0
    obj = settings.CUMPLIMIENTO_OBJETIVO
    comp.append(("Cumplimiento SLA consolidación", cum, semaforo(cum, (obj, obj - settings.EQ_MARGEN_PP), True),
                 f"{n_cum} embarques zarpados con dato"))
    n_act = int(act["embarque"].nunique()) if act is not None and len(act) else 0
    alta = int(casos.loc[casos["prioridad"] == "Alta", "embarque"].nunique()) if casos is not None and len(casos) else 0
    alta_act = 0
    if n_act and casos is not None and len(casos):
        alta_act = int(casos[(casos["prioridad"] == "Alta") & casos["embarque"].isin(set(act["embarque"]))]["embarque"]
                       .nunique())
    p_alta = alta_act / n_act if n_act else np.nan
    comp.append(("Activos con caso de prioridad alta", p_alta, semaforo(p_alta, s["alta"]),
                 f"{alta_act} de {n_act} embarques en curso"))
    prox = pd.DataFrame()
    if act is not None and len(act):
        prox = act[act["etd"].between(today, today + pd.Timedelta(days=settings.ALERT_HORIZON_DAYS))]
    sin_ok = int((~prox["etd_ok"].fillna(False).astype(bool)).sum()) if len(prox) and "etd_ok" in prox else 0
    p_sin = sin_ok / len(prox) if len(prox) else np.nan
    comp.append((f"ETD próximos {settings.ALERT_HORIZON_DAYS} días sin confirmar", p_sin, semaforo(p_sin, s["sin_ok"]),
                 f"{sin_ok} de {len(prox)} embarques"))
    p_des = _pct(z["_desvio_alto"]) if len(z) else np.nan
    n_des = int(z["_desvio_alto"].notna().sum()) if len(z) else 0
    comp.append((f"Salen > {settings.EQ_DESVIO_DIAS} d después de la ETD estimada", p_des, semaforo(p_des, s["desvio"]),
                 f"{n_des} embarques con ETD estimada cargada"))
    estados = [c[2] for c in comp if c[2]]
    general = "bad" if "bad" in estados else "warn" if "warn" in estados else "ok" if estados else ""
    return {"general": general, "componentes": comp, "casos_alta": alta}


def mensual(z: pd.DataFrame, por: str | None = None) -> pd.DataFrame:
    """Por mes de ETD (y opcionalmente por analista / agente): embarques, % SLA, medianas de tramos y desvío."""
    if z is None or z.empty:
        return pd.DataFrame()
    claves = ["mes"] + ([por] if por else [])
    g = z.groupby(claves, dropna=True)
    return pd.DataFrame({
        "embarques": g.size(),
        "cumple": g["cumple_consolidacion"].apply(lambda s: _pct(s)),
        "n_cumple": g["cumple_consolidacion"].apply(lambda s: int(s.notna().sum())),
        "med_consol": g["dias_consolidacion"].median(),
        "pct_tarde": g["_tarde"].apply(lambda s: _pct(s)),
        "med_listo_etd": g["dias_listo_etd"].median(),
        "pct_desvio_alto": g["_desvio_alto"].apply(lambda s: _pct(s)),
    }).reset_index()


def mensual_analista(z: pd.DataFrame | None, aer: pd.DataFrame | None) -> pd.DataFrame:
    """Mes a mes de un analista: marítimos zarpados (mensual) + aéreos entregados (cantidad, % SLA, punta a punta)."""
    mar = mensual(z) if z is not None and len(z) else pd.DataFrame(columns=["mes"])
    if aer is not None and len(aer):
        a = aer.assign(mes=aer["etd"].dt.to_period("M").dt.to_timestamp())
        c = a[a["dias_aereo"].notna() & a["sla_vig"].notna()]
        g = a.groupby("mes")
        ae = pd.DataFrame({"aereos": g["embarque"].nunique(), "med_aereo": g["dias_aereo"].median()})
        ae["cumple_aereo"] = (c["dias_aereo"] <= c["sla_vig"]).groupby(c["mes"]).mean()
        ae = ae.reset_index()
    else:
        ae = pd.DataFrame(columns=["mes", "aereos", "med_aereo", "cumple_aereo"])
    if mar.empty and ae.empty:
        return pd.DataFrame()
    m = mar.merge(ae, on="mes", how="outer") if len(mar) else ae
    for c in ("embarques", "aereos"):
        if c in m:
            m[c] = m[c].fillna(0)
    return m.sort_values("mes").reset_index(drop=True)


def semanal(z: pd.DataFrame, today: pd.Timestamp, semanas: int = 13) -> pd.DataFrame:
    """% dentro de SLA por semana de ETD (lunes), últimas `semanas` semanas."""
    if z is None or z.empty:
        return pd.DataFrame(columns=["semana", "embarques", "cumple", "n_cumple"])
    inicio = (today - pd.Timedelta(days=today.weekday())) - pd.Timedelta(weeks=semanas - 1)
    d = z[z["etd"] >= inicio]
    sem = d["etd"] - pd.to_timedelta(d["etd"].dt.weekday, unit="D")
    g = d.groupby(sem.dt.normalize())
    return pd.DataFrame({"embarques": g.size(), "cumple": g["cumple_consolidacion"].apply(_pct),
                         "n_cumple": g["cumple_consolidacion"].apply(lambda s: int(s.notna().sum()))}) \
        .rename_axis("semana").reset_index()


def conclusiones(z: pd.DataFrame, analistas: pd.DataFrame, agentes: pd.DataFrame, casos: pd.DataFrame | None,
                 today: pd.Timestamp) -> list[tuple[str, str]]:
    """Frases (tono, texto) armadas solo con datos: cada una exige muestra mínima y un cambio relevante.
    tono: good | bad | neutral."""
    out: list[tuple[str, str]] = []
    n_min = settings.MIN_SAMPLE
    if len(z):
        m = mensual(z)
        ult = today.to_period("M").to_timestamp() - pd.offsets.MonthBegin(1)
        a, b = m[m["mes"] == ult], m[m["mes"] == ult - pd.offsets.MonthBegin(1)]
        if len(a) and len(b) and a["n_cumple"].iloc[0] >= n_min and b["n_cumple"].iloc[0] >= n_min:
            va, vb = a["cumple"].iloc[0], b["cumple"].iloc[0]
            if abs(va - vb) >= 0.05:
                out.append(("good" if va > vb else "bad",
                            f"El cumplimiento de SLA de consolidación {'mejoró' if va > vb else 'empeoró'} de {vb:.0%} a "
                            f"{va:.0%} ({ult:%m/%Y} vs mes anterior; {int(a['n_cumple'].iloc[0])} embarques)."))
        le, tarde = _med(z["dias_listo_etd"]), _pct(z["_tarde"])
        if le == le:
            atraso = _med(z.loc[z["_tarde"].eq(True), "dias_atraso_instr"])
            out.append(("neutral", f"Con la carga lista e instruida, los agentes tardan {le:.0f} d (mediana) en zarpar."
                        + (f" El {tarde:.0%} de las instrucciones salió después del packeo (mediana {atraso:.0f} d de "
                           "atraso)." if tarde == tarde and atraso == atraso else "")))
        fuera = z[z["_fuera"]]
        if len(fuera) >= n_min:
            sin = int((fuera["_causa"] == "").sum())
            if sin / len(fuera) >= 0.3:
                out.append(("bad", f"{sin} de {len(fuera)} embarques fuera de SLA no tienen «Tipo de demora»: no se "
                                   "puede saber si la demora fue del proveedor, del agente o nuestra."))
            else:
                causas = fuera["_causa"].replace("", np.nan).dropna().value_counts()
                if len(causas):
                    out.append(("neutral", f"Principal causa de los fuera de SLA: {causas.index[0]} "
                                           f"({causas.iloc[0]} de {len(fuera)})."))
    if analistas is not None and len(analistas):
        tot = analistas["activos"].sum()
        top = analistas.sort_values("activos", ascending=False).iloc[0]
        if tot >= n_min and top["activos"] / tot > settings.EQ_CONCENTRACION:
            out.append(("bad", f"{top['analista']} tiene {top['activos']} de los {tot} embarques en curso con responsable "
                               f"({top['activos'] / tot:.0%}): carga concentrada."))
        alta = analistas["casos_alta"].sum()
        if alta >= 3:
            ta = analistas.sort_values("casos_alta", ascending=False).iloc[0]
            if ta["casos_alta"] / alta >= 0.5:
                out.append(("bad", f"{ta['analista']} concentra {ta['casos_alta']} de {alta} embarques con casos de "
                                   "prioridad alta."))
    if agentes is not None and len(agentes):
        ok = agentes[agentes["embarques"] >= n_min]
        peor = ok[ok["delta_cumple"] <= -settings.EQ_DETERIORO_PP].sort_values("delta_cumple")
        for _, r in peor.head(2).iterrows():
            out.append(("bad", f"{r['agente']}: el cumplimiento bajó de {r['cumple_prev']:.0%} a {r['cumple']:.0%} "
                               "contra el período anterior."))
        mejor = ok[ok["delta_cumple"] >= settings.EQ_DETERIORO_PP].sort_values("delta_cumple", ascending=False)
        for _, r in mejor.head(1).iterrows():
            out.append(("good", f"{r['agente']}: el cumplimiento subió de {r['cumple_prev']:.0%} a {r['cumple']:.0%} "
                                "contra el período anterior."))
    return out
