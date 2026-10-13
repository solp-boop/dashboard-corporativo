"""Costos y captura (nivel 2): cuánto pagamos, cuánto capturamos y dónde hay oportunidad.

Reúne lo que antes estaba en «Fletes y gastos pagados» y «Cotizaciones», en cuatro vistas:
¿Cuánto gastamos? · ¿Cuánto ahorramos? · ¿Qué renegocio? · ¿Nos cobran lo negociado? · ¿Cómo vienen las tarifas? ·
Contenedores (una sola botonera de tarjetas, views/costos._navegacion).
"""
from __future__ import annotations

import numpy as np
import pandas as pd
import plotly.graph_objects as go
import streamlit as st

from components import charts
from components import sla as sla_view
from components.kpi_cards import KPI, cert_status, cert_sub, kpi_row
from components.layout import chart_title, empty, esc, guard, require, section
from components.tables import ColSpec, data_table, solo_descarga
from config import settings
from config.mappings import MODOS_MARITIMOS
from utils import calculations as calc
from utils import bandeja
from utils import captura as cap
from utils import costos as cs
from utils import formatting as fmt
from utils import freight
from utils import oportunidades as oport
from views import cotizaciones, fletes_pagados
from views._common import ctx, filtered, memo, month_labels, negociacion, today

DIMS = [("forwarder", "Agente"), ("puerto", "Puerto"), ("medio", "Medio"), ("tipo_ctnr", "Tipo de contenedor"),
        ("linea", "Línea marítima"), ("responsable", "Responsable")]
COST_PARTS = [("flete_pagado", "Flete internacional"), ("gastos_locales", "Gastos locales ARG"),
              ("gastos_origen", "Gastos en origen")]


def _ventana_prev(filters, t):
    if not filters.start:
        return None
    end = min(pd.Timestamp(filters.end), t) if filters.end else t
    return pd.Timestamp(filters.start) - pd.DateOffset(years=1), end - pd.DateOffset(years=1)


def _datos(bundle, filters, use_period=True):
    t = today()
    h = filtered(bundle, "historicas", filters, use_period=use_period)
    a = filtered(bundle, "aereos", filters, use_period=use_period) if bundle.get("aereos") is not None else None
    if h is not None:
        h = freight.add_market_reference(h[h["modo"].isin(MODOS_MARITIMOS) & (h["etd"] <= t) & (h["flete_pagado"] > 0)],
                                         bundle.get("cotizaciones"))
    return h, a, cs.pagos(h, a, t)


def _motor(bundle, filters, h_all) -> dict:
    """Oportunidades, adherencia, alertas y acciones (utils.oportunidades). Una vez por carga, día y filtros."""
    t = today()

    def calc_():
        cot = bundle.get("cotizaciones")
        op = oport.oportunidades(h_all, cot, t, reservas=bundle.get("reservas"))
        adh = oport.adherencia(h_all, cot, desde=t - pd.Timedelta(days=365))
        al = oport.alertas(h_all, cot, t, op, adh)
        return {"op": op, "adh": adh, "al": al, "top": oport.top_acciones(op, al)}
    clave = ("costos_motor", t, tuple(sorted((k, tuple(v)) for k, v in filters.selections.items() if v)))
    return memo(bundle, clave, calc_)


PRIO_ICON = {"Alta": "🔴 Alta", "Media": "🟡 Media", "Baja": "⚪ Baja"}
TIPO_ICON = {"Inmediata": "🔴 Inmediata", "Investigar": "🟡 Investigar", "Seguimiento": "🔵 Seguimiento", "OK": "🟢 OK"}


def _acciones(m: dict) -> None:
    """Franja fija arriba de las vistas: las 3–5 acciones con más impacto en USD."""
    top = m["top"]
    if top is None or top.empty:
        return
    tiles = []
    for _, r in top.iterrows():
        if r.get("usd_mes") == r.get("usd_mes") and r.get("usd_mes"):
            monto = f"{fmt.fmt_usd(r['usd_mes'])}<span class='u'> / mes</span>"
        elif r.get("usd") == r.get("usd") and r.get("usd"):
            monto = f"{fmt.fmt_usd(r['usd'])}<span class='u'> a reclamar</span>"
        else:
            monto = "<span class='u'>sin monto estimable</span>"
        tiles.append(f"<div class='acc {esc(str(r['prioridad']).lower())}'><div class='p'>{esc(r['prioridad'])} · "
                     f"{esc(r['titulo'])}</div><div class='n'>{monto}</div><div class='s'>{esc(r['texto'])}</div></div>")
    st.markdown("<div class='section-sub' style='margin:.2rem 0 .4rem'><b>Acciones de mayor impacto</b> · "
                f"criterio comparable, últimos {settings.NEGOCIAR_VENTANA_DIAS} días, destino Argentina, solo flete</div>"
                f"<div class='acciones'>{''.join(tiles)}</div>", unsafe_allow_html=True)


def render() -> None:
    bundle, filters = ctx()
    if require(bundle, "historicas") is None:
        return
    t = today()
    h, a, p = _datos(bundle, filters)
    h_all, _, p_all = _datos(bundle, filters, use_period=False)
    ventana = _ventana_prev(filters, t)
    p_prev = p_all[p_all["etd"].between(*ventana)] if ventana else None
    m = None
    with guard("Motor de oportunidades"):
        if h_all is not None and len(h_all):
            m = _motor(bundle, filters, h_all)
    # Una sola botonera con la pregunta que responde cada vista (antes eran dos niveles de pestañas).
    vista = _navegacion(bundle, p, m, t)
    if vista == "gasto":
        _gasto(bundle, h, a, p, p_all, p_prev, h_all, ventana)
    elif vista == "captura":
        _captura(bundle, filters, h, ventana, m)
    elif vista in ("hacer", "mercado", "cobro"):
        _tarifas(bundle, h, m, h_all, a, sub={"cobro": "negociacion"}.get(vista, vista))
    else:
        from views import resumen
        _equipos(h)
        with guard("Contenedores"):
            resumen.render_contenedores(bundle, filters)
        resumen.render_especiales(bundle, filters)


VISTAS = {
    "gasto": "¿Cuánto gastamos?",
    "captura": "¿Cuánto ahorramos?",
    "hacer": "¿Qué renegocio esta semana?",
    "cobro": "¿Nos cobran lo negociado?",
    "mercado": "¿Cómo vienen las tarifas?",
    "contenedores": "Contenedores y cargas especiales",
}
# Enlaces viejos (?vista=tarifas / validacion) siguen funcionando.
VISTAS_ALIAS = {"tarifas": "hacer", "validacion": "cobro"}


def _navegacion(bundle, p, m, t) -> str:
    """Tarjetas con la pregunta de cada vista y su dato principal: se ve de un vistazo dónde entrar."""
    pedida = st.query_params.get("vista")
    pedida = VISTAS_ALIAS.get(pedida, pedida)
    if pedida in VISTAS and pedida != st.session_state.get("_costos_qp"):
        st.session_state["costos_vista"] = pedida
    if st.session_state.get("costos_vista") not in VISTAS:
        st.session_state["costos_vista"] = "gasto"
    datos = {k: "" for k in VISTAS}
    try:
        if p is not None and len(p):
            datos["gasto"] = f"{fmt.fmt_usd(float(p['costo'].sum()))} en el período · validación de pago"
        datos["captura"] = "negociación · 40 NOR · certificación"
        if m:
            op, adh = m["op"], m["adh"]
            inm = op[op["tipo"] == "Inmediata"]
            datos["hacer"] = (f"{fmt.plural(len(inm), 'ruta')} para renegociar · "
                              f"{fmt.fmt_usd(float(inm['ahorro_mes'].sum()))}/mes" if len(inm) else "sin rutas urgentes")
            rec = adh[adh["etd"] >= t - pd.Timedelta(days=90)] if len(adh) else adh
            datos["cobro"] = (f"{fmt.fmt_usd(float(rec['exceso'].sum()))} cobrados de más (90 días) · validación"
                              if len(rec) else "validación de fletes")
        mm = memo(bundle, ("mercado_mes", "40ST/40HQ", t),
                  lambda: cs.mercado_mes(bundle.get("cotizaciones"), "40ST/40HQ", t))
        cerrados = mm[mm["mes"] < t.to_period("M").to_timestamp()] if len(mm) else mm
        if len(cerrados):
            u = cerrados.iloc[-1]
            datos["mercado"] = f"40ST/HQ {fmt.fmt_month(u['mes'])}: {fmt.fmt_usd(u['mediana'], compact=False)}"
        datos["contenedores"] = "equipo conveniente · espacio vacío · IMO"
    except Exception:  # noqa: BLE001 · el dato de la tarjeta es accesorio: nunca rompe la navegación
        pass
    vista = st.radio("Vista", list(VISTAS), format_func=VISTAS.get, key="costos_vista", horizontal=True,
                     captions=[datos[k] or " " for k in VISTAS], label_visibility="collapsed")
    st.session_state["_costos_qp"] = vista
    if st.query_params.get("vista") != vista:
        st.query_params["vista"] = vista
    return vista

