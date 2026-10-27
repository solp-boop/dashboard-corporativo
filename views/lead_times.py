"""Tiempos (nivel 2): situación → ¿qué lo explica? → operaciones.

Cinco pestañas: marítimo (consolidación), aéreo punta a punta, tránsito y puertos, time to market y cargas DG / IMO.
Lo zarpado incluye lo que ya salió y sigue en Reservas.
"""
from __future__ import annotations

import re

import numpy as np
import pandas as pd
import streamlit as st

from components import sla as sla_view
from components.drill import diagnostico
from components.kpi_cards import KPI, kpi_row
from components.layout import chart_title, coverage, empty, guard, require, section, semaforo_legend
from components.tables import ColSpec, data_table, solo_descarga
from config import settings
from utils import calculations as calc
from utils import data_cleaning as dc
from utils import diagnostico as dg
from utils import formatting as fmt
from utils import panorama as pan
from utils import objetivo, productos, sla
from views._common import ctx, filtered, memo, today

ETAPAS = [
    ("dias_comex", "Comex: packeo → instrucción"),
    ("dias_agente", "Agente: instrucción → ETD"),
    ("dias_consolidacion", "Consolidación: packeo → ETD"),
    ("dias_tt", "Tránsito: ETD → ETA"),
    ("dias_total", "Total: fin de producción → ETA"),
]

# Tramos del punta a punta aéreo, con quién es dueño de cada uno (orden real de los hitos en la planilla).
TRAMOS_AEREO = [
    ("dias_packeo_wh", "Origen · packeo → WH"),
    ("dias_wh_instr", "Bidcom · WH → instrucción"),
    ("dias_instr_etd", "Agente · instrucción → ETD"),
    ("dias_etd_eta", "Agente · vuelo ETD → ETA"),
    ("dias_eta_caldas", "Argentina · ETA → Caldas"),
]

DIMS_MAR = [
    dg.Dimension("puerto", "Puerto"), dg.Dimension("forwarder", "Agente"),
    dg.Dimension("proveedores", "Proveedor", multiple=True), dg.Dimension("categories", "Category manager", multiple=True),
    dg.Dimension("responsable", "Responsable"), dg.Dimension("estructura", "Mono / consolidado"),
    dg.Dimension("booking", "Modalidad de booking"), dg.Dimension("tipo_carga", "Tipo de carga"),
    dg.Dimension("imo", "IMO / DG"), dg.Dimension("tipo_demora", "Causa"),
]
DIMS_TT = [
    dg.Dimension("puerto", "Puerto"), dg.Dimension("forwarder", "Agente"), dg.Dimension("linea", "Línea marítima"),
    dg.Dimension("tipo_carga", "Tipo de carga"),
]



# ---------------------------------------------------------------------------
# Preparación
# ---------------------------------------------------------------------------
def _ventana_prev(filters, t: pd.Timestamp) -> tuple[pd.Timestamp, pd.Timestamp] | None:
    """Mismo período del año anterior (None si el período no tiene inicio)."""
    if not filters.start:
        return None
    end = min(pd.Timestamp(filters.end), t) if filters.end else t
    return pd.Timestamp(filters.start) - pd.DateOffset(years=1), end - pd.DateOffset(years=1)


def _fuente_so(bundle) -> pd.DataFrame | None:
    """Embarque → SO, proveedor, category: Embarques Históricos (cerrados) + Planificación (en curso)."""
    partes = []
    eh, pl = bundle.get("emb_hist"), bundle.get("planif")
    if eh is not None and len(eh):
        partes.append(eh[[c for c in ("embarque", "so", "proveedor", "category") if c in eh]])
    if pl is not None and len(pl) and "embarque" in pl:
        p = pl.rename(columns={"category_manager": "category"})
        partes.append(p[[c for c in ("embarque", "so", "proveedor", "category") if c in p]])
    return pd.concat(partes, ignore_index=True, sort=False) if partes else None


def _maritimo_ops(bundle, filters, t, use_period=True) -> pd.DataFrame:
    h = filtered(bundle, "historicas", filters, use_period=use_period)
    r = filtered(bundle, "reservas", filters, use_period=use_period) if bundle.get("reservas") is not None else None
    z = sla.zarpados_con_reservas(h, r, t)
    z = dg.unir_emb_hist(z, None, indice=memo(bundle, "indice_so", lambda: dg.indice_emb_hist(_fuente_so(bundle))))
    z["imo"] = _imo(z)
    z["obj_tt"] = z["sla_tt"].where(z["sla_puerto_definido"].fillna(False).astype(bool)) \
        if "sla_puerto_definido" in z else np.nan
    return z


def _imo(d: pd.DataFrame) -> pd.Series:
    """«Carga IMO / DG», «Sin IMO» o «Sin dato». Reservas no tiene «DG»: se toma «CARGA IMO» (SI / NO)."""
    v = d["dg"].astype(object) if "dg" in d else pd.Series(None, index=d.index, dtype=object)
    if "carga_imo" in d:
        txt = d["carga_imo"].map(lambda x: dc.fold(x) if isinstance(x, str) else "")
        v = v.where(v.notna(), txt.map({"si": True, "no": False}))
    def etiqueta(x):
        if x is None or x is pd.NA or (isinstance(x, float) and np.isnan(x)):
            return dg.SIN_DATO
        return "Carga IMO / DG" if bool(x) else "Sin IMO"
    return v.map(etiqueta)


def _tipo_label(t) -> str:
    return sla_view.TIPO_LABEL.get(t, str(t).title()) if isinstance(t, str) else "Sin SLA"


def _aereo_ops(a: pd.DataFrame) -> pd.DataFrame:
    d = a.copy()
    d["tipo_label"] = d["tipo_sla"].map(_tipo_label) if "tipo_sla" in d else "Sin dato"
    if {"f_instruccion", "f_ingreso_wh", "etd"} <= set(d.columns):
        # Si se instruyó antes de que la carga llegara al WH, ese tiempo es de origen: el agente empieza a
        # contar desde lo último entre instrucción e ingreso al WH, y «WH → instrucción» no baja de 0.
        inicio = d[["f_instruccion", "f_ingreso_wh"]].max(axis=1)
        d["dias_instr_etd"] = (d["etd"] - inicio).dt.days.where(lambda x: x.between(0, 90))
        d["dias_wh_instr"] = (d["f_instruccion"] - d["f_ingreso_wh"]).dt.days.clip(lower=0).where(lambda x: x <= 90)
    d["imo"] = _imo(d)
    d["sla_vig"] = d["sla_aereo"].where(d["sla_vigente"].fillna(False).astype(bool)) if "sla_vigente" in d else np.nan
    tramos = [c for c, _ in TRAMOS_AEREO if c in d]
    nombres = dict(TRAMOS_AEREO)
    d["tramo_largo"] = None
    if tramos and len(d):
        con = d[tramos].notna().any(axis=1)
        if con.any():
            d.loc[con, "tramo_largo"] = d.loc[con, tramos].clip(lower=0).idxmax(axis=1).map(nombres)
    for raw, col in (("f_fondos_raw", "f_fondos"), ("f_oficializacion_raw", "f_oficializacion")):
        d[col] = dc.parse_dates(d[raw])[0] if raw in d else pd.NaT
    d["dias_eta_fondos"] = (d["f_fondos"] - d["eta"]).dt.days.where(lambda s: s.between(-5, 90))
    d["dias_eta_ofic"] = (d["f_oficializacion"] - d["eta"]).dt.days.where(lambda s: s.between(-5, 90))
    return d


