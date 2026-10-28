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
                    pattern=dict(shape=["/" if p else "" for p in partial], fgcolor="white", size=6, fillmode="overlay")),
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
                                                           fgcolor="white", size=6, fillmode="overlay")),
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


TIPO_LABEL = {"REPUESTOS": "Repuestos", "MUESTRAS": "Muestras", "DJI AGRAS": "DJI Agras", "MARCAS": "Marcas",
              "DJI": "DJI", "GADNIC": "GADNIC"}


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
    con_est = set(summary["estructura"]) != {"Total"}
    head = (["Grupo"] + (["Estructura"] if con_est else []) + [q + ("*" if q == this_q else "") for q in qs]
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
            + (f"<td style='text-align:left'>{r['estructura']}</td>" if con_est else "")
            + "".join(cells) + anio
            + f"<td>{fmt.fmt_num(r['objetivo'], 1) + ' d' if r['objetivo'] == r['objetivo'] else '—'}</td>"
            f"<td class='var'>{var}</td>"
            f"<td style='text-align:left'>{dot}{html.escape(estado or 'Muestra chica')}</td></tr>")
    st.markdown('<div class="scorecard compact"><table><thead><tr>' + "".join(f"<th>{h}</th>" for h in head)
                + f'</tr></thead><tbody>{"".join(rows)}</tbody></table></div>', unsafe_allow_html=True)
    notas = sorted({n for n in summary["nota"] if n})
    universo = ("" if con_est else " Universo completo: SO marítimas y aéreas con destino "
                f"{settings.PRODUCTOS_DESTINO or 'todos'}, sin muestras ni repuestos.")
    st.caption(f"\\*{this_q} en curso.{universo} Mediana de días de consolidación por SO, por trimestre de ETD. Base = Q1; objetivo = base −15 %; "
               "se compara el último trimestre cerrado («actual») contra la base. La columna del año es la "
               "mediana de todas las SO del año." + (" " + " ".join(notas) if notas else ""))


def ttm_botones(key: str = "prod_mes") -> tuple[str, str]:
    """Botones de Grupo y Medio del time to market: mandan sobre toda la sección."""
    from utils.productos import GRUPOS, MEDIOS
    labels = {"todas": "Todas las SO (100 %)", **GRUPOS}
    c1, c2 = st.columns([3, 2], gap="small")
    elegido = c1.segmented_control("Grupo", list(labels), default="todas", key=key,
                                   format_func=lambda g: labels[g]) or "todas"
    medio = c2.segmented_control("Medio", list(MEDIOS), default="todos", key=f"{key}_medio",
                                 format_func=lambda m: MEDIOS[m]) or "todos"
    return elegido, medio


