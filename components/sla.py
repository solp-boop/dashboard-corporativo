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
def productos_table(summary: pd.DataFrame, today: pd.Timestamp) -> None:
    """Grupo × estructura: mediana por trimestre del año, objetivo (Q1 −15 %) y estado."""
    qs = ["Q1", "Q2", "Q3", "Q4"]
    this_q = f"Q{(today.month - 1) // 3 + 1}"
    head = (["Grupo", "Estructura"] + [q + ("*" if q == this_q else "") for q in qs]
            + [f"Año {today.year}", "Objetivo", "Variación", "Estado"])
    colors = {"Cumple": "ok", "Reduce, sin llegar": "warn", "No reduce": "bad"}
    rows = []
    span = summary.groupby("grupo", sort=False)["grupo"].transform("size")
    first = ~summary["grupo"].duplicated()
    for idx, r in summary.iterrows():
        cells = []
        for q in qs:
            v, n = r[q], r[q + "_n"]
            if v != v:
                cells.append('<td class="na">—</td>')
                continue
            tag = " · base" if q == r["base_q"] else (" · actual" if q == r["actual_q"] else "")
            cls = ' class="hl"' if tag else ""
            cells.append(f'<td{cls}>{fmt.fmt_int(v)} d<span class="n">n={fmt.fmt_int(n)}{tag}</span></td>')
        anio = (f'<td>{fmt.fmt_int(r["anio"])} d<span class="n">n={fmt.fmt_int(r["anio_n"])}</span></td>'
                if r["anio"] == r["anio"] else '<td class="na">—</td>')
        estado = r["estado"]
        dot = f'<i class="dot {colors[estado]}"></i>' if estado in colors else ""
        var = (f'{fmt.fmt_pct(r["variacion"], signed=True)}<span class="n">{r["actual_q"]} vs {r["base_q"]}</span>'
               if r["variacion"] == r["variacion"] else "—")
        rows.append(
            "<tr>" + (f"<th class='rowh' rowspan='{span[idx]}'>{html.escape(r['grupo'])}</th>" if first[idx] else "")
            + f"<td style='text-align:left'>{r['estructura']}</td>"
            + "".join(cells) + anio
            + f"<td>{fmt.fmt_num(r['objetivo'], 1) + ' d' if r['objetivo'] == r['objetivo'] else '—'}</td>"
            f"<td class='var'>{var}</td>"
            f"<td style='text-align:left'>{dot}{html.escape(estado or 'Muestra chica')}</td></tr>")
    st.markdown('<div class="scorecard compact"><table><thead><tr>' + "".join(f"<th>{h}</th>" for h in head)
                + f'</tr></thead><tbody>{"".join(rows)}</tbody></table></div>', unsafe_allow_html=True)
    notas = sorted({n for n in summary["nota"] if n})
    st.caption(f"*{this_q} en curso. Mediana de días de consolidación por SO, por trimestre de ETD. Base = Q1; objetivo = base −15 %; "
               "se compara el último trimestre cerrado («actual») contra la base. La columna del año es la "
               "mediana de todas las SO del año." + (" " + " ".join(notas) if notas else ""))