def _kpi(i: pan.Indicador) -> KPI:
    return KPI(i.nombre, i.valor, unit=i.unidad, sub=i.sub, status=i.estado, badge=i.badge, help=i.ayuda,
               delta=i.delta, tono=i.tono)


def _mediana_delta(d_all: pd.DataFrame, col: str, t: pd.Timestamp) -> tuple[str, str]:
    last = t.to_period("M").to_timestamp() - pd.offsets.MonthBegin(1)
    prev = last - pd.offsets.MonthBegin(1)
    mes = calc.month_start(d_all["etd"])
    a, b = d_all.loc[mes == last, col].dropna(), d_all.loc[mes == prev, col].dropna()
    if len(a) < settings.MIN_SAMPLE or len(b) < settings.MIN_SAMPLE:
        return "", ""
    diff = a.median() - b.median()
    m = lambda x: fmt.fmt_month(x, long=True).split()[0].lower()  # noqa: E731
    flecha = "▲" if diff > 0 else ("▼" if diff < 0 else "=")
    return f"{flecha} {fmt.fmt_int(abs(diff))} d {m(last)} vs {m(prev)}", ("bad" if diff > 0 else "good" if diff < 0 else "neutral")


# ---------------------------------------------------------------------------
def render() -> None:
    bundle, filters = ctx()
    if require(bundle, "historicas") is None:
        return
    t = today()
    # Se dibuja solo la vista elegida (con pestañas se calculaban las cuatro en cada interacción).
    vistas = {"maritimo": "Marítimo · consolidación", "aereo": "Aéreo · punta a punta",
              "transito": "Tránsito y puertos", "ttm": "Time to market", "dg": "Cargas DG / IMO"}
    # ?vista=aereo (desde las tarjetas de Panorama) abre directo en esa vista.
    pedida = st.query_params.get("vista")
    if pedida in vistas and pedida != st.session_state.get("_tiempos_qp"):
        st.session_state["tiempos_vista"] = pedida
    st.session_state.setdefault("tiempos_vista", "maritimo")
    vista = st.segmented_control("Vista", list(vistas), format_func=vistas.get, key="tiempos_vista",
                                 label_visibility="collapsed") or "maritimo"
    st.session_state["_tiempos_qp"] = vista
    if st.query_params.get("vista") != vista:
        st.query_params["vista"] = vista
    ventana = _ventana_prev(filters, t)
    z = z_all = z_prev = None
    if vista in ("maritimo", "transito", "dg"):
        with guard("Preparación de tiempos marítimos"):
            # Solo destino Argentina (o sin destino cargado): así tarjetas, tablas y Panorama dan lo mismo.
            from utils.tiempos_mes import solo_argentina
            z = solo_argentina(_maritimo_ops(bundle, filters, t))
            z_all = solo_argentina(_maritimo_ops(bundle, filters, t, use_period=False))
            z_prev = z_all[z_all["etd"].between(*ventana)] if ventana else None
        if z is None:
            return
    if vista == "maritimo":
        _maritimo(bundle, filters, z, z_all, z_prev)
    elif vista == "aereo":
        _aereo(bundle, filters, ventana)
    elif vista == "transito":
        _transito(bundle, filters, z, z_all, z_prev)
    elif vista == "dg":
        _cargas_dg(bundle, filters, z, t)
    else:
        _time_to_market(bundle, filters, ventana)


# ---------------------------------------------------------------------------
# Marítimo
# ---------------------------------------------------------------------------
CASOS_MAR = [
    ColSpec("embarque", "Embarque"), ColSpec("sos", "SO"), ColSpec("proveedores", "Proveedor"),
    ColSpec("forwarder", "Agente"), ColSpec("responsable", "Responsable"), ColSpec("puerto", "Puerto"),
    ColSpec("estructura", "Estructura"), ColSpec("f_packeo_min", "Packeo", "date"), ColSpec("etd", "ETD", "date"),
    ColSpec("dias_consolidacion", "Consolidación (d)", "days"), ColSpec("sla_consolidacion", "SLA (d)", "days"),
    ColSpec("_exc", "Excedidos (d)", "days"), ColSpec("tipo_demora", "Causa"),
    ColSpec("observaciones", "Observaciones", width="large"),
]