def productos_mes_table(t: pd.DataFrame, today: pd.Timestamp, elegido: str = "todas", medio: str = "todos") -> None:
    """Tabla mes a mes del grupo y el medio elegidos: SO, % del universo, mínimo, mediana y máximo."""
    if t.empty:
        st.markdown('<div class="empty">Sin datos.</div>', unsafe_allow_html=True)
        return
    grupos = t.attrs.get("grupos", {})
    labels = {g: ("Todas las SO (100 %)" if g == "todas" else lbl) for g, lbl in grupos.items()}
    this_month = today.to_period("M").to_timestamp()
    tot_so = t.iloc[-1]["todas|todos|so"] if "todas|todos|so" in t else 0
    pre = f"{elegido}|{medio}"

    def d(v, bold=False):
        if v != v:
            return "<td class='na'>—</td>"
        txt = f"{fmt.fmt_int(v)} d"
        return f"<td><b>{txt}</b></td>" if bold else f"<td>{txt}</td>"

    head = ["Mes ETD", "SO", "% del universo", "Mín.", "Mediana", "Máx."]
    rows = []
    for _, r in t.iterrows():
        total = pd.isna(r["mes"])
        label = (f"Total {today.year}" if total else
                 fmt.fmt_month(r["mes"], long=True) + (" · en curso" if r["mes"] == this_month else ""))
        n, base = r[f"{pre}|so"], r["todas|todos|so"]
        pct = fmt.fmt_pct(n / base) if base else "—"
        style = " style='font-weight:600;background:rgba(120,130,150,0.10)'" if total else ""
        rows.append(f"<tr{style}><th class='rowh'>{html.escape(label)}</th>"
                    f"<td>{fmt.fmt_int(n) if n else '—'}</td><td>{pct if n else '—'}</td>"
                    + d(r[f"{pre}|min"]) + d(r[f"{pre}|med"], bold=True) + d(r[f"{pre}|max"]) + "</tr>")
    st.markdown('<div class="scorecard compact"><table><thead><tr>' + "".join(f"<th>{h}</th>" for h in head)
                + f'</tr></thead><tbody>{"".join(rows)}</tbody></table></div>', unsafe_allow_html=True)
    tot = t.iloc[-1]
    mar, aer, otro = (int(tot.get(f"{elegido}|{m}|so", 0)) for m in ("Marítimo", "Aéreo", "otro"))
    tod = int(tot.get(f"{elegido}|todos|so", 0))
    cierra = "cierra" if mar + aer + otro == tod else "no cierra"
    st.caption(f"Control {today.year} · {labels[elegido]}: {fmt.fmt_int(tod)} SO = {fmt.fmt_int(mar)} marítimas + "
               f"{fmt.fmt_int(aer)} aéreas + {fmt.fmt_int(otro)} fuera de ambos (AIR DJI Baynal / RC Online / Aeropix "
               f"u otro código) → {cierra}.")
    st.caption(f"\\* Universo completo: SO de Embarques Historicos ya zarpadas, con destino "
               f"{settings.PRODUCTOS_DESTINO or 'todos'}, sin muestras ni repuestos (tipo de negocio aéreo MUESTRAS / "
               f"REPUESTOS y SO «Muestras» / «Repuestos» en Planificación). {fmt.fmt_int(tot_so)} SO en el año, por mes "
               "de ETD. SO = SO por envío (una SO que viajó en 2 embarques cuenta 2). Marítimo = embarques FCL; "
               "aéreo = embarques AIR sin DJI Baynal / RC Online / Aeropix. Días de consolidación por SO («Tiempo de "
               "consolidacion»): mínimo, mediana y máximo; 0 días o negativos son sin dato. «% del universo» = SO del "
               "cuadro / todas las SO del mes. El total toma todas las SO del año (no es la suma de los meses).")


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
                        pattern=dict(shape=["/" if q == this_q else "" for q in qs], fgcolor="white", size=6, fillmode="overlay")),
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


def objetivo_q_chart(summary: pd.DataFrame, today: pd.Timestamp, key: str) -> None:
    """Barras por trimestre, una serie por grupo, con el objetivo de cada grupo como línea punteada."""
    if summary.empty or summary[["Q1", "Q2", "Q3", "Q4"]].isna().all().all():
        st.markdown('<div class="empty">Sin datos.</div>', unsafe_allow_html=True)
        return
    qs = ["Q1", "Q2", "Q3", "Q4"]
    this_q = f"Q{(today.month - 1) // 3 + 1}"
    x = [q + (" (en curso)" if q == this_q else "") for q in qs]
    fig = go.Figure()
    for i, (_, r) in enumerate(summary.iterrows()):
        color = settings.SERIES[i % len(settings.SERIES)]
        y = [r[q] for q in qs]
        fig.add_bar(x=x, y=y, name=r["grupo"], marker=dict(
                        color=color, cornerradius=4,
                        pattern=dict(shape=["/" if q == this_q else "" for q in qs], fgcolor="white", size=6, fillmode="overlay")),
                    text=[f"{fmt.fmt_int(v)} d" if v == v else "" for v in y], textposition="outside",
                    cliponaxis=False, customdata=[r[q + "_n"] for q in qs], offsetgroup=str(i),
                    hovertemplate=f"{r['grupo']} · %{{x}}: %{{y:.0f}} d (%{{customdata}} SO)<extra></extra>")
        if r["objetivo"] == r["objetivo"]:
            fig.add_scatter(x=x, y=[r["objetivo"]] * 4, name=f"Obj. {fmt.fmt_num(r['objetivo'], 1)} d",
                            mode="lines", line=dict(color=color, width=1.5, dash="dash"),
                            hovertemplate=f"Objetivo {r['grupo']}: %{{y:.1f}} d<extra></extra>")
    charts.theme(fig, height=340, y_title="días (mediana)")
    fig.update_layout(barmode="group", bargap=0.25)
    charts.show(fig, key=key)


