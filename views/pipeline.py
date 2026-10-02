"""Pipeline de origen (Planif cargas): qué volumen viene, cuándo sale y cuánto falta instruir."""
from __future__ import annotations

import numpy as np
import pandas as pd
import plotly.graph_objects as go
import streamlit as st

from components import charts
from components.kpi_cards import KPI, kpi_row
from components.layout import chart_title, coverage, empty, filter_notes, guard, require, section
from components.tables import ColSpec, data_table
from config import settings
from utils import calculations as calc
from utils import data_cleaning as dc
from utils import formatting as fmt
from views._common import ctx, filtered, today

ESTADOS = ["Instruida", "Pendiente", "Sin clasificar"]
ESTADO_COLORS = {"Instruida": settings.SERIES[0], "Pendiente": settings.SERIES[1],
                 "Sin clasificar": settings.SERIES_OTHER}
METRICS = {"M3": ("m3", "m³"), "Contenedores": ("cnt", "cont."), "FOB (USD)": ("fob", "USD"),
           "Cantidad de SO": ("so", "SO")}


def per_so(df: pd.DataFrame) -> pd.DataFrame:
    """Una fila por SO (Planif tiene una fila por línea de producto)."""
    g = df.groupby("so", sort=False)
    first_cols = ["embarque", "proveedor", "puerto", "destino", "estado_instruccion", "estructura",
                  "tipo_negocio", "responsable", "tipo_carga", "category_manager"]
    out = g[first_cols].first()  # primer valor no vacío de cada SO
    out = out.join(g.agg(f_instruccion=("f_instruccion", "min"), etd=("etd", "min"), eta=("eta", "min"),
                         m3=("m3", "sum"), fob=("fob", "sum")))
    return out.reset_index()


def es_maritimo(df: pd.DataFrame) -> pd.Series:
    """SO que viajan en barco según la modalidad de costeo (Barco… o Costo Híbrido Puerto ZFLP)."""
    mod = df["modalidad"].map(lambda v: dc.fold(v) if v else "")
    return mod.str.startswith("barco") | mod.str.contains("costo hibrido puerto zflp", regex=False)


def containers(d: pd.DataFrame, embarque_cnt: dict[str, float]) -> pd.DataFrame:
    """Contenedores por mes y estado.

    - SO con embarque cargado en Reservas: contenedores reales de ese embarque
      (cada embarque se cuenta una sola vez, en el mes de su primera SO).
    - El resto de las SO marítimas: estimado = m³ / M3_POR_CONTENEDOR.
    """
    d = d[es_maritimo(d)].copy()
    d["_emb"] = d["embarque"].map(lambda v: dc.fold(v) if v else "")
    has_real = d["_emb"].isin(embarque_cnt)
    real = (d[has_real].sort_values("mes").groupby("_emb", as_index=False)
            .agg(mes=("mes", "first"), estado_instruccion=("estado_instruccion", "first")))
    real["valor"] = real["_emb"].map(embarque_cnt)
    real = real.groupby(["mes", "estado_instruccion"], as_index=False)["valor"].sum()
    est = d[~has_real].groupby(["mes", "estado_instruccion"], as_index=False)["m3"].sum()
    est["valor"] = est["m3"] / settings.M3_POR_CONTENEDOR
    out = pd.concat([real, est[["mes", "estado_instruccion", "valor"]]])
    out = out.groupby(["mes", "estado_instruccion"], as_index=False)["valor"].sum()
    out["valor"] = out["valor"].round(0)
    return out


def _agg(df: pd.DataFrame, by: list[str], metric: str) -> pd.DataFrame:
    if metric == "so":
        return df.groupby(by, observed=True)["so"].nunique().rename("valor").reset_index()
    return df.groupby(by, observed=True)[metric].sum().rename("valor").reset_index()


