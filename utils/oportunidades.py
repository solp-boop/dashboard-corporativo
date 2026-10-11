"""Motor de oportunidades de costos: comparabilidad de cotizaciones, oportunidades de negociación, alertas,
adherencia (pagado vs cotizado) y ahorro por selección. Un único lugar para el criterio comercial; la franja de
acciones, la solapa Tarifas y la Captura leen de acá. Sin Streamlit, para poder testearlo.

Comparable = mismo POL, destino y tipo de contenedor, vigente en el mismo período, mismo pagadero (si ambos lo
informan), mismo tipo de servicio (directo / trasbordo; «a confirmar» compara con advertencia) y tránsito dentro de
± OPORT_TT_TOL días. Las tarifas son por contenedor, en USD, solo flete (los locales ARG se informan aparte).
"""
from __future__ import annotations

import numpy as np
import pandas as pd

from config import settings
from utils.data_cleaning import fold
from utils.negociar import periodo

_PUERTOS_TS = ("hong kong", "busan", "singapur", "singapore", "kaohsiung", "colombo", "port klang", "shanghai",
               "ningbo", "tanjung", "manzanillo", "callao", "cartagena", "santos", "algeciras")


def servicio(row) -> str:
    """Directo / Trasbordo / A confirmar / Sin dato, a partir de «Tipo de Servicio» y «Transbordo»."""
    txt = " ".join(fold(row.get(k)) for k in ("servicio", "transbordo") if isinstance(row.get(k), str))
    if not txt.strip() or txt.strip() in {"-", "- -"}:
        return "Sin dato"
    if "confirm" in txt:
        return "A confirmar"
    if "trasbordo" in txt or "transbordo" in txt or "t/s" in txt or any(p in txt for p in _PUERTOS_TS):
        return "Trasbordo"
    if "direct" in txt or "regular" in txt:
        return "Directo"
    return "Sin dato"


def preparar(c: pd.DataFrame) -> pd.DataFrame:
    """Cotizaciones con ruta plegada, servicio normalizado y pagadero."""
    if c is None or c.empty:
        return pd.DataFrame(columns=["_p", "tipo_ctnr", "forwarder", "flete", "servicio_n", "tt", "pagadero_n"])
    x = c.copy()
    x["_p"] = x["puerto"].map(fold)
    x["servicio_n"] = x.apply(servicio, axis=1)
    x["pagadero_n"] = x["pagadero"].map(lambda v: fold(v).upper() if isinstance(v, str) and v.strip() else None) \
        if "pagadero" in x else None
    x["tt"] = pd.to_numeric(x["tt"], errors="coerce") if "tt" in x else np.nan
    return x


def comparable(a, b) -> tuple[bool, str]:
    """¿La cotización b se puede comparar con a? Devuelve (sí/no, motivo cuando no o advertencia)."""
    pa, pb = a["pagadero_n"], b["pagadero_n"]
    if isinstance(pa, str) and isinstance(pb, str) and pa != pb:
        return False, f"pagadero distinto ({pb.lower()})"
    sa, sb = a["servicio_n"], b["servicio_n"]
    if {sa, sb} == {"Directo", "Trasbordo"}:
        return False, f"servicio distinto ({sb.lower()})"
    if a["tt"] == a["tt"] and b["tt"] == b["tt"] and abs(a["tt"] - b["tt"]) > settings.OPORT_TT_TOL:
        return False, f"tránsito {b['tt']:.0f} d vs {a['tt']:.0f} d"
    if "A confirmar" in (sa, sb) or "Sin dato" in (sa, sb):
        return True, "servicio a confirmar"
    return True, ""


def _uso(hist: pd.DataFrame, today: pd.Timestamp, dias: int, destino: str = "Argentina") -> pd.DataFrame:
    h = hist[(hist["etd"] <= today) & (hist["etd"] > today - pd.Timedelta(days=dias)) & hist["tipo_ctnr"].notna()
             & hist["puerto"].notna()]
    if "destino" in h:
        h = h[h["destino"] == destino]
    return h.assign(_p=h["puerto"].map(fold), _c=h["contenedores"].fillna(1))


def _u(v) -> str:
    return f"USD {v:,.0f}".replace(",", ".")