def objetivo_mes_chart(mensual: pd.DataFrame, summary: pd.DataFrame, key: str) -> None:
    """Mediana mensual por grupo, con el objetivo de cada grupo como línea punteada."""
    if mensual.empty:
        st.markdown('<div class="empty">Sin datos.</div>', unsafe_allow_html=True)
        return
    months = sorted(mensual["mes"].unique())
    x = [fmt.fmt_month(m) for m in months]
    fig = go.Figure()
    for i, (_, r) in enumerate(summary.iterrows()):
        color = settings.SERIES[i % len(settings.SERIES)]
        s = mensual[mensual["grupo"] == r["grupo"]].set_index("mes").reindex(months)
        fig.add_scatter(x=x, y=s["mediana"], name=r["grupo"], mode="lines+markers",
                        line=dict(color=color, width=2), marker=dict(size=8), customdata=s["so"].fillna(0),
                        hovertemplate=f"{r['grupo']}: %{{y:.0f}} d (%{{customdata}} SO)<extra></extra>")
        if r["objetivo"] == r["objetivo"]:
            fig.add_scatter(x=x, y=[r["objetivo"]] * len(x), name=f"Objetivo {r['grupo']}", mode="lines",
                            line=dict(color=color, width=1.2, dash="dash"), showlegend=False,
                            hovertemplate=f"Objetivo {r['grupo']}: %{{y:.1f}} d<extra></extra>")
    charts.theme(fig, height=320, y_title="días (mediana)")
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
                    pattern=dict(shape=["/" if x == this_month else "" for x in m["mes"]], fgcolor="white", size=6, fillmode="overlay")),
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


# ---------------------------------------------------------------------------
# Matrices mes a mes (tablas HTML con el estilo de cierre de mes)
# ---------------------------------------------------------------------------
def _mes_txt(m: pd.Timestamp, today: pd.Timestamp) -> str:
    return fmt.fmt_month(m).capitalize() + ("*" if m == today.to_period("M").to_timestamp() else "")


def tipo_mes_matrix(t: pd.DataFrame, today: pd.Timestamp, medida: str = "dias") -> None:
    """Tipo de negocio × mes de ETD. medida="dias": mediana de días (verde si ≤ SLA del tipo, rojo si no);
    medida="pct": % de embarques dentro del SLA de su tipo (verde si llega al objetivo); medida="cant": cantidad de
    embarques, con el total del período al final."""
    if t.empty:
        st.markdown('<div class="empty">Sin aéreos con «Total» cargado en el período.</div>', unsafe_allow_html=True)
        return
    desde = pd.Timestamp(settings.SLA_AEREO_DESDE)
    meses = sorted(t["mes"].unique())
    orden = [TIPO_LABEL.get(k, k.title()) for k in settings.SLA_AEREO_POR_TIPO]
    tipos = [x for x in orden if x in set(t["tipo"])] + sorted(set(t["tipo"]) - set(orden) - {"Todos"}) + ["Todos"]
    idx = t.set_index(["tipo", "mes"])
    sla_tipo = {k: t.loc[t["tipo"] == k, "sla"].dropna().median() for k in tipos}
    obj = settings.CUMPLIMIENTO_OBJETIVO

    head = ["Tipo de negocio", "SLA"] + [_mes_txt(m, today) for m in meses] + (["Total"] if medida == "cant" else [])
    body = []
    for tp in tipos:
        sla_v = sla_tipo.get(tp)
        cells = [f"<th class='rowh'>{html.escape(tp)}</th>",
                 f"<td>{fmt.fmt_int(sla_v) + ' d' if sla_v == sla_v and sla_v is not None else '—'}</td>"]
        for m in meses:
            if (tp, m) not in idx.index:
                cells.append("<td class='na'>—</td>")
                continue
            r = idx.loc[(tp, m)]
            pre = " pre" if m < desde else ""
            if medida == "cant":
                cells.append(f"<td class='{pre.strip()}'>{fmt.fmt_int(r['n'])}</td>")
                continue
            if medida == "pct":
                if r["pct"] != r["pct"]:
                    cells.append(f"<td class='na{pre}'>—<span class='n'>n={int(r['n'])}</span></td>")
                    continue
                cls = "ok" if r["pct"] >= obj else "bad"
                cells.append(f"<td class='{cls}{pre}'>{fmt.fmt_pct(r['pct'])}"
                             f"<span class='n'>{int(r['dentro'])} de {int(r['n'])}</span></td>")
            else:
                cls = "" if tp == "Todos" or sla_v != sla_v or sla_v is None else \
                    ("ok" if r["mediana"] <= sla_v else "bad")
                cells.append(f"<td class='{cls}{pre}'>{fmt.fmt_int(r['mediana'])} d"
                             f"<span class='n'>n={int(r['n'])}</span></td>")
        if medida == "cant":
            cells.append(f"<td><b>{fmt.fmt_int(t.loc[t['tipo'] == tp, 'n'].sum())}</b></td>")
        style = " class='tot'" if tp == "Todos" else ""
        body.append(f"<tr{style}>" + "".join(cells) + "</tr>")
    st.markdown('<div class="scorecard compact matriz"><table><thead><tr>' + "".join(f"<th>{h}</th>" for h in head)
                + f'</tr></thead><tbody>{"".join(body)}</tbody></table></div>', unsafe_allow_html=True)