# ---------------------------------------------------------------------------
def _estado_pago(h) -> None:
    """Flete marítimo que todavía no está validado para pagar: observado (en análisis) y pendiente de validar."""
    if h is None or h.empty or "resultado_validacion" not in h:
        return
    est = h["resultado_validacion"].fillna("Pendiente")
    tot = float(h["flete_pagado"].clip(lower=0).sum())
    sv = h[est != "Validado"]
    chart_title("¿Cuánto del flete marítimo está validado para pagar?",
                "Lo que todavía no está validado y se está procesando: no está en el costo de arriba")

    def k(nombre, d, status, ayuda):
        v = float(d["flete_pagado"].clip(lower=0).sum())
        return KPI(nombre, fmt.fmt_usd(v), status=status if len(d) else "ok", help=ayuda,
                   sub=f"<b>{fmt.fmt_pct(v / tot if tot else float('nan'))}</b> del flete marítimo facturado · "
                       f"{fmt.fmt_int(len(d))} embarques")
    kpi_row([
        k("Sin validar (en proceso)", sv, "warn", "Observados + pendientes de validar: flete facturado por el agente que "
          "todavía no está aprobado para pagar."),
        k("Observado (en análisis)", h[est == "Observado"], "warn", "«Resultado Validación» = Observado: el agente "
          "tiene que ajustar."),
        k("Pendiente de validar", h[est == "Pendiente"], "bad", "Sin «Resultado Validación» ni check de validación."),
    ], columns=3)


def _certificacion(h) -> None:
    """Captura fiscal: lo que no se certifica como flete sale de la base imponible de aduana."""
    if h is None or h.empty or "flete_certificado" not in h:
        return
    d = h[(h["flete_pagado"] > 0) & (h["flete_certificado"] > 0)].copy()
    section("3 · Certificación de flete · detalle",
            "«Flete Int PAGADO» es el 100 % del flete; «Flete Certificado» es lo que se declara como flete. La diferencia "
            "la factura el agente por otro concepto y sale de la base imponible de aduana: pagamos menos derechos. No se "
            "suma a 1 + 2 porque es un ahorro de aduana, no de flete.")
    if d.empty:
        empty("Sin embarques con flete certificado en el período.")
        return
    d["base_fuera"] = (d["flete_pagado"] - d["flete_certificado"]).clip(lower=0)
    d["validado"] = d["resultado_validacion"] == "Validado" if "resultado_validacion" in d else False
    pag, cert, fuera = (float(d[c].sum()) for c in ("flete_pagado", "flete_certificado", "base_fuera"))
    pct = cert / pag if pag else float("nan")
    st_, badge = cert_status(pct)
    en_val = 1 - float(d["validado"].mean())
    kpi_row([
        KPI("Flete pagado − certificado", fmt.fmt_usd(fuera), status="ok" if fuera > 0 else "",
            sub=f"pagado {fmt.fmt_usd(pag)} − certificado {fmt.fmt_usd(cert)} · {fmt.fmt_int(len(d))} embarques",
            help="Suma de (Flete Int PAGADO − Flete Certificado): la parte del flete que no entra en la base de aduana."),
        KPI("Certificación de flete", fmt.fmt_pct(pct), status=st_, badge=badge,
            sub=f"certificado / pagado · máximo {fmt.fmt_pct(settings.KPI_CERTIFICACION_MAX)}"),
        KPI("En validación", fmt.fmt_pct(en_val), status="warn" if en_val > 0 else "ok",
            sub=f"de los embarques certificados todavía no está validado para pagar "
                f"({fmt.fmt_int(int((~d['validado']).sum()))})",
            help="La certificación ya ocurrió en aduana; esto indica cuánto de esa captura corresponde a fletes que "
                 "todavía no se validaron para pagar al agente."),
    ])
    g = d.assign(mes=calc.month_start(d["etd"])).groupby("mes").agg(
        n=("embarque", "nunique"), pag=("flete_pagado", "sum"), cert=("flete_certificado", "sum"),
        fuera=("base_fuera", "sum"), val=("validado", "mean")).reset_index().sort_values("mes")
    g["pct"] = g["cert"] / g["pag"]
    g["en_val"] = 1 - g["val"]
    g["mes_txt"] = g["mes"].map(lambda m: fmt.fmt_month(m).capitalize())
    cols = [ColSpec("mes_txt", "Mes ETD"), ColSpec("n", "Embarques", "int"), ColSpec("pag", "Flete pagado (USD)", "usd"),
            ColSpec("cert", "Flete certificado (USD)", "usd"), ColSpec("pct", "% certificación", "pct"),
            ColSpec("fuera", "Pagado − certificado (USD)", "usd"), ColSpec("en_val", "% en validación", "pct")]
    data_table(g, cols, key="co_cert_mes", filename="certificacion_flete_mes", search=False)
    solo_descarga(d.sort_values("base_fuera", ascending=False), [
        ColSpec("embarque", "Embarque"), ColSpec("etd", "ETD", "date"), ColSpec("forwarder", "Agente"),
        ColSpec("puerto", "Puerto"), ColSpec("flete_pagado", "Flete pagado (USD)", "usd"),
        ColSpec("flete_certificado", "Flete certificado (USD)", "usd"),
        ColSpec("base_fuera", "Pagado − certificado (USD)", "usd"), ColSpec("resultado_validacion", "Validación"),
        ColSpec("responsable", "Responsable"),
    ], key="co_cert_casos", filename="certificacion_por_embarque", label="Descargar certificación por embarque")


def _yoy(v: float, prev: pd.DataFrame | None, col: str) -> tuple[str, str]:
    """Delta contra el mismo período del año anterior (más gasto = malo)."""
    if prev is None or prev.empty or col not in prev:
        return "", ""
    b = float(prev[col].clip(lower=0).fillna(0).sum())
    if not b:
        return "", ""
    d = v / b - 1
    return f"{'▲' if d > 0 else '▼'} {fmt.fmt_pct(abs(d))} vs año anterior ({fmt.fmt_usd(b)})", \
        ("bad" if d > 0 else "good")