# ---------------------------------------------------------------------------
def oportunidades(hist: pd.DataFrame, cot: pd.DataFrame | None, today: pd.Timestamp, dias: int | None = None,
                  reservas: pd.DataFrame | None = None, destino: str = "Argentina") -> pd.DataFrame:
    """Una fila por ruta × contenedor usada en la ventana, con la tarifa actual del agente principal, la mejor
    comparable, la diferencia, el ahorro por mes, con quién negociar, la tarifa objetivo, la acción y la prioridad."""
    dias = dias or settings.NEGOCIAR_VENTANA_DIAS
    cols = ["ruta", "puerto", "tipo_ctnr", "contenedores", "embarques", "agente", "tarifa_actual", "servicio_actual",
            "tt_actual", "vence", "mejor", "mejor_agente", "mejor_servicio", "mejor_tt", "dif_usd", "dif_pct",
            "ahorro_mes", "negociar_con", "objetivo", "accion", "tipo", "prioridad", "score", "agentes",
            "menor_no_comparable", "motivo_no_comparable", "confianza"]
    h = _uso(hist, today, dias, destino)
    cur = preparar(periodo(cot, today, "curso", destino))
    if h.empty:
        return pd.DataFrame(columns=cols)
    meses = dias / 30.0
    prox = preparar(periodo(cot, today, "proxima", destino))
    urg_rutas = set()
    if reservas is not None and len(reservas):
        from utils.resumen_kpis import tipo_ctnr as tipo_rk
        r = reservas[(reservas["etd"] >= today) & (reservas["etd"] <= today + pd.Timedelta(days=30))]
        mapa = {"20 ST": "20ST", "40 ST": "40ST/40HQ", "40 HQ": "40ST/40HQ", "40 NOR": "40NOR"}
        urg_rutas = {(fold(p), mapa.get(tipo_rk(t))) for p, t in zip(r["puerto"], r["tipo_carga"]) if isinstance(p, str)}
    rows = []
    for (p, tipo), g in h.groupby(["_p", "tipo_ctnr"]):
        cont = float(g["_c"].sum())
        principal = g.groupby("forwarder")["_c"].sum().idxmax() if g["forwarder"].notna().any() else None
        q = cur[(cur["_p"] == p) & (cur["tipo_ctnr"] == tipo)] if len(cur) else cur
        agentes = int(q["forwarder"].nunique()) if len(q) else 0
        base = {"ruta": f"{g['puerto'].iloc[0]} · {tipo}", "puerto": g["puerto"].iloc[0], "tipo_ctnr": tipo,
                "contenedores": cont, "embarques": int(g["embarque"].nunique()), "agente": principal,
                "agentes": agentes}
        mine = q[q["forwarder"].map(fold) == fold(principal)].sort_values("flete") if principal and len(q) else q.iloc[0:0]
        otros = q[q["forwarder"].map(fold) != fold(principal)] if principal and len(q) else q
        if len(q) == 0:
            rows.append({**base, "accion": f"Sin cotizaciones vigentes para {base['ruta']}: pedir a {principal} y a "
                                          "2 agentes más", "tipo": "Investigar", "negociar_con": principal,
                         "score": cont * 10, "confianza": "Baja"})
            continue
        if mine.empty:
            best = q.sort_values("flete").iloc[0]
            rows.append({**base, "mejor": best["flete"], "mejor_agente": best["forwarder"],
                         "mejor_servicio": best["servicio_n"], "mejor_tt": best["tt"], "negociar_con": principal,
                         "objetivo": best["flete"], "tipo": "Investigar", "score": cont * 20, "confianza": "Media",
                         "accion": f"Pedir cotización a {principal} para {base['ruta']} (no tiene tarifa vigente); la "
                                   f"menor hoy es {_u(best['flete'])} de {best['forwarder']}"})
            continue
        a = mine.iloc[0]
        vence = a.get("validez_hasta")
        comp, no_comp = [], []
        for _, b in otros.iterrows():
            ok, motivo = comparable(a, b)
            (comp if ok else no_comp).append((b, motivo))
        mejor = min(comp, key=lambda x: x[0]["flete"]) if comp else None
        menor_nc = min(no_comp, key=lambda x: x[0]["flete"]) if no_comp else None
        fila = {**base, "tarifa_actual": a["flete"], "servicio_actual": a["servicio_n"], "tt_actual": a["tt"],
                "vence": vence}
        if menor_nc is not None and (mejor is None or menor_nc[0]["flete"] < mejor[0]["flete"]) \
                and menor_nc[0]["flete"] < a["flete"]:
            fila["menor_no_comparable"] = menor_nc[0]["flete"]
            fila["motivo_no_comparable"] = f"{menor_nc[0]['forwarder']}: {menor_nc[1]}"
        if mejor is None or mejor[0]["flete"] >= a["flete"]:
            fila.update({"mejor": a["flete"], "mejor_agente": principal, "dif_usd": 0.0, "dif_pct": 0.0,
                         "ahorro_mes": 0.0, "tipo": "OK", "score": 0.0,
                         "accion": f"{principal} tiene la mejor tarifa comparable"
                                   + (" (única cotización: pedir más)" if agentes == 1 else "")})
            rows.append(fila)
            continue
        b, aviso = mejor
        dif = float(a["flete"] - b["flete"])
        pct = dif / a["flete"]
        ahorro = dif * cont / meses
        conf = "Alta" if cont >= settings.OPORT_MIN_N and agentes >= 3 and not aviso else \
            ("Media" if cont >= settings.OPORT_MIN_CONT else "Baja")
        urg = 1.5 if (p, tipo) in urg_rutas or (pd.notna(vence) and vence <= today + pd.Timedelta(
            days=settings.OPORT_VENCE_DIAS)) else 1.0
        score = ahorro * {"Alta": 1.0, "Media": 0.7, "Baja": 0.4}[conf] * urg
        negociar = dif >= settings.OPORT_UMBRAL_USD and pct >= settings.OPORT_UMBRAL_PCT and \
            cont >= settings.OPORT_MIN_CONT
        tt_txt = f", TT {b['tt']:.0f} d" if b["tt"] == b["tt"] else ""
        fila.update({"mejor": b["flete"], "mejor_agente": b["forwarder"], "mejor_servicio": b["servicio_n"],
                     "mejor_tt": b["tt"], "dif_usd": dif, "dif_pct": pct, "ahorro_mes": ahorro, "score": score,
                     "negociar_con": principal, "objetivo": b["flete"], "confianza": conf,
                     "tipo": "Inmediata" if negociar else "Seguimiento",
                     "accion": (f"Renegociar {fila['ruta']} con {principal}: {b['forwarder']} ofrece {_u(b['flete'])} "
                                f"({b['servicio_n'].lower()}{tt_txt}), {_u(dif)} menos por contenedor; movimos "
                                f"{cont:.0f} contenedores en {dias} días → ahorro estimado {_u(ahorro)} por mes"
                                + (f" · {aviso}" if aviso else "")) if negociar else
                               f"Diferencia chica con {b['forwarder']} ({_u(dif)}): seguir"})
        rows.append(fila)
    t = pd.DataFrame(rows)
    for c in cols:
        if c not in t:
            t[c] = np.nan
    t["prioridad"] = np.select([t["score"] >= 2000, t["score"] >= 500], ["Alta", "Media"], "Baja")
    # «Investigar» no tiene ahorro estimable (falta la cotización): la prioridad la da el volumen en juego.
    inv = t["tipo"] == "Investigar"
    t.loc[inv, "prioridad"] = np.select([t.loc[inv, "contenedores"] >= 4 * settings.OPORT_MIN_N,
                                         t.loc[inv, "contenedores"] >= settings.OPORT_MIN_N], ["Alta", "Media"], "Baja")
    t.loc[t["tipo"] == "OK", "prioridad"] = ""
    orden = {"Inmediata": 0, "Investigar": 1, "Seguimiento": 2, "OK": 3}
    return t.assign(_o=t["tipo"].map(orden)).sort_values(["_o", "score"], ascending=[True, False]) \
        .drop(columns="_o")[cols].reset_index(drop=True)