def mes_matrix(d: pd.DataFrame, columnas: list[tuple[str, str]], today: pd.Timestamp,
               resaltar: list[str] | None = None, extra: list[tuple[str, str]] | None = None,
               pct: tuple[str, str] | None = None, textos: list[tuple[str, str]] | None = None,
               fecha: str = "Mes ETD", n_label: str = "Embarques", textos_al_final: bool = False,
               total_label: str | None = None, medio_dia: bool = False) -> None:
    """Meses (filas) × etapas o tramos (columnas): mediana de días. `resaltar`: columnas entre las que se marca
    la más larga de cada mes. `extra`: columnas que se muestran después, sin resaltar. `pct`: (columna, título) de
    un % de cumplimiento, en verde si llega al objetivo y en rojo si no."""
    if d.empty:
        st.markdown('<div class="empty">Sin datos.</div>', unsafe_allow_html=True)
        return
    extra = extra or []
    textos = textos or []
    t_ini, t_fin = ([], textos) if textos_al_final else (textos, [])
    head = [fecha, n_label] + [lbl for _, lbl in t_ini] + ([pct[1]] if pct else []) + \
        [lbl for _, lbl in columnas + extra] + [lbl for _, lbl in t_fin]
    body = []
    for _, r in d.sort_values("mes", na_position="last").iterrows():
        cand = {c: r.get(c) for c in (resaltar or []) if r.get(c) == r.get(c) and r.get(c) is not None}
        mx = max(cand, key=cand.get) if cand else None
        total = pd.isna(r["mes"])
        mes_txt = (total_label or f"Total {today.year}") if total else _mes_txt(r["mes"], today)
        cells = [f"<th class='rowh'>{mes_txt}</th>", f"<td>{fmt.fmt_int(r['n'])}</td>"]
        for c, _ in t_ini:
            v = r.get(c)
            cells.append(f"<td>{html.escape(str(v)) if isinstance(v, str) and v else '—'}</td>")
        if pct:
            v = r.get(pct[0])
            cells.append("<td class='na'>—</td>" if v != v or v is None else
                         f"<td class='{'ok' if v >= settings.CUMPLIMIENTO_OBJETIVO else 'bad'}'>{fmt.fmt_pct(v)}</td>")
        for c, _ in columnas + extra:
            v = r.get(c)
            if v != v or v is None:
                cells.append("<td class='na'>—</td>")
            else:
                txt = (f"{v:.1f}".replace(".", ",") if medio_dia and v % 1 else fmt.fmt_int(v))
                cells.append(f"<td class='{'hl' if c == mx else ''}'>{txt} d</td>")
        for c, _ in t_fin:
            v = r.get(c)
            cells.append(f"<td>{html.escape(str(v)) if isinstance(v, str) and v else '—'}</td>")
        body.append(("<tr class='tot'>" if total else "<tr>") + "".join(cells) + "</tr>")
    st.markdown('<div class="scorecard compact matriz"><table><thead><tr>' + "".join(f"<th>{h}</th>" for h in head)
                + f'</tr></thead><tbody>{"".join(body)}</tbody></table></div>', unsafe_allow_html=True)