def _maritimo(bundle, filters, z, z_all, z_prev) -> None:
    t = today()
    section("Consolidación marítima",
            f"Packeo mínimo → ETD contra el SLA: monoproveedor según la ETD ({calc.sla_mono_txt()}), consolidado "
            f"según el puerto (por defecto {settings.SLA_CONSOLIDACION_DEFAULT} d). Incluye lo que ya zarpó y sigue "
            "en Reservas.")
    if z.empty:
        empty()
        return
    with guard("Situación marítima"):
        d = z.dropna(subset=["dias_consolidacion"])
        fuera = d[d["dias_consolidacion"] > d["sla_consolidacion"]]
        delta, tono = _mediana_delta(z_all, "dias_consolidacion", t)
        causas = fuera["tipo_demora"].dropna()
        top = causas.value_counts()
        kpi_row([
            _kpi(pan.sla_consolidacion(z, z_all, t)),
            KPI("Consolidación (mediana)", fmt.fmt_int(d["dias_consolidacion"].median()) if len(d) else "—", "d",
                sub=f"P75 {fmt.fmt_int(d['dias_consolidacion'].quantile(.75))} d · P90 "
                    f"{fmt.fmt_int(d['dias_consolidacion'].quantile(.9))} d · n={fmt.fmt_int(len(d))}" if len(d) else "",
                delta=delta, tono=tono, help="Mediana de días de packeo mínimo → ETD. La flecha compara el último mes "
                                              "cerrado con el anterior."),
            KPI("Fuera de SLA", fmt.fmt_int(len(fuera)), status="bad" if len(fuera) else "ok",
                sub=(f"se pasan <b>{fmt.fmt_int((fuera['dias_consolidacion'] - fuera['sla_consolidacion']).median())} d"
                     f"</b> (mediana) · {fmt.fmt_pct(len(causas) / len(fuera))} con causa cargada") if len(fuera) else ""),
            KPI("Causa principal", top.index[0] if len(top) else "—",
                sub=f"<b>{fmt.fmt_pct(top.iloc[0] / len(causas))}</b> de los fuera de SLA con causa" if len(top) else
                "Sin causas cargadas", help="«Tipo de demora» más frecuente entre los embarques fuera de SLA."),
        ])
    with guard("Etapas por mes"):
        section("Tiempo de consolidación · mes a mes",
                "Consolidación (packeo mínimo → ETD) por mes de ETD: mínimo, mediana y máximo, solo destino Argentina. "
                "100 % = todos los embarques. SLA = el definido: monoproveedor según la ETD ("
                f"{calc.sla_mono_txt()}), consolidado según el puerto (mediana del mes). «% en SLA» = embarques dentro del "
                "SLA (verde si llega al "
                f"{fmt.fmt_pct(settings.CUMPLIMIENTO_OBJETIVO)}). * mes en curso.")
        base = z[z["destino"].isna() | (z["destino"] == "Argentina")] if "destino" in z else z
        estructura = st.segmented_control("Estructura", ["100 %", "Monoproveedor", "Consolidado"], default="100 %",
                                          key="tm_mar_estructura", label_visibility="collapsed") or "100 %"
        if estructura != "100 %":
            base = base[base["estructura"] == estructura]
        x = base.dropna(subset=["etd", "dias_consolidacion"]).assign(mes=lambda d: calc.month_start(d["etd"]))
        if x.empty:
            empty()
        else:
            g = x.groupby("mes")

            def sla_txt(d):
                mono = d.loc[d["estructura"] == "Monoproveedor", "sla_consolidacion"].median()
                cons = d.loc[d["estructura"] == "Consolidado", "sla_consolidacion"].median()
                partes = ([f"Mono {fmt.fmt_int(mono)} d"] if mono == mono and estructura != "Consolidado" else []) + \
                         ([f"Conso {fmt.fmt_int(cons)} d"] if cons == cons and estructura != "Monoproveedor" else [])
                return " · ".join(partes)
            tab = pd.DataFrame({
                "sla_txt": g.apply(sla_txt, include_groups=False),
                "n": g.size(), "cons_min": g["dias_consolidacion"].min(), "cons_med": g["dias_consolidacion"].median(),
                "cons_max": g["dias_consolidacion"].max(),
                "pct_sla": g.apply(lambda d: (d["dias_consolidacion"] <= d["sla_consolidacion"])[
                    d["sla_consolidacion"].notna()].mean(), include_groups=False),
            }).reset_index()
            tot = {"mes": pd.NaT, "n": len(x), "sla_txt": "", "cons_min": x["dias_consolidacion"].min(),
                   "cons_med": x["dias_consolidacion"].median(), "cons_max": x["dias_consolidacion"].max(),
                   "pct_sla": (x["dias_consolidacion"] <= x["sla_consolidacion"])[x["sla_consolidacion"].notna()].mean()}
            sla_view.mes_matrix(pd.concat([tab, pd.DataFrame([tot])], ignore_index=True),
                                [("cons_min", "Mín."), ("cons_med", "Mediana"), ("cons_max", "Máx.")], t,
                                resaltar=["cons_med"], pct=("pct_sla", "% en SLA"), textos=[("sla_txt", "SLA")])

    section("Análisis para descargar",
            "Elegí la dimensión y bajá el Excel: resumen por esa dimensión y detalle de cada embarque.")
    with guard("Diagnóstico marítimo"):
        diagnostico(z, DIMS_MAR, "dias_consolidacion", "sla_consolidacion", key="tm_mar", casos_cols=CASOS_MAR,
                    prev=z_prev, prev_txt="el mismo período del año anterior", unidad="embarques")



def _cierre_maritimo(bundle, filters, z: pd.DataFrame) -> None:
    with guard("Cierre de mes"):
        st.markdown('<div class="section-sub"><b>Cierre de mes</b> · el período, los dos últimos meses cerrados y '
                    'cómo viene el mes en curso</div>', unsafe_allow_html=True)
        sc = sla.scorecard(filtered(bundle, "historicas", filters, use_period=False),
                           filtered(bundle, "reservas", filters, use_period=False),
                           z, today(), lambda m: fmt.fmt_month(m, long=True).split()[0])
        sla_view.scorecard_table(sc)
        coverage(int(z["dias_consolidacion"].notna().sum()), len(z), "embarques del período con consolidación calculable")
    with guard("Tabla por puerto"):
        st.markdown('<div class="section-sub"><b>Tiempos por puerto de origen</b> · mediana real vs target de '
                    f'Validaciones, puertos con ≥ {settings.MIN_SAMPLE} embarques</div>', unsafe_allow_html=True)
        semaforo_legend()
        g = z.groupby("puerto").agg(
            embarques=("embarque", "count"),
            cons=("dias_consolidacion", "median"), tt=("dias_tt", "median"), total=("dias_total", "median"),
            sla_tt=("sla_tt", "median"), sla_total=("sla_total", "median"),
            definido=("sla_puerto_definido", "max"),
        ).reset_index()
        g["cumple"] = z.groupby("puerto").apply(
            lambda d: calc.cumplimiento(d["dias_consolidacion"], d["sla_consolidacion"])[0],
            include_groups=False).reindex(g["puerto"]).values
        g = g[g["embarques"] >= settings.MIN_SAMPLE].sort_values("embarques", ascending=False)
        sla_map = bundle.sla_puertos.set_index("puerto")["sla_consolidacion"] if not bundle.sla_puertos.empty else {}
        g["sla_cons"] = g["puerto"].map(sla_map).fillna(settings.SLA_CONSOLIDACION_DEFAULT)
        g["estado"] = calc.semaforo(g["total"], g["sla_total"])
        g["target"] = np.where(g["definido"].fillna(False).astype(bool), "Validaciones", "Por defecto")
        data_table(g, [
            ColSpec("puerto", "Puerto"), ColSpec("embarques", "Embarques", "int"),
            ColSpec("cons", "Consolidación (d)", "days"), ColSpec("sla_cons", "SLA consolidado (d)", "days"),
            ColSpec("cumple", "% cumple consol.", "pct"),
            ColSpec("tt", "Tránsito (d)", "days"), ColSpec("sla_tt", "Target tránsito (d)", "days"),
            ColSpec("total", "Total (d)", "days"), ColSpec("sla_total", "Target total (d)", "days"),
            ColSpec("estado", "Estado", "status"), ColSpec("target", "Origen del target"),
        ], key="sla_puertos", filename="tiempos_por_puerto", search=False)


# ---------------------------------------------------------------------------
# Tránsito
# ---------------------------------------------------------------------------
CASOS_TT = [
    ColSpec("embarque", "Embarque"), ColSpec("puerto", "Puerto"), ColSpec("forwarder", "Agente"),
    ColSpec("linea", "Línea"), ColSpec("etd", "ETD", "date"), ColSpec("eta", "ETA", "date"),
    ColSpec("dias_tt", "Tránsito (d)", "days"), ColSpec("obj_tt", "Objetivo (d)", "days"),
    ColSpec("_exc", "Excedidos (d)", "days"), ColSpec("responsable", "Responsable"),
]