# ---------------------------------------------------------------------------
def adherencia(hist: pd.DataFrame, cot: pd.DataFrame | None, desde: pd.Timestamp | None = None) -> pd.DataFrame:
    """Cada embarque marítimo con su propia cotización vigente a la fecha de ETD: lo pagado contra lo
    cotizado por ese mismo agente para esa ruta y contenedor (la más alta de sus tarifas, para no acusar de más)."""
    cols = ["embarque", "etd", "forwarder", "puerto", "tipo_ctnr", "contenedores", "pagado", "cotizado", "dif",
            "dif_pct", "exceso", "pago_mas", "responsable"]
    if hist is None or hist.empty or cot is None or cot.empty:
        return pd.DataFrame(columns=cols)
    x = hist[(hist["flete_por_ctnr"] > 0) & hist["tipo_ctnr"].notna()]
    if desde is not None:
        x = x[x["etd"] >= desde]
    # La tarifa que aplica es la vigente al zarpe (ETD): cruzando por fecha de instrucción, en los meses de suba
    # parecía que «pagamos más» cuando en realidad cambió la quincena.
    x = x.assign(_f=x["forwarder"].map(fold), _p=x["puerto"].map(fold), _d=x["etd"]).reset_index()
    c = cot.assign(_f=cot["forwarder"].map(fold), _p=cot["puerto"].map(fold))
    keys = ["_f", "_p", "tipo_ctnr"] + (["destino"] if "destino" in c and "destino" in x else [])
    m = x.merge(c[keys + ["validez_desde", "validez_hasta", "flete"]], on=keys, how="inner")
    m = m[(m["_d"] >= m["validez_desde"]) & (m["_d"] <= m["validez_hasta"])]
    if m.empty:
        return pd.DataFrame(columns=cols)
    # Si el agente tenía varias tarifas (líneas o servicios distintos), se compara contra la MÁS ALTA: solo cuenta como
    # «pagó más» lo que supera cualquier tarifa que ese agente cotizó para esa ruta y contenedor (criterio conservador).
    g = m.groupby("index").agg(cotizado=("flete", "max"), cotizado_min=("flete", "min")).join(x.set_index("index"))
    g["pagado"] = g["flete_por_ctnr"]
    g["dif"] = g["pagado"] - g["cotizado"]
    g["dif_pct"] = g["dif"] / g["cotizado"]
    g["pago_mas"] = g["dif_pct"] > settings.OPORT_ADHERENCIA_TOL
    g["exceso"] = (g["dif"].clip(lower=0) * g["contenedores"].fillna(1)).where(g["pago_mas"], 0.0)
    if "responsable" not in g:
        g["responsable"] = None
    return g.reset_index(drop=True)[cols].sort_values("exceso", ascending=False)


