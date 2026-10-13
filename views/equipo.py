"""Equipo y agentes (nivel 2): herramienta de gestión del equipo de analistas y de los forwarders.

Cinco vistas: Resumen (salud operativa + conclusiones) · Analistas · Agentes · Alertas · Evolución.
Indicadores y reglas en utils/equipo.py. Período = el de la barra lateral (por defecto, desde inicio de año); lo
«en curso» no depende del período. Reemplaza a la pestaña anterior (views/analistas.py y views/agentes.py, que
siguen en el repo).
"""
from __future__ import annotations

import html

import numpy as np
import pandas as pd
import plotly.graph_objects as go
import streamlit as st

from components import charts
from components.kpi_cards import KPI, kpi_row
from components.layout import chart_title, empty, esc, filter_notes, guard, require, section
from components.tables import ColSpec, data_table
from config import settings
from utils import equipo as eq
from utils import formatting as fmt
from views._common import ctx, en_curso, filtered, memo, today

VISTAS = {"resumen": "Resumen", "analistas": "Analistas", "agentes": "Agentes", "alertas": "Alertas",
          "evolucion": "Evolución"}
ESTADO_TXT = {"ok": "Controlado", "warn": "Seguimiento", "bad": "Intervenir"}


def _pct(v) -> str:
    return fmt.fmt_pct(v) if v == v else "—"


def _dias(v) -> str:
    return f"{fmt.fmt_int(v)} d" if v == v else "—"


def _ventana_anterior(filters, t: pd.Timestamp):
    """Mismo largo que el período elegido, inmediatamente antes."""
    if not filters.start:
        return None
    ini = pd.Timestamp(filters.start)
    fin = min(pd.Timestamp(filters.end), t) if filters.end else t
    largo = fin - ini
    return ini - largo - pd.Timedelta(days=1), ini - pd.Timedelta(days=1)


def _datos(bundle, filters):
    t = today()
    h = filtered(bundle, "historicas", filters)
    z = eq.zarpados(h, t)
    h_all = filtered(bundle, "historicas", filters, use_period=False)
    v = _ventana_anterior(filters, t)
    z_prev = eq.zarpados(h_all[h_all["etd"].between(*v)], t) if v is not None and h_all is not None else None
    act, _ = en_curso(bundle, filters)
    from views.accion import casos as casos_bandeja
    casos = casos_bandeja(bundle, filters)
    if len(casos):
        casos = casos.assign(quien=[eq.quien_resuelve(tp, ac) for tp, ac in zip(casos["tipo"], casos["accion"])])
    so = memo(bundle, "so_por_embarque", lambda: _so_por_embarque(bundle))
    return t, z, z_prev, act, casos, so


def _so_por_embarque(bundle) -> pd.Series | None:
    """Cantidad de SO distintas por embarque (Embarques Históricos + Planif cargas)."""
    partes = [d[["embarque", "so"]] for d in (bundle.get("emb_hist"), bundle.get("planif"))
              if d is not None and {"embarque", "so"} <= set(d.columns)]
    if not partes:
        return None
    d = pd.concat(partes).dropna()
    return d.drop_duplicates().groupby("embarque")["so"].nunique()


def render() -> None:
    bundle, filters = ctx()
    if require(bundle, "historicas") is None:
        return
    st.session_state.setdefault("eq_vista", "resumen")
    vista = st.segmented_control("Vista", list(VISTAS), format_func=VISTAS.get, key="eq_vista",
                                 label_visibility="collapsed") or "resumen"
    with guard("Datos del equipo"):
        t, z, z_prev, act, casos, so = _datos(bundle, filters)
    an = eq.por_analista(z, act, casos, so)
    ag = eq.por_agente(z, act, z_prev)
    {"resumen": _resumen, "analistas": _analistas, "agentes": _agentes, "alertas": _alertas,
     "evolucion": _evolucion}[vista](bundle=bundle, filters=filters, t=t, z=z, z_prev=z_prev, act=act, casos=casos,
                                     an=an, ag=ag)