def _transito(bundle, filters, z, z_all, z_prev) -> None:
    from utils import tiempos_mes as tm
    t = today()
    section("Tránsito marítimo · ETD → ETA",
            "Acá no hay objetivo: lo que se mira es que el tránsito no se disperse del que tenemos en Validaciones para "
            f"cada puerto («Transito ARG»; monoproveedor usa «-Monoproducto» si existe). Un embarque está en rango si "
            f"queda a ± {settings.TT_RANGO_DIAS} días de Validaciones; se levanta la mano cuando más del "
            f"{fmt.fmt_pct(settings.TT_ALERTA_FUERA)} queda fuera. Solo embarques que ya llegaron.")
    llego = lambda x: x[x["eta"] <= t].dropna(subset=["dias_tt"])  # noqa: E731 · ETA futura = estimada
    d = llego(z)
    if d.empty:
        empty("Sin embarques llegados en el período.")
        return
    with guard("Situación tránsito"):
        x = tm.con_desvio(d)
        con = x[x["rango"] != "Sin Validaciones"]
        fuera = con[con["rango"] != "En rango"]
        pf = len(fuera) / len(con) if len(con) else float("nan")
        delta, tono = _mediana_delta(llego(z_all), "dias_tt", t)
        puertos = tm.dispersion_puerto(llego(z_all), t)
        revisar = puertos[puertos["revisar"]]["puerto"].tolist() if len(puertos) else []
        q = d["dias_tt"].quantile([.25, .75])
        kpi_row([
            KPI("Tránsito (mediana)", fmt.fmt_int(d["dias_tt"].median()), "d", delta=delta, tono=tono,
                sub=f"P25–P75 {fmt.fmt_int(q[.25])}–{fmt.fmt_int(q[.75])} d · n={fmt.fmt_int(len(d))}"),
            KPI(f"Fuera de ± {settings.TT_RANGO_DIAS} d de Validaciones", fmt.fmt_pct(pf) if len(con) else "—",
                status=("bad" if pf > settings.TT_ALERTA_FUERA else "ok") if len(con) else "",
                badge=("Revisar" if pf > settings.TT_ALERTA_FUERA else "") if len(con) else "",
                sub=f"<b>{fmt.fmt_int((fuera['rango'] == 'Más largo').sum())}</b> más largos · "
                    f"<b>{fmt.fmt_int((fuera['rango'] == 'Más corto').sum())}</b> más cortos · de "
                    f"{fmt.fmt_int(len(con))} con Validaciones",
                help=f"Embarques cuyo tránsito se aleja más de {settings.TT_RANGO_DIAS} días (para arriba o para "
                     "abajo) del tránsito de Validaciones de su puerto. Rojo cuando pasa el "
                     f"{fmt.fmt_pct(settings.TT_ALERTA_FUERA)}."),
            KPI("Dispersión (P75 − P25)", fmt.fmt_int(q[.75] - q[.25]), "d",
                sub="ancho del 50 % central de los tránsitos: cuanto más chico, más previsible"),
            KPI("Puertos para revisar", fmt.fmt_int(len(revisar)), status="warn" if revisar else "ok",
                sub=", ".join(revisar[:3]) + (" …" if len(revisar) > 3 else "") if revisar else
                "últimos 3 meses cerrados, puertos con ≥ 5 embarques",
                help=f"Puertos con más del {fmt.fmt_pct(settings.TT_ALERTA_FUERA)} de los embarques fuera de "
                     f"± {settings.TT_RANGO_DIAS} días de Validaciones en los últimos 3 meses cerrados."),
        ])
    with guard("Tránsito mes a mes"):
        section("Tránsito · dispersión mes a mes (por ETA)",
                "Solo embarques que ya llegaron, por mes de llegada. P25 / P75 = el 25 % más rápido y el 25 % más lento; "
                f"«Fuera de ± {settings.TT_RANGO_DIAS} d» en rojo = hay que levantar la mano ese mes. * mes en curso.")
        lineas = ["Todas las líneas"] + list(d["linea"].map(tm.linea).value_counts().index) if "linea" in d \
            else ["Todas las líneas"]
        ln = st.selectbox("Línea marítima", lineas, key="tm_tt_linea")
        dd = d if ln == "Todas las líneas" else d[d["linea"].map(tm.linea) == ln]
        sla_view.dispersion_matrix(tm.dispersion_mes(dd), t)

    with guard("Punta a punta mono vs conso"):
        section("Punta a punta · mes a mes · monoproveedor vs consolidado (por ETA)",
                "Fin de producción → ETA, mediana por mes de llegada, solo destino Argentina y embarques que ya "
                "llegaron con fin de producción cargado. * mes en curso.")
        pp = tm.punta_a_punta_mes(llego(z_all[z_all["eta"].dt.year == t.year]) if "eta" in z_all else d)
        sla_view.punta_mes_matrix(pp, t)
        solo_descarga(llego(z_all[z_all["eta"].dt.year == t.year]).dropna(subset=["dias_total"]), [
            ColSpec("embarque", "Embarque"), ColSpec("estructura", "Estructura"), ColSpec("puerto", "Puerto"),
            ColSpec("forwarder", "Agente"), ColSpec("f_fin_produccion", "Fin de producción", "date"),
            ColSpec("etd", "ETD", "date"), ColSpec("eta", "ETA", "date"),
            ColSpec("dias_consolidacion", "Consolidación (d)", "days"), ColSpec("dias_tt", "Tránsito (d)", "days"),
            ColSpec("dias_total", "Punta a punta (d)", "days"), ColSpec("responsable", "Responsable"),
        ], key="tm_pp_casos", filename=f"punta_a_punta_{t:%Y%m%d}", label="Descargar embarques")

    with guard("Líneas marítimas"):
        section("Líneas marítimas · mes a mes (por ETA)",
                "¿Con qué línea llega la carga y cuánto tarda cada una? «% de la carga» = contenedores de cada línea "
                "sobre el total del mes (incluye lo que todavía viaja, por ETA estimada). «Tránsito» = mediana de lo "
                "que ya llegó; ▲ rojo = subió 5 días o más contra el mes anterior de la misma línea.")
        medida = st.segmented_control("Ver", ["% de la carga", "Tránsito (mediana)"], default="% de la carga",
                                      key="tm_tt_lineas_medida", label_visibility="collapsed") or "% de la carga"
        z_eta = z_all[z_all["eta"].dt.year == t.year] if "eta" in z_all else z_all
        g = tm.lineas_mes(z_eta.assign(dias_tt=z_eta["dias_tt"].where(z_eta["eta"] <= t)))
        sla_view.linea_mes_matrix(g, t, "pct" if medida.startswith("%") else "tt")

    with guard("Terminales"):
        section("Terminal de llegada · Buenos Aires (por ETA)",
                "% de los contenedores que llega a cada terminal, por mes de ETA. La planilla no tiene la terminal: "
                "se deduce de la línea marítima (información pública de octubre 2026). Hapag-Lloyd y ONE usan más de "
                "una terminal según el servicio, por eso van aparte. «Sin definir» = línea sin terminal conocida o "
                "embarque sin línea cargada.")
        mapa = settings.TERMINAL_POR_LINEA
        if not mapa:
            empty("Falta definir qué terminal usa cada línea marítima (la planilla no tiene la terminal). Cuando "
                  "esté la tabla línea → terminal, este cuadro se completa solo.")
        else:
            gt = g.assign(linea=g["linea"].map(lambda x: mapa.get(x, "Sin definir")))
            gt = gt[gt["linea"] != "Sin definir"] if st.toggle("Ocultar «Sin definir»", value=False,
                                                                   key="tm_tt_term_sin") else gt
            gt = gt.groupby(["linea", "mes"], as_index=False).agg(n=("n", "sum"), cont=("cont", "sum"),
                                                                 tt_med=("tt_med", "median"))
            gt["pct"] = gt["cont"] / gt.groupby("mes")["cont"].transform("sum")
            sla_view.linea_mes_matrix(gt, t, "pct", titulo="Terminal")

    with guard("Subas de tránsito"):
        subas = tm.subas_tt(d)
        section("Casos para preventa · tránsito más largo de lo esperado",
                "Embarques llegados que superaron el objetivo de su puerto, o la mediana de su línea de los 3 meses "
                "anteriores en 7 días o más. Se descargan en Excel.")
        solo_descarga(subas, [
            ColSpec("embarque", "Embarque"), ColSpec("sos", "SO"), ColSpec("linea_u", "Línea"),
            ColSpec("puerto", "Puerto"), ColSpec("forwarder", "Agente"), ColSpec("etd", "ETD", "date"),
            ColSpec("eta", "ETA", "date"), ColSpec("dias_tt", "Tránsito (d)", "days"),
            ColSpec("obj_tt", "Objetivo puerto (d)", "days"), ColSpec("vs_obj", "vs objetivo (d)", "days"),
            ColSpec("ref_linea", "Mediana línea 3 meses (d)", "days"), ColSpec("vs_linea", "vs línea (d)", "days"),
            ColSpec("responsable", "Responsable"),
        ], key="tm_tt_subas", filename=f"transito_mas_largo_{t:%Y%m%d}", label="Descargar casos")

    section("Análisis para descargar",
            "Elegí la dimensión y bajá el Excel: resumen por esa dimensión y detalle de cada embarque.")
    with guard("Diagnóstico tránsito"):
        diagnostico(d, DIMS_TT, "dias_tt", "obj_tt", key="tm_tt", casos_cols=CASOS_TT,
                    prev=llego(z_prev) if z_prev is not None else None,
                    prev_txt="el mismo período del año anterior", unidad="embarques")
    with st.expander("Dispersión por puerto · últimos 3 meses cerrados"):
        with guard("Tránsito por puerto"):
            sla_view.dispersion_matrix(tm.dispersion_puerto(llego(z_all), t), t, por="puerto")
            st.caption(f"Puertos con ≥ 5 embarques llegados. Rojo = más del {fmt.fmt_pct(settings.TT_ALERTA_FUERA)} "
                       f"fuera de ± {settings.TT_RANGO_DIAS} días del tránsito de Validaciones: revisar con el agente "
                       "o actualizar Validaciones.")