def _gasto(bundle, h, a, p, p_all, p_prev, h_all=None, ventana=None) -> None:
    from utils import panorama as pan
    t = today()
    section("¿Cuánto pagamos?", "Lo validado para pagar: marítimos con «Resultado Validación» = Validado (o el check de "
                                "Validación Logística Internacional) y aéreos zarpados del período. Costo total = flete "
                                "certificado + otros gastos (lo que no se certificó) + gastos en origen + gastos en destino.")
    if p.empty:
        empty()
        return
    with guard("KPIs de gasto"):
        def validado(d):
            if d is None or d.empty or "resultado_validacion" not in d:
                return d
            return d[(d["medio"] != "Marítimo") | (d["resultado_validacion"] == "Validado")]

        def con_partes(d):
            if d is None or d.empty:
                return d
            pag = d["flete_pagado"].clip(lower=0).fillna(0)
            cert = d["flete_certificado"].clip(lower=0).fillna(0).clip(upper=pag) if "flete_certificado" in d else pag * 0
            return d.assign(flete_cert=cert, otros_gastos=pag - cert)
        pv, pv_all, pv_prev = (con_partes(validado(x)) for x in (p, p_all, p_prev))
        ind = pan.costo(pv, pv_all, t)
        fl = calc.describe(h["flete_por_ctnr"]) if h is not None and len(h) else calc.describe(pd.Series(dtype=float))
        kg = calc.describe((a["flete_pagado"] / a["chargeable"].where(a["chargeable"] > 0))[
            (a["etd"] <= t) & (a["flete_pagado"] > 0)]) if a is not None and len(a) and "chargeable" in a \
            else calc.describe(pd.Series(dtype=float))
        cm3 = calc.describe(h["costo_por_m3"]) if h is not None and len(h) else calc.describe(pd.Series(dtype=float))

        def parte(col):
            v = pv[col].clip(lower=0).fillna(0)
            mar, aer = float(v[pv["medio"] == "Marítimo"].sum()), float(v[pv["medio"] == "Aéreo"].sum())
            return mar + aer, f"marítimo {fmt.fmt_usd(mar)} · aéreo {fmt.fmt_usd(aer)}"
        tot_costo = float(pv["costo"].sum())
        tarjetas = []
        for col, nombre, ayuda in (
                ("flete_cert", "Flete internacional certificado", "«Flete Certificado»: lo que se declara como flete "
                 "en aduana."),
                ("otros_gastos", "Otros gastos (no certificado)", "«Flete Int PAGADO» − «Flete Certificado»: la parte "
                 "del flete que el agente factura por otro concepto y no entra en la base imponible."),
                ("gastos_origen", "Gastos en origen", "«TOTAL GASTOS ORIGEN» (marítimo) y «Gastos en Origen» (aéreo)."),
                ("gastos_locales", "Gastos en destino", "«Gastos Locales» de marítimo y aéreo.")):
            v, sub = parte(col)
            dl, tono = _yoy(v, pv_prev, col)
            tarjetas.append(KPI(nombre, fmt.fmt_usd(v), help=ayuda, delta=dl, tono=tono,
                                sub=f"<b>{fmt.fmt_pct(v / tot_costo if tot_costo else float('nan'))}</b> del costo · {sub}"))
        kpi_row(tarjetas + [
            KPI("Costo logístico total", fmt.fmt_usd(tot_costo), sub=ind.sub, delta=ind.delta, tono=ind.tono,
                help=ind.ayuda + f" {fmt.fmt_int(len(pv))} embarques validados para pagar.")], columns=5)
        chart_title("Costo unitario", "Marítimo y aéreo, todos los embarques zarpados del período con flete")
        kpi_row([
            KPI("Flete por contenedor", fmt.fmt_usd(fl.median, compact=False) if fl.enough else "—",
                sub=f"Marítimo · mediana · P25–P75 {fmt.fmt_usd(fl.p25, compact=False)}–"
                    f"{fmt.fmt_usd(fl.p75, compact=False)}" if fl.enough else "Marítimo"),
            KPI("Aéreo · USD por kg", f"USD {fmt.fmt_num(kg.median, 1)}" if kg.enough else "—",
                sub=f"Mediana sobre chargeable · n={fmt.fmt_int(kg.n)}" if kg.enough else "Sin chargeable cargado"),
            KPI("Costo por m³", fmt.fmt_usd(cm3.median, compact=False) if cm3.enough else "—",
                sub="Marítimo · mediana del costo total / m³"),
        ], columns=4)
        _estado_pago(h)
    with guard("Costo por contenedor mes a mes"):
        t = today()
        conceptos = {"flete_por_ctnr": "Flete internacional", "locales_por_ctnr": "Gastos en destino",
                     "origen_por_ctnr": "Gastos en origen"}
        section(f"Costo por contenedor · mes a mes {t.year}",
                "Mediana por contenedor (marítimo, todos los destinos del filtro) contra el mismo mes de "
                f"{t.year - 1}. Rojo = subió; verde = bajó. * mes en curso.")
        c1, c2 = st.columns(2, gap="small")
        with c1:
            col = st.segmented_control("Concepto", list(conceptos), default="flete_por_ctnr", format_func=conceptos.get,
                                       key="co_concepto_mes", label_visibility="collapsed") or "flete_por_ctnr"
        with c2:
            tipo = st.segmented_control("Contenedor", ["40ST/40HQ", "20ST", "40NOR"], default="40ST/40HQ",
                                        key="co_flete_mes_tipo", label_visibility="collapsed") or "40ST/40HQ"
        base = h_all if h_all is not None else h
        if col != "flete_por_ctnr" and col in base:
            base = base[base[col] > 0]          # sin el gasto cargado no entra en la mediana
        sla_view.flete_mes_matrix(cs.concepto_mes(base, tipo, t.year, col), t)



    c1, c2 = st.columns(2, gap="medium")
    with c1, guard("Costo mensual"):
        chart_title("Costo logístico por mes", "USD por mes de ETD · marítimo y aéreo")
        m = p.assign(mes=calc.month_start(p["etd"]))
        months = sorted(m["mes"].unique())[-12:]
        if not months:
            empty()
        else:
            fig = go.Figure()
            for i, (col, label) in enumerate(COST_PARTS):
                s = m.groupby("mes")[col].apply(lambda x: x.clip(lower=0).sum()).reindex(months).fillna(0)
                fig.add_bar(x=month_labels(pd.Series(months)), y=s.values, name=label,
                            marker=dict(color=settings.SERIES[i], cornerradius=3),
                            hovertemplate=f"%{{x}} · {label}: USD %{{y:,.0f}}<extra></extra>")
            fig.update_layout(barmode="stack")
            charts.theme(fig, y_title="USD")
            charts.show(fig, key="co_mes")
    with c2, guard("Concentración"):
        chart_title("Concentración del gasto", "Flete internacional del período por agente · los 5 principales")
        f = p.assign(forwarder=p["forwarder"].fillna("Sin agente")).groupby("forwarder")["flete_pagado"] \
            .apply(lambda x: x.clip(lower=0).sum()).sort_values(ascending=False)
        tot = float(f.sum())
        if not tot:
            empty()
        else:
            top = f.head(5)
            fig = charts.hbar(top.index, (top / tot * 100).values, x_suffix=" %",
                              text=[f"{v / tot:.0%} · {fmt.fmt_usd(v)}" for v in top.values],
                              hover="%{y}: %{x:.0f} % del flete<extra></extra>", height=300)
            fig.update_xaxes(range=[0, float(top.iloc[0] / tot * 100) * 1.7])
            charts.show(fig, key="co_concentracion")
            lider = f.index[0]
            st.caption(f"{lider} concentra {f.iloc[0] / tot:.0%} del flete; los 3 primeros, "
                       f"{f.head(3).sum() / tot:.0%}." + (" Dependencia alta: ver alertas en Tarifas."
                                                          if f.iloc[0] / tot > settings.OPORT_CONCENTRACION else ""))

    # Detalle para investigar (no es un indicador): queda plegado al final.
    with st.expander("¿Dónde se va el gasto? · detalle por agente, puerto, medio, contenedor, línea o responsable"):
        st.markdown("<div class='section-sub'>Por dimensión, ordenado por gasto. Hacé clic en una fila para ver sus embarques.</div>", unsafe_allow_html=True)
        with guard("Gasto por dimensión"):
            nombres = dict(DIMS)
            dim = st.segmented_control("Ver por", list(nombres), default="forwarder", format_func=nombres.get,
                                       key="co_dim", label_visibility="collapsed") or "forwarder"
            tb = cs.por_dimension(p, dim, p_prev)
            if tb.empty:
                empty()
            else:
                show = pd.DataFrame({
                    nombres[dim]: tb["grupo"], "Embarques": tb["embarques"].map(lambda v: fmt.fmt_int(v)),
                    "Gasto (USD)": tb["gasto"].map(lambda v: fmt.fmt_int(v)),
                    "% del gasto": (tb["pct_gasto"] * 100).round(0),
                    "Flete / cont. (USD)": tb["flete_ctnr"].map(lambda v: fmt.fmt_int(v) if v == v else None), "Costo / FOB": tb["incidencia"].map(lambda v: fmt.fmt_pct(v, 1) if v == v else None),
                    "vs cotizaciones": (tb["vs_mercado"] * 100).round(0),
                })
                config = {
                    "Gasto (USD)": st.column_config.TextColumn("Gasto (USD)"),
                    "% del gasto": st.column_config.ProgressColumn("% del gasto", format="%d %%", min_value=0, max_value=100),
                    "Flete / cont. (USD)": st.column_config.TextColumn("Flete / cont. (USD)", help="Mediana, solo marítimo"),
                    "Costo / FOB": st.column_config.TextColumn("Costo / FOB"),
                    "vs cotizaciones": st.column_config.NumberColumn("vs cotizaciones", format="%+d %%",
                                                                help="Flete pagado vs mediana de nuestras cotizaciones del mes, "
                                                                     "ponderado por contenedores. Negativo = debajo"),
                }
                if tb["delta_ctnr"].notna().any():
                    show["Δ flete / cont. (USD)"] = tb["delta_ctnr"].map(
                        lambda v: ("+" if v > 0 else "") + fmt.fmt_int(v) if v == v else None)
                    config["Δ flete / cont. (USD)"] = st.column_config.TextColumn(
                        "Δ flete / cont. (USD)", help="Contra el mismo período del año anterior")
                ev = st.dataframe(show, column_config=config, hide_index=True, width="stretch",
                                  height=min(420, 38 + 35 * len(show)), on_select="rerun", selection_mode="single-row",
                                  key=f"co_tabla_{dim}", placeholder="—")
                filas = ev.selection.rows if ev is not None and hasattr(ev, "selection") else []
                i = filas[0] if filas and filas[0] < len(tb) else 0
                grupo = tb.iloc[i]["grupo"]
                c = cs.casos(p, dim, grupo).sort_values("costo", ascending=False)
                st.markdown(f'<div class="section-sub"><b>{fmt.plural(len(c), "embarque")} · '
                            f'{nombres[dim].lower()}: {grupo}</b></div>', unsafe_allow_html=True)
                data_table(c, [
                    ColSpec("embarque", "Embarque"), ColSpec("medio", "Medio"), ColSpec("etd", "ETD", "date"),
                    ColSpec("forwarder", "Agente"), ColSpec("puerto", "Puerto"), ColSpec("tipo_ctnr", "Tipo"),
                    ColSpec("contenedores", "Cont.", "int"), ColSpec("flete_pagado", "Flete (USD)", "usd"),
                    ColSpec("flete_por_ctnr", "Flete / cont.", "usd"), ColSpec("mercado_mes", "Cotizaciones / cont.", "usd"),
                    ColSpec("vs_mercado", "vs cotizaciones", "pct"), ColSpec("gastos_origen", "Origen (USD)", "usd"),
                    ColSpec("gastos_locales", "Locales (USD)", "usd"), ColSpec("costo", "Costo total (USD)", "usd"),
                    ColSpec("responsable", "Responsable"),
                ], key=f"co_casos_{dim}", filename="gasto_por_embarque", search=len(c) > 12)