def linea_mes_matrix(g: pd.DataFrame, today: pd.Timestamp, medida: str = "pct", max_lineas: int = 10,
                     titulo: str = "Línea marítima") -> None:
    """Línea marítima × mes de ETA. medida="pct": % de los contenedores que llegaron ese mes con cada línea;
    medida="tt": mediana de tránsito, con ▲ / ▼ contra el mes anterior de la misma línea (rojo si sube 5 d o más)."""
    if g.empty:
        st.markdown('<div class="empty">Sin embarques con ETA en el período.</div>', unsafe_allow_html=True)
        return
    meses = sorted(g["mes"].unique())[-12:]
    g = g[g["mes"].isin(meses)]
    orden = g.groupby("linea")["cont"].sum().sort_values(ascending=False)
    lineas = [x for x in orden.index if x != "Sin dato"][:max_lineas] + (["Sin dato"] if "Sin dato" in orden else [])
    idx = g.set_index(["linea", "mes"])
    head = [titulo, "Cont. en el período"] + [_mes_txt(m, today) for m in meses]
    body = []
    for ln in lineas:
        cells = [f"<th class='rowh'>{html.escape(ln)}</th>", f"<td>{fmt.fmt_int(orden[ln])}</td>"]
        prev = np.nan
        for m in meses:
            if (ln, m) not in idx.index:
                cells.append("<td class='na'>—</td>")
                continue
            r = idx.loc[(ln, m)]
            if medida == "pct":
                cells.append(f"<td>{fmt.fmt_pct(r['pct'])}<span class='n'>{fmt.fmt_int(r['cont'])} cont.</span></td>")
            else:
                v = r["tt_med"]
                if v != v:
                    cells.append("<td class='na'>—<span class='n'>en tránsito</span></td>")
                    continue
                dif = v - prev if prev == prev else np.nan
                cls = "bad" if dif == dif and dif >= 5 else ("ok" if dif == dif and dif <= -5 else "")
                flecha = (f"{'▲' if dif > 0 else '▼'} {fmt.fmt_int(abs(dif))} d" if dif == dif and dif != 0 else "")
                cells.append(f"<td class='{cls}'>{fmt.fmt_int(v)} d<span class='n'>{flecha or f'n={int(r.n)}'}</span></td>")
                prev = v
        body.append("<tr>" + "".join(cells) + "</tr>")
    if medida == "pct":
        tot = g.groupby("mes")["cont"].sum()
        body.append("<tr class='tot'><th class='rowh'>Total</th><td>" + fmt.fmt_int(tot.sum()) + "</td>"
                    + "".join(f"<td>100 %<span class='n'>{fmt.fmt_int(tot.get(m, 0))} cont.</span></td>" for m in meses)
                    + "</tr>")
    st.markdown('<div class="scorecard compact matriz"><table><thead><tr>' + "".join(f"<th>{h}</th>" for h in head)
                + f'</tr></thead><tbody>{"".join(body)}</tbody></table></div>', unsafe_allow_html=True)


def _var_td(v, sube_es_malo: bool = True) -> str:
    if v != v or v is None:
        return "<td class='na'>—</td>"
    cls = ("bad" if v > 0.005 else "ok" if v < -0.005 else "") if sube_es_malo else ""
    flecha = "▲" if v > 0.005 else ("▼" if v < -0.005 else "=")
    return f"<td class='{cls}'>{flecha} {fmt.fmt_pct(abs(v))}</td>"


def flete_mes_matrix(t: pd.DataFrame, today: pd.Timestamp) -> None:
    """Mes · mediana por contenedor · mismo mes del año anterior · variación."""
    if t.empty:
        st.markdown('<div class="empty">Sin fletes pagados para este contenedor.</div>', unsafe_allow_html=True)
        return
    y = today.year
    head = ["Mes ETD", "Embarques", f"Mediana / cont. {y}", f"Mismo mes {y - 1}", f"vs {y - 1}"]
    body = []
    for _, r in t.iterrows():
        total = pd.isna(r["mes"])
        lbl = f"Año {y} (a la fecha)" if total else _mes_txt(r["mes"], today)
        ant = r["anio_ant"]
        body.append(("<tr class='tot'>" if total else "<tr>")
                    + f"<th class='rowh'>{lbl}</th><td>{fmt.fmt_int(r['n'])}</td>"
                    + f"<td class='hl'>{fmt.fmt_usd(r['mediana'], compact=False)}</td>"
                    + (f"<td>{fmt.fmt_usd(ant, compact=False)}</td>" if ant == ant else "<td class='na'>—</td>")
                    + _var_td(r["var_anio"]) + "</tr>")
    st.markdown('<div class="scorecard compact matriz"><table><thead><tr>' + "".join(f"<th>{h}</th>" for h in head)
                + f'</tr></thead><tbody>{"".join(body)}</tbody></table></div>', unsafe_allow_html=True)