def productos_mes_table(t: pd.DataFrame, today: pd.Timestamp) -> None:
    """Tabla mes a mes: SO y mediana de consolidación por grupo y estructura."""
    if t.empty:
        st.markdown('<div class="empty">Sin datos.</div>', unsafe_allow_html=True)
        return
    grupos = t.attrs.get("grupos", {})
    ests = ["Consolidado", "Monoproveedor"]
    h1 = ['<th rowspan="3">Mes ETD</th>'] + [f'<th colspan="4" style="text-align:center">{html.escape(l)}</th>'
                                             for l in grupos.values()]
    h2 = [f'<th colspan="2" style="text-align:center">{e}</th>' for _ in grupos for e in ests]
    h3 = ["<th>SO</th><th>Mediana</th>" for _ in grupos for _ in ests]
    this_month = today.to_period("M").to_timestamp()
    rows = []
    for _, r in t.iterrows():
        total = pd.isna(r["mes"])
        label = (f"Total {today.year}" if total else
                 fmt.fmt_month(r["mes"], long=True) + (" · en curso" if r["mes"] == this_month else ""))
        cells = []
        for g in grupos:
            for e in ests:
                n, m = r[f"{g}|{e}|so"], r[f"{g}|{e}|med"]
                cells.append(f"<td>{fmt.fmt_int(n) if n else '—'}</td>"
                             f"<td>{fmt.fmt_int(m) + ' d' if m == m else '—'}</td>")
        style = " style='font-weight:600;background:rgba(120,130,150,0.10)'" if total else ""
        rows.append(f"<tr{style}><th class='rowh'>{html.escape(label)}</th>{''.join(cells)}</tr>")
    st.markdown('<div class="scorecard compact"><table><thead><tr>' + "".join(h1) + "</tr><tr>" + "".join(h2)
                + "</tr><tr>" + "".join(h3) + f'</tr></thead><tbody>{"".join(rows)}</tbody></table></div>',
                unsafe_allow_html=True)
    st.caption("Embarques Historicos: SO marítimas ya zarpadas, por mes de ETD. Mediana del «Tiempo de "
               "consolidacion» por SO; la estructura es la del embarque en Reservas Históricas. "
               "La fila del total es la mediana de todas las SO del año (no la suma de los meses).")


def productos_q_chart(summary: pd.DataFrame, grupo_label: str, today: pd.Timestamp, key: str) -> None:
    """Barras por trimestre (consolidado / monoproveedor) con el objetivo como línea punteada."""
    s = summary[summary["grupo"] == grupo_label]
    if s.empty or s[["Q1", "Q2", "Q3", "Q4"]].isna().all().all():
        st.markdown('<div class="empty">Sin datos.</div>', unsafe_allow_html=True)
        return
    qs = ["Q1", "Q2", "Q3", "Q4"]
    this_q = f"Q{(today.month - 1) // 3 + 1}"
    x = [q + (" (en curso)" if q == this_q else "") for q in qs]
    fig = go.Figure()
    for i, est in enumerate(["Consolidado", "Monoproveedor"]):
        r = s[s["estructura"] == est]
        if r.empty:
            continue
        r = r.iloc[0]
        color = settings.SERIES[0] if est == "Consolidado" else settings.SERIES[2]
        y = [r[q] for q in qs]
        n = [r[q + "_n"] for q in qs]
        fig.add_bar(x=x, y=y, name=est, marker=dict(
                        color=color, cornerradius=4,
                        pattern=dict(shape=["/" if q == this_q else "" for q in qs], fgcolor="white", size=6)),
                    text=[f"{fmt.fmt_int(v)} d" if v == v else "" for v in y], textposition="outside",
                    cliponaxis=False, customdata=n, offsetgroup=str(i),
                    hovertemplate=f"{est} · %{{x}}: %{{y:.0f}} d (%{{customdata}} SO)<extra></extra>")
        if r["objetivo"] == r["objetivo"]:
            fig.add_scatter(x=x, y=[r["objetivo"]] * 4, name=f"Obj. {fmt.fmt_num(r['objetivo'], 1)} d",
                            mode="lines", line=dict(color=color, width=1.5, dash="dash"),
                            hovertemplate=f"Objetivo {est.lower()}: %{{y:.1f}} d<extra></extra>")
    charts.theme(fig, height=320, y_title="días (mediana)")
    fig.update_layout(barmode="group", bargap=0.3)
    charts.show(fig, key=key)


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


def _air_monthly(a: pd.DataFrame) -> pd.DataFrame:
    d = a[a["sla_aereo"].notna()].assign(mes=lambda x: x["etd"].dt.to_period("M").dt.to_timestamp())
    d["ok"] = d["dias_aereo"] <= d["sla_aereo"]
    d["desvio"] = d["dias_aereo"] - d["sla_aereo"]
    return d