# ---------------------------------------------------------------------------
# Aéreo
# ---------------------------------------------------------------------------
CASOS_AER = [
    ColSpec("embarque", "Embarque"), ColSpec("tipo_label", "Tipo de negocio"), ColSpec("forwarder", "Agente"),
    ColSpec("aerolinea", "Aerolínea"), ColSpec("puerto", "Origen"), ColSpec("f_packeo_min", "Packeo", "date"),
    ColSpec("etd", "ETD", "date"),
    ColSpec("dias_packeo_wh", "Packeo→WH", "days"), ColSpec("dias_wh_instr", "WH→instr.", "days"),
    ColSpec("dias_instr_etd", "Instr.→ETD", "days"), ColSpec("dias_etd_eta", "Vuelo", "days"),
    ColSpec("dias_eta_caldas", "ETA→Caldas", "days"), ColSpec("dias_aereo", "Total (d)", "days"),
    ColSpec("sla_vig", "SLA (d)", "days"), ColSpec("_exc", "Excedidos (d)", "days"),
    ColSpec("tramo_largo", "Tramo más largo"), ColSpec("tipo_demora", "Causa"),
]


def _aereo(bundle, filters, ventana) -> None:
    if bundle.get("aereos") is None:
        empty("Sin datos de Seguimiento Aéreos.")
        return
    t = today()
    a_all = filtered(bundle, "aereos", filters)
    a = _aereo_ops(sla_view.air_zarpados(a_all, t))
    desde = pd.Timestamp(settings.SLA_AEREO_DESDE)

    section("Punta a punta · aéreo",
            "Packeo mínimo → ETA Caldas (columna «Total» de Seguimiento Aéreos). Cada embarque contra el SLA de su tipo "
            f"de negocio, vigente desde el {desde:%d/%m/%Y}.")
    with guard("KPIs punta a punta"):
        todos = _aereo_ops(sla_view.air_zarpados(filtered(bundle, "aereos", filters, use_period=False), t))
        vig = a[a["sla_vig"].notna()]
        fuera = vig[vig["dias_aereo"] > vig["sla_vig"]]
        por_dueno: dict[str, float] = {}
        for c, lbl in TRAMOS_AEREO:          # el agente tiene dos tramos: se suman
            if c in a:
                v = a[c].clip(lower=0).median()
                dueno = lbl.split(" · ")[0]
                por_dueno[dueno] = por_dueno.get(dueno, 0) + (v if v == v else 0)
        quien = max(por_dueno, key=por_dueno.get) if por_dueno else "—"
        kpi_row([
            _kpi(pan.punta_aereo(a, todos, t)),
            KPI("Fuera de SLA", fmt.fmt_int(len(fuera)), status="bad" if len(fuera) else "ok",
                sub=f"se pasan <b>{fmt.fmt_int((fuera['dias_aereo'] - fuera['sla_vig']).median())} d</b> (mediana)"
                if len(fuera) else "—"),
            KPI("¿De quién es el tiempo?", quien, sub=" · ".join(f"{k} {fmt.fmt_int(v)} d" for k, v in por_dueno.items()),
                help="Suma de las medianas de los tramos de cada responsable: Origen (packeo → WH), Bidcom "
                     "(WH → instrucción), Agente (instrucción → ETD y vuelo), Argentina (ETA → Caldas). Las medianas "
                     "se calculan por separado, así que la suma no es exactamente el total."),
            KPI("Liberación en Argentina", fmt.fmt_int(a["dias_eta_caldas"].median()) if a["dias_eta_caldas"].notna().any()
                else "—", "d",
                sub=(f"ETA → fondos {fmt.fmt_int(a['dias_eta_fondos'].median())} d (n={a['dias_eta_fondos'].notna().sum()})"
                     f" · → oficialización {fmt.fmt_int(a['dias_eta_ofic'].median())} d "
                     f"(n={a['dias_eta_ofic'].notna().sum()})") if a["dias_eta_ofic"].notna().any() else "ETA → Caldas",
                help="ETA → ETA Caldas (mediana). Debajo, cuánto tardan la acreditación de fondos y la oficialización "
                     "desde la ETA, cuando están cargadas (muchas dicen «No aplica»)."),
        ])
    from utils import tiempos_mes as tm
    with guard("Tipo de negocio por mes"):
        section("Mes a mes por tipo de negocio",
                "Mes de ETD. Verde = dentro del SLA del tipo; rojo = fuera. En gris e itálica, los meses anteriores al "
                f"{desde:%d/%m/%Y} (el SLA todavía no regía: solo referencia). La cantidad cuenta los embarques "
                "zarpados con «Total» cargado. * mes en curso.")
        medida = st.segmented_control("Medida", ["Días (mediana)", "% dentro del SLA", "Cantidad de embarques"],
                                      default="Días (mediana)", key="tm_aer_medida",
                                      label_visibility="collapsed") or "Días (mediana)"
        tabla = tm.tipo_por_mes(a.assign(_sla_tipo=a["sla_aereo"] if "sla_aereo" in a else np.nan),
                                sla="_sla_tipo")
        sla_view.tipo_mes_matrix(tabla, t, "pct" if medida.startswith("%") else
                                 "cant" if medida.startswith("Cantidad") else "dias")

    with guard("Tramos por mes"):
        section("¿En qué tramo se va el tiempo? · mes a mes",
                "Mediana de cada tramo por mes de ETD; resaltado, el tramo más largo del mes. Los tramos se miden por "
                "separado, así que no suman exactamente el total.")
        tipos = ["Todos"] + [x for x in [sla_view.TIPO_LABEL.get(k, k.title()) for k in settings.SLA_AEREO_POR_TIPO]
                             if x in set(a["tipo_label"])]
        elegido = st.selectbox("Tipo de negocio", tipos, key="tm_aer_tramo_tipo")
        sub = a if elegido == "Todos" else a[a["tipo_label"] == elegido]
        cols = [(c, lbl) for c, lbl in TRAMOS_AEREO if c in a]
        tab = tm.por_mes(sub, [c for c, _ in cols] + ["dias_aereo"])
        sla_view.mes_matrix(tab, cols, t, resaltar=[c for c, _ in cols], extra=[("dias_aereo", "Total punta a punta")])

    with guard("Descarga aéreo"):
        det = a.assign(mes=a["etd"].dt.strftime("%m/%Y"),
                       _sla_ref=a["sla_aereo"] if "sla_aereo" in a else np.nan)
        det["cumple"] = np.where(det["_sla_ref"].isna(), "", np.where(det["dias_aereo"] <= det["_sla_ref"], "Sí", "No"))
        det["_exc"] = (det["dias_aereo"] - det["_sla_ref"]).clip(lower=0)
        resumen = tabla.assign(mes_txt=pd.to_datetime(tabla["mes"]).dt.strftime("%m/%Y"))
        cols_det = [ColSpec("mes", "Mes ETD")] + CASOS_AER[:1] + [ColSpec("tipo_label", "Tipo de negocio")] + \
            [c for c in CASOS_AER[2:] if c.source not in ("sla_vig", "_exc")] + \
            [ColSpec("_sla_ref", "SLA del tipo (d)", "days"), ColSpec("cumple", "Dentro del SLA"),
             ColSpec("_exc", "Excedidos (d)", "days")]
        solo_descarga(det.sort_values(["etd"]), cols_det, key="tm_aer_det", filename=f"aereos_por_tipo_y_mes_{t:%Y%m%d}",
                      label="Descargar detalle por embarque, tipo y mes",
                      hojas={"Resumen tipo x mes": (resumen, [
                          ColSpec("tipo", "Tipo de negocio"), ColSpec("mes_txt", "Mes ETD"), ColSpec("n", "Embarques", "int"),
                          ColSpec("mediana", "Mediana (d)", "days"), ColSpec("sla", "SLA (d)", "days"),
                          ColSpec("dentro", "Dentro del SLA", "int"), ColSpec("pct", "% dentro", "pct")])})
        st.caption("El Excel trae una fila por embarque (tramos, total, SLA del tipo y si llegó) y una solapa con el "
                   "resumen tipo × mes. Antes del " f"{desde:%d/%m/%Y} el SLA es solo referencia.")


