"""Visualizaciones de SLA: gráfico mensual con mes en curso parcial y tabla de cierre."""
from __future__ import annotations

import html

import numpy as np

import pandas as pd
import plotly.graph_objects as go
import streamlit as st

from components import charts
from config import settings
from utils import formatting as fmt
from utils.sla import Celda, Cierre

STATUS = {"ok": settings.COLORS["green"], "warn": settings.COLORS["amber"], "bad": settings.COLORS["red"]}


def compliance_chart(monthly: pd.DataFrame, today: pd.Timestamp, key: str, height: int = 300) -> None:
    """Barras de % dentro del SLA por mes; el mes en curso va claro y rayado ('parcial')."""
    if monthly.empty:
        st.markdown('<div class="empty">Sin embarques con datos suficientes.</div>', unsafe_allow_html=True)
        return
    this_month = today.to_period("M").to_timestamp()
    m = monthly.sort_values("mes").tail(13)
    labels = [fmt.fmt_month(x) + (" (parcial)" if x == this_month else "") for x in m["mes"]]
    partial = [x == this_month for x in m["mes"]]
    colors = [settings.SERIES[1] if p else settings.SERIES[0] for p in partial]
    fig = go.Figure(go.Bar(
        x=labels, y=m["pct"] * 100,
        marker=dict(color=colors, cornerradius=4,
                    pattern=dict(shape=["/" if p else "" for p in partial], fgcolor="white", size=6)),
        text=[fmt.fmt_pct(v) for v in m["pct"]], textposition="outside", cliponaxis=False,
        customdata=m["n"],
        hovertemplate="%{x}<br>Dentro del SLA: %{y:.0f} %<br>Embarques: %{customdata}<extra></extra>",
    ))
    if settings.CUMPLIMIENTO_OBJETIVO is not None:
        fig.add_hline(y=settings.CUMPLIMIENTO_OBJETIVO * 100,
                      line=dict(color=settings.COLORS["slate"], width=1.2, dash="dash"),
                      annotation_text=f"Objetivo {fmt.fmt_pct(settings.CUMPLIMIENTO_OBJETIVO)}",
                      annotation_position="top left",
                      annotation_font=dict(size=11, color=settings.COLORS["slate"]))
    charts.theme(fig, height=height, y_suffix=" %", legend=False)
    fig.update_yaxes(range=[0, 110])
    charts.show(fig, key=key)


def _fmt_celda(c: Celda) -> str:
    if c.valor != c.valor:
        return '<td class="na">—</td>'
    v = fmt.fmt_pct(c.valor) if c.tipo == "pct" else f"{fmt.fmt_int(c.valor)} d"
    dot = f'<i class="dot {c.estado}"></i>' if c.estado else ""
    small = (f'<span class="n">n={c.n}</span>' if c.n < settings.MIN_SAMPLE
             else f'<span class="n">n={fmt.fmt_int(c.n)}</span>')
    return f"<td>{dot}{html.escape(v)}{small}</td>"


def scorecard_table(sc: Cierre) -> None:
    head = "".join(f"<th>{html.escape(c)}</th>" for c in ["Indicador"] + sc.columnas)
    rows = []
    for label, cells in sc.filas:
        tds = []
        for c in cells:
            tds.append(f'<td class="var">{html.escape(c)}</td>' if isinstance(c, str) else _fmt_celda(c))
        rows.append(f"<tr><th class='rowh'>{html.escape(label)}</th>{''.join(tds)}</tr>")
    st.markdown(f'<div class="scorecard"><table><thead><tr>{head}</tr></thead>'
                f'<tbody>{"".join(rows)}</tbody></table></div>', unsafe_allow_html=True)
    obj = (f"cumplimiento contra el objetivo de {fmt.fmt_pct(settings.CUMPLIMIENTO_OBJETIVO)}"
           if settings.CUMPLIMIENTO_OBJETIVO is not None else "cumplimiento sin objetivo definido")
    st.caption(f"Semáforo: tiempos contra su SLA; {obj}. Sin color cuando hay menos de "
               f"{settings.MIN_SAMPLE} embarques (n). «Proyectado» suma a lo ya zarpado las Reservas con ETD en el mes.")


