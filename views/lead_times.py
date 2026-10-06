"""Lead times y SLA: marítimo, aéreo punta a punta y time to market (pestañas)."""
from __future__ import annotations

import numpy as np
import pandas as pd
import plotly.graph_objects as go
import streamlit as st

from components import charts
from components.kpi_cards import KPI, kpi_row
from components.layout import (chart_title, coverage, empty, filter_notes, guard, require, section,
                               semaforo_legend)
from components.tables import ColSpec, data_table
from config import settings
from config.mappings import MODOS_MARITIMOS
from utils import calculations as calc
from utils import formatting as fmt
from components import sla as sla_view
from utils import productos, sla
from views._common import ctx, filtered, month_labels, today

ETAPAS = [
    ("dias_comex", "Comex: packeo → instrucción"),
    ("dias_agente", "Agente: instrucción → ETD"),
    ("dias_consolidacion", "Consolidación: packeo → ETD"),
    ("dias_tt", "Tránsito: ETD → ETA"),
    ("dias_total", "Total: fin de producción → ETA"),
]


def render() -> None:
    bundle, filters = ctx()
    base = require(bundle, "historicas")
    if base is None:
        return
    df = filtered(bundle, "historicas", filters)
    df = df[df["modo"].isin(MODOS_MARITIMOS) & (df["etd"] <= today())]
    filter_notes(base, filters, "Reservas Históricas")
    tab_mar, tab_aer, tab_ttm = st.tabs(["Marítimo", "Aéreo · punta a punta", "Time to market"])
    with tab_mar:
        _maritimo(bundle, filters, df)
    with tab_aer:
        _aereo(bundle, filters)
    with tab_ttm:
        _time_to_market(bundle)


