"""Lead times y SLA (Reservas Históricas, marítimo)."""
from __future__ import annotations

import numpy as np
import pandas as pd
import plotly.graph_objects as go
import streamlit as st

from components import charts
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

    section("Cierre de mes · aéreo",
            f"Columna Total de Seguimiento Aéreos por tipo de negocio. El SLA rige desde el "
            f"{settings.SLA_AEREO_DESDE:%d/%m/%Y}; antes se muestran solo los tiempos.")
    if bundle.get("aereos") is not None:
        with guard("Cierre aéreo"):
            a = sla_view.air_zarpados(filtered(bundle, "aereos", filters), today())
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

    if bundle.get("emb_hist") is not None:
        section("SKU nuevos y top ranking · objetivo −15 %",
                "Evolución de la mediana del tiempo de consolidación por SO, contra el objetivo de reducirla un "
                f"{fmt.fmt_pct(settings.REDUCCION_OBJETIVO)} respecto de la base.")
        with guard("SKU nuevos y top ranking"):
            dp = productos.base_lines(bundle.get("emb_hist"), today())
            summ = productos.summary(dp, today())
            sla_view.productos_table(summ, today())
            g1, g2 = st.columns(2, gap="medium")
            for col, (grupo, label) in zip((g1, g2), productos.GRUPOS.items()):
                with col:
                    chart_title(label, "Mediana mensual por estructura · línea punteada = objetivo")
                    sla_view.productos_chart(productos.monthly(dp, grupo), summ, label, key=f"lt_prod_{grupo}")
            chart_title(f"Mes a mes {today().year} · cantidad de SO y mediana de consolidación",
                        "Todas las SO marítimas, SKU nuevos y top ranking, por estructura")
            sla_view.productos_mes_table(productos.mes_a_mes(dp, today().year), today())

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