# ---------------------------------------------------------------------------
def _resumen(*, bundle, filters, t, z, act, casos, an, ag, **_) -> None:
    section("¿Cómo está la operación?",
            "«Salud operativa» es un semáforo general: toma el peor de los cuatro indicadores de al lado (no es un "
            "promedio ni un puntaje). Verde = controlado · amarillo = seguimiento · rojo = intervenir. El ⓘ de cada "
            "tarjeta explica cómo se mide y sus umbrales. Histórico = marítimos zarpados del período; «en curso» no "
            "depende del período.")
    with guard("Salud operativa"):
        s = eq.salud(z, act, casos, t)
        rojos = [c for c in s["componentes"] if c[2] == "bad"]
        amarillos = [c for c in s["componentes"] if c[2] == "warn"]
        motivo = rojos or amarillos
        sub = ("En " + ("rojo" if rojos else "amarillo") + ": " + " · ".join(f"{esc(c[0])} ({_pct(c[1])})"
                                                                         for c in motivo)) if motivo else \
            "Los cuatro indicadores en verde"
        umbral = settings.EQ_SALUD
        obj = settings.CUMPLIMIENTO_OBJETIVO
        tarjetas = [KPI("Salud operativa", ESTADO_TXT.get(s["general"], "—"), status=s["general"], sub=sub,
                        help="Semáforo general de la operación: toma el PEOR de los 4 indicadores de al lado (no es un "
                             "promedio ni un puntaje). Rojo = algún indicador en rojo → intervenir. Amarillo = alguno "
                             "en amarillo → seguimiento. Verde = los 4 en verde. Umbrales: SLA verde ≥ "
                             f"{obj:.0%}, rojo < {obj - settings.EQ_MARGEN_PP:.0%} · prioridad alta verde ≤ "
                             f"{umbral['alta'][0]:.0%}, rojo > {umbral['alta'][1]:.0%} · ETD sin confirmar verde ≤ "
                             f"{umbral['sin_ok'][0]:.0%}, rojo > {umbral['sin_ok'][1]:.0%} · salen tarde verde ≤ "
                             f"{umbral['desvio'][0]:.0%}, rojo > {umbral['desvio'][1]:.0%}.")]
        ayudas = {
            "Cumplimiento SLA consolidación": "Marítimos zarpados del período con packeo → ETD dentro del SLA de su "
                                              "puerto (monoproveedor: SLA mono). Más es mejor.",
            "Activos con caso de prioridad alta": "Embarques EN CURSO que tienen al menos un caso de prioridad alta en "
                                                  "la Bandeja de acción (ETD en ≤ 3 días sin confirmar, zarpó sin "
                                                  "documentos, ya pasó el SLA…). Menos es mejor.",
            "ETD próximos": "Embarques en curso con ETD en los próximos días que todavía no tienen «ETD OK FFWW». "
                            "Menos es mejor.",
            "Salen >": "Marítimos zarpados del período cuya ETD real fue más de "
                       f"{settings.EQ_DESVIO_DIAS} días después de la ETD estimada (solo los que tienen ETD estimada). "
                       "Menos es mejor.",
        }
        for nombre, valor, estado, base in s["componentes"]:
            ayuda = next((v for k, v in ayudas.items() if nombre.startswith(k)), "")
            tarjetas.append(KPI(nombre, _pct(valor), status=estado, sub=esc(base), help=ayuda))
        kpi_row(tarjetas, columns=5)

    with guard("KPIs del equipo"):
        n_act = int(act["embarque"].nunique()) if len(act) else 0
        alta = int(casos.loc[casos["prioridad"] == "Alta", "embarque"].nunique()) if len(casos) else 0
        kpi_row([
            KPI("En curso", fmt.fmt_int(n_act), sub=" · ".join(
                f"{r['analista']} {fmt.fmt_int(r['activos'])}" for _, r in an[an["activos"] > 0].iterrows())
                + (f" · aéreos sin responsable {fmt.fmt_int(n_act - an['activos'].sum())}"
                   if len(an) and n_act > an["activos"].sum() else "") if len(an) else ""),
            KPI("Zarpados en el período", fmt.fmt_int(len(z)), sub="marítimos · embarques únicos"),
            KPI("Casos abiertos", fmt.fmt_int(casos["embarque"].nunique()) if len(casos) else "0",
                status="bad" if alta else "ok", link="accion",
                sub=f"embarques en la Bandeja · <b>{fmt.fmt_int(alta)}</b> con prioridad alta (en curso, ya zarpados "
                    "y datos a corregir)",
                help="Incluye todo lo de la Bandeja de acción, no solo lo en curso: por eso es más que el indicador de "
                     "salud «activos con caso de prioridad alta», que mira solo los embarques en curso."),
            KPI("Instrucción tardía", _pct(eq._pct(z["_tarde"])) if len(z) else "—",
                sub="instruidos después de que la carga estaba lista",
                help="Bidcom / analista: % de embarques cuya instrucción salió después del último packeo (en un "
                     "consolidado se espera a todos los proveedores)."),
            KPI("Listo → ETD", _dias(eq._med(z["dias_listo_etd"])) if len(z) else "—",
                sub="mediana · lo que depende del agente",
                help="Días desde que la carga está lista e instruida (la mayor de último packeo e instrucción) "
                     "hasta la ETD."),
        ])

    with guard("Conclusiones"):
        section("Conclusiones de gestión", "Armadas solo con los datos del período: cada una exige muestra mínima "
                                           f"(n ≥ {settings.MIN_SAMPLE}) y un cambio relevante.")
        frases = eq.conclusiones(z, an, ag, casos, t)
        if not frases:
            empty("Sin conclusiones con muestra suficiente para los filtros elegidos.")
        else:
            icono = {"good": "🟢", "bad": "🔴", "neutral": "🔵"}
            st.markdown("\n".join(f"- {icono[tn]} {txt}" for tn, txt in frases))

    with st.expander("Cómo se mide · y qué todavía no se puede medir"):
        st.markdown(
            "- **Unidad**: embarque único. Las SO se cuentan aparte. Tiempos por **mediana** (P25–P75 para la "
            "dispersión), siempre con su n. Un dato faltante **no** cuenta como incumplimiento.\n"
            "- **Analista (lo que controla)**: instruir a tiempo (*instrucción tardía*) y tener la gestión al día "
            "(casos de la Bandeja a su cargo, fuera de SLA sin causa cargada, fletes sin validar).\n"
            "- **Agente (lo que controla)**: *listo → ETD*, desvío de la ETD real contra la estimada, ETD confirmada "
            "(«ETD OK FFWW»), booking in advance y demoras con «Tipo de demora» = Agente.\n"
            "- **Resultado del proceso**: cumplimiento del SLA de consolidación (packeo → ETD, SLA por puerto; "
            f"monoproveedor {settings.SLA_CONSOLIDACION_MONO} d). Incluye causas externas (proveedor, naviera, "
            "puerto, clima): por eso no se usa solo para evaluar a una persona.\n"
            "- **No medible hoy**: confirmación de booking en 48/72 h (la planilla no tiene la fecha de confirmación "
            "del booking; «Fecha de confirmación» es la de salida y está cargada en ~40 %), «sin actualización» (no "
            "hay fecha de última modificación por fila) y roleos (no se guarda el historial de ETD; se usa el desvío "
            "contra la ETD estimada). Agregando esas columnas se pueden sumar.")