def _maritimo(bundle, filters, df) -> None:
    st.caption("Solo embarques marítimos ya zarpados. SLA de consolidación: "
               f"monoproveedor según la ETD, {calc.sla_mono_txt()}; consolidado según el target por puerto "
               f"de Validaciones (por defecto {settings.SLA_CONSOLIDACION_DEFAULT} d).")
    if df.empty:
        empty()
        return

    section("Cierre de mes · marítimo",
            "El período elegido en la barra lateral, los dos últimos meses cerrados y cómo viene el mes en curso.")
    with guard("Cierre de mes"):
        # Los meses usan los filtros de la barra lateral salvo el período.
        sc = sla.scorecard(filtered(bundle, "historicas", filters, use_period=False),
                           filtered(bundle, "reservas", filters, use_period=False),
                           df, today(), lambda m: fmt.fmt_month(m, long=True).split()[0])
        sla_view.scorecard_table(sc)
        coverage(int(df["dias_consolidacion"].notna().sum()), len(df), "embarques del período con consolidación calculable")

    section("Transit time por puerto · cierre",
            "TT real de Reservas Históricas (ETD → ETA) de los últimos 3 meses cerrados, por puerto, contra el "
            "objetivo de tránsito de Validaciones («Transito ARG»).")
    with guard("Transit time por puerto"):
        from views.resumen import tt_puerto_table
        tt_puerto_table(filtered(bundle, "historicas", filters, use_period=False), today(), key="lt_tt_puerto")

    section("Apertura del período")
    c1, c2 = st.columns(2, gap="medium")
    with c1, guard("Cumplimiento mensual"):
        chart_title("Cumplimiento de SLA por mes", "% dentro de SLA de consolidación · mes de ETD")
        d = df.dropna(subset=["dias_consolidacion", "estructura"]).copy()
        d["mes"] = calc.month_start(d["etd"])
        d["ok"] = d["dias_consolidacion"] <= d["sla_consolidacion"]
        g = d.groupby(["mes", "estructura"]).agg(pct=("ok", "mean"), n=("ok", "size")).reset_index()
        months = sorted(g["mes"].unique())[-12:]
        if not months:
            empty()
        else:
            fig = go.Figure()
            for i, est in enumerate(["Monoproveedor", "Consolidado"]):
                s = g[g["estructura"] == est].set_index("mes").reindex(months)
                fig.add_bar(x=month_labels(pd.Series(months)), y=s["pct"] * 100, name=est,
                            marker=dict(color=settings.SERIES[i], cornerradius=3),
                            customdata=s["n"].fillna(0),
                            hovertemplate=f"%{{x}} · {est}: %{{y:.0f}} % (n=%{{customdata}})<extra></extra>")
            charts.theme(fig, y_suffix=" %")
            fig.update_yaxes(range=[0, 105])
            charts.show(fig, key="sla_mes")

    with c2, guard("Etapas"):
        chart_title("¿En qué etapa se va el tiempo?", "Mediana y rango P25–P75 por etapa (días)")
        rows = []
        for col, label in ETAPAS:
            s = calc.describe(df[col])
            if s.n:
                rows.append((label, s))
        if not rows:
            empty()
        else:
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
            charts.show(fig, key="sla_etapas")

    section("Tiempos por puerto de origen",
            f"Mediana real vs target de Validaciones · puertos con ≥ {settings.MIN_SAMPLE} embarques. "
            "El semáforo compara el total (fin de producción → ETA) con el target total.")
    with guard("Tabla por puerto"):
        semaforo_legend()
        g = df.groupby("puerto").agg(
            embarques=("embarque", "count"),
            cons=("dias_consolidacion", "median"), tt=("dias_tt", "median"), total=("dias_total", "median"),
            n_total=("dias_total", "count"),
            sla_cons=("sla_consolidacion", "median"), sla_tt=("sla_tt", "median"), sla_total=("sla_total", "median"),
            definido=("sla_puerto_definido", "max"),
        ).reset_index()
        g["cumple"] = df.groupby("puerto").apply(
            lambda d: calc.cumplimiento(d["dias_consolidacion"], d["sla_consolidacion"])[0],
            include_groups=False).reindex(g["puerto"]).values
        g = g[g["embarques"] >= settings.MIN_SAMPLE].sort_values("embarques", ascending=False)
        # SLA de consolidado del puerto (el de mono es fijo y se aclara arriba).
        sla_map = bundle.sla_puertos.set_index("puerto")["sla_consolidacion"] if not bundle.sla_puertos.empty else {}
        g["sla_cons"] = g["puerto"].map(sla_map).fillna(settings.SLA_CONSOLIDACION_DEFAULT)
        g["estado"] = calc.semaforo(g["total"], g["sla_total"])
        g["target"] = np.where(g["definido"], "Validaciones", "Por defecto")
        data_table(g, [
            ColSpec("puerto", "Puerto"), ColSpec("embarques", "Embarques", "int"),
            ColSpec("cons", "Consolidación (d)", "days"), ColSpec("sla_cons", "SLA consolidado (d)", "days"),
            ColSpec("cumple", "% cumple consol.", "pct"),
            ColSpec("tt", "Tránsito (d)", "days"), ColSpec("sla_tt", "Target tránsito (d)", "days"),
            ColSpec("total", "Total (d)", "days"), ColSpec("sla_total", "Target total (d)", "days"),
            ColSpec("estado", "Estado", "status"), ColSpec("target", "Origen del target"),
        ], key="sla_puertos", filename="tiempos_por_puerto", search=False)

    c1, c2 = st.columns(2, gap="medium")
    with c1, guard("Booking"):
        chart_title("Consolidación según modalidad de booking", f"Mediana · referencia {settings.REF_CONSOLIDACION_BOOKING} d")
        g = calc.median_by(df, "booking", "dias_consolidacion")
        if g.empty:
            empty()
        else:
            fig = charts.hbar(g["booking"], g["mediana"],
                              text=[f"{fmt.fmt_int(v)} d · n={n}" for v, n in zip(g["mediana"], g["n"])],
                              hover="%{y}: %{x:.0f} d<extra></extra>", x_title="días",
                              ref_value=settings.REF_CONSOLIDACION_BOOKING, ref_label="Referencia")
            charts.show(fig, key="sla_booking")

    with c2, guard("Causas de demora"):
        chart_title("Principales causas de demora", "Embarques con «Tipo de demora» informado")
        causes = df["tipo_demora"].dropna()
        if causes.empty:
            empty("No hay causas de demora cargadas en el período.")
        else:
            g = causes.value_counts()
            top = g.head(8)
            fig = charts.hbar(top.index, top.values, text=[str(v) for v in top.values],
                              hover="%{y}: %{x} embarques<extra></extra>", x_title="embarques")
            charts.show(fig, key="sla_causas")
            coverage(int(causes.size), len(df), "embarques con causa informada")

    section("Embarques fuera de SLA")
    with guard("Detalle fuera de SLA"):
        bad = df[df["estado_consolidacion"] == calc.SEMAFORO_BAD].sort_values("etd", ascending=False)
        data_table(bad, [
            ColSpec("embarque", "Embarque"), ColSpec("etd", "ETD", "date"), ColSpec("puerto", "Puerto"),
            ColSpec("forwarder", "Forwarder"), ColSpec("estructura", "Estructura"), ColSpec("booking", "Booking"),
            ColSpec("dias_comex", "Comex (d)", "days"), ColSpec("dias_agente", "Agente (d)", "days"),
            ColSpec("dias_consolidacion", "Consolidación (d)", "days"),
            ColSpec("sla_consolidacion", "SLA (d)", "days"), ColSpec("tipo_demora", "Tipo de demora"),
            ColSpec("responsable", "Responsable"), ColSpec("observaciones", "Observaciones", width="large"),
        ], key="sla_bad", filename="embarques_fuera_de_sla")