def cotizaciones_matrix(t: pd.DataFrame, agentes: list[str]) -> None:
    """Ruta × agente: la menor tarifa que cotizó cada uno (verde = la menor de la ruta; ● = el agente que más
    usamos en esa ruta), la menor, su variación contra el período anterior y con quién negociar."""
    if t.empty:
        st.markdown('<div class="empty">No hay cotizaciones para este período en nuestras rutas.</div>',
                    unsafe_allow_html=True)
        return
    head = ["Ruta", "Cont. 60 d"] + agentes + ["Menor tarifa", "vs período anterior", "Con quién negociar"]
    body = []
    for _, r in t.iterrows():
        cells = [f"<th class='rowh'>{html.escape(str(r['puerto']))} · {html.escape(str(r['tipo_ctnr']))}</th>",
                 f"<td>{fmt.fmt_int(r['contenedores'])}</td>"]
        for a in agentes:
            v = r.get(a)
            usa = isinstance(r["agente"], str) and r["agente"].strip().lower() == a.strip().lower()
            marca = " ●" if usa else ""
            if v != v or v is None:
                cells.append(f"<td class='na'>—{marca}</td>")
            else:
                cls = "ok" if v <= r["menor"] else ""
                cells.append(f"<td class='{cls}'>{fmt.fmt_int(v)}{marca}</td>")
        linea = r.get("menor_linea") if isinstance(r.get("menor_linea"), str) else None
        tt = r.get("menor_tt")
        tt = f"TT {fmt.fmt_int(tt)} d" if isinstance(tt, (int, float)) and tt == tt else None
        extra = " · ".join(x for x in (linea, tt) if x)
        cells.append(f"<td class='hl'>USD {fmt.fmt_int(r['menor'])}<span class='n'>{html.escape(str(r['menor_agente']))}"
                     f"{' · ' + html.escape(extra) if extra else ''}</span></td>")
        cells.append(_var_td(r["var"]))
        cls = {"Negociar": "bad", "Pedir": "", "OK": "ok"}.get(r["estado"], "")
        cells.append(f"<td class='{cls}' style='text-align:left;white-space:normal;min-width:16rem'>"
                     f"{html.escape(str(r['negociar']))}</td>")
        body.append("<tr>" + "".join(cells) + "</tr>")
    st.markdown('<div class="scorecard compact matriz"><table><thead><tr>' + "".join(f"<th>{h}</th>" for h in head)
                + f'</tr></thead><tbody>{"".join(body)}</tbody></table></div>', unsafe_allow_html=True)


# ---------------------------------------------------------------------------
# Objetivo −15 % contra el año anterior (utils.objetivo)
# ---------------------------------------------------------------------------
_EST_CLS = {"Cumple": "ok", "Reduce, sin llegar": "warn", "No reduce": "bad"}
_MESES_C = ["Ene", "Feb", "Mar", "Abr", "May", "Jun", "Jul", "Ago", "Sep", "Oct", "Nov", "Dic"]


def objetivo_kpis(res: dict, unidad: str) -> None:
    """Tres tarjetas: reducción mono, conso y total ponderada (acumulado del año contra el año anterior)."""
    from components.kpi_cards import KPI, kpi_row
    y, ult = res["anio"], res["ult_mes"]
    tramo = f"{_MESES_C[0].lower()}–{_MESES_C[ult - 1].lower()}" if ult >= 1 else ""
    obj = settings.REDUCCION_OBJETIVO
    st_map = {"Cumple": "ok", "Reduce, sin llegar": "warn", "No reduce": "bad"}
    cards = []
    ac = res["acumulado"].set_index("estructura") if len(res["acumulado"]) else pd.DataFrame()
    for e, lbl in (("Monoproveedor", "Monoproveedor"), ("Consolidado", "Consolidado")):
        if e not in ac.index or ac.loc[e, "var"] != ac.loc[e, "var"]:
            cards.append(KPI(f"{lbl} · vs {y - 1}", "—", sub=f"Sin datos de {y - 1} para comparar"))
            continue
        r = ac.loc[e]
        cards.append(KPI(f"{lbl} · vs {y - 1}", fmt.fmt_pct(r["var"], signed=True), status=st_map.get(r["estado"], ""),
                         badge=r["estado"] if r["estado"] in st_map else "",
                         sub=f"mediana {fmt.fmt_num(r['ant'], 1)} → <b>{fmt.fmt_num(r['act'], 1)} d</b> · objetivo "
                             f"{fmt.fmt_num(r['objetivo'], 1)} d · {tramo} · n={fmt.fmt_int(r['n_ant'])} / "
                             f"{fmt.fmt_int(r['n_act'])} {unidad}"))
    t = res["total"]
    pesos = " · ".join(f"{'mono' if k == 'Monoproveedor' else 'conso'} {v:.0%}" for k, v in t["pesos"].items())
    cards.append(KPI(f"Total ponderado · objetivo −{fmt.fmt_pct(obj)}",
                     fmt.fmt_pct(t["var"], signed=True) if t["var"] == t["var"] else "—",
                     status=st_map.get(t["estado"], ""), badge=t["estado"] if t["estado"] in st_map else "",
                     sub=((f"faltan <b>{fmt.fmt_num((t['var'] + obj) * 100, 1)} pp</b> · " if t["var"] > -obj else "")
                          + f"pesos {y}: {pesos}") if t["var"] == t["var"] and pesos else
                         f"Sin datos de {y - 1} para comparar",
                     help="Promedio de la variación de mono y de conso, ponderado por el volumen de este año. No "
                          "depende de cuánto mono o conso mandamos: si cambia la mezcla, el total no se mueve solo."))
    kpi_row(cards, columns=3)


