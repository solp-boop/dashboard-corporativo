"""Tiempos (nivel 2): situación → ¿qué lo explica? → operaciones.

Cuatro pestañas: marítimo (consolidación), aéreo punta a punta, tránsito y puertos, time to market.
Lo zarpado incluye lo que ya salió y sigue en Reservas.
"""
from __future__ import annotations

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
from utils import productos, sla
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
              "transito": "Tránsito y puertos", "ttm": "Time to market"}
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
    if vista in ("maritimo", "transito"):
        with guard("Preparación de tiempos marítimos"):
            z = _maritimo_ops(bundle, filters, t)
            z_all = _maritimo_ops(bundle, filters, t, use_period=False)
            z_prev = z_all[z_all["etd"].between(*ventana)] if ventana else None
        if z is None:
            return
    if vista == "maritimo":
        _maritimo(bundle, filters, z, z_all, z_prev)
    elif vista == "aereo":
        _aereo(bundle, filters, ventana)
    elif vista == "transito":
        _transito(bundle, filters, z, z_all, z_prev)
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
        from utils import tiempos_mes as tm
        section("¿En qué etapa se va el tiempo? · mes a mes",
                "Mes de ETD. Mediana de cada etapa (días); resaltada, la más larga entre Comex y Agente. Si se instruyó "
                "antes del packeo, Comex = 0 y el agente cuenta desde el packeo. «% en SLA» = "
                "embarques con consolidación dentro del SLA (verde si llega al "
                f"{fmt.fmt_pct(settings.CUMPLIMIENTO_OBJETIVO)}). Tránsito y total, solo lo que ya llegó. * mes en curso.")
        # El 60 % de los embarques se instruye antes del packeo: si no, «Comex» da negativo y «Agente» supera a la
        # consolidación. Igual que en aéreo, el agente cuenta desde lo último entre instrucción y packeo, y Comex no
        # baja de 0: así Comex + Agente = consolidación de cada embarque.
        zz = z.copy()
        if {"dias_comex", "dias_consolidacion"} <= set(zz.columns):
            zz["dias_comex"] = zz["dias_comex"].clip(lower=0)
            zz["dias_agente"] = (zz["dias_consolidacion"] - zz["dias_comex"]).where(lambda x: x >= 0)
        nombres = {"dias_comex": "Comex: packeo → instrucción", "dias_agente": "Agente: instrucción → ETD"}
        etapas = [(c, nombres.get(c, lbl)) for c, lbl in ETAPAS if c in zz]
        tab = tm.por_mes(zz, [c for c, _ in etapas], llegados=["dias_tt", "dias_total"], today=t)
        ok = z.dropna(subset=["dias_consolidacion", "sla_consolidacion", "etd"])
        cumple = (ok["dias_consolidacion"] <= ok["sla_consolidacion"]).groupby(calc.month_start(ok["etd"])).mean()
        tab["pct_sla"] = tab["mes"].map(cumple)
        sla_view.mes_matrix(tab, etapas, t, resaltar=["dias_comex", "dias_agente"], pct=("pct_sla", "% en SLA"))

    section("¿Qué lo explica?",
            "Embarques del período por dimensión, ordenados por cuánto explican de los fuera de SLA.")
    with guard("Diagnóstico marítimo"):
        diagnostico(z, DIMS_MAR, "dias_consolidacion", "sla_consolidacion", key="tm_mar", casos_cols=CASOS_MAR,
                    prev=z_prev, prev_txt="el mismo período del año anterior", unidad="embarques")

    with st.expander("Cierre de mes, cumplimiento y tiempos por puerto"):
        chart_title("Cumplimiento mes a mes", "% de embarques con consolidación dentro del SLA")
        sla_view.compliance_chart(sla.monthly_compliance(z), t, key="tm_mar_cumpl")
        _cierre_maritimo(bundle, filters, z)


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
    from utils import resumen_kpis as rk
    from views.resumen import tt_puerto_table
    t = today()
    section("Tránsito marítimo · ETD → ETA",
            "Cada embarque contra el objetivo de tránsito de su puerto (Validaciones · «Transito ARG»; monoproveedor usa "
            "el renglón «-Monoproducto» si existe). Solo embarques que ya llegaron.")
    llego = lambda x: x[x["eta"] <= t].dropna(subset=["dias_tt"])  # noqa: E731 · ETA futura = estimada
    d = llego(z)
    if d.empty:
        empty("Sin embarques llegados en el período.")
        return
    with guard("Situación tránsito"):
        pct, ok, n = rk.tt_vs_objetivo(d)
        fuera = d[d["dias_tt"] > d["obj_tt"]]
        delta, tono = _mediana_delta(llego(z_all), "dias_tt", t)
        tab, _, _ = rk.tt_por_puerto(sla.zarpados(filtered(bundle, "historicas", filters, use_period=False), t), t)
        sobre = tab[tab["estado"] == "Fuera de SLA"]["puerto"].tolist() if len(tab) else []
        enough = n >= settings.MIN_SAMPLE
        kpi_row([
            KPI("Tránsito (mediana)", fmt.fmt_int(d["dias_tt"].median()), "d", delta=delta, tono=tono,
                sub=f"P90 {fmt.fmt_int(d['dias_tt'].quantile(.9))} d · n={fmt.fmt_int(len(d))}"),
            KPI("En objetivo", fmt.fmt_pct(pct) if enough else "—",
                status=("ok" if pct >= settings.CUMPLIMIENTO_OBJETIVO else "bad") if enough else "",
                sub=f"<b>{fmt.fmt_int(ok)}</b> de {fmt.fmt_int(n)} con objetivo de su puerto"),
            KPI("Fuera de objetivo", fmt.fmt_int(len(fuera)), status="bad" if len(fuera) else "ok",
                sub=f"se pasan <b>{fmt.fmt_int((fuera['dias_tt'] - fuera['obj_tt']).median())} d</b> (mediana)"
                if len(fuera) else ""),
            KPI("Puertos sobre objetivo", fmt.fmt_int(len(sobre)), status="warn" if sobre else "ok",
                sub=", ".join(sobre[:3]) + (" …" if len(sobre) > 3 else "") if sobre else "últimos 3 meses cerrados",
                help="Puertos cuya mediana de tránsito de los últimos 3 meses cerrados supera el objetivo en más de "
                     f"{fmt.fmt_pct(settings.SLA_WARNING_TOLERANCE)}."),
        ])
    section("¿Qué lo explica?", "Embarques del período por dimensión, ordenados por cuánto explican de los fuera de "
                                "objetivo.")
    with guard("Diagnóstico tránsito"):
        diagnostico(d, DIMS_TT, "dias_tt", "obj_tt", key="tm_tt", casos_cols=CASOS_TT,
                    prev=llego(z_prev) if z_prev is not None else None,
                    prev_txt="el mismo período del año anterior", unidad="embarques")
    with st.expander("Cierre por puerto · últimos 3 meses cerrados"):
        with guard("Tránsito por puerto"):
            tt_puerto_table(filtered(bundle, "historicas", filters, use_period=False), t, key="lt_tt_puerto")


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
                f"{desde:%d/%m/%Y} (el SLA todavía no regía: solo referencia). * mes en curso.")
        medida = st.segmented_control("Medida", ["Días (mediana)", "% dentro del SLA"], default="Días (mediana)",
                                      key="tm_aer_medida", label_visibility="collapsed") or "Días (mediana)"
        tabla = tm.tipo_por_mes(a.assign(_sla_tipo=a["sla_aereo"] if "sla_aereo" in a else np.nan),
                                sla="_sla_tipo")
        sla_view.tipo_mes_matrix(tabla, t, "pct" if medida.startswith("%") else "dias")

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
    ColSpec("etd", "ETD", "date"), ColSpec("tiempo", "Consolidación (d)", "days"),
    ColSpec("objetivo", "Objetivo (d)", "days"), ColSpec("_exc", "Excedidos (d)", "days"),
]