def air_compliance_chart(a: pd.DataFrame, today: pd.Timestamp, key: str, height: int = 300) -> None:
    """% dentro del SLA de su tipo, por mes. Antes del SLA: referencia en gris."""
    d = _air_monthly(a)
    if d.empty:
        st.markdown('<div class="empty">Sin embarques aéreos con «Total» y tipo con SLA.</div>',
                    unsafe_allow_html=True)
        return
    desde = pd.Timestamp(settings.SLA_AEREO_DESDE)
    this_month = today.to_period("M").to_timestamp()
    m = d.groupby("mes").agg(pct=("ok", "mean"), n=("ok", "size")).reset_index().sort_values("mes").tail(13)
    vig = m["mes"] >= desde
    labels = [fmt.fmt_month(x) + (" (parcial)" if x == this_month else "") for x in m["mes"]]
    fig = go.Figure(go.Bar(
        x=labels, y=m["pct"] * 100,
        marker=dict(color=[settings.SERIES[0] if v else settings.SERIES_OTHER for v in vig], cornerradius=4,
                    pattern=dict(shape=["/" if x == this_month else "" for x in m["mes"]], fgcolor="white", size=6)),
        text=[fmt.fmt_pct(v) for v in m["pct"]], textposition="outside", cliponaxis=False,
        customdata=list(zip(m["n"], ["SLA vigente" if v else "Referencia (antes del SLA)" for v in vig])),
        hovertemplate="%{x}<br>Dentro del SLA: %{y:.0f} %<br>%{customdata[1]}<br>Embarques: %{customdata[0]}"
                      "<extra></extra>",
    ))
    if settings.CUMPLIMIENTO_OBJETIVO is not None:
        fig.add_hline(y=settings.CUMPLIMIENTO_OBJETIVO * 100, line=dict(color=settings.COLORS["slate"], width=1.2,
                                                                         dash="dash"))
    if vig.any() and not vig.all():
        i = int(vig.values.argmax())
        fig.add_vline(x=i - 0.5, line=dict(color=settings.COLORS["slate"], width=1.2, dash="dot"))
        fig.add_annotation(x=i - 0.5, y=1, yref="paper", text="SLA vigente", showarrow=False, xanchor="left",
                           font=dict(size=11, color=settings.COLORS["slate"]))
    charts.theme(fig, height=height, y_suffix=" %", legend=False)
    fig.update_yaxes(range=[0, 110])
    charts.show(fig, key=key)


def air_deviation_chart(a: pd.DataFrame, today: pd.Timestamp, key: str, height: int = 320) -> None:
    """Días contra el SLA (Total − SLA del tipo), mediana por mes y tipo de negocio. 0 = justo en el SLA."""
    d = _air_monthly(a)
    if d.empty:
        st.markdown('<div class="empty">Sin datos.</div>', unsafe_allow_html=True)
        return
    months = sorted(d["mes"].unique())[-13:]
    x = [fmt.fmt_month(m) for m in months]
    top = list(d["tipo_sla"].value_counts().index[:4])
    cmap = charts.color_map([TIPO_LABEL.get(t, t) for t in top])
    fig = go.Figure()
    for t in top:
        s = d[d["tipo_sla"] == t].groupby("mes")["desvio"].agg(["median", "size"]).reindex(months)
        name = TIPO_LABEL.get(t, t)
        fig.add_scatter(x=x, y=s["median"], name=name, mode="lines+markers", connectgaps=True,
                        line=dict(color=cmap[name], width=2), marker=dict(size=8), customdata=s["size"].fillna(0),
                        hovertemplate=f"{name}: %{{y:+.0f}} d vs SLA (%{{customdata}} emb.)<extra></extra>")
    fig.add_hline(y=0, line=dict(color=settings.COLORS["slate"], width=1.2, dash="dash"),
                  annotation_text="SLA", annotation_position="top left",
                  annotation_font=dict(size=11, color=settings.COLORS["slate"]))
    charts.theme(fig, height=height, y_title="días vs SLA (mediana)")
    fig.update_yaxes(rangemode="normal", zeroline=False)
    charts.show(fig, key=key)
    if d["tipo_sla"].nunique() > 4:
        st.caption("Se muestran los 4 tipos con más embarques; el resto está en la tabla.")