# ---------------------------------------------------------------------------
def _analistas(*, bundle, filters, t, z, act, casos, an, **_) -> None:
    section("Analistas · comparativa",
            "Cuatro dimensiones separadas, sin puntaje único: carga, resultado del proceso, gestión propia y "
            "seguimiento. Histórico = marítimos zarpados del período; los aéreos no tienen responsable en la planilla. "
            f"No se muestran {', '.join(settings.EQ_ANALISTAS_EXCLUIDOS)} (ya no están en el equipo); sus embarques "
            "siguen contando en los totales.")
    filter_notes(bundle.get("historicas"), filters, "Reservas Históricas")
    if an.empty:
        empty()
        return
    with guard("Tabla de analistas"):
        tabla = an.assign(fuera_ext_txt=[f"{fe} de {f}" if f else "—" for fe, f in zip(an["fuera_ext"], an["fuera"])])
        data_table(tabla, [
            ColSpec("analista", "Analista"),
            ColSpec("activos", "En curso", "int"), ColSpec("pct_activos", "% del equipo", "pct"),
            ColSpec("embarques", "Zarpados", "int"), ColSpec("so", "SO", "int"),
            ColSpec("pct_conso", "% consolidado", "pct"),
            ColSpec("cumple", "% SLA consol.", "pct"), ColSpec("fuera_ext_txt", "Fuera SLA con causa externa"),
            ColSpec("pct_tarde", "% instrucción tardía", "pct"), ColSpec("med_atraso", "Atraso instr. (d)", "days"),
            ColSpec("casos", "Casos abiertos", "int"), ColSpec("casos_analista", "Los resuelve el analista", "int"),
            ColSpec("casos_alta", "Con prioridad alta", "int"),
            ColSpec("fuera_sin_causa", "Fuera SLA sin causa", "int"),
        ], key="eq_an_tabla", filename="analistas", search=False,
            caption="Carga: en curso, zarpados, SO y mezcla (un consolidado es más complejo) · Resultado: % SLA y cuántos "
                    "fuera de SLA tienen causa externa (proveedor, naviera / puerto / clima, agente) · Gestión propia: "
                    "instrucción tardía y su atraso mediano · Seguimiento: casos abiertos que resuelve el analista, "
                    "prioridad alta y fuera de SLA sin «Tipo de demora».")

    with guard("Detalle de analista"):
        nombres = list(an["analista"])
        quien = st.selectbox("Ver un analista", nombres, key="eq_an_sel")
        r = an[an["analista"] == quien].iloc[0]
        zz = z[z["responsable"] == quien] if len(z) else z
        eq_med = {c: an[c].median() for c in ("cumple", "pct_tarde", "activos")}
        kpi_row([
            KPI("En curso", fmt.fmt_int(r["activos"]), sub=f"equipo: mediana {fmt.fmt_int(eq_med['activos'])} por analista"),
            KPI("Zarpados", fmt.fmt_int(r["embarques"]),
                sub=f"{_pct(r.get('pct_conso', np.nan))} consolidado · {fmt.fmt_int(r['so'])} SO" if r["embarques"] else ""),
            KPI("% SLA consolidación", _pct(r.get("cumple", np.nan)),
                status=eq.semaforo(r.get("cumple", np.nan), (settings.CUMPLIMIENTO_OBJETIVO,
                                                             settings.CUMPLIMIENTO_OBJETIVO - settings.EQ_MARGEN_PP),
                                   True) if r.get("n_cumple", 0) >= settings.MIN_SAMPLE else "",
                sub=f"equipo {_pct(eq_med['cumple'])} · n={fmt.fmt_int(r.get('n_cumple', 0))}"),
            KPI("Instrucción tardía", _pct(r.get("pct_tarde", np.nan)),
                sub=f"equipo {_pct(eq_med['pct_tarde'])} · atraso mediano {_dias(r.get('med_atraso', np.nan))}"),
            KPI("Casos abiertos", fmt.fmt_int(r["casos"]), status="warn" if r["casos_alta"] else "",
                sub=f"<b>{fmt.fmt_int(r['casos_analista'])}</b> los resuelve el analista · "
                    f"<b>{fmt.fmt_int(r['casos_alta'])}</b> con prioridad alta",
                help="Embarques con al menos un caso en la Bandeja de acción. Los demás los resuelve el agente o el "
                     "proveedor (ver columna «Resuelve»)."),
        ])
        if len(zz):
            m = eq.mensual(zz)
            chart_title(f"{quien} · mes a mes", "Mes de ETD · marítimos zarpados")
            data_table(m.assign(mes=m["mes"].dt.strftime("%m/%Y")), [
                ColSpec("mes", "Mes"), ColSpec("embarques", "Zarpados", "int"), ColSpec("cumple", "% SLA", "pct"),
                ColSpec("n_cumple", "n SLA", "int"), ColSpec("med_consol", "Consolidación (d)", "days"),
                ColSpec("pct_tarde", "% instrucción tardía", "pct"),
            ], key="eq_an_mes", filename=f"analista_{quien}_mensual", search=False, height=min(420, 38 + 35 * len(m)))
        cc = casos[(casos["responsable"] == quien)] if len(casos) else casos
        if len(cc):
            chart_title(f"Casos abiertos de {quien}", "De la Bandeja de acción · quién resuelve cada uno")
            data_table(cc, [
                ColSpec("prioridad", "Prioridad"), ColSpec("embarque", "Embarque"), ColSpec("situacion", "Situación"),
                ColSpec("agente", "Agente"), ColSpec("quien", "Resuelve"), ColSpec("accion", "Acción", width="large"),
                ColSpec("etd", "ETD", "date"),
            ], key="eq_an_casos", filename=f"casos_{quien}", search=len(cc) > 12, height=min(420, 38 + 35 * len(cc)))