def objetivo_matrix(res: dict, today: pd.Timestamp) -> None:
    """Mes × (mono, conso): mediana del año anterior, objetivo (−15 %), mediana de este año y variación."""
    m = res["mensual"]
    if m.empty:
        st.markdown('<div class="empty">Sin datos para comparar con el año anterior.</div>', unsafe_allow_html=True)
        return
    y = res["anio"]
    ests = [("Monoproveedor", "Monoproveedor"), ("Consolidado", "Consolidado")]
    head1 = "<tr><th rowspan='2'>Mes ETD</th>" + "".join(f"<th colspan='4'>{l}</th>" for _, l in ests) + "</tr>"
    head2 = "<tr>" + "".join(f"<th>{y - 1}</th><th>Objetivo</th><th>{y}</th><th>Variación</th>" for _ in ests) + "</tr>"

    def celdas(r) -> str:
        if r is None:
            return "<td class='na'>—</td>" * 4
        d = lambda v, n: (f"{fmt.fmt_num(v, 1)} d<span class='n'>n={fmt.fmt_int(n)}</span>"  # noqa: E731
                          if v == v else "—")
        cls = _EST_CLS.get(r["estado"], "pre" if r["estado"] == "En curso" else "")
        var = fmt.fmt_pct(r["var"], signed=True) if r["var"] == r["var"] else "—"
        if r["estado"] == "Muestra chica":
            var += "<span class='n'>muestra chica</span>"
        return (f"<td>{d(r['ant'], r['n_ant'])}</td><td>{fmt.fmt_num(r['objetivo'], 1) + ' d' if r['objetivo'] == r['objetivo'] else '—'}</td>"
                f"<td class='hl'>{d(r['act'], r['n_act'])}</td><td class='{cls}'>{var}</td>")
    body = []
    for mes in sorted(m["mes"].unique()):
        fila = f"<tr><th class='rowh'>{_MESES_C[mes - 1]}{'*' if mes == today.month else ''}</th>"
        for e, _ in ests:
            x = m[(m["mes"] == mes) & (m["estructura"] == e)]
            fila += celdas(x.iloc[0] if len(x) else None)
        body.append(fila + "</tr>")
    ac = res["acumulado"].set_index("estructura") if len(res["acumulado"]) else pd.DataFrame()
    if len(ac):
        lbl = f"Acumulado ene–{_MESES_C[res['ult_mes'] - 1].lower()}"
        body.append(f"<tr class='tot'><th class='rowh'>{lbl}</th>"
                    + "".join(celdas(ac.loc[e] if e in ac.index else None) for e, _ in ests) + "</tr>")
    st.markdown("<div class='scorecard compact matriz'><table><thead>" + head1 + head2 + "</thead><tbody>"
                + "".join(body) + "</tbody></table></div>", unsafe_allow_html=True)
    st.caption(f"Objetivo = mediana del mismo mes de {y - 1} × {1 - settings.REDUCCION_OBJETIVO:.2f}. Verde = bajó "
               f"{fmt.fmt_pct(settings.REDUCCION_OBJETIVO)} o más; amarillo = bajó menos; rojo = subió. Sin color si "
               f"algún año tiene menos de {settings.OBJ_MIN_N} casos. * mes en curso (no se califica).")