def adherencia_por_agente(a: pd.DataFrame) -> pd.DataFrame:
    if a.empty:
        return pd.DataFrame(columns=["forwarder", "embarques", "pago_mas", "pct", "exceso", "dif_med"])
    g = a.groupby("forwarder").agg(embarques=("embarque", "size"), pago_mas=("pago_mas", "sum"),
                                   exceso=("exceso", "sum"), dif_med=("dif", "median")).reset_index()
    g["pct"] = g["pago_mas"] / g["embarques"]
    return g.sort_values("exceso", ascending=False).reset_index(drop=True)


# ---------------------------------------------------------------------------
def por_seleccion(hist: pd.DataFrame, cot: pd.DataFrame | None, desde: pd.Timestamp | None = None) -> pd.DataFrame:
    """Ahorro por selección: para cada embarque, la mediana de las cotizaciones comparables de OTROS agentes vigentes
    al zarpe (ETD) menos lo que pagamos, × contenedores. Positivo = elegimos más barato que la alternativa típica."""
    cols = ["embarque", "etd", "forwarder", "puerto", "tipo_ctnr", "contenedores", "pagado", "alternativa",
            "alternativas", "ahorro"]
    if hist is None or hist.empty or cot is None or cot.empty:
        return pd.DataFrame(columns=cols)
    x = hist[(hist["flete_por_ctnr"] > 0) & hist["tipo_ctnr"].notna()]
    if desde is not None:
        x = x[x["etd"] >= desde]
    # La tarifa que aplica es la vigente al zarpe (ETD): cruzando por fecha de instrucción, en los meses de suba
    # parecía que «pagamos más» cuando en realidad cambió la quincena.
    x = x.assign(_f=x["forwarder"].map(fold), _p=x["puerto"].map(fold), _d=x["etd"]).reset_index()
    c = preparar(cot)
    keys = ["_p", "tipo_ctnr"] + (["destino"] if "destino" in c and "destino" in x else [])
    m = x[keys + ["index", "_f", "_d"]].merge(
        c[keys + ["forwarder", "validez_desde", "validez_hasta", "flete"]].assign(_fa=c["forwarder"].map(fold)),
        on=keys, how="inner")
    m = m[(m["_d"] >= m["validez_desde"]) & (m["_d"] <= m["validez_hasta"]) & (m["_fa"] != m["_f"])]
    if m.empty:
        return pd.DataFrame(columns=cols)
    alt = m.groupby(["index", "_fa"])["flete"].min().groupby(level=0).agg(["median", "size"])
    g = alt.join(x.set_index("index"))
    g = g.rename(columns={"median": "alternativa", "size": "alternativas"})
    g["pagado"] = g["flete_por_ctnr"]
    g["ahorro"] = (g["alternativa"] - g["pagado"]) * g["contenedores"].fillna(1)
    return g.reset_index(drop=True)[cols]