# ---------------------------------------------------------------------------
def _agentes(*, bundle, filters, t, z, z_prev, act, ag, **_) -> None:
    section("Agentes · servicio, tiempos y confiabilidad",
            "Marítimos zarpados del período. Para comparar parejo, elegí la estructura (y el puerto en la barra "
            f"lateral). Solo se evalúan agentes con ≥ {settings.MIN_SAMPLE} embarques.")
    estr = st.segmented_control("Estructura", ["Todos", "Monoproveedor", "Consolidado"], default="Todos",
                                key="eq_ag_estr", label_visibility="collapsed") or "Todos"
    if estr != "Todos":
        z = z[z["estructura"] == estr] if len(z) else z
        z_prev = z_prev[z_prev["estructura"] == estr] if z_prev is not None and len(z_prev) else z_prev
        ag = eq.por_agente(z, act, z_prev)
    if ag.empty:
        empty()
        return
    with guard("KPIs de agentes"):
        pag = z.loc[z["flete_pagado"] > 0, "flete_pagado"].sum()
        cert = z.loc[z["flete_pagado"] > 0, "flete_certificado"].sum()
        kpi_row([
            KPI("Embarques", fmt.fmt_int(len(z)), sub=f"{fmt.fmt_int(ag['agente'].nunique())} agentes"),
            KPI("Listo → ETD", _dias(eq._med(z["dias_listo_etd"])),
                sub=f"mediana · P25–P75 {_dias(z['dias_listo_etd'].quantile(.25))}–{_dias(z['dias_listo_etd'].quantile(.75))}"),
            KPI("% SLA consolidación", _pct(eq._pct(z["cumple_consolidacion"]))),
            KPI(f"Salen > {settings.EQ_DESVIO_DIAS} d tarde", _pct(eq._pct(z["_desvio_alto"])),
                sub=f"vs ETD estimada · n={fmt.fmt_int(z['_desvio_alto'].notna().sum())}"),
            KPI("Flete certificado", _pct(cert / pag if pag else np.nan), sub="certificado / pagado"),
        ])
    with guard("Cuadro de agentes"):
        tabla = ag.assign(rango=[f"{fmt.fmt_int(a)}–{fmt.fmt_int(b)}" if a == a else "—" for a, b in zip(ag["p25"], ag["p75"])],
                          delta_txt=[("▲ " if d > 0 else "▼ " if d < 0 else "= ") + f"{abs(d) * 100:.0f} pp" if d == d else "—"
                                     for d in ag["delta_cumple"]],
                          revisar=ag["revisar"].replace("", "—"))
        data_table(tabla, [
            ColSpec("agente", "Agente"), ColSpec("revisar", "Requiere revisión", width="large"),
            ColSpec("embarques", "Zarpados", "int"), ColSpec("share", "% del total", "pct"),
            ColSpec("activos", "En curso", "int"),
            ColSpec("cumple", "% SLA", "pct"), ColSpec("delta_txt", "vs período ant."),
            ColSpec("med_listo_etd", "Listo → ETD (d)", "days"), ColSpec("rango", "P25–P75"),
            ColSpec("med_desvio", "Desvío ETD (d)", "days"), ColSpec("pct_desvio_alto", f"% > {settings.EQ_DESVIO_DIAS} d tarde", "pct"),
            ColSpec("pct_advance", "% in advance", "pct"), ColSpec("pct_etd_ok", "% ETD OK (en curso)", "pct"),
            ColSpec("demoras_agente", "Demoras con el agente involucrado", "int"), ColSpec("certificacion", "% certificado", "pct"),
        ], key="eq_ag_tabla", filename="agentes", search=False,
            caption="Listo → ETD: desde que la carga está lista e instruida hasta la ETD (lo que depende del agente); "
                    "P25–P75 = dispersión. Desvío ETD = ETD real − ETD estimada. «Requiere revisión» se marca solo con "
                    f"n ≥ {settings.MIN_SAMPLE}: cumplimiento {settings.EQ_MARGEN_PP * 100:.0f} pp bajo el objetivo, caída ≥ "
                    f"{settings.EQ_DETERIORO_PP * 100:.0f} pp, listo → ETD {settings.EQ_LENTO_PCT:.0%} sobre el total, "
                    "muchas salidas tarde o 3+ demoras con el agente involucrado («Tipo de demora» que menciona al agente, aunque sea compartida, p. ej. «Proveedor + Agente»).")
    ok = ag[ag["embarques"] >= settings.MIN_SAMPLE]
    if len(ok):
        c1, c2 = st.columns(2, gap="medium")
        with c1, guard("Listo a ETD por agente"):
            chart_title("Listo → ETD por agente", "Mediana en días · P25–P75 en el cuadro y al pasar el mouse")
            g = ok.dropna(subset=["med_listo_etd"]).sort_values("med_listo_etd", ascending=False)
            fig = charts.hbar(g["agente"], g["med_listo_etd"],
                              text=[f"{fmt.fmt_int(v)} d · n={n}" for v, n in zip(g["med_listo_etd"], g["n_listo_etd"])],
                              hover="%{y}: %{x:.0f} d · P25–P75 %{customdata}<extra></extra>", x_title="días",
                              ref_value=eq._med(z["dias_listo_etd"]), ref_label="Total")
            fig.update_traces(customdata=[f"{fmt.fmt_int(a)}–{fmt.fmt_int(b)} d" for a, b in zip(g["p25"], g["p75"])],
                              selector=dict(type="bar"))
            charts.show(fig, key="eq_ag_listo")
        with c2, guard("SLA por agente"):
            chart_title("Cumplimiento de SLA de consolidación", "% de embarques dentro del SLA · línea = objetivo")
            g = ok.dropna(subset=["cumple"]).sort_values("cumple")
            fig = charts.hbar(g["agente"], g["cumple"] * 100, text=[f"{_pct(v)} · n={n}" for v, n in zip(g["cumple"], g["n_cumple"])],
                              hover="%{y}: %{x:.0f} %<extra></extra>", x_title="%", x_suffix=" %",
                              ref_value=settings.CUMPLIMIENTO_OBJETIVO * 100, ref_label="Objetivo")
            charts.show(fig, key="eq_ag_sla")