def _tramo_mas_largo(a: pd.DataFrame) -> str:
    """«Tramo · N d»: el tramo aéreo con la mediana más larga (lo usa el Resumen)."""
    med = {lbl: a[c].clip(lower=0).median() for c, lbl in TRAMOS_AEREO if c in a and a[c].notna().any()}
    if not med:
        return "—"
    lbl = max(med, key=med.get)
    return f"{lbl} · {fmt.fmt_int(med[lbl])} d"


# ---------------------------------------------------------------------------
# Time to market
# ---------------------------------------------------------------------------
CASOS_TTM = [
    ColSpec("so", "SO"), ColSpec("embarque", "Embarque"), ColSpec("proveedor", "Proveedor"),
    ColSpec("category", "Category manager"), ColSpec("grupo", "Grupo"), ColSpec("modo", "Modo"),
    ColSpec("estructura", "Estructura"), ColSpec("etd", "ETD", "date"), ColSpec("tiempo", "Consolidación (d)", "days"),
    ColSpec("objetivo", "Objetivo (d)", "days"), ColSpec("_exc", "Excedidos (d)", "days"),
]


def _por_so(du: pd.DataFrame, objetivo: float) -> pd.DataFrame:
    if du.empty:
        return pd.DataFrame(columns=["so", "tiempo"])
    agg = {"tiempo": ("tiempo_consolidacion", "median"), "embarque": ("embarque", "first"), "etd": ("etd", "max")}
    if "estructura" in du:
        agg["estructura"] = ("estructura", "first")
    for c in ("proveedor", "category"):
        if c in du:
            agg[c] = (c, "first")
    for c in ("es_nuevo", "es_top", "maritimo"):
        if c in du:
            agg[c] = (c, "max")
    g = du.groupby("so").agg(**agg).reset_index()
    nuevo = g["es_nuevo"].fillna(False).astype(bool) if "es_nuevo" in g else False
    top = g["es_top"].fillna(False).astype(bool) if "es_top" in g else False
    g["grupo"] = np.where(nuevo, "SKU nuevo", np.where(top, f"Top ranking (1–{settings.TOP_RANKING_MAX})", "Resto"))
    g["modo"] = np.where(g["maritimo"].fillna(False).astype(bool), "Marítimo", "Aéreo / otro") \
        if "maritimo" in g else "Sin dato"
    g["objetivo"] = objetivo
    return g