def _mercado(bundle, t: pd.Timestamp) -> None:
    """Comparativa del flete de mercado mes a mes (como el reporte de fletes de la gerencia): año en curso con la
    variación contra el mes anterior, y los últimos 13 meses para ver cada mes contra el mismo del año anterior."""
    section("¿Cómo se mueve el flete de mercado?",
            "Mediana de «Valor Flete» de «Cotizaciones Maritimos Negociado» por mes de «Validez Quincena Desde»: "
            "todas las tarifas cotizadas (todos los puertos y agentes, no se aplican los filtros). Mismo criterio que el "
            "reporte de fletes de la gerencia. Rojo = subió; verde = bajó. * mes en curso.")
    c1, c2 = st.columns(2, gap="small")
    with c1:
        tipo = st.segmented_control("Contenedor", ["40ST/40HQ", "20ST", "40NOR"], default="40ST/40HQ",
                                    key="co_mkt_tipo", label_visibility="collapsed") or "40ST/40HQ"
    with c2:
        vistas = {"ytd": f"Año {t.year} · mes a mes", "yoy": "Últimos 13 meses · vs año anterior"}
        vista = st.segmented_control("Vista", list(vistas), default="ytd", format_func=vistas.get,
                                     key="co_mkt_vista", label_visibility="collapsed") or "ytd"
    mm = memo(bundle, ("mercado_mes", tipo, t), lambda: cs.mercado_mes(bundle.get("cotizaciones"), tipo, t))
    if mm.empty:
        empty("No hay cotizaciones cargadas para este contenedor.")
        return
    actual = t.to_period("M").to_timestamp()
    if vista == "ytd":
        d = mm[mm["mes"].dt.year == t.year]
        var_col, var_nombre = "var_mes", "vs mes anterior"
    else:
        d = mm[mm["mes"] >= actual - pd.DateOffset(months=12)]
        var_col, var_nombre = "var_anio", "vs año anterior"
    if d.empty:
        empty()
        return
    etiqueta = [fmt.fmt_month(m) + ("*" if m == actual else "") for m in d["mes"]]

    def celda_var(v) -> str:
        if v != v:
            return "<td class='na'>—</td>"
        cls = "bad" if v > 0.005 else "ok" if v < -0.005 else ""
        return f"<td class='{cls}'>{'▲' if v > 0 else '▼' if v < 0 else '='} {fmt.fmt_pct(abs(v))}</td>"

    filas = []
    for lab, (_, r) in zip(etiqueta, d.iterrows()):
        extra = (f"<td>{fmt.fmt_usd(r['anio_ant'], compact=False)}</td>" if vista == "yoy" else "")
        filas.append(f"<tr><th class='rowh'>{esc(lab)}</th><td>{fmt.fmt_usd(r['mediana'], compact=False)}"
                     f"<span class='n'>{fmt.plural(int(r['n']), 'tarifa')}</span></td>{extra}"
                     f"{celda_var(r[var_col])}</tr>")
    cab = ("<th>Período</th><th>Mediana flete</th>" + ("<th>Mismo mes año ant.</th>" if vista == "yoy" else "")
           + f"<th>{var_nombre}</th>")
    g1, g2 = st.columns([2, 3] if vista == "ytd" else [1, 1], gap="medium")
    with g1:
        st.markdown(f"<div class='scorecard matriz compact'><table><thead><tr>{cab}</tr></thead>"
                    f"<tbody>{''.join(filas)}</tbody></table></div>", unsafe_allow_html=True)
    with g2:
        fig = go.Figure()
        colores = [settings.SERIES[0] if (vista == "ytd" or m.year == t.year) else settings.SERIES[1] for m in d["mes"]]
        fig.add_bar(x=etiqueta, y=d["mediana"], marker=dict(color=colores, cornerradius=3),
                    text=[fmt.fmt_usd(v, compact=False).replace("USD ", "") for v in d["mediana"]],
                    textposition="outside", textfont=dict(size=11), constraintext="none", cliponaxis=False,
                    name="Mediana", hovertemplate="%{x}: USD %{y:,.0f}<extra></extra>")
        if vista == "ytd" and d["anio_ant"].notna().any():
            fig.add_scatter(x=etiqueta, y=d["anio_ant"], mode="markers", name=f"Mismo mes {t.year - 1}",
                            marker=dict(color=settings.SERIES[3], size=16, symbol="line-ew-open",
                                        line=dict(width=3, color=settings.SERIES[3])),
                            hovertemplate=f"%{{x}} · {t.year - 1}: USD %{{y:,.0f}}<extra></extra>")
        charts.theme(fig, y_title="USD por contenedor", legend=vista == "ytd", height=max(360, 57 * len(d) + 20))
        fig.update_yaxes(range=[0, float(pd.concat([d["mediana"], d["anio_ant"]]).max()) * 1.18])
        if vista == "yoy":
            fig.update_layout(title=dict(text=f"Azul oscuro = {t.year} · azul claro = {t.year - 1}",
                                         font=dict(size=11, color=settings.COLORS["slate"]), x=0.01, y=0.98))
        charts.show(fig, key=f"co_mkt_{vista}")


def _puente(h, h_all, ventana) -> None:
    """Puente volumen / mezcla / precio del flete marítimo pagado contra el mismo período del año anterior."""
    t = today()
    if h_all is None or h_all.empty:
        return
    if ventana:
        cur, prev = h, h_all[h_all["etd"].between(*ventana)]
        txt = "el período elegido vs el mismo período del año anterior"
    else:
        cur = h_all[h_all["etd"].dt.year == t.year]
        prev = h_all[(h_all["etd"].dt.year == t.year - 1) & (h_all["etd"] <= t - pd.DateOffset(years=1))]
        txt = f"{t.year} a la fecha vs el mismo tramo de {t.year - 1}"
    r = cs.puente(prev, cur)
    section("¿Por qué cambió el flete pagado?",
            f"Flete internacional marítimo, {txt}. Volumen = más o menos contenedores; mezcla = otro reparto entre "
            "20 ST, 40 ST/HQ y 40 NOR; precio = cada equipo más caro o más barato. Usa promedios por equipo para que "
            "las partes sumen exacto (es la única excepción a la mediana).")
    if not r:
        empty("Falta uno de los dos períodos para comparar.")
        return
    c1, c2 = st.columns([3, 2], gap="medium")
    with c1:
        fig = go.Figure(go.Waterfall(
            x=["Año anterior", "Volumen", "Mezcla", "Precio", "Actual"],
            measure=["absolute", "relative", "relative", "relative", "total"],
            y=[r["base"], r["volumen"], r["mezcla"], r["precio"], r["final"]],
            text=[fmt.fmt_usd(r["base"]), *(("+" if v > 0 else "−") + fmt.fmt_usd(abs(v))
                                            for v in (r["volumen"], r["mezcla"], r["precio"])), fmt.fmt_usd(r["final"])],
            textposition="outside", connector=dict(line=dict(color="#CBD2D9", width=1)),
            increasing=dict(marker=dict(color="#D64545")), decreasing=dict(marker=dict(color="#2F9E6E")),
            totals=dict(marker=dict(color=settings.SERIES[0])),
            hovertemplate="%{x}: USD %{y:,.0f}<extra></extra>"))
        charts.theme(fig, y_title="USD", legend=False)
        charts.show(fig, key="co_puente")
    with c2:
        d = r["final"] - r["base"]
        kpi_row([
            KPI("Variación del flete", ("+" if d > 0 else "−") + fmt.fmt_usd(abs(d)),
                status="bad" if d > 0 else "ok",
                sub=f"{fmt.fmt_int(r['q0'])} → {fmt.fmt_int(r['q1'])} contenedores"),
            KPI("Por precio", ("+" if r["precio"] > 0 else "−") + fmt.fmt_usd(abs(r["precio"])),
                status="bad" if r["precio"] > 0 else "ok",
                sub="lo que depende de la tarifa: es la parte que se negocia"),
        ], columns=1)


def _pagado_vs_mercado_chart(bundle, h) -> None:
    tipos = fletes_pagados.TIPOS
    tipo = st.segmented_control("Tipo de contenedor", tipos, default=tipos[0], key="co_tipo",
                                label_visibility="collapsed") or tipos[0]
    if h is None or h.empty:
        empty()
        return
    tt = h[(h["tipo_ctnr"] == tipo) & (h["destino"] == "Argentina")].assign(mes=lambda x: calc.month_start(x["etd"]))
    cot = bundle.get("cotizaciones")
    cot_ar = cot[cot["destino"] == "Argentina"] if cot is not None and "destino" in cot else None
    mk = freight.market_by_month(cot_ar) if cot_ar is not None else pd.DataFrame()
    mk = mk[mk["tipo_ctnr"] == tipo].set_index("mes") if len(mk) else mk
    months = sorted(tt["mes"].unique())[-12:]
    if not months:
        empty(f"No hay embarques {tipo} con flete cargado en el período.")
        return
    x = month_labels(pd.Series(months))
    paid = tt.groupby("mes")["flete_por_ctnr"].median().reindex(months)
    fig = go.Figure()
    fig.add_scatter(x=x, y=paid.values, name="Pagado (mediana)", mode="lines+markers",
                    line=dict(color=settings.SERIES[0], width=2.5), marker=dict(size=8),
                    hovertemplate="Pagado: USD %{y:,.0f}<extra></extra>")
    if len(mk):
        fig.add_scatter(x=x, y=mk["mercado"].reindex(months).values, name="Mediana de cotizaciones", mode="lines+markers",
                        line=dict(color=settings.SERIES[1], width=2), marker=dict(size=8),
                        hovertemplate="Cotizaciones (mediana): USD %{y:,.0f}<extra></extra>")
        fig.add_scatter(x=x, y=mk["mejor"].reindex(months).values, name="Mejor cotización", mode="lines",
                        line=dict(color=settings.SERIES[2], width=1.5, dash="dash"),
                        hovertemplate="Mejor: USD %{y:,.0f}<extra></extra>")
    charts.theme(fig, y_title="USD por contenedor")
    charts.show(fig, key="co_vs_mercado")