# ---------------------------------------------------------------------------
# Aéreos
# ---------------------------------------------------------------------------
def air_zarpados(aer: pd.DataFrame, today: pd.Timestamp) -> pd.DataFrame:
    return aer[(aer["etd"] <= today) & aer["dias_aereo"].notna()]


def air_chart(a: pd.DataFrame, today: pd.Timestamp, key: str, height: int = 300) -> None:
    """Mediana del tiempo total aéreo por mes; antes del SLA en gris, desde el SLA en azul."""
    if a.empty:
        st.markdown('<div class="empty">Sin embarques aéreos con «Total» cargado.</div>', unsafe_allow_html=True)
        return
    d = a.assign(mes=a["etd"].dt.to_period("M").dt.to_timestamp())
    desde = pd.Timestamp(settings.SLA_AEREO_DESDE)
    this_month = today.to_period("M").to_timestamp()
    rows = []
    for mes, g in d.groupby("mes"):
        con_sla = g[g["sla_aereo"].notna()]
        pct = (con_sla["dias_aereo"] <= con_sla["sla_aereo"]).mean() if (mes >= desde and len(con_sla)) else None
        rows.append((mes, g["dias_aereo"].median(), len(g), pct))
    m = pd.DataFrame(rows, columns=["mes", "mediana", "n", "pct"]).sort_values("mes").tail(13)
    vigente = m["mes"] >= desde
    labels = [fmt.fmt_month(x) + (" (parcial)" if x == this_month else "") for x in m["mes"]]
    colors = [settings.SERIES[0] if v else settings.SERIES_OTHER for v in vigente]
    hover = [f"Dentro del SLA: {fmt.fmt_pct(p)}" if p is not None and p == p else "Antes del SLA"
             for p in m["pct"]]
    fig = go.Figure(go.Bar(
        x=labels, y=m["mediana"], marker=dict(color=colors, cornerradius=4,
                                              pattern=dict(shape=["/" if x == this_month else "" for x in m["mes"]],
                                                           fgcolor="white", size=6)),
        text=[f"{fmt.fmt_int(v)} d" for v in m["mediana"]], textposition="outside", cliponaxis=False,
        customdata=list(zip(m["n"], hover)),
        hovertemplate="%{x}<br>Mediana: %{y:.0f} d<br>%{customdata[1]}<br>Embarques: %{customdata[0]}<extra></extra>",
    ))
    if vigente.any() and not vigente.all():
        i = int(vigente.values.argmax())
        fig.add_vline(x=i - 0.5, line=dict(color=settings.COLORS["slate"], width=1.2, dash="dash"))
        fig.add_annotation(x=i - 0.5, y=1, yref="paper", text="SLA vigente", showarrow=False, xanchor="left",
                           font=dict(size=11, color=settings.COLORS["slate"]))
    charts.theme(fig, height=height, y_title="días", legend=False)
    charts.show(fig, key=key)


TIPO_LABEL = {"REPUESTOS": "Repuestos", "MUESTRAS": "Muestras", "DJI AGRAS": "DJI Agras", "MARCAS": "Marcas"}


def air_table(a: pd.DataFrame, today: pd.Timestamp) -> pd.DataFrame:
    """Por tipo de negocio: antes del SLA, desde el SLA y último mes cerrado."""
    desde = pd.Timestamp(settings.SLA_AEREO_DESDE)
    last = today.to_period("M").to_timestamp() - pd.offsets.MonthBegin(1)
    nxt = last + pd.offsets.MonthBegin(1)
    rows = []
    tipos = list(settings.SLA_AEREO_POR_TIPO)
    for tipo in tipos + ["Sin SLA definido"]:
        g = a[a["tipo_sla"].isna()] if tipo == "Sin SLA definido" else a[a["tipo_sla"] == tipo.upper()]
        antes, vig = g[g["etd"] < desde], g[g["etd"] >= desde]
        ult = g[(g["etd"] >= last) & (g["etd"] < nxt)]
        sla = settings.SLA_AEREO_POR_TIPO.get(tipo)

        def pct(x):
            return (x["dias_aereo"] <= x["sla_aereo"]).mean() if len(x) and sla else np.nan

        rows.append({
            "tipo": TIPO_LABEL.get(tipo, tipo), "sla": sla,
            "antes": antes["dias_aereo"].median(), "antes_n": len(antes),
            "desde": vig["dias_aereo"].median(), "desde_n": len(vig), "desde_pct": pct(vig),
            "ult": ult["dias_aereo"].median(), "ult_n": len(ult), "ult_pct": pct(ult),
        })
    out = pd.DataFrame(rows)
    return out[(out["antes_n"] + out["desde_n"]) > 0]