def _time_to_market(bundle, filters, ventana) -> None:
    if bundle.get("emb_hist") is None or not len(bundle.get("emb_hist")):
        empty("Sin datos de Embarques Historicos.")
        return
    t = today()
    du = memo(bundle, ("ttm_universo", t), lambda: productos.base_universo(
            bundle.get("emb_hist"), t, bundle.get("aereos"), bundle.get("planif"), bundle.get("historicas")))
    section(f"Time to market · mes a mes {t.year}*",
            "* Universo completo de SO con destino Argentina, marítimas y aéreas, sin muestras ni repuestos. Los "
            "botones de grupo y medio mandan sobre toda la sección: tabla, objetivo −15 % y descarga.")
    grupo, medio = sla_view.ttm_botones()
    with guard("Time to market mes a mes"):
        sla_view.productos_mes_table(productos.mes_a_mes(du, t.year), t, grupo, medio)

    sel, nombre = productos.seleccion(du, grupo, medio)
    sub_g = sel[sel[grupo].fillna(False).astype(bool)] if grupo in sel else sel
    res = objetivo.vs_anio_anterior(productos.por_envio(sub_g), t, "etd", "tiempo")
    section(f"Time to market · objetivo −{fmt.fmt_pct(settings.REDUCCION_OBJETIVO)} vs {t.year - 1} · {nombre}",
            "Por SO (columna «Tiempo de consolidación» de Embarques Historicos), monoproveedor y consolidado por "
            f"separado, contra el mismo mes de {t.year - 1}. El total pondera las dos por el volumen de {t.year}. Cada "
            "combinación de botones tiene su cuadro igual en la hoja Envío mensual («TIME TO MARKET · … · OBJETIVO»).")
    with guard("Objetivo −15 %"):
        sla_view.objetivo_kpis(res, "SO")
        sla_view.objetivo_matrix(res, t)

    with guard("Descarga time to market"):
        ini = pd.Timestamp(filters.start) if filters.start else pd.Timestamp(t.year, 1, 1)
        fin = min(pd.Timestamp(filters.end), t) if filters.end else t
        so = _por_so(sub_g[sub_g["etd"].between(ini, fin)], np.nan)
        if len(so):
            so["objetivo"] = objetivo.objetivo_por_fila(so, res, "etd")
        if len(so) and so["objetivo"].notna().any():
            fuera = so[so["tiempo"] > so["objetivo"]].assign(_exc=lambda x: x["tiempo"] - x["objetivo"])
            solo_descarga(fuera.sort_values("_exc", ascending=False), CASOS_TTM, key="tm_ttm_fuera",
                          filename=f"time_to_market_sobre_objetivo_{t:%Y%m%d}",
                          label=f"Descargar SO por encima del objetivo · {nombre}")
            st.caption(f"SO del período ({nombre}) cuya consolidación supera el objetivo de su estructura y su mes "
                       f"(mismo mes de {t.year - 1} −{fmt.fmt_pct(settings.REDUCCION_OBJETIVO)}). Se descarga en Excel; "
                       "no se muestra en pantalla.")


# ---------------------------------------------------------------------------
# Cargas DG / IMO
# ---------------------------------------------------------------------------
IMO = "Carga IMO / DG"
EST_IMO, EST_BAT, EST_GEN = "IMO / DG", "Con baterías · aceptada como carga general", "Carga general"
ESTADOS_DG = [EST_IMO, EST_BAT, EST_GEN]
_BATERIA = re.compile(r"bater|battery|batteries|litio|lithium|un ?3480|un ?3481|un ?3090|un ?3091", re.IGNORECASE)


def _estado_dg(d: pd.DataFrame) -> pd.Series:
    """IMO / DG · Con baterías aceptada como carga general (DG = NO pero «Observaciones» o «Tipo de demora» mencionan
    baterías / litio / UN3480…) · Carga general · Sin dato."""
    texto = pd.Series("", index=d.index)
    for c in ("observaciones", "tipo_demora"):
        if c in d:
            texto = texto + " " + d[c].fillna("").astype(str)
    bateria = texto.str.contains(_BATERIA, na=False)
    imo = d["imo"] if "imo" in d else _imo(d)
    return pd.Series(np.select([imo == IMO, (imo == "Sin IMO") & bateria, imo == "Sin IMO"],
                               [EST_IMO, EST_BAT, EST_GEN], dg.SIN_DATO), index=d.index)


def _pct_sla(x: pd.DataFrame, col: str = "cumple_consolidacion") -> float:
    c = x[col].dropna() if col in x else pd.Series(dtype=bool)
    return float(c.astype(bool).mean()) if len(c) else np.nan