def render() -> None:
    bundle, filters = ctx()
    base = require(bundle, "planif")
    if base is None:
        return
    df = filtered(bundle, "planif", filters)

    section("Mercadería en origen", "Órdenes de compra (SO) de Planificación de cargas, por fecha ETD.")
    with guard("KPIs de origen"):
        so = per_so(df) if not df.empty else df
        total_m3 = so["m3"].sum() if len(so) else 0
        inst = so[so["estado_instruccion"] == "Instruida"] if len(so) else so
        pend = so[so["estado_instruccion"] == "Pendiente"] if len(so) else so
        sincl = so[so["estado_instruccion"] == "Sin clasificar"] if len(so) else so
        kpi_row([
            KPI("SO", fmt.fmt_int(len(so)), sub=f"<b>{fmt.fmt_int(df['proveedor'].nunique())}</b> proveedores"),
            KPI("Volumen", fmt.fmt_int(total_m3), unit="m³"),
            KPI("FOB", fmt.fmt_usd(so["fob"].sum() if len(so) else 0)),
            KPI("Instruido", fmt.fmt_pct(inst["m3"].sum() / total_m3 if total_m3 else np.nan),
                sub=f"<b>{fmt.fmt_int(len(inst))}</b> SO · {fmt.fmt_int(inst['m3'].sum())} m³ del volumen"),
            KPI("Pendiente de instruir", fmt.fmt_int(len(pend)), unit="SO",
                sub=f"<b>{fmt.fmt_int(pend['m3'].sum())} m³</b>"
                    + (f" · {fmt.fmt_int(len(sincl))} SO sin estado claro" if len(sincl) else "")),
        ])
        filter_notes(base, filters, "Planificación de cargas")
        if len(sincl):
            st.caption(f"«Sin clasificar»: {fmt.fmt_int(len(sincl))} SO con un valor en «Fecha de Instrucción» "
                       "que no es fecha ni «SIN INSTRUCCION». Se listan en la tabla de abajo.")

    if df.empty:
        empty()
        return

    section("¿Cuándo sale el volumen?", "Proyección por mes. Los meses anteriores al actual se agrupan en «Anteriores».")
    with guard("Proyección mensual"):
        a, b = st.columns([1, 1])
        metric_label = a.segmented_control("Medida", list(METRICS), default="M3", key="pl_metric")
        date_label = b.segmented_control("Fecha", ["ETD", "ETA"], default="ETD", key="pl_date")
        metric_label = metric_label or "M3"
        date_col = "eta" if date_label == "ETA" else "etd"
        metric, unit = METRICS[metric_label]
        d = df.dropna(subset=[date_col]).copy()
        this_month = today().to_period("M").to_timestamp()
        d["mes"] = calc.month_start(d[date_col])
        d.loc[d["mes"] < this_month, "mes"] = pd.Timestamp("1900-01-01")
        if metric == "cnt":
            emb_cnt = {}
            for key in ("historicas", "reservas"):  # Reservas (más actual) pisa a Históricas
                src = bundle.get(key)
                if src is not None:
                    ok = src.dropna(subset=["embarque"])
                    ok = ok[ok["contenedores"] > 0]
                    emb_cnt.update(dict(zip(ok["embarque"].map(dc.fold), ok["contenedores"])))
            g = containers(d, emb_cnt)
        else:
            g = _agg(d, ["mes", "estado_instruccion"], metric)
        if metric == "cnt":  # meses sin contenedores marítimos no aportan
            tot = g.groupby("mes")["valor"].sum()
            g = g[g["mes"].isin(tot[tot > 0].index)]
        months = sorted(g["mes"].unique())
        labels = {mm: ("Anteriores" if mm.year == 1900 else fmt.fmt_month(mm)) for mm in months}
        fig = go.Figure()
        for est in ESTADOS:
            s = g[g["estado_instruccion"] == est].set_index("mes")["valor"].reindex(months).fillna(0)
            if s.sum() == 0:
                continue
            fig.add_bar(x=[labels[mm] for mm in months], y=s.values, name=est,
                        marker=dict(color=ESTADO_COLORS[est], cornerradius=3),
                        hovertemplate=f"%{{x}} · {est}: %{{y:,.0f}} {unit}<extra></extra>")
        totals = g.groupby("mes")["valor"].sum().reindex(months)
        fig.add_scatter(x=[labels[mm] for mm in months], y=totals.values, mode="text",
                        text=[fmt.fmt_usd(v) if metric == "fob" else fmt.fmt_int(v) for v in totals.values],
                        textposition="top center", showlegend=False, hoverinfo="skip",
                        textfont=dict(size=11, color=settings.COLORS["slate"]))
        fig.update_layout(barmode="stack")
        charts.theme(fig, height=360, y_title=unit)
        chart_title(f"{metric_label} por mes de {date_label} y estado de instrucción")
        charts.show(fig, key="pl_mes")
        if metric == "cnt":
            st.caption("Contenedores reales para las SO que ya tienen embarque en Reservas; para el resto se estima "
                       f"m³ / {settings.M3_POR_CONTENEDOR}. Solo SO marítimas (modalidad Barco o Costo Híbrido Puerto ZFLP).")
        sin_fecha = df[date_col].isna().sum()
        if sin_fecha:
            st.caption(f"{fmt.fmt_int(sin_fecha)} líneas sin {date_label} no se muestran en el gráfico.")

    section("Por puerto y semana", "El mes elegido aplica a los dos: volumen por puerto y semana a semana (ETD). "
            "«Total» suma todos los meses desde el actual.")
    this_month = today().to_period("M").to_timestamp()
    months_avail = sorted(calc.month_start(df["etd"].dropna()).unique())
    future = [m for m in months_avail if m >= this_month] or months_avail
    opciones = ["Total"] + future
    sel = st.segmented_control("Mes ETD", opciones, default="Total", key="pl_week_month",
                               format_func=lambda m: m if isinstance(m, str) else fmt.fmt_month(m, long=True))
    sel = sel or "Total"
    if future:
        en_meses = calc.month_start(df["etd"]).isin(future)
    else:
        en_meses = pd.Series(False, index=df.index)
    w_all = df[en_meses].copy()
    w = w_all if sel == "Total" else w_all[calc.month_start(w_all["etd"]) == sel].copy()
    fuera = df[~en_meses]
    sel_txt = f"Total desde {fmt.fmt_month(future[0], long=True).lower()}" if (sel == "Total" and future) else (
        "Total" if sel == "Total" else fmt.fmt_month(sel, long=True))

    c1, c2 = st.columns(2, gap="medium")
    with c1, guard("Volumen por puerto"):
        chart_title("Volumen por puerto de salida", f"m³ · {sel_txt} · % sobre el total del mes elegido")
        if w.empty:
            empty("Sin SO con ETD en ese mes.")
        else:
            wp = w.assign(puerto=w["puerto"].astype(object).where(w["puerto"].notna(), "Sin puerto"))
            g = wp.groupby(["puerto", "estado_instruccion"], observed=True)["m3"].sum().reset_index()
            order = g.groupby("puerto")["m3"].sum().sort_values(ascending=False)
            total_m3 = float(order.sum())
            top = list(order.index[:10])
            fig = go.Figure()
            for est in ESTADOS:
                sub = g[g["estado_instruccion"] == est].set_index("puerto")["m3"].reindex(top).fillna(0)
                if sub.sum() == 0:
                    continue
                fig.add_bar(y=top, x=sub.values, name=est, orientation="h",
                            marker=dict(color=ESTADO_COLORS[est], cornerradius=3),
                            hovertemplate=f"%{{y}} · {est}: %{{x:,.0f}} m³<extra></extra>")
            tot = order.reindex(top)
            fig.add_scatter(y=top, x=tot.values, mode="text", showlegend=False, hoverinfo="skip",
                            text=[f"  {fmt.fmt_int(v)} m³ · {fmt.fmt_pct(v / total_m3 if total_m3 else np.nan)}"
                                  for v in tot.values],
                            textposition="middle right", cliponaxis=False,
                            textfont=dict(size=11, color=settings.COLORS["slate"]))
            fig.update_layout(barmode="stack")
            charts.theme(fig, height=max(260, 30 * len(top) + 80), y_title="m³", horizontal=True)
            fig.update_yaxes(autorange="reversed")
            fig.update_xaxes(range=[0, float(tot.max()) * 1.55])
            charts.show(fig, key="pl_puerto")
            extra = f"Total: {fmt.fmt_int(total_m3)} m³ en {fmt.fmt_int(len(order))} puertos."
            if len(order) > 10:
                extra += f" Otros {len(order) - 10} puertos: {fmt.fmt_int(order.iloc[10:].sum())} m³."
            st.caption(extra)

    with c2, guard("Semana a semana"):
        chart_title("Semana a semana (ETD)", f"{sel_txt} · base para reservar espacio y negociar tarifas")
        if w.empty:
            empty("Sin SO con ETD en ese mes.")
        else:
            w["semana"] = calc.week_start(w["etd"])
            t = w.groupby("semana").agg(so=("so", "nunique"), m3=("m3", "sum"), fob=("fob", "sum"),
                                         proveedores=("proveedor", "nunique")).reset_index()
            mono = w[w["estructura"] == "Monoproveedor"].groupby("semana")["m3"].sum()
            t["mono"] = t["semana"].map(mono).fillna(0)
            t["cons"] = t["m3"] - t["mono"]
            mar = w[es_maritimo(w)]
            m3_mar = mar.groupby("semana")["m3"].sum()
            t["cnt_est"] = (t["semana"].map(m3_mar).fillna(0) / settings.M3_POR_CONTENEDOR).round(0)
            t["semana_txt"] = t["semana"].map(lambda x: f"{x:%d/%m} – {(x + pd.Timedelta(days=6)):%d/%m}")
            data_table(t, [
                ColSpec("semana_txt", "Semana"), ColSpec("so", "SO", "int"),
                ColSpec("m3", "M3 total", "int"), ColSpec("mono", "M3 mono", "int"),
                ColSpec("cons", "M3 consolidado", "int"),
                ColSpec("cnt_est", f"Cont. estimados (m³/{settings.M3_POR_CONTENEDOR})", "int"),
                ColSpec("proveedores", "Proveedores", "int"),
                ColSpec("fob", "FOB (USD)", "usd"),
            ], key="pl_weeks", filename="proyeccion_semanal", search=False,
                caption=f"Total: {fmt.fmt_int(t['m3'].sum())} m³")
    if len(fuera):
        st.caption(f"No entran en esta vista {fmt.fmt_int(fuera['so'].nunique())} SO con ETD anterior a "
                   f"{fmt.fmt_month(this_month, long=True).lower()} o sin ETD "
                   f"({fmt.fmt_int(fuera['m3'].sum())} m³). Están en el detalle por SO.")

    section("Tipo de negocio", "Clasificación por marca y tipo de envío (muestras y repuestos aparte).")
    with guard("Tipo de negocio"):
        so = per_so(df)
        tn = so.pivot_table(index="tipo_negocio", columns="estado_instruccion", values="so",
                            aggfunc="count", fill_value=0)
        tn = tn.reindex(columns=[e for e in ESTADOS if e in tn.columns])
        tn["Total SO"] = tn.sum(axis=1)
        tn["M3"] = so.groupby("tipo_negocio")["m3"].sum()
        tn = tn.sort_values("Total SO", ascending=False).reset_index().rename(columns={"tipo_negocio": "Tipo de negocio"})
        cols = [ColSpec("Tipo de negocio", "Tipo de negocio")] + \
               [ColSpec(c, f"SO {c.lower()}", "int") for c in ESTADOS if c in tn.columns] + \
               [ColSpec("Total SO", "Total SO", "int"), ColSpec("M3", "M3", "int")]
        data_table(tn, cols, key="pl_tn", filename="tipo_negocio", search=False)

    section("Detalle por SO")
    with guard("Detalle por SO"):
        so = per_so(df).sort_values(["etd", "so"])
        coverage(int(so["etd"].notna().sum()), len(so), "SO con ETD")
        data_table(so, [
            ColSpec("so", "SO"), ColSpec("estado_instruccion", "Estado"), ColSpec("embarque", "Embarque"),
            ColSpec("proveedor", "Proveedor", width="medium"), ColSpec("puerto", "Puerto"),
            ColSpec("destino", "Destino"), ColSpec("estructura", "Estructura"),
            ColSpec("tipo_negocio", "Tipo de negocio"), ColSpec("f_instruccion", "Instrucción", "date"),
            ColSpec("etd", "ETD", "date"), ColSpec("eta", "ETA", "date"),
            ColSpec("m3", "M3", "num"), ColSpec("fob", "FOB (USD)", "usd"),
            ColSpec("responsable", "Responsable"),
        ], key="pl_so", filename="pipeline_so")