# ---------------------------------------------------------------------------
def alertas(hist: pd.DataFrame, cot: pd.DataFrame | None, today: pd.Timestamp, op: pd.DataFrame,
            adh: pd.DataFrame | None = None, destino: str = "Argentina") -> pd.DataFrame:
    """Situaciones a atender, cada una con tipo (Inmediata / Investigar / Seguimiento), detalle, acción y USD."""
    rows = []
    s = settings
    # Pagamos más de lo cotizado (por agente, últimos 90 días)
    if adh is not None and len(adh):
        rec = adh[adh["etd"] >= today - pd.Timedelta(days=90)]
        for _, r in adherencia_por_agente(rec).iterrows():
            if r["pago_mas"] > 0 and r["exceso"] > 0:
                rows.append({"tipo": "Inmediata", "situacion": "Pagamos más de lo cotizado", "sujeto": r["forwarder"],
                             "detalle": f"{int(r['pago_mas'])} de {int(r['embarques'])} embarques (90 d) pagaron por "
                                        f"encima de su propia cotización", "usd": r["exceso"],
                             "accion": f"Reclamar a {r['forwarder']} {_u(r['exceso'])} (descargar casos)"})
    # Tarifas por vencer sin la siguiente
    cur = preparar(periodo(cot, today, "curso", destino))
    prox = preparar(periodo(cot, today, "proxima", destino))
    if len(op) and len(cur):
        for _, r in op[op["vence"].notna()].iterrows():
            if r["vence"] <= today + pd.Timedelta(days=s.OPORT_VENCE_DIAS):
                tiene = len(prox) and ((prox["_p"] == fold(r["puerto"])) & (prox["tipo_ctnr"] == r["tipo_ctnr"])
                                       & (prox["forwarder"].map(fold) == fold(r["agente"]))).any()
                if not tiene:
                    rows.append({"tipo": "Inmediata", "situacion": "Tarifa por vencer", "sujeto": r["ruta"],
                                 "detalle": f"La tarifa de {r['agente']} vence el {r['vence']:%d/%m} y no hay la siguiente",
                                 "usd": np.nan, "accion": f"Pedir a {r['agente']} la próxima quincena de {r['ruta']}"})
    # Poca competencia
    if len(op):
        poca = op[(op["agentes"] <= 1)]
        for _, r in poca.iterrows():
            rows.append({"tipo": "Investigar", "situacion": "Poca competencia", "sujeto": r["ruta"],
                         "detalle": f"{int(r['agentes'])} agente cotiza · {r['contenedores']:.0f} contenedores en la ventana",
                         "usd": np.nan, "accion": "Pedir cotización a 2 agentes más"})
        nc = op[op["menor_no_comparable"].notna()]
        for _, r in nc.iterrows():
            rows.append({"tipo": "Investigar", "situacion": "Menor tarifa no comparable", "sujeto": r["ruta"],
                         "detalle": f"Hay {_u(r['menor_no_comparable'])} pero no es comparable ({r['motivo_no_comparable']})",
                         "usd": np.nan, "accion": "Pedir esa tarifa en las mismas condiciones (servicio, TT, pagadero)"})
    # Dependencia de un agente (90 días)
    h = _uso(hist, today, 90, destino)
    if len(h):
        share = h.groupby("forwarder")["_c"].sum() / h["_c"].sum()
        for ag, v in share[share > s.OPORT_CONCENTRACION].items():
            rows.append({"tipo": "Seguimiento", "situacion": "Dependencia de un agente", "sujeto": ag,
                         "detalle": f"{v:.0%} de los contenedores de los últimos 90 días", "usd": np.nan,
                         "accion": "Repartir rutas donde otro agente tiene tarifa comparable"})
    # Suba de la menor tarifa por ruta (en curso vs anterior)
    ant = preparar(periodo(cot, today, "anterior", destino))
    if len(op) and len(cur) and len(ant):
        for _, r in op.iterrows():
            a = cur[(cur["_p"] == fold(r["puerto"])) & (cur["tipo_ctnr"] == r["tipo_ctnr"])]["flete"].min()
            b = ant[(ant["_p"] == fold(r["puerto"])) & (ant["tipo_ctnr"] == r["tipo_ctnr"])]["flete"].min()
            if a == a and b == b and b > 0 and a / b - 1 > s.OPORT_SUBA:
                rows.append({"tipo": "Seguimiento", "situacion": "Suba de tarifas", "sujeto": r["ruta"],
                             "detalle": f"La menor pasó de {_u(b)} a {_u(a)} (+{a / b - 1:.0%})", "usd": np.nan,
                             "accion": "Adelantar reservas o negociar por volumen"})
    # Pagado por encima del histórico propio (último mes cerrado vs 6 previos, por ruta)
    hh = hist[(hist["flete_por_ctnr"] > 0) & hist["tipo_ctnr"].notna()]
    if "destino" in hh:
        hh = hh[hh["destino"] == destino]
    if len(hh):
        hh = hh.assign(_p=hh["puerto"].map(fold), mes=hh["etd"].dt.to_period("M").dt.to_timestamp())
        last = today.to_period("M").to_timestamp() - pd.offsets.MonthBegin(1)
        for (p, tipo), g in hh.groupby(["_p", "tipo_ctnr"]):
            ult = g[g["mes"] == last]["flete_por_ctnr"]
            prev = g[(g["mes"] < last) & (g["mes"] >= last - pd.DateOffset(months=6))]["flete_por_ctnr"]
            if len(ult) >= 3 and len(prev) >= s.OPORT_MIN_N and ult.median() / prev.median() - 1 > s.OPORT_SOBRE_HISTORICO:
                rows.append({"tipo": "Investigar", "situacion": "Encima del histórico propio",
                             "sujeto": f"{g['puerto'].iloc[0]} · {tipo}",
                             "detalle": f"{last:%m/%Y}: mediana {_u(ult.median())} vs {_u(prev.median())} de los 6 meses "
                                        f"previos (+{ult.median() / prev.median() - 1:.0%}, n={len(ult)})",
                             "usd": np.nan, "accion": "Revisar con el agente qué cambió"})
    t = pd.DataFrame(rows, columns=["tipo", "situacion", "sujeto", "detalle", "usd", "accion"])
    orden = {"Inmediata": 0, "Investigar": 1, "Seguimiento": 2}
    return t.assign(_o=t["tipo"].map(orden)).sort_values(["_o", "usd"], ascending=[True, False],
                                                        na_position="last").drop(columns="_o").reset_index(drop=True)