# ---------------------------------------------------------------------------
def _alertas(*, bundle, filters, t, z, act, casos, an, ag, **_) -> None:
    section("¿Dónde hay que intervenir?",
            "Qué está mal, quién tiene que resolverlo y qué hacer. Casos por operación (de la Bandeja de acción) y "
            "alertas del equipo. Cada caso lleva su embarque.")
    with guard("Alertas del equipo"):
        alertas = []
        tot = an["activos"].sum() if len(an) else 0
        for _, r in an.iterrows():
            if tot >= settings.MIN_SAMPLE and r["activos"] / tot > settings.EQ_CONCENTRACION:
                alertas.append(("🔴", f"Carga concentrada: {r['analista']} tiene {r['activos']} de {tot} embarques en "
                                      f"curso ({r['activos'] / tot:.0%}).", "Coordinación: redistribuir nuevas instrucciones"))
        for _, r in ag[(ag["embarques"] >= settings.MIN_SAMPLE) & (ag["revisar"] != "")].iterrows():
            if r["revisar"] != "Muestra chica":
                alertas.append(("🟡", f"{r['agente']}: {r['revisar']}.", "Revisión de servicio con el agente"))
        if alertas:
            st.markdown("\n".join(f"- {i} {html.escape(txt)} → *{acc}*" for i, txt, acc in alertas))
        else:
            st.caption("Sin alertas de equipo con el criterio actual.")
    if casos is None or casos.empty:
        empty("No hay casos abiertos para los filtros elegidos.")
        return
    with guard("Casos"):
        q = casos.groupby("quien")["embarque"].nunique().sort_values(ascending=False)
        kpi_row([KPI("Casos abiertos", fmt.fmt_int(casos["embarque"].nunique()),
                     sub=f"<b>{fmt.fmt_int(casos.loc[casos['prioridad'] == 'Alta', 'embarque'].nunique())}</b> embarques "
                         f"con prioridad alta · {fmt.fmt_int(len(casos))} casos", link="accion")]
                + [KPI(f"Resuelve: {k}", fmt.fmt_int(v), sub="embarques") for k, v in q.items()])
        c1, c2 = st.columns(2, gap="small")
        with c1:
            sel_a = st.selectbox("Analista", ["Todos"] + sorted(x for x in casos["responsable"].dropna().unique()
                                                                if not eq.excluido(x)), key="eq_al_an")
        with c2:
            sel_q = st.selectbox("Resuelve", ["Todos"] + list(q.index), key="eq_al_q")
        v = casos
        if sel_a != "Todos":
            v = v[v["responsable"] == sel_a]
        if sel_q != "Todos":
            v = v[v["quien"] == sel_q]
        data_table(v, [
            ColSpec("prioridad", "Prioridad"), ColSpec("embarque", "Embarque"), ColSpec("responsable", "Analista"),
            ColSpec("agente", "Agente"), ColSpec("situacion", "Qué pasa / etapa", width="medium"),
            ColSpec("dias", "Días", "int"), ColSpec("excedido", "Días sobre SLA", "int"), ColSpec("causa", "Motivo"),
            ColSpec("quien", "Resuelve"), ColSpec("accion", "Acción", width="large"), ColSpec("etd", "ETD", "date"),
        ], key="eq_al_tabla", filename=f"alertas_equipo_{t:%Y%m%d}", search=len(v) > 12,
            height=min(520, 38 + 35 * len(v)))