# ---------------------------------------------------------------------------
def _cuatro_ahorros(bundle, h, m, casos_neg, r, hay_sin, prev_txt="") -> None:
    """Los cuatro ahorros, separados para no contar dos veces: realizado (suma), negociado, por selección y potencial
    (no se suman: miden otra cosa)."""
    neg = negociacion(bundle)
    if len(neg) and len(h):
        neg = neg[(neg["validez_hasta"] >= h["etd"].min()) & (neg["validez_desde"] <= h["etd"].max())]
    rb = neg["rebaja_pct"][neg["rebaja_pct"] > 0] if len(neg) else pd.Series(dtype=float)
    sel = oport.por_seleccion(h, bundle.get("cotizaciones"))
    pot = m["op"][m["op"]["tipo"] == "Inmediata"] if m else pd.DataFrame()
    kpi_row([
        KPI("Realizado", fmt.fmt_usd(r["total"]), status="ok" if r["total"] > 0 else "", delta=prev_txt,
            tono="good" if prev_txt.startswith("▲") else ("bad" if prev_txt.startswith("▼") else "neutral"),
            sub="negociación de tarifas + uso de 40 NOR, sobre embarques ya pagados",
            help="Plata que efectivamente dejamos de pagar. Es la única de las cuatro que se acumula como resultado."),
        KPI("Negociado", (f"{fmt.fmt_pct(rb.median())}" if hay_sin and len(rb) else "—"),
            sub=(f"rebaja mediana sobre la tarifa original · n={fmt.fmt_int(len(rb))} tarifas rebajadas de "
                 f"{fmt.fmt_int(len(neg))}" if hay_sin else "Falta la solapa «SIN NEGOCIAR»"),
            help="Cuánto bajamos la tarifa al negociar, sin importar si después embarcamos con ella. Mide la "
                 "negociación, no el resultado (por eso no se suma)."),
        KPI("Por selección", fmt.fmt_usd(float(sel["ahorro"].sum())) if len(sel) else "—",
            status=("ok" if sel["ahorro"].sum() > 0 else "bad") if len(sel) else "",
            sub=(f"mediana {('+' if sel['ahorro'].median() > 0 else '')}{fmt.fmt_usd(sel['ahorro'].median(), compact=False)}"
                 f" por embarque · {fmt.fmt_pct((sel['ahorro'] > 0).mean())} eligió más barato · n="
                 f"{fmt.fmt_int(len(sel))}") if len(sel) else "Sin cotizaciones de otros agentes al zarpe",
            help="Para cada embarque: mediana de las tarifas de OTROS agentes vigentes al zarpe (misma ruta y "
                 "contenedor) menos lo que pagamos, × contenedores. Positivo = elegimos mejor que la alternativa típica. "
                 "No se suma al realizado (se superpone con la negociación)."),
        KPI("Potencial", fmt.fmt_usd(float(pot["ahorro_mes"].sum())) if len(pot) else "USD 0",
            sub=f"por mes · {fmt.fmt_int(len(pot))} rutas para renegociar hoy (ver Tarifas)",
            status="warn" if len(pot) else "ok",
            help="Si el agente actual iguala la mejor tarifa comparable, al ritmo de contenedores de los últimos "
                 f"{settings.NEGOCIAR_VENTANA_DIAS} días. Es plata por capturar, no capturada."),
    ], columns=4)
    if len(sel) or len(casos_neg):
        solo_descarga(sel.sort_values("ahorro"), [
            ColSpec("embarque", "Embarque"), ColSpec("etd", "ETD", "date"), ColSpec("forwarder", "Agente"),
            ColSpec("puerto", "Puerto"), ColSpec("tipo_ctnr", "Tipo"), ColSpec("contenedores", "Cont.", "int"),
            ColSpec("pagado", "Pagado / cont. (USD)", "usd"),
            ColSpec("alternativa", "Mediana otros agentes (USD)", "usd"),
            ColSpec("alternativas", "Agentes comparados", "int"), ColSpec("ahorro", "Ahorro por selección (USD)", "usd"),
        ], key="co_sel", filename="ahorro_por_seleccion", label="Descargar ahorro por selección por embarque")