def _aereo(bundle, filters) -> None:
    if bundle.get("aereos") is None:
        empty("Sin datos de Seguimiento Aéreos.")
        return
    a_all = filtered(bundle, "aereos", filters)
    a = sla_view.air_zarpados(a_all, today())
    desde = pd.Timestamp(settings.SLA_AEREO_DESDE)

    section("Punta a punta · aéreo",
            "Packeo mínimo → ETA Caldas (columna «Total» de Seguimiento Aéreos), aéreos con ETD en el período. "
            f"Cada embarque contra el SLA de su tipo de negocio, vigente desde el {desde:%d/%m/%Y}.")
    with guard("KPIs punta a punta"):
        tot = calc.describe(a["dias_aereo"])
        vig = a[a["sla_vigente"] & a["sla_aereo"].notna()]
        pct, n = calc.cumplimiento(vig["dias_aereo"], vig["sla_aereo"])
        fuera = vig[vig["dias_aereo"] > vig["sla_aereo"]]
        exceso = (fuera["dias_aereo"] - fuera["sla_aereo"]).median() if len(fuera) else np.nan
        kpi_row([
            KPI("Punta a punta (mediana)", fmt.fmt_int(tot.median) if tot.enough else "—", unit="d",
                sub=f"P25–P75: <b>{fmt.fmt_int(tot.p25)}–{fmt.fmt_int(tot.p75)} d</b> · "
                    f"P90 {fmt.fmt_int(a['dias_aereo'].quantile(.9)) if tot.n else '—'} d · n={fmt.fmt_int(tot.n)}"),
            KPI("Dentro del SLA de su tipo", fmt.fmt_pct(pct) if n >= settings.MIN_SAMPLE else "—",
                status=("ok" if pct >= settings.CUMPLIMIENTO_OBJETIVO else "bad") if n >= settings.MIN_SAMPLE else "",
                sub=f"<b>{fmt.fmt_int(n - len(fuera))}</b> de {fmt.fmt_int(n)} desde el {desde:%d/%m}"),
            KPI("Fuera de SLA", fmt.fmt_int(len(fuera)), status="bad" if len(fuera) else "ok",
                sub=f"se pasan <b>{fmt.fmt_int(exceso)} d</b> (mediana)" if len(fuera) else "—"),
            KPI("Tramo más largo", _tramo_mas_largo(a), sub="mediana del período"),
        ])

    c1, c2 = st.columns(2, gap="medium")
    with c1, guard("Tramos por mes"):
        chart_title("¿Dónde se va el tiempo? · por mes",
                    "Mediana de cada tramo por mes de ETD (días) · los tramos se miden por separado")
        _tramos_chart(a_all)
    with c2, guard("Tramos por tipo"):
        chart_title("¿Dónde se va el tiempo? · por tipo de negocio",
                    "Mediana de cada tramo desde el SLA vigente · marca = SLA del tipo")
        _tramos_tipo_chart(a_all[a_all["etd"] >= desde])

    section("Cierre de mes por tipo de negocio",
            f"Columna «Total» de Seguimiento Aéreos. El SLA rige desde el "
            f"{settings.SLA_AEREO_DESDE:%d/%m/%Y}; antes se muestran solo los tiempos.")
    with guard("Cierre aéreo"):
        t_air = sla_view.air_table(a, today())
        last = today().to_period("M").to_timestamp() - pd.offsets.MonthBegin(1)
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
            sla_view.air_compliance_chart(a, today(), key="lt_air_pct")
        with c2:
            chart_title("Días contra el SLA, por tipo de negocio",
                        "Mediana de Total − SLA del tipo. 0 = justo en el SLA; positivo = tarde")
            sla_view.air_deviation_chart(a, today(), key="lt_air_dev")

    section("Aéreos fuera de SLA", f"Embarques con ETD desde el {desde:%d/%m/%Y} cuyo «Total» supera el SLA de su tipo.")
    with guard("Aéreos fuera de SLA"):
        f = a[a["sla_vigente"] & (a["dias_aereo"] > a["sla_aereo"])].copy()
        if f.empty:
            empty("No hay aéreos fuera de SLA.")
        else:
            f["exceso"] = f["dias_aereo"] - f["sla_aereo"]
            f["tipo_negocio"] = f["tipo_sla"].map(
                lambda t: sla_view.TIPO_LABEL.get(t, str(t).title()) if isinstance(t, str) else "").where(
                f["tipo_sla"].notna(), f["tipo_negocio"])
            data_table(f.sort_values("exceso", ascending=False), [
                ColSpec("embarque", "Embarque"), ColSpec("tipo_negocio", "Tipo de negocio"),
                ColSpec("forwarder", "Forwarder"), ColSpec("puerto", "Origen"), ColSpec("etd", "ETD", "date"),
                ColSpec("dias_packeo_wh", "Packeo→WH (d)", "days"), ColSpec("dias_wh_etd", "WH→ETD (d)", "days"),
                ColSpec("dias_etd_eta", "ETD→ETA (d)", "days"), ColSpec("dias_eta_caldas", "ETA→Caldas (d)", "days"),
                ColSpec("dias_aereo", "Total (d)", "days"), ColSpec("sla_aereo", "SLA (d)", "days"),
                ColSpec("exceso", "Exceso (d)", "days"), ColSpec("tipo_demora", "Tipo de demora"),
            ], key="lt_air_fuera", filename="aereos_fuera_de_sla", search=False)