# ---------------------------------------------------------------------------
def _evolucion(*, bundle, filters, t, z, **_) -> None:
    section("Evolución", "Marítimos zarpados por semana y mes de ETD. * mes / semana en curso.")
    if z is None or z.empty:
        empty()
        return
    with guard("Semanal"):
        chart_title("Cumplimiento de SLA por semana", "Últimas 13 semanas · % dentro del SLA · el texto muestra n")
        w = eq.semanal(z, t)
        if w.empty:
            empty()
        else:
            fig = go.Figure(go.Bar(x=[f"{d:%d/%m}" for d in w["semana"]], y=w["cumple"] * 100,
                                   text=[f"{_pct(v)}<br>n={n}" for v, n in zip(w["cumple"], w["n_cumple"])],
                                   textposition="outside", cliponaxis=False,
                                   marker=dict(color=[settings.COLORS["green"] if v >= settings.CUMPLIMIENTO_OBJETIVO
                                                      else settings.COLORS["red"] for v in w["cumple"].fillna(0)],
                                               cornerradius=3),
                                   hovertemplate="Semana del %{x}: %{y:.0f} %<extra></extra>"))
            fig.add_hline(y=settings.CUMPLIMIENTO_OBJETIVO * 100, line=dict(color=settings.COLORS["slate"], dash="dash"))
            charts.theme(fig, y_title="% dentro de SLA", y_suffix=" %", height=320, legend=False)
            fig.update_yaxes(range=[0, 115])
            charts.show(fig, key="eq_ev_sem")
    with guard("Mensual"):
        m = eq.mensual(z)
        meses = m["mes"].dt.strftime("%m/%Y")
        chart_title("Tiempos y confiabilidad mes a mes", "Medianas en días · % que salió > "
                                                         f"{settings.EQ_DESVIO_DIAS} d después de la ETD estimada")
        data_table(m.assign(mes=meses), [
            ColSpec("mes", "Mes"), ColSpec("embarques", "Zarpados", "int"), ColSpec("cumple", "% SLA", "pct"),
            ColSpec("med_consol", "Consolidación (d)", "days"), ColSpec("med_listo_etd", "Listo → ETD (d)", "days"),
            ColSpec("pct_tarde", "% instrucción tardía", "pct"),
            ColSpec("pct_desvio_alto", f"% > {settings.EQ_DESVIO_DIAS} d tarde", "pct"),
        ], key="eq_ev_mes", filename="equipo_mensual", search=False, height=min(460, 38 + 35 * len(m)))
    c1, c2 = st.columns(2, gap="medium")
    with c1, guard("Carga por analista"):
        chart_title("Zarpados por mes y analista", "Embarques marítimos")
        p = eq.mensual(z, "responsable")
        p = p[~p["responsable"].map(eq.excluido)] if len(p) else p
        if p.empty:
            empty()
        else:
            piv = p.pivot(index="mes", columns="responsable", values="embarques").fillna(0)
            top = list(piv.sum().sort_values(ascending=False).index)
            cmap = charts.color_map(top[:4])
            fig = go.Figure()
            for name in top[:4]:
                fig.add_scatter(x=[f"{d:%m/%y}" for d in piv.index], y=piv[name], name=name, mode="lines+markers",
                                line=dict(color=cmap[name], width=2), hovertemplate=f"{name}: %{{y:.0f}}<extra></extra>")
            charts.theme(fig, y_title="embarques", height=320)
            charts.show(fig, key="eq_ev_an")
    with c2, guard("SLA por agente"):
        chart_title("% SLA por mes · agentes principales", f"Solo meses con n ≥ {settings.MIN_SAMPLE}")
        p = eq.mensual(z, "forwarder")
        if p.empty:
            empty()
        else:
            top = list(z["forwarder"].value_counts().index[:4])
            cmap = charts.color_map(top)
            fig = go.Figure()
            for name in top:
                d = p[(p["forwarder"] == name) & (p["n_cumple"] >= settings.MIN_SAMPLE)]
                fig.add_scatter(x=[f"{m_:%m/%y}" for m_ in d["mes"]], y=d["cumple"] * 100, name=name,
                                mode="lines+markers", line=dict(color=cmap[name], width=2),
                                hovertemplate=f"{name}: %{{y:.0f}} %<extra></extra>")
            fig.add_hline(y=settings.CUMPLIMIENTO_OBJETIVO * 100, line=dict(color=settings.COLORS["slate"], dash="dash"))
            charts.theme(fig, y_title="% dentro de SLA", y_suffix=" %", height=320)
            charts.show(fig, key="eq_ev_ag")