def _captura(bundle, filters, h, ventana, m=None) -> None:
    from views._common import periodo_txt
    section("¿Cuánto capturamos?", f"Embarques marítimos zarpados {periodo_txt(filters)}.")
    st.markdown(
        '<div class="panel" style="margin-bottom:.8rem"><div class="panel-title">Cómo se lee</div>'
        '<div style="font-size:.88rem;line-height:1.55;color:var(--ink-2)">'
        '<b>1 · Negociación de tarifas:</b> (tarifa que cotizó el agente − tarifa negociada) × contenedores. '
        '<i>Ej.: cotizó USD 2.000, cerramos en USD 1.800 y mandamos 3 contenedores → USD 600.</i><br>'
        '<b>2 · 40 NOR:</b> lo que ahorramos por mandar la carga en 40 NOR en vez de 40 ST/HQ = (mediana pagada por un '
        '40 ST/HQ ese mes − lo pagado por el 40 NOR) × contenedores.<br>'
        '<b>3 · Certificación de flete:</b> flete internacional pagado − flete certificado = la parte del flete que no '
        'entra en la base de aduana.'
        '</div></div>', unsafe_allow_html=True)
    if h is None or h.empty:
        empty()
        return
    with guard("Captura"):
        neg = negociacion(bundle)
        casos_neg = cap.por_negociacion(h, neg)
        nor = freight.nor_savings(h)
        nor = nor.dropna(subset=["ahorro"]) if len(nor) else nor
        r = cap.resumen(casos_neg, nor)
        hay_sin = bundle.get("cot_sin_negociar") is not None and len(bundle.get("cot_sin_negociar"))
        prev_txt = ""
        if ventana:
            hp = filtered(bundle, "historicas", filters, use_period=False)
            hp = hp[hp["modo"].isin(MODOS_MARITIMOS) & hp["etd"].between(*ventana) & (hp["flete_pagado"] > 0)]
            nor_p = freight.nor_savings(hp)
            r0 = cap.resumen(cap.por_negociacion(hp, neg), nor_p.dropna(subset=["ahorro"]) if len(nor_p) else nor_p)
            d = r["total"] - r0["total"]
            prev_txt = (f"{'▲' if d > 0 else '▼' if d < 0 else '='} {fmt.fmt_usd(abs(d))} vs mismo período del año "
                        f"anterior ({fmt.fmt_usd(r0['total'])})")
        sin_base = int(h["embarque"].nunique()) - int(r["neg_emb"]) if hay_sin else 0
        d_cert = h[(h["flete_pagado"] > 0) & (h["flete_certificado"] > 0)] if "flete_certificado" in h else h.iloc[0:0]
        fuera = float((d_cert["flete_pagado"] - d_cert["flete_certificado"]).clip(lower=0).sum())
        kpi_row([
            KPI("1 · Negociación de tarifas", fmt.fmt_usd(r["negociacion"]) if hay_sin else "—",
                status="ok" if hay_sin and r["negociacion"] > 0 else "",
                sub=(f"total del período · <b>{fmt.fmt_int(r['neg_emb'])}</b> embarques con su tarifa negociada · "
                     f"{fmt.fmt_int(sin_base)} sin base comparable (no suman)" if hay_sin else
                     "Falta la solapa «Cotizaciones Maritimos SIN NEGOCIAR»"),
                help="(Tarifa sin negociar − tarifa negociada) × contenedores, para los embarques cuyo flete pagado "
                     f"coincide (± {fmt.fmt_pct(cap.TOLERANCIA)}) con una tarifa negociada vigente al zarpe del mismo "
                     "forwarder, puerto y tipo de contenedor."),
            KPI("2 · 40 NOR en vez de 40 ST/HQ", fmt.fmt_usd(r["nor"]), status="ok" if r["nor"] > 0 else "",
                sub=f"total del período · <b>{fmt.fmt_int(r['nor_cont'])}</b> contenedores 40 NOR",
                help="(Mediana pagada por un 40 ST/HQ ese mes − flete pagado por el 40 NOR) × contenedores. Un mes "
                     "puede dar negativo si el 40 NOR salió más caro."),
            KPI("Ahorro en flete (1 + 2)", fmt.fmt_usd(r["total"]), delta=prev_txt,
                tono="good" if prev_txt.startswith("▲") else ("bad" if prev_txt.startswith("▼") else "neutral"),
                sub="negociación + 40 NOR: lo que dejamos de pagar de flete"),
            KPI("3 · Certificación de flete", fmt.fmt_usd(fuera), status="ok" if fuera > 0 else "",
                sub=f"flete pagado − flete certificado · {fmt.fmt_int(len(d_cert))} embarques · fuera de la base "
                    "de aduana (detalle abajo)",
                help="Suma de (Flete Int PAGADO − Flete Certificado). No se suma al ahorro en flete: es lo que sale de "
                     "la base imponible de aduana."),
        ])
        with guard("Certificación de flete"):
            _certificacion(h)
        g = cap.mensual(casos_neg, nor)
        if len(g):
            chart_title("Captura por mes", "USD por mes de ETD y fuente · la línea es el acumulado del período")
            x = month_labels(g["mes"])
            fig = go.Figure()
            fig.add_bar(x=x, y=g["negociacion"], name="Negociación de tarifas",
                        marker=dict(color=settings.SERIES[0], cornerradius=3),
                        hovertemplate="%{x} · negociación: USD %{y:,.0f}<extra></extra>")
            fig.add_bar(x=x, y=g["nor"], name="40 NOR", marker=dict(color=settings.SERIES[1], cornerradius=3),
                        hovertemplate="%{x} · 40 NOR: USD %{y:,.0f}<extra></extra>")
            fig.add_scatter(x=x, y=g["acumulado"], name="Acumulado", mode="lines+markers", yaxis="y2",
                            line=dict(color=settings.SERIES[2], width=2),
                            hovertemplate="%{x} · acumulado: USD %{y:,.0f}<extra></extra>")
            fig.update_layout(barmode="stack", yaxis2=dict(overlaying="y", side="right", showgrid=False,
                                                           tickformat=",.0f", rangemode="tozero"))
            charts.theme(fig, y_title="USD por mes")
            charts.show(fig, key="co_captura_mes")
    with guard("Captura por trimestre"):
        t = today()
        qq = cap.por_trimestre(casos_neg, nor, t.year)
        q_act = f"Q{(t.month - 1) // 3 + 1}"
        chart_title(f"Resultado por trimestre · {t.year}", "Negociación de tarifas + uso de 40 NOR · * en curso")
        kpi_row([KPI(f"{r['q']}{'*' if r['q'] == q_act else ''} · captura", fmt.fmt_usd(r["total"]),
                     status="ok" if r["total"] > 0 else ("bad" if r["total"] < 0 else ""),
                     sub=f"negociación {fmt.fmt_usd(r['negociacion'])} · 40 NOR {fmt.fmt_usd(r['nor'])} "
                         f"({fmt.fmt_int(r['nor_cont'])} cont.)") for _, r in qq.iterrows()], columns=4)

    with guard("Captura por agente"):
        ag = cap.por_agente(h, casos_neg, nor)
        chart_title("Captura por agente", "Ordenado por captura total del período")
        data_table(ag, [
            ColSpec("agente", "Agente"), ColSpec("negociacion", "1 · Negociación (USD)", "usd"),
            ColSpec("nor", "2 · 40 NOR (USD)", "usd"), ColSpec("total", "Captura total (USD)", "usd"),
            ColSpec("embarques", "Embarques del período", "int"),
            ColSpec("con_tarifa", "Embarques con tarifa negociada", "int"),
        ], key="co_cap_agente", filename="captura_por_agente", search=False)

    with guard("Descargas captura"):
        partes = []
        if len(casos_neg):
            partes.append(casos_neg.assign(v=casos_neg["captura"])[["forwarder", "mes", "v"]])
        if len(nor):
            partes.append(nor.assign(v=nor["ahorro"])[["forwarder", "mes", "v"]])
        if partes:
            mm = pd.concat(partes, ignore_index=True).assign(forwarder=lambda x: x["forwarder"].fillna("Sin agente"))
            pv = mm.pivot_table(index="forwarder", columns="mes", values="v", aggfunc="sum", fill_value=0)
            pv = pv.loc[pv.sum(axis=1).sort_values(ascending=False).index]
            pv.loc["Total"] = pv.sum()
            pv["Total"] = pv.sum(axis=1)
            pv.columns = [fmt.fmt_month(c).capitalize() if c != "Total" else c for c in pv.columns]
            pv = pv.reset_index().rename(columns={"forwarder": "Agente"})
            solo_descarga(pv, [ColSpec("Agente", "Agente")] + [ColSpec(c, c, "usd") for c in pv.columns[1:]],
                          key="co_cap_mes_agente", filename="captura_mes_por_agente",
                          label="Descargar captura mes por agente")
        c1, c2 = st.columns(2, gap="medium")
        with c1:
            solo_descarga(casos_neg, [
                ColSpec("embarque", "Embarque"), ColSpec("etd", "ETD", "date"), ColSpec("forwarder", "Agente"),
                ColSpec("puerto", "Puerto"), ColSpec("tipo_ctnr", "Tipo"), ColSpec("contenedores", "Cont.", "int"),
                ColSpec("flete_original", "Sin negociar (USD)", "usd"),
                ColSpec("flete_negociado", "Negociada (USD)", "usd"), ColSpec("flete_por_ctnr", "Pagado (USD)", "usd"),
                ColSpec("captura", "Captura (USD)", "usd"),
            ], key="co_neg", filename="captura_negociacion", label="Descargar embarques con tarifa negociada")
        with c2:
            solo_descarga(nor, [
                ColSpec("embarque", "Embarque"), ColSpec("etd", "ETD", "date"), ColSpec("forwarder", "Agente"),
                ColSpec("puerto", "Puerto"), ColSpec("contenedores", "Cont.", "int"),
                ColSpec("ref_hq", "Mediana 40 ST/HQ del mes (USD)", "usd"),
                ColSpec("flete_por_ctnr", "Pagado 40 NOR (USD)", "usd"), ColSpec("ahorro", "Ahorro (USD)", "usd"),
            ], key="co_nor", filename="captura_40nor", label="Descargar embarques 40 NOR")


# ---------------------------------------------------------------------------
def _lista_acciones(op: pd.DataFrame, al: pd.DataFrame) -> pd.DataFrame:
    """Una sola lista de qué hacer: las rutas para renegociar o sin cotización (oportunidades) y las alertas, sin
    repetir la misma ruta como «Poca competencia» cuando ya figura como «Falta cotización»."""
    filas = []
    for _, r in op[op["tipo"].isin(["Inmediata", "Investigar"])].iterrows():
        renegociar = r["tipo"] == "Inmediata"
        filas.append({
            "tipo": r["tipo"], "prioridad": r["prioridad"],
            "situacion": "Renegociar tarifa" if renegociar else "Falta cotización",
            "sujeto": r["ruta"],
            "detalle": (f"{r['agente']} {fmt.fmt_usd(r['tarifa_actual'], compact=False)} vs {r['mejor_agente']} "
                        f"{fmt.fmt_usd(r['mejor'], compact=False)} · {r['contenedores']:.0f} cont."
                        if renegociar else f"{r['contenedores']:.0f} cont. en {settings.NEGOCIAR_VENTANA_DIAS} días"),
            "usd": r["ahorro_mes"] if renegociar else np.nan, "accion": r["accion"]})
    falta = {f["sujeto"] for f in filas if f["situacion"] == "Falta cotización"}
    for _, r in al.iterrows():
        if r["situacion"] == "Poca competencia" and r["sujeto"] in falta:
            continue
        filas.append({"tipo": r["tipo"], "prioridad": "Alta" if r["tipo"] == "Inmediata" else
                      "Media" if r["tipo"] == "Investigar" else "Baja",
                      "situacion": r["situacion"], "sujeto": r["sujeto"], "detalle": r["detalle"], "usd": r["usd"],
                      "accion": r["accion"]})
    t = pd.DataFrame(filas, columns=["tipo", "prioridad", "situacion", "sujeto", "detalle", "usd", "accion"])
    if t.empty:
        return t
    orden_t = {"Inmediata": 0, "Investigar": 1, "Seguimiento": 2}
    orden_p = {"Alta": 0, "Media": 1, "Baja": 2}
    return t.assign(_t=t["tipo"].map(orden_t), _p=t["prioridad"].map(orden_p).fillna(3)) \
        .sort_values(["_t", "_p", "usd"], ascending=[True, True, False], na_position="last") \
        .drop(columns=["_t", "_p"]).reset_index(drop=True)