def _cargas_dg(bundle, filters, z: pd.DataFrame, t: pd.Timestamp) -> None:
    """Cargas peligrosas en un lugar: total, marítimo y aéreo. Además de IMO / DG y carga general, distingue las
    cargas con baterías que la línea aceptó como carga general (DG = NO con baterías en los comentarios)."""
    from views import resumen
    mar = z.assign(estado_dg=_estado_dg(z)) if len(z) else z
    a_all = filtered(bundle, "aereos", filters) if bundle.get("aereos") is not None else None
    aer = _aereo_ops(sla_view.air_zarpados(a_all, t)) if a_all is not None and len(a_all) else pd.DataFrame()
    aer = aer[aer["modo"] == "Aéreo"] if len(aer) and "modo" in aer else aer
    aer = aer.assign(estado_dg=_estado_dg(aer)) if len(aer) else aer

    # ---- Total
    section("Cargas DG / IMO · total",
            "Embarques que zarparon en el período: marítimos (destino Argentina) y aéreos (sin courier). «Con baterías · "
            "aceptada como carga general» = figura DG / IMO = NO pero los comentarios («Observaciones» o «Tipo de "
            "demora») mencionan baterías, litio o UN3480 / UN3481 / UN3090 / UN3091: el agente o la línea la tomó como "
            "carga general.")
    with guard("DG total"):
        def cuenta(x):
            v = x["estado_dg"].value_counts() if len(x) else pd.Series(dtype=int)
            return {e: int(v.get(e, 0)) for e in ESTADOS_DG + [dg.SIN_DATO]}
        cm, ca = cuenta(mar), cuenta(aer)
        tot = {e: cm[e] + ca[e] for e in cm}
        con_dato = sum(tot[e] for e in ESTADOS_DG)

        def tarjeta(e, nombre):
            return KPI(nombre, fmt.fmt_int(tot[e]),
                       sub=f"<b>{fmt.fmt_pct(tot[e] / con_dato if con_dato else np.nan)}</b> · marítimo "
                           f"{fmt.fmt_int(cm[e])} · aéreo {fmt.fmt_int(ca[e])}")
        kpi_row([KPI("Embarques con dato", fmt.fmt_int(con_dato),
                     sub=f"marítimo {fmt.fmt_int(sum(cm[e] for e in ESTADOS_DG))} · aéreo "
                         f"{fmt.fmt_int(sum(ca[e] for e in ESTADOS_DG))} · sin dato {fmt.fmt_int(tot[dg.SIN_DATO])}"),
                 tarjeta(EST_IMO, "IMO / DG"), tarjeta(EST_BAT, "Con baterías · como carga general"),
                 tarjeta(EST_GEN, "Carga general")])

    # ---- Marítimo
    section("Marítimo", "Consolidación = packeo mínimo → ETD contra su SLA · tránsito = ETD → ETA. Todo por mediana.")
    d = mar[mar["estado_dg"] != dg.SIN_DATO] if len(mar) else mar
    if d.empty:
        empty("Sin marítimos con el dato IMO / DG cargado en el período.")
    else:
        with guard("DG marítimo"):
            filas = []
            for e in ESTADOS_DG:
                g = d[d["estado_dg"] == e]
                filas.append({"estado": e, "embarques": len(g), "pct": len(g) / len(d),
                              "cons": g["dias_consolidacion"].median(), "sla": _pct_sla(g),
                              "tt": g["dias_tt"].median() if "dias_tt" in g else np.nan})
            data_table(pd.DataFrame(filas), [
                ColSpec("estado", "Estado"), ColSpec("embarques", "Embarques", "int"), ColSpec("pct", "% del total", "pct"),
                ColSpec("cons", "Consolidación (d)", "days"), ColSpec("sla", "% dentro de SLA", "pct"),
                ColSpec("tt", "Tránsito (d)", "days"),
            ], key="dg_mar_estado", filename="cargas_dg_maritimo", search=False)
        with guard("DG mes a mes"):
            chart_title("Mes a mes · marítimo", "Por mes de ETD")
            m = d.assign(mes=d["etd"].dt.to_period("M").dt.to_timestamp())
            filas = []
            for mes, g in m.groupby("mes"):
                gi, gb = (g[g["estado_dg"] == e] for e in (EST_IMO, EST_BAT))
                ge = g[g["estado_dg"].isin([EST_IMO, EST_BAT])]
                filas.append({"mes": fmt.fmt_month(mes), "imo": len(gi), "bat": len(gb), "esp": len(ge),
                              "cons_imo": gi["dias_consolidacion"].median(), "cons_bat": gb["dias_consolidacion"].median(),
                              "cons_esp": ge["dias_consolidacion"].median(),
                              "sla_imo": _pct_sla(gi), "sla_bat": _pct_sla(gb), "sla_esp": _pct_sla(ge)})
            tabla = pd.DataFrame(filas).iloc[::-1]
            st.caption("Solo cargas especiales: IMO / DG, con baterías aceptadas como carga general, y las dos juntas "
                       "(IMO + baterías). Consolidación = mediana de packeo mínimo → ETD.")
            data_table(tabla, [
                ColSpec("mes", "Mes ETD"), ColSpec("imo", "IMO / DG", "int"),
                ColSpec("bat", "Baterías como carga general", "int"), ColSpec("esp", "IMO + baterías", "int"),
                ColSpec("cons_imo", "Consolidación IMO / DG (d)", "days"),
                ColSpec("cons_bat", "Consolidación baterías (d)", "days"),
                ColSpec("cons_esp", "Consolidación IMO + baterías (d)", "days"),
                ColSpec("sla_imo", "% SLA IMO / DG", "pct"), ColSpec("sla_bat", "% SLA baterías", "pct"),
                ColSpec("sla_esp", "% SLA IMO + baterías", "pct"),
            ], key="dg_mes", filename="cargas_dg_mensual", search=False, height=min(460, 38 + 35 * len(tabla)))
        with guard("DG por agente"):
            chart_title("¿Quién mueve las cargas IMO y con baterías?", "Por agente · marítimo")
            x = d[d["estado_dg"] != EST_GEN]
            if len(x):
                g = x.groupby("forwarder").agg(imo=("estado_dg", lambda s: int((s == EST_IMO).sum())),
                                               bat=("estado_dg", lambda s: int((s == EST_BAT).sum())),
                                               consolidacion=("dias_consolidacion", "median"))
                g["sla"] = x.groupby("forwarder").apply(_pct_sla)
                data_table(g.reset_index().sort_values("imo", ascending=False), [
                    ColSpec("forwarder", "Agente"), ColSpec("imo", "IMO / DG", "int"),
                    ColSpec("bat", "Baterías como carga general", "int"), ColSpec("consolidacion", "Consolidación (d)", "days"),
                    ColSpec("sla", "% SLA", "pct"),
                ], key="dg_agente", filename="cargas_dg_por_agente", search=False)
            else:
                empty("Sin cargas IMO ni con baterías en el período.")
        solo_descarga(d[d["estado_dg"] != EST_GEN].sort_values("etd", ascending=False),
                      [ColSpec("estado_dg", "Estado DG")] + CASOS_MAR + [ColSpec("dias_tt", "Tránsito (d)", "days")],
                      key="dg_casos", filename="maritimo_imo_y_baterias",
                      label="Descargar marítimos IMO y con baterías del período")

    # ---- Aéreo
    section("Aéreo", "Punta a punta = packeo mínimo → ETA Caldas («Total» de Seguimiento Aéreos) contra el SLA de su "
                     "tipo de negocio · vuelo = ETD → ETA.")
    da = aer[aer["estado_dg"] != dg.SIN_DATO] if len(aer) else aer
    if da.empty:
        empty("Sin aéreos con el dato DG cargado en el período.")
    else:
        with guard("DG aéreo"):
            filas = []
            for e in ESTADOS_DG:
                g = da[da["estado_dg"] == e]
                vig = g[g["sla_vig"].notna()] if "sla_vig" in g else g.iloc[0:0]
                filas.append({"estado": e, "cargas": len(g), "pct": len(g) / len(da),
                              "total": g["dias_aereo"].median(),
                              "sla": float((vig["dias_aereo"] <= vig["sla_vig"]).mean()) if len(vig) else np.nan,
                              "vuelo": g["dias_etd_eta"].median() if "dias_etd_eta" in g else np.nan})
            data_table(pd.DataFrame(filas), [
                ColSpec("estado", "Estado"), ColSpec("cargas", "Cargas", "int"), ColSpec("pct", "% del total", "pct"),
                ColSpec("total", "Punta a punta (d)", "days"), ColSpec("sla", "% dentro de SLA", "pct"),
                ColSpec("vuelo", "Vuelo ETD → ETA (d)", "days"),
            ], key="dg_aer_estado", filename="cargas_dg_aereo", search=False)
            casos = da[da["estado_dg"] != EST_GEN]
            if len(casos):
                solo_descarga(casos.sort_values("etd", ascending=False), [
                    ColSpec("estado_dg", "Estado DG"), ColSpec("embarque", "Embarque"), ColSpec("etd", "ETD", "date"),
                    ColSpec("forwarder", "Agente"), ColSpec("puerto", "Origen"), ColSpec("tipo_label", "Tipo de negocio"),
                    ColSpec("dias_aereo", "Punta a punta (d)", "days"), ColSpec("observaciones", "Observaciones", width="large"),
                ], key="dg_aer_casos", filename="aereo_dg_y_baterias", label="Descargar aéreos DG y con baterías")

    # ---- En curso y costo
    with guard("DG en curso"):
        res = filtered(bundle, "reservas", filters, use_period=False) if bundle.get("reservas") is not None else None
        if res is not None and len(res) and "carga_imo" in res:
            r = res.assign(imo=_imo(res))
            r = r.assign(estado_dg=_estado_dg(r))
            curso = r[r["estado_dg"].isin([EST_IMO, EST_BAT])]
            section("En curso", "Reservas con «CARGA IMO» = SI o con baterías en los comentarios · «DOC IMO (MSDS)» es "
                                "la documentación que hay que tener antes de la salida")
            if len(curso):
                cur = curso.assign(doc=curso["doc_imo"].fillna("Sin cargar") if "doc_imo" in curso else "Sin dato",
                                   etd_ok_txt=curso["etd_ok"].map({True: "Sí", False: "No"}).fillna("No")
                                   if "etd_ok" in curso else "")
                data_table(cur.sort_values("etd"), [
                    ColSpec("estado_dg", "Estado"), ColSpec("embarque", "Embarque"), ColSpec("etd", "ETD", "date"),
                    ColSpec("forwarder", "Agente"), ColSpec("puerto", "Puerto"), ColSpec("responsable", "Responsable"),
                    ColSpec("doc", "DOC IMO (MSDS)"), ColSpec("etd_ok_txt", "ETD OK FFWW"),
                ], key="dg_curso", filename="cargas_dg_en_curso", search=False)
            else:
                st.caption("No hay embarques en curso con carga IMO ni con baterías en los comentarios.")

    with guard("DG costo"):
        resumen.render_especiales(bundle, filters)