# ---------------------------------------------------------------------------
# SKU nuevos y top ranking
# ---------------------------------------------------------------------------
def productos_table(summary: pd.DataFrame) -> None:
    head = ["Grupo", "Estructura", "Base", "Actual", "Variación", "Objetivo (−15 %)", "Estado", "SO en el año"]
    rows = []
    colors = {"Cumple": "ok", "Reduce, sin llegar": "warn", "No reduce": "bad"}
    for _, r in summary.iterrows():
        def d(v, n, per):
            if v != v:
                return '<td class="na">—</td>'
            return f'<td>{fmt.fmt_int(v)} d<span class="n">{html.escape(per)} · n={fmt.fmt_int(n)}</span></td>'
        estado = r["estado"]
        dot = f'<i class="dot {colors[estado]}"></i>' if estado in colors else ""
        var = fmt.fmt_pct(r["variacion"], signed=True) if r["variacion"] == r["variacion"] else "—"
        rows.append(
            f"<tr><th class='rowh'>{html.escape(r['grupo'])}</th><td style='text-align:left'>{r['estructura']}</td>"
            f"{d(r['base'], r['base_n'], r['base_txt'])}{d(r['actual'], r['actual_n'], r['actual_txt'])}"
            f"<td class='var'>{var}</td>"
            f"<td>{fmt.fmt_num(r['objetivo'], 1) + ' d' if r['objetivo'] == r['objetivo'] else '—'}</td>"
            f"<td style='text-align:left'>{dot}{html.escape(estado or 'Muestra chica')}</td>"
            f"<td>{fmt.fmt_int(r['so_anio'])}</td></tr>")
    st.markdown('<div class="scorecard"><table><thead><tr>' + "".join(f"<th>{h}</th>" for h in head)
                + f'</tr></thead><tbody>{"".join(rows)}</tbody></table></div>', unsafe_allow_html=True)
    notas = sorted({n for n in summary["nota"] if n})
    st.caption("Mediana del «Tiempo de consolidacion» por SO (Embarques Historicos), según la estructura del "
               "embarque en Reservas Históricas. Base y actual por mes de ETD; «actual» = últimos "
               f"{settings.COMPARACION_MESES} meses cerrados." + (" " + " ".join(notas) if notas else ""))


def productos_chart(monthly: pd.DataFrame, summary: pd.DataFrame, grupo_label: str, key: str) -> None:
    if monthly.empty:
        st.markdown('<div class="empty">Sin datos.</div>', unsafe_allow_html=True)
        return
    fig = go.Figure()
    months = sorted(monthly["mes"].unique())
    x = [fmt.fmt_month(m) for m in months]
    for i, est in enumerate(["Consolidado", "Monoproveedor"]):
        s = monthly[monthly["estructura"] == est].set_index("mes").reindex(months)
        color = settings.SERIES[i]
        fig.add_scatter(x=x, y=s["mediana"], name=est, mode="lines+markers",
                        line=dict(color=color, width=2), marker=dict(size=8), customdata=s["so"].fillna(0),
                        hovertemplate=f"{est}: %{{y:.0f}} d (%{{customdata}} SO)<extra></extra>")
        obj = summary[(summary["grupo"] == grupo_label) & (summary["estructura"] == est)]["objetivo"]
        if len(obj) and obj.iloc[0] == obj.iloc[0]:
            fig.add_scatter(x=x, y=[obj.iloc[0]] * len(x), name=f"Objetivo {est.lower()}", mode="lines",
                            line=dict(color=color, width=1.2, dash="dash"),
                            hovertemplate=f"Objetivo {est.lower()}: %{{y:.1f}} d<extra></extra>")
    charts.theme(fig, height=300, y_title="días (mediana)")
    charts.show(fig, key=key)