def _tarifas(bundle, h, m=None, h_all=None, a=None, sub: str = "hacer") -> None:
    """Tarifas en tres vistas: qué renegociar esta semana, cómo vienen las tarifas y si nos cobran lo negociado."""
    t = today()
    dias = settings.NEGOCIAR_VENTANA_DIAS
    if sub == "mercado":
        _cotizaciones_cuadro(bundle, h, t, dias)
        with guard("Flete de mercado"):
            _mercado(bundle, t)
        with guard("Pagado vs mercado"):
            section("Flete por contenedor: pagado vs cotizaciones del mes",
                    "Marítimo, destino Argentina · mediana pagada vs mediana y mejor de nuestras cotizaciones del mes "
                    "(son tarifas negociadas por nosotros, no un índice de mercado)")
            _pagado_vs_mercado_chart(bundle, h)
        with st.expander("Todas las cotizaciones: mapa de tarifas y evolución del mercado"):
            cotizaciones.render()
        return
    if sub == "negociacion":
        _adherencia(m)
        _validacion(h, a)
        return

    section("¿Qué hacemos esta semana con las tarifas?",
            f"Rutas marítimas destino Argentina usadas en los últimos {dias} días. Se compara solo contra tarifas "
            "comparables: mismo puerto, contenedor y quincena, mismo pagadero, mismo servicio (directo / trasbordo) y "
            f"tránsito dentro de ± {settings.OPORT_TT_TOL} días. Solo flete por contenedor, en USD.")
    if h is None or h.empty or not m:
        empty()
        return
    with guard("Acciones de mayor impacto"):
        _acciones(m)
    op, adh, al = m["op"], m["adh"], m["al"]
    with guard("KPIs de tarifas"):
        inm = op[op["tipo"] == "Inmediata"]
        rec = adh[adh["etd"] >= t - pd.Timedelta(days=90)] if len(adh) else adh
        pm = rec[rec["pago_mas"]] if len(rec) else rec
        uno = op[op["agentes"] <= 1]
        kpi_row([
            KPI("Rutas para renegociar ya", fmt.fmt_int(len(inm)), status="warn" if len(inm) else "ok",
                sub=f"de <b>{fmt.fmt_int(len(op))}</b> rutas usadas · diferencia ≥ "
                    f"{fmt.fmt_pct(settings.OPORT_UMBRAL_PCT)} y ≥ USD {settings.OPORT_UMBRAL_USD} por contenedor"),
            KPI("Ahorro potencial", fmt.fmt_usd(float(inm["ahorro_mes"].sum())), unit="/ mes",
                status="warn" if len(inm) else "ok", sub="si el agente actual iguala la mejor comparable",
                help="(Tarifa del agente principal − mejor tarifa comparable de otro agente) × contenedores por mes "
                     f"de los últimos {dias} días, en las rutas para renegociar."),
            KPI("Pagamos más de lo cotizado", fmt.fmt_pct(len(pm) / len(rec)) if len(rec) else "—",
                status=("bad" if len(pm) / len(rec) > 0.1 else "warn" if len(pm) else "ok") if len(rec) else "",
                sub=(f"{fmt.fmt_int(len(pm))} de {fmt.fmt_int(len(rec))} embarques (90 d) · "
                     f"<b>{fmt.fmt_usd(float(pm['exceso'].sum()))}</b> por encima") if len(rec) else
                    "Sin embarques con cotización vigente al zarpe",
                help="Flete pagado por contenedor contra la tarifa que ese mismo agente cotizó para la ruta y "
                     f"contenedor, vigente a la ETD. Cuenta si supera la más alta de sus tarifas en más de "
                     f"{fmt.fmt_pct(settings.OPORT_ADHERENCIA_TOL)}."),
            KPI("Rutas con un solo agente", fmt.fmt_int(len(uno)), status="warn" if len(uno) else "ok",
                sub="sin competencia en la quincena en curso: pedir más cotizaciones"),
        ])

    with guard("Lista de acciones"):
        lista = _lista_acciones(op, al)
        section("Lista de acciones", "Todo lo que hay que hacer, en una sola lista y por orden: 🔴 Inmediata (esta "
                "semana) · 🟡 Investigar (falta un dato o una cotización) · 🔵 Seguimiento (mirar la tendencia).")
        if lista.empty:
            empty("Sin acciones pendientes con el criterio actual.")
        else:
            res = lista.groupby(["tipo", "situacion"]).size().reset_index(name="n")
            orden = {"Inmediata": 0, "Investigar": 1, "Seguimiento": 2}
            res = res.assign(_o=res["tipo"].map(orden)).sort_values(["_o", "n"], ascending=[True, False])
            st.markdown("<div class='chips'>" + "".join(
                f"<span class='chip {esc(r['tipo'].lower())}'>{esc(r['situacion'])} <b>{r['n']}</b></span>"
                for _, r in res.iterrows()) + "</div>", unsafe_allow_html=True)
            ver_todo = st.toggle("Ver también Seguimiento", value=False, key="co_lista_seg")
            v = lista if ver_todo else lista[lista["tipo"] != "Seguimiento"]
            data_table(v.assign(tipo=v["tipo"].map(TIPO_ICON), prioridad=v["prioridad"].map(PRIO_ICON).fillna("")), [
                ColSpec("tipo", "Tipo"), ColSpec("prioridad", "Prioridad"), ColSpec("situacion", "Qué pasa"),
                ColSpec("sujeto", "Ruta / agente"), ColSpec("detalle", "Detalle", width="medium"),
                ColSpec("usd", "USD", "usd"), ColSpec("accion", "Qué hacer", width="large"),
            ], key="co_lista", filename=f"acciones_tarifas_{t:%Y%m%d}", search=len(v) > 12,
                height=min(460, 38 + 35 * len(v)), caption="USD: ahorro por mes si se renegocia, o lo pagado de más "
                                                            "para reclamar.")

    with st.expander("Detalle por ruta: tarifa actual, mejor comparable, objetivo y vencimiento"):
        with guard("Oportunidades"):
            ver = st.segmented_control("Ver", ["accion", "todas"], default="accion", key="co_op_ver",
                                       format_func={"accion": "Para actuar", "todas": "Todas las rutas"}.get,
                                       label_visibility="collapsed") or "accion"
            o = op if ver == "todas" else op[op["tipo"].isin(["Inmediata", "Investigar"])]
            o = o.assign(prioridad=o["prioridad"].map(PRIO_ICON).fillna(""), tipo=o["tipo"].map(TIPO_ICON))
            data_table(o, [
                ColSpec("prioridad", "Prioridad"), ColSpec("tipo", "Tipo"), ColSpec("puerto", "Ruta (POL)"),
                ColSpec("tipo_ctnr", "Equipo"), ColSpec("contenedores", f"Cont. {dias} d", "int"),
                ColSpec("agente", "Agente actual"), ColSpec("tarifa_actual", "Tarifa actual", "usd"),
                ColSpec("mejor", "Mejor comparable", "usd"), ColSpec("mejor_agente", "La ofrece"),
                ColSpec("dif_usd", "Diferencia (USD)", "usd"), ColSpec("dif_pct", "Diferencia %", "pct"),
                ColSpec("ahorro_mes", "Ahorro potencial / mes", "usd"), ColSpec("negociar_con", "Negociar con"),
                ColSpec("objetivo", "Tarifa objetivo", "usd"), ColSpec("vence", "Vence", "date"),
                ColSpec("agentes", "Agentes que cotizan", "int"), ColSpec("confianza", "Confianza"),
                ColSpec("accion", "Acción", width="large"),
                ColSpec("motivo_no_comparable", "Menor no comparable"),
            ], key=f"co_oport_{ver}", filename=f"oportunidades_{t:%Y%m%d}", search=len(o) > 12)


def _adherencia(m) -> None:
    t = today()
    with guard("Adherencia"):
        section("¿Pagamos lo que nos cotizaron?",
                "Por agente, últimos 12 meses: flete pagado por contenedor contra la tarifa que ese agente cotizó para "
                "la ruta y contenedor vigente al zarpe (ETD). Se compara contra la más alta de sus tarifas, para no "
                "marcar de más.")
        adh = m["adh"] if m else pd.DataFrame()
        pa = oport.adherencia_por_agente(adh) if len(adh) else pd.DataFrame()
        if pa.empty:
            empty("Sin embarques con cotización propia vigente al zarpe.")
            return
        data_table(pa, [
            ColSpec("forwarder", "Agente"), ColSpec("embarques", "Embarques comparados", "int"),
            ColSpec("pago_mas", "Pagaron más", "int"), ColSpec("pct", "% pagaron más", "pct"),
            ColSpec("dif_med", "Diferencia mediana / cont.", "usd"), ColSpec("exceso", "Exceso total (USD)", "usd"),
        ], key="co_adh_ag", filename="adherencia_por_agente", search=False)
        solo_descarga(adh[adh["pago_mas"]], [
            ColSpec("embarque", "Embarque"), ColSpec("etd", "ETD", "date"), ColSpec("forwarder", "Agente"),
            ColSpec("puerto", "Puerto"), ColSpec("tipo_ctnr", "Tipo"), ColSpec("contenedores", "Cont.", "int"),
            ColSpec("pagado", "Pagado / cont. (USD)", "usd"), ColSpec("cotizado", "Cotizado / cont. (USD)", "usd"),
            ColSpec("dif_pct", "Diferencia %", "pct"), ColSpec("exceso", "Exceso (USD)", "usd"),
            ColSpec("responsable", "Responsable"),
        ], key="co_adh_casos", filename=f"pagamos_mas_que_lo_cotizado_{t:%Y%m%d}",
            label="Descargar embarques que pagaron más que lo cotizado")