def top_acciones(op: pd.DataFrame, al: pd.DataFrame, n: int = 4) -> pd.DataFrame:
    """Las n acciones de mayor impacto: oportunidades inmediatas por score y alertas inmediatas con USD. «texto» es
    corto (cabe en una tarjeta); el detalle completo está en «accion» de cada tabla."""
    filas = []
    for _, r in op[op["tipo"] == "Inmediata"].iterrows():
        filas.append({"tipo": "Inmediata", "titulo": f"Renegociar {r['ruta']}", "con": r["negociar_con"],
                      "objetivo": r["objetivo"], "usd_mes": r["ahorro_mes"], "prioridad": r["prioridad"],
                      "texto": f"Con {r['negociar_con']}: de {_u(r['tarifa_actual'])} a {_u(r['objetivo'])} por "
                               f"contenedor ({r['mejor_agente']} lo ofrece) · {r['contenedores']:.0f} cont. en "
                               f"{settings.NEGOCIAR_VENTANA_DIAS} d",
                      "score": r["score"]})
    for _, r in al[(al["tipo"] == "Inmediata") & al["usd"].notna()].iterrows():
        filas.append({"tipo": "Inmediata", "titulo": f"Reclamar a {r['sujeto']}", "con": r["sujeto"],
                      "objetivo": np.nan, "usd_mes": np.nan, "usd": r["usd"], "prioridad": "Alta",
                      "texto": f"{r['situacion']}: {r['detalle']}", "score": r["usd"] / 3})
    for _, r in al[(al["tipo"] == "Inmediata") & al["usd"].isna()].head(2).iterrows():
        filas.append({"tipo": "Inmediata", "titulo": f"{r['situacion']} · {r['sujeto']}", "con": r["sujeto"],
                      "objetivo": np.nan, "usd_mes": np.nan, "texto": r["accion"], "prioridad": "Media", "score": 1})
    t = pd.DataFrame(filas)
    if t.empty:
        return t
    return t.sort_values("score", ascending=False).head(n).reset_index(drop=True)