def _por_so(du: pd.DataFrame, objetivo: float) -> pd.DataFrame:
    if du.empty:
        return pd.DataFrame(columns=["so", "tiempo"])
    agg = {"tiempo": ("tiempo_consolidacion", "median"), "embarque": ("embarque", "first"), "etd": ("etd", "max")}
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
    summ = productos.objetivo_universo(du, t)
    section(f"Time to market · mes a mes {t.year}*",
            "* Universo completo de SO, marítimas y aéreas, sin muestras ni repuestos. Elegí el grupo (todas las SO "
            "= 100 %, SKU nuevos o top ranking) y el medio (todos, solo marítimo o solo aéreo).")
    with guard("Time to market mes a mes"):
        sla_view.productos_mes_table(productos.mes_a_mes(du, t.year), t)

    section("Objetivo −15 %",
            "Mediana del tiempo de consolidación por SO contra el objetivo de reducirla un "
            f"{fmt.fmt_pct(settings.REDUCCION_OBJETIVO)} respecto de Q1.")
    with guard("Objetivo −15 %"):
        sla_view.productos_table(summ, t)
        chart_title("Mediana mensual por grupo", "Mes de ETD · línea punteada = objetivo de cada grupo")
        sla_view.objetivo_mes_chart(productos.mensual_universo(du, t.year), summ, key="lt_obj15_mes")

    fila = summ[summ["grupo"] == "Todas las SO"] if len(summ) else summ
    objetivo = float(fila.iloc[0]["objetivo"]) if len(fila) and fila.iloc[0]["objetivo"] == fila.iloc[0]["objetivo"] \
        else np.nan
    with guard("Descarga time to market"):
        ini = pd.Timestamp(filters.start) if filters.start else pd.Timestamp(t.year, 1, 1)
        fin = min(pd.Timestamp(filters.end), t) if filters.end else t
        so = _por_so(du[du["etd"].between(ini, fin)], objetivo)
        if objetivo == objetivo and len(so):
            fuera = so[so["tiempo"] > so["objetivo"]].assign(_exc=lambda x: x["tiempo"] - x["objetivo"])
            solo_descarga(fuera.sort_values("_exc", ascending=False), CASOS_TTM, key="tm_ttm_fuera",
                          filename=f"time_to_market_sobre_objetivo_{t:%Y%m%d}",
                          label="Descargar SO por encima del objetivo")
            st.caption(f"SO del período cuya consolidación supera el objetivo de todas las SO "
                       f"({fmt.fmt_num(objetivo, 1)} d). Se descarga en Excel; no se muestra en pantalla.")