# ---------------------------------------------------------------------------
# Tránsito: dispersión contra Validaciones · Punta a punta mono vs conso
# ---------------------------------------------------------------------------
def _dias(v) -> str:
    return "—" if v != v or v is None else (f"{fmt.fmt_int(v)} d" if float(v).is_integer() else f"{fmt.fmt_num(v, 1)} d")


def dispersion_matrix(t: pd.DataFrame, today: pd.Timestamp, por: str = "mes") -> None:
    """Mes (o puerto) × dispersión: P25, mediana, P75, ancho P75 − P25 y % fuera de ± TT_RANGO_DIAS del tránsito
    de Validaciones (rojo cuando pasa TT_ALERTA_FUERA: hay que levantar la mano)."""
    if t.empty:
        st.markdown('<div class="empty">Sin embarques llegados.</div>', unsafe_allow_html=True)
        return
    r = settings.TT_RANGO_DIAS
    primera = "Mes ETA" if por == "mes" else "Puerto"
    head = [primera, "Embarques"] + (["Validaciones"] if por != "mes" else []) + \
        ["P25", "Mediana", "P75", "Dispersión (P75 − P25)", f"Fuera de ± {r} d", "Más largos", "Más cortos"]
    body = []
    rows = t.sort_values("mes", na_position="last") if por == "mes" else t
    for _, x in rows.iterrows():
        total = por == "mes" and pd.isna(x["mes"])
        lbl = (f"Total {today.year}" if total else _mes_txt(x["mes"], today)) if por == "mes" else html.escape(str(x["puerto"]))
        f = x["fuera"]
        cls = "" if f != f else ("bad" if f > settings.TT_ALERTA_FUERA else "ok")
        body.append(("<tr class='tot'>" if total else "<tr>") + f"<th class='rowh'>{lbl}</th><td>{fmt.fmt_int(x['n'])}</td>"
                    + (f"<td>{_dias(x['obj'])}</td>" if por != "mes" else "")
                    + f"<td>{_dias(x['p25'])}</td><td class='hl'>{_dias(x['med'])}</td><td>{_dias(x['p75'])}</td>"
                    + f"<td>{_dias(x['iqr'])}</td>"
                    + (f"<td class='{cls}'>{fmt.fmt_pct(f)}<span class='n'>n={fmt.fmt_int(x['n_val'])}</span></td>"
                       if f == f else "<td class='na'>—</td>")
                    + f"<td>{fmt.fmt_int(x['largos'])}</td><td>{fmt.fmt_int(x['cortos'])}</td></tr>")
    st.markdown("<div class='scorecard compact matriz'><table><thead><tr>" + "".join(f"<th>{h}</th>" for h in head)
                + "</tr></thead><tbody>" + "".join(body) + "</tbody></table></div>", unsafe_allow_html=True)


def punta_mes_matrix(t: pd.DataFrame, today: pd.Timestamp) -> None:
    """Mes de ETA × monoproveedor / consolidado / total: mediana de fin de producción → ETA y n."""
    if t.empty:
        st.markdown('<div class="empty">Sin embarques llegados con fin de producción.</div>', unsafe_allow_html=True)
        return
    head = "<tr><th rowspan='2'>Mes ETA</th><th colspan='2'>Monoproveedor</th><th colspan='2'>Consolidado</th>" \
           "<th colspan='2'>Total</th></tr><tr>" + "<th>Mediana</th><th>Embarques</th>" * 3 + "</tr>"
    body = []
    for _, x in t.sort_values("mes", na_position="last").iterrows():
        total = pd.isna(x["mes"])
        lbl = f"Total {today.year}" if total else _mes_txt(x["mes"], today)
        body.append(("<tr class='tot'>" if total else "<tr>") + f"<th class='rowh'>{lbl}</th>"
                    + f"<td class='hl'>{_dias(x['mono_med'])}</td><td>{fmt.fmt_int(x['mono_n'])}</td>"
                    + f"<td class='hl'>{_dias(x['conso_med'])}</td><td>{fmt.fmt_int(x['conso_n'])}</td>"
                    + f"<td>{_dias(x['med'])}</td><td>{fmt.fmt_int(x['n'])}</td></tr>")
    st.markdown("<div class='scorecard compact matriz'><table><thead>" + head + "</thead><tbody>" + "".join(body)
                + "</tbody></table></div>", unsafe_allow_html=True)
