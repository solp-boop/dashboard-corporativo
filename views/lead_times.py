"""Tiempos (nivel 2): situación → ¿qué lo explica? → operaciones.

Cuatro pestañas: marítimo (consolidación), aéreo punta a punta, tránsito y puertos, time to market.
Lo zarpado incluye lo que ya salió y sigue en Reservas.
"""
from __future__ import annotations

import numpy as np
import pandas as pd
import plotly.graph_objects as go
import streamlit as st

from components import charts
from components import sla as sla_view
from components.drill import diagnostico
from components.kpi_cards import KPI, kpi_row
from components.layout import chart_title, coverage, empty, guard, require, section, semaforo_legend
from components.tables import ColSpec, data_table
from config import settings
from utils import calculations as calc
from utils import data_cleaning as dc
from utils import diagnostico as dg
from utils import formatting as fmt
from utils import panorama as pan
from utils import productos, sla
from views._common import ctx, filtered, month_labels, today

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
DIMS_AER = [
    dg.Dimension("tipo_label", "Tipo de negocio"), dg.Dimension("tramo_largo", "Tramo más largo"),
    dg.Dimension("forwarder", "Agente"), dg.Dimension("aerolinea", "Aerolínea"), dg.Dimension("puerto", "Origen"),
    dg.Dimension("imo", "IMO / DG"), dg.Dimension("tipo_demora", "Causa"),
]
DIMS_TTM = [
    dg.Dimension("proveedor", "Proveedor"), dg.Dimension("category", "Category manager"),
    dg.Dimension("grupo", "SKU nuevo / top ranking"), dg.Dimension("modo", "Modo"),
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
    z = dg.unir_emb_hist(z, _fuente_so(bundle))
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
    tab_mar, tab_aer, tab_tt, tab_ttm = st.tabs(["Marítimo · consolidación", "Aéreo · punta a punta",
                                                 "Tránsito y puertos", "Time to market"])
    ventana = _ventana_prev(filters, t)
    z = z_all = z_prev = None
    with guard("Preparación de tiempos marítimos"):
        z = _maritimo_ops(bundle, filters, t)
        z_all = _maritimo_ops(bundle, filters, t, use_period=False)
        z_prev = z_all[z_all["etd"].between(*ventana)] if ventana else None
    if z is None:
        return
    with tab_mar:
        _maritimo(bundle, filters, z, z_all, z_prev)
    with tab_aer:
        _aereo(bundle, filters, ventana)
    with tab_tt:
        _transito(bundle, filters, z, z_all, z_prev)
    with tab_ttm:
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
        c1, c2 = st.columns(2, gap="medium")
        with c1:
            chart_title("Cumplimiento mes a mes", "% de embarques con consolidación dentro del SLA")
            sla_view.compliance_chart(sla.monthly_compliance(z), t, key="tm_mar_cumpl")
        with c2:
            chart_title("¿En qué etapa se va el tiempo?",
                        "Mediana y rango P25–P75 por etapa (días) · tránsito y total, solo lo que ya llegó")
            _etapas_chart(z)

    section("¿Qué lo explica?",
            "Embarques del período por dimensión, ordenados por cuánto explican de los fuera de SLA.")
    with guard("Diagnóstico marítimo"):
        diagnostico(z, DIMS_MAR, "dias_consolidacion", "sla_consolidacion", key="tm_mar", casos_cols=CASOS_MAR,
                    prev=z_prev, prev_txt="el mismo período del año anterior", unidad="embarques")

    with st.expander("Cierre de mes y tiempos por puerto"):
        _cierre_maritimo(bundle, filters, z)


def _etapas_chart(df: pd.DataFrame) -> None:
    llegados = df[df["eta"] <= today()] if "eta" in df else df
    rows = [(label, calc.describe((llegados if col in ("dias_tt", "dias_total") else df)[col]))
            for col, label in ETAPAS if col in df]
    rows = [(lbl, s) for lbl, s in rows if s.n]
    if not rows:
        empty()
        return
    labels = [r[0] for r in rows]
    med = [r[1].median for r in rows]
    fig = go.Figure(go.Bar(
        y=labels, x=med, orientation="h", marker=dict(color=settings.SERIES[0], cornerradius=4),
        error_x=dict(type="data", symmetric=False, array=[r[1].p75 - r[1].median for r in rows],
                     arrayminus=[r[1].median - r[1].p25 for r in rows],
                     color=settings.COLORS["slate"], thickness=1.2, width=4),
        text=[f"{fmt.fmt_int(v)} d" for v in med], textposition="inside",
        customdata=[[r[1].p25, r[1].p75, r[1].n] for r in rows],
        hovertemplate="%{y}<br>Mediana: %{x:.0f} d<br>P25–P75: %{customdata[0]:.0f}–%{customdata[1]:.0f} d"
                      "<br>n=%{customdata[2]}<extra></extra>",
    ))
    charts.theme(fig, height=320, y_title="días", horizontal=True, legend=False)
    fig.update_yaxes(autorange="reversed")
    charts.show(fig, key="tm_mar_etapas")


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
    c1, c2 = st.columns(2, gap="medium")
    with c1, guard("Tramos por mes"):
        chart_title("¿Dónde se va el tiempo? · por mes",
                    "Mediana de cada tramo por mes de ETD (días) · los tramos se miden por separado")
        _tramos_chart(a)
    with c2, guard("Tramos por tipo"):
        chart_title("¿Dónde se va el tiempo? · por tipo de negocio",
                    "Mediana de cada tramo desde el SLA vigente · marca = SLA del tipo")
        _tramos_tipo_chart(a[a["etd"] >= desde])

    section("¿Qué lo explica?", "Aéreos del período por dimensión. Los fuera de SLA se cuentan desde el "
                                f"{desde:%d/%m/%Y}; antes solo se ven los tiempos.")
    with guard("Diagnóstico aéreo"):
        prev = None
        if ventana:
            ap = _aereo_ops(sla_view.air_zarpados(filtered(bundle, "aereos", filters, use_period=False), t))
            prev = ap[ap["etd"].between(*ventana)]
        diagnostico(a, DIMS_AER, "dias_aereo", "sla_vig", key="tm_aer", casos_cols=CASOS_AER, prev=prev,
                    prev_txt="el mismo período del año anterior", unidad="aéreos")

    with st.expander("Cierre de mes por tipo de negocio"):
        with guard("Cierre aéreo"):
            t_air = sla_view.air_table(a, t)
            last = t.to_period("M").to_timestamp() - pd.offsets.MonthBegin(1)
            data_table(t_air, [
                ColSpec("tipo", "Tipo de negocio"), ColSpec("sla", "SLA (d)", "days"),
                ColSpec("antes", "Antes del SLA · mediana (d)", "days"), ColSpec("antes_n", "n", "int"),
                ColSpec("desde", "Desde el SLA · mediana (d)", "days"),
                ColSpec("desde_pct", "Desde el SLA · % dentro", "pct"), ColSpec("desde_n", "n ", "int"),
                ColSpec("ult", f"{fmt.fmt_month(last, long=True)} · mediana (d)", "days"),
                ColSpec("ult_pct", f"{fmt.fmt_month(last, long=True)} · % dentro", "pct"),
                ColSpec("ult_n", "n  ", "int"),
            ], key="lt_air", filename="sla_aereo_por_tipo", search=False)
            c1, c2 = st.columns(2, gap="medium")
            with c1:
                chart_title("Cumplimiento mes a mes",
                            "% dentro del SLA de su tipo. En gris, meses anteriores al SLA (referencia)")
                sla_view.air_compliance_chart(a, t, key="lt_air_pct")
            with c2:
                chart_title("Días contra el SLA, por tipo de negocio",
                            "Mediana de Total − SLA del tipo. 0 = justo en el SLA; positivo = tarde")
                sla_view.air_deviation_chart(a, t, key="lt_air_dev")


def _tramo_mas_largo(a: pd.DataFrame) -> str:
    med = {lbl: a[c].clip(lower=0).median() for c, lbl in TRAMOS_AEREO if c in a and a[c].notna().any()}
    if not med:
        return "—"
    lbl = max(med, key=med.get)
    return f"{lbl} · {fmt.fmt_int(med[lbl])} d"


def _tramos_chart(a: pd.DataFrame) -> None:
    d = a.dropna(subset=["etd"]).copy()
    if d.empty:
        empty()
        return
    d["mes"] = calc.month_start(d["etd"])
    months = sorted(d["mes"].unique())[-12:]
    fig = go.Figure()
    colors = settings.SERIES + ["#3E8E7E", settings.SERIES_OTHER]
    for i, (col, lbl) in enumerate(TRAMOS_AEREO):
        if col not in d:
            continue
        s = d.groupby("mes")[col].apply(lambda x: x.clip(lower=0).median()).reindex(months).fillna(0)
        fig.add_bar(x=month_labels(pd.Series(months)), y=s.values, name=lbl,
                    marker=dict(color=colors[i], cornerradius=2),
                    hovertemplate=f"%{{x}} · {lbl}: %{{y:.0f}} d<extra></extra>")
    fig.update_layout(barmode="stack")
    charts.theme(fig, height=380, y_title="días (mediana)")
    charts.show(fig, key="lt_air_tramos_mes")


def _tramos_tipo_chart(a: pd.DataFrame) -> None:
    if a.empty:
        empty()
        return
    d = a.copy()
    tipos = d["tipo_label"].value_counts().index[:6].tolist()
    fig = go.Figure()
    colors = settings.SERIES + ["#3E8E7E", settings.SERIES_OTHER]
    for i, (col, lbl) in enumerate(TRAMOS_AEREO):
        if col not in d:
            continue
        s = d.groupby("tipo_label")[col].apply(lambda x: x.clip(lower=0).median()).reindex(tipos).fillna(0)
        fig.add_bar(y=tipos, x=s.values, name=lbl, orientation="h",
                    marker=dict(color=colors[i], cornerradius=2),
                    hovertemplate=f"%{{y}} · {lbl}: %{{x:.0f}} d<extra></extra>")
    sla_by_label = {sla_view.TIPO_LABEL.get(k, k.title()): v for k, v in settings.SLA_AEREO_POR_TIPO.items()}
    fig.add_scatter(y=tipos, x=[sla_by_label.get(t) for t in tipos], mode="markers", name="SLA del tipo",
                    marker=dict(symbol="line-ns-open", size=22, color=settings.COLORS["slate"], line=dict(width=3)),
                    hovertemplate="%{y} · SLA %{x} d<extra></extra>")
    fig.update_layout(barmode="stack")
    charts.theme(fig, height=380, y_title="días (mediana)", horizontal=True)
    fig.update_layout(margin=dict(l=8, r=24, t=28, b=8))
    fig.update_yaxes(autorange="reversed")
    charts.show(fig, key="lt_air_tramos_tipo")


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
    du = productos.base_universo(bundle.get("emb_hist"), t, bundle.get("aereos"), bundle.get("planif"),
                                      bundle.get("historicas"))
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
    section("¿Qué lo explica?",
            "SO del período por proveedor, category manager, grupo y modo. «Fuera» = SO cuya consolidación supera el "
            f"objetivo de todas las SO ({fmt.fmt_num(objetivo, 1)} d)." if objetivo == objetivo else
            "SO del período por proveedor, category manager, grupo y modo.")
    with guard("Diagnóstico time to market"):
        ini = pd.Timestamp(filters.start) if filters.start else pd.Timestamp(t.year, 1, 1)
        fin = min(pd.Timestamp(filters.end), t) if filters.end else t
        so = _por_so(du[du["etd"].between(ini, fin)], objetivo)
        prev = None
        if ventana:
            prev = _por_so(du[du["etd"].between(*ventana)], objetivo)
        diagnostico(so, DIMS_TTM, "tiempo", "objetivo" if objetivo == objetivo else None, key="tm_ttm",
                    casos_cols=CASOS_TTM, id_col="so", prev=prev, prev_txt="el mismo período del año anterior",
                    unidad="SO")