def _cotizaciones_cuadro(bundle, h, t, dias) -> None:
    from utils import negociar
    cot = bundle.get("cotizaciones")
    section("Cotizaciones: ruta × agente",
            "Tarifas de «Cotizaciones Maritimos Negociado» (destino Argentina) para las rutas que usamos en los "
            f"últimos {dias} días. La mejor tarifa es la menor. Verde = la menor de la ruta; ● = el agente con el que más "
            "embarcamos esa ruta. Por contenedor, en USD. Este cuadro compara todas las tarifas; la tabla de "
            "oportunidades, solo las comparables.")
    with guard("Cotizaciones"):
        cur = negociar.periodo(cot, t, "curso")
        prox = negociar.periodo(cot, t, "proxima")
        rango = lambda c: (f"{c['validez_desde'].min():%d/%m} – {c['validez_hasta'].max():%d/%m}"  # noqa: E731
                           if len(c) else "sin tarifas")
        opciones = {"curso": f"En curso ({rango(cur)})", "proxima": f"Próximas ({rango(prox)})"}
        cual = st.segmented_control("Período", list(opciones), default="curso", format_func=opciones.get,
                                    key="co_cot_periodo", label_visibility="collapsed") or "curso"
        todas = st.toggle("Ver también rutas que no usamos", value=False, key="co_cot_todas")
        m, agentes = negociar.matriz(h, cot, t, cual, dias, solo_nuestras=not todas)
        if m.empty:
            empty("Todavía no hay cotizaciones cargadas para las próximas quincenas." if cual == "proxima" else
                  "No hay cotizaciones vigentes para nuestras rutas.")
            return
        var = m["var"].median()
        st.caption(f"{fmt.fmt_int(len(negociar.periodo(cot, t, cual)))} tarifas de {fmt.fmt_int(len(agentes))} agentes"
                   + (f" · la menor tarifa de cada ruta {'subió' if var > 0 else 'bajó'} {fmt.fmt_pct(abs(var))} "
                      "(mediana) contra el período anterior" if var == var else ""))
        sla_view.cotizaciones_matrix(m, agentes)
        solo_descarga(m, [ColSpec("puerto", "Puerto"), ColSpec("tipo_ctnr", "Contenedor"),
                          ColSpec("contenedores", f"Cont. {dias} d", "int"), ColSpec("agente", "Agente principal")]
                      + [ColSpec(a, a, "usd") for a in agentes]
                      + [ColSpec("menor", "Menor (USD)", "usd"), ColSpec("menor_agente", "La ofrece"),
                         ColSpec("menor_linea", "Línea"), ColSpec("var", "vs anterior", "pct"),
                         ColSpec("negociar", "Con quién negociar")],
                      key=f"co_cot_{cual}", filename=f"cotizaciones_{cual}_{t:%Y%m%d}",
                      label="Descargar cuadro")


def _equipos(h) -> None:
    """Costo por equipo (por m³), espacio vacío y sobrecosto IMO comparable."""
    section("¿Qué equipo nos conviene?", "Marítimo, embarques zarpados del período. El flete por m³ cargado compara "
            "equipos de distinto tamaño: es lo que pagamos por cada m³ que viajó. Todo por mediana.")
    if h is None or h.empty:
        empty()
        return
    with guard("Costo por equipo"):
        eq = cs.equipos(h)
        if eq.empty:
            empty("Sin m³ cargados para calcular costo por m³.")
        else:
            show = pd.DataFrame({
                "Equipo": eq["equipo"], "Contenedores": eq["contenedores"].map(fmt.fmt_int),
                "Flete / cont. (USD)": eq["flete_ctnr"].map(lambda v: fmt.fmt_int(v)),
                "Capacidad (m³)": eq["capacidad"].map(lambda v: fmt.fmt_num(v, 0) if v == v else "—"),
                "Ocupación": eq["ocupacion"].map(lambda v: fmt.fmt_pct(v) if v == v else "—"),
                "m³ cargados / cont.": eq["m3_cargado"].map(lambda v: fmt.fmt_num(v, 1)),
                "USD por m³ cargado": eq["flete_m3"].map(lambda v: fmt.fmt_num(v, 1)),
                "USD por m³ de capacidad": eq["flete_m3_cap"].map(lambda v: fmt.fmt_num(v, 1) if v == v else "—"),
                "n embarques": eq["n"].map(fmt.fmt_int),
            })
            st.dataframe(show, hide_index=True, width="stretch", height=38 + 35 * len(show))
        u = settings.OCUPACION_UMBRAL
        ev = cs.espacio_vacio(h, u)
        imo = cs.imo_sobrecosto(h)
        kpi_row([
            KPI(f"Embarques con ocupación < {fmt.fmt_pct(u)}", fmt.fmt_int(ev["bajos"]),
                status="warn" if ev["bajos"] else "ok",
                sub=f"{fmt.fmt_pct(ev['pct'])} de {fmt.fmt_int(ev['n'])} embarques con m³ y capacidad · "
                    f"{fmt.fmt_int(ev['cont_bajos'])} contenedores"),
            KPI("Flete pagado por espacio vacío", fmt.fmt_usd(ev["usd_vacio"]), status="warn" if ev["usd_vacio"] else "",
                sub="flete × (1 − ocupación) en esos embarques · es una cota: no toda carga se puede consolidar"),
            KPI("Sobrecosto IMO comparable",
                ("+" if imo.get("dif_med", 0) > 0 else "") + fmt.fmt_usd(imo["dif_med"], compact=False)
                if imo.get("n_celdas") else "—",
                sub=(f"mediana por contenedor ({fmt.fmt_pct(imo['pct_med'])}) · misma ruta, equipo y mes · "
                     f"n={fmt.fmt_int(imo['n_celdas'])} comparaciones") if imo.get("n_celdas") else
                    "Sin meses con carga IMO y no IMO en la misma ruta y equipo"),
        ], columns=3)
        if ev["bajos"]:
            c = ev["casos"].assign(vacio=lambda x: x["flete_pagado"] * (1 - x["ocup"].clip(upper=1)))
            solo_descarga(c.sort_values("vacio", ascending=False), [
                ColSpec("embarque", "Embarque"), ColSpec("etd", "ETD", "date"), ColSpec("forwarder", "Agente"),
                ColSpec("puerto", "Puerto"), ColSpec("tipo_ctnr", "Tipo"), ColSpec("contenedores", "Cont.", "int"),
                ColSpec("m3", "m³", "num"), ColSpec("ocup", "Ocupación", "pct"),
                ColSpec("flete_pagado", "Flete (USD)", "usd"), ColSpec("vacio", "Flete por espacio vacío (USD)", "usd"),
                ColSpec("responsable", "Responsable"),
            ], key="co_vacio", filename="contenedores_con_espacio_vacio", label="Descargar contenedores con espacio vacío")


# ---------------------------------------------------------------------------
def _cert_aereo(aa, cert_a) -> KPI:
    """Aéreo: sin objetivo; el estado lo da la tendencia (último mes cerrado vs primer mes con certificación)."""
    from views.resumen import _cert_tendencia
    if aa is None or aa.empty:
        return KPI("Certificado · aéreo", "—", badge="Sin objetivo")
    k = _cert_tendencia(aa, lambda d: (float(d["flete_certificado"].sum() / d["flete_pagado"].sum())
                                       if len(d) and d["flete_pagado"].sum() else float("nan")))
    return KPI("Certificado · aéreo", fmt.fmt_pct(cert_a), badge="Sin objetivo", status=k.status,
               sub=(f"{k.value} último mes cerrado · " + k.sub) if k.value != "—" else "Se espera que baje")


def _validacion(h, a) -> None:
    section("Validación de fletes y certificación", "Resultado de la validación de Logística Internacional y "
                                                    "flete certificado por fuera.")
    if h is None or h.empty:
        empty()
        return
    with guard("Validación"):
        v = h["resultado_validacion"].fillna("Sin validar").value_counts()
        cert_m, n_m = fletes_pagados._cert(h)
        aa = a[(a["etd"] <= today()) & (a["flete_pagado"] > 0)] if a is not None and len(a) else None
        cert_a = float(aa["flete_certificado"].sum() / aa["flete_pagado"].sum()) if aa is not None and len(aa) else float("nan")
        st_m, b_m = cert_status(cert_m) if n_m >= settings.MIN_SAMPLE else ("", "")
        kpi_row([
            KPI("Validados", fmt.fmt_int(v.get("Validado", 0)), sub=fmt.fmt_pct(v.get("Validado", 0) / len(h))
                + " de los embarques marítimos"),
            KPI("Observados", fmt.fmt_int(v.get("Observado", 0)), status="warn" if v.get("Observado", 0) else "",
                sub=f"Con diferencia o datos faltantes · <b>{fmt.fmt_int(v.get('Sin validar', 0))}</b> sin validar"),
            KPI("Certificado · marítimo", fmt.fmt_pct(cert_m), status=st_m, badge=b_m,
                sub=cert_sub() + " · certificado / pagado"),
            _cert_aereo(aa, cert_a),
        ])
        cols = [ColSpec("embarque", "Embarque"), ColSpec("etd", "ETD", "date"), ColSpec("forwarder", "Agente"),
                ColSpec("responsable", "Responsable (analista)"), ColSpec("resultado_validacion", "Resultado"),
                ColSpec("motivo_observacion", "Motivo", width="medium"),
                ColSpec("flete_pagado", "Flete pagado (USD)", "usd"), ColSpec("flete_cotizado", "Flete cotizado (USD)", "usd"),
                ColSpec("gastos_origen", "Origen (USD)", "usd"), ColSpec("gastos_locales", "Locales (USD)", "usd")]
        pend = bandeja.pendientes_validar(h, today())
        obs = h[h["resultado_validacion"] == "Observado"].sort_values("etd", ascending=False)
        c1, c2 = st.columns(2, gap="medium")
        with c1:
            solo_descarga(pend, cols, key="co_pend", filename=f"fletes_pendientes_de_validar_{today():%Y%m%d}",
                          label="Descargar pendientes de validar")
            st.caption("Para reclamar a cada analista: embarques zarpados sin resultado de validación.")
        with c2:
            solo_descarga(obs, cols, key="co_obs", filename=f"fletes_observados_{today():%Y%m%d}",
                          label="Descargar observados")
            st.caption("Para reclamar a cada agente el ajuste. También están en la Bandeja de acción.")