TRAMOS_AEREO = [
    ("dias_packeo_wh", "Packeo → WH"),
    ("dias_wh_etd", "WH → ETD"),
    ("dias_etd_eta", "ETD → ETA"),
    ("dias_eta_caldas", "ETA → Caldas"),
]


def _tramo_mas_largo(a: pd.DataFrame) -> str:
    med = {lbl: a[c].median() for c, lbl in TRAMOS_AEREO if c in a and a[c].notna().any()}
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
    colors = settings.SERIES + [settings.SERIES_OTHER]
    for i, (col, lbl) in enumerate(TRAMOS_AEREO):
        s = d.groupby("mes")[col].median().reindex(months)
        fig.add_bar(x=month_labels(pd.Series(months)), y=s.values, name=lbl,
                    marker=dict(color=colors[i], cornerradius=2),
                    hovertemplate=f"%{{x}} · {lbl}: %{{y:.0f}} d<extra></extra>")
    fig.update_layout(barmode="stack")
    charts.theme(fig, height=360, y_title="días (mediana)")
    charts.show(fig, key="lt_air_tramos_mes")


def _tramos_tipo_chart(a: pd.DataFrame) -> None:
    if a.empty:
        empty()
        return
    d = a.copy()
    d["tipo"] = d["tipo_sla"].map(lambda t: sla_view.TIPO_LABEL.get(t, str(t).title()) if isinstance(t, str) else "Sin SLA")
    tipos = d["tipo"].value_counts().index[:6].tolist()
    fig = go.Figure()
    colors = settings.SERIES + [settings.SERIES_OTHER]
    for i, (col, lbl) in enumerate(TRAMOS_AEREO):
        s = d.groupby("tipo")[col].median().reindex(tipos)
        fig.add_bar(y=tipos, x=s.values, name=lbl, orientation="h",
                    marker=dict(color=colors[i], cornerradius=2),
                    hovertemplate=f"%{{y}} · {lbl}: %{{x:.0f}} d<extra></extra>")
    sla_by_label = {sla_view.TIPO_LABEL.get(k, k.title()): v for k, v in settings.SLA_AEREO_POR_TIPO.items()}
    fig.add_scatter(y=tipos, x=[sla_by_label.get(t) for t in tipos], mode="markers", name="SLA del tipo",
                    marker=dict(symbol="line-ns-open", size=22, color=settings.COLORS["slate"], line=dict(width=3)),
                    hovertemplate="%{y} · SLA %{x} d<extra></extra>")
    fig.update_layout(barmode="stack")
    charts.theme(fig, height=360, y_title="días (mediana)", horizontal=True)
    fig.update_layout(margin=dict(l=8, r=24, t=28, b=8))
    fig.update_yaxes(autorange="reversed")
    charts.show(fig, key="lt_air_tramos_tipo")


def _time_to_market(bundle) -> None:
    if bundle.get("emb_hist") is None:
        empty("Sin datos de Embarques Historicos.")
        return
    t = today()
    section(f"Time to market · mes a mes {t.year}*",
            "* Universo completo de SO, marítimas y aéreas, sin muestras ni repuestos. Elegí el grupo: todas las SO "
            "(100 %), SKU nuevos o top ranking.")
    with guard("Time to market mes a mes"):
        du = productos.base_universo(bundle.get("emb_hist"), t, bundle.get("aereos"), bundle.get("planif"))
        sla_view.productos_mes_table(productos.mes_a_mes(du, t.year), t)

    section("Objetivo −15 %",
            "Universo completo (marítimo y aéreo, sin muestras ni repuestos): evolución de la mediana del tiempo de "
            f"consolidación por SO, contra el objetivo de reducirla un {fmt.fmt_pct(settings.REDUCCION_OBJETIVO)} "
            "respecto de la base (Q1).")
    with guard("Objetivo −15 %"):
        summ = productos.objetivo_universo(du, t)
        sla_view.productos_table(summ, t)
        chart_title("Mediana mensual por grupo", "Mes de ETD · línea punteada = objetivo de cada grupo")
        sla_view.objetivo_mes_chart(productos.mensual_universo(du, t.year), summ, key="lt_obj15_mes")
