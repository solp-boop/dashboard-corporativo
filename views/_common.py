"""Utilidades compartidas por las vistas."""
from __future__ import annotations

import pandas as pd

from components.filters import current_filters
from services.data_loader import DataBundle, get_data
from config.mappings import ESTADIOS_CERRADOS, MODOS_MARITIMOS
from utils.data_cleaning import fold
from utils.filters import FilterState, apply_filters
from utils import formatting as fmt


def ctx() -> tuple[DataBundle, FilterState]:
    return get_data(), current_filters()


def filtered(bundle: DataBundle, key: str, filters: FilterState, use_period: bool = True) -> pd.DataFrame | None:
    df = bundle.get(key)
    if df is None:
        return None
    return apply_filters(df, filters, use_period=use_period)


def month_labels(months: pd.Series) -> list[str]:
    return [fmt.fmt_month(m) for m in months]


def today() -> pd.Timestamp:
    return pd.Timestamp.today().normalize()


def periodo_txt(filters: FilterState) -> str:
    """'entre el 01/01/2026 y hoy' según el período elegido en la barra lateral."""
    if not filters.has_period:
        return "en todo el histórico"
    a = f"el {filters.start:%d/%m/%Y}" if filters.start else "el inicio del histórico"
    if filters.end and pd.Timestamp(filters.end) < today():
        return f"entre {a} y el {filters.end:%d/%m/%Y}"
    return f"entre {a} y hoy"


def stat_sub(stat, unit: str = "d") -> str:
    """'P25–P75: 15–31 d · n=120'."""
    if not stat.n:
        return "Sin datos suficientes"
    return (f"P25–P75: <b>{fmt.fmt_int(stat.p25)}–{fmt.fmt_int(stat.p75)} {unit}</b> · "
            f"n={fmt.fmt_int(stat.n)}")


GRUPOS_MODO = ["Marítimo", "Aéreo", "Camión"]


def split_html(items: list[tuple[str, int, str, str]], unit: str = "emb.", show_count: bool = True) -> str:
    """Barra 100 % + leyenda. items = (etiqueta, cantidad, color, texto extra)."""
    import html as _h
    n = sum(k for _, k, _, _ in items)
    segs, legend = [], []
    for g, k, color, extra in items:
        if not k:
            continue
        pct = k / n
        label = fmt.fmt_pct(pct) if pct >= 0.08 else ""
        segs.append(f'<div class="seg" style="width:{pct * 100:.2f}%;background:{color}" '
                    f'title="{_h.escape(g)}: {k} ({fmt.fmt_pct(pct)})">{label}</div>')
        legend.append(f'<div class="item"><i style="background:{color}"></i><b>{_h.escape(g)}</b>'
                      + (f'<span>{fmt.fmt_pct(pct)} · {fmt.fmt_int(k)} {unit}{extra}</span></div>' if show_count
                      else f'<span>{fmt.fmt_pct(pct)}{extra}</span></div>'))
    return f'<div class="splitbar">{"".join(segs)}</div><div class="legend-row">{"".join(legend)}</div>'


def en_curso(bundle: DataBundle, filters: FilterState) -> tuple[pd.DataFrame, dict]:
    """Embarques en curso = definición única para Resumen y Embarques en curso.

    - Marítimos y camión: solapa Reservas, filas con "Responsable de la carga".
      Los embarques AIR de Reservas se excluyen (se toman de Seguimiento Aéreos).
    - Aéreos: solapa SEGUIMIENTO AEREOS, todo lo que no está ENTREGADO.
    - Se aplican los filtros de la barra lateral, salvo el período: un embarque
      en curso se muestra aunque su ETD esté fuera del rango o vacía.

    Devuelve (DataFrame, info) con info = conteos de lo excluido.
    """
    parts, info = [], {"sin_responsable": 0, "air_en_reservas": 0, "aereos_entregados": 0}
    res = bundle.get("reservas")
    if res is not None and not res.empty:
        is_air = res["embarque"].map(lambda v: fold(v).startswith("air"))
        has_resp = res["responsable"].notna()
        info["air_en_reservas"] = int(is_air.sum())
        info["sin_responsable"] = int((~has_resp & ~is_air).sum())
        r = res[has_resp & ~is_air].copy()
        r["fuente"] = "Reservas"
        parts.append(r)
    aer = bundle.get("aereos")
    if aer is not None and not aer.empty:
        cerrado = aer["estadio"].map(lambda v: fold(v).upper() in {e.upper() for e in ESTADIOS_CERRADOS})
        info["aereos_entregados"] = int(cerrado.sum())
        a = aer[~cerrado].copy()
        a["fuente"] = "Seguimiento Aéreos"
        parts.append(a)
    if not parts:
        return pd.DataFrame(), info
    df = pd.concat(parts, ignore_index=True, sort=False)

    def grupo(row) -> str:
        if row["fuente"] == "Seguimiento Aéreos" or row["modo"] in ("Aéreo", "Courier"):
            return "Aéreo"
        if row["modo"] in MODOS_MARITIMOS:
            return "Marítimo"
        if row["modo"] == "Terrestre":
            return "Camión"
        return "Marítimo" if str(row["embarque"]).upper().startswith(("FCL", "LCL")) else "Otro"

    df["grupo_modo"] = df.apply(grupo, axis=1)
    df["etd_ok"] = df["etd_ok"].fillna(False).astype(bool)
    return apply_filters(df, filters, use_period=False), info


def kpis_en_curso(df: pd.DataFrame, info: dict | None = None) -> None:
    """Bloque «¿Cómo estamos hoy?»: mismas cifras en Resumen y Embarques en curso.

    Fila 1: los cuatro números principales.
    Fila 2: medio de envío (reparto por modo) y qué pasa en los próximos 7 días.
    """
    import html

    import numpy as np
    import streamlit as st

    from components.kpi_cards import KPI, kpi_row
    from config import settings

    n = len(df)
    t = today()
    week = df["etd"].between(t, t + pd.Timedelta(days=settings.ALERT_HORIZON_DAYS))
    ok_n = int(df["etd_ok"].sum())
    is_mar = df["grupo_modo"] == "Marítimo"

    kpi_row([
        KPI("Embarques en curso", fmt.fmt_int(n)),
        KPI("Contenedores marítimos", fmt.fmt_int(df.loc[is_mar, "contenedores"].sum())),
        KPI("Volumen en proceso", fmt.fmt_int(df["m3"].sum()), unit="m³"),
        KPI("FOB en proceso", fmt.fmt_usd(df["fob"].sum())),
    ])

    # ---- Medio de envío (barra 100 % por modo)
    colors = {"Marítimo": settings.SERIES[0], "Aéreo": settings.SERIES[1], "Camión": settings.SERIES[2]}
    split = split_html([
        (g, int((df["grupo_modo"] == g).sum()), colors[g],
         f" · {fmt.fmt_int(df.loc[df['grupo_modo'] == g, 'contenedores'].sum())} cont." if g == "Marítimo" else "")
        for g in GRUPOS_MODO])

    # ---- Próximos 7 días
    pct_ok = ok_n / n if n else np.nan
    wk_cont = int(df.loc[week & is_mar, "contenedores"].sum())
    st.markdown(
        f"""<div class="today-grid">
          <div class="panel">
            <div class="panel-title">Medio de envío</div>
            {split}
          </div>
          <div class="panel">
            <div class="panel-title">Próximos {settings.ALERT_HORIZON_DAYS} días</div>
            <div class="big">{fmt.fmt_int(week.sum())} <span>embarques zarpan</span></div>
            <div class="muted">{fmt.fmt_int(df.loc[week, "m3"].sum())} m³ · {fmt.fmt_int(wk_cont)} contenedores</div>
            <div class="progress-label"><span>ETD confirmado por el forwarder</span>
              <b>{html.escape(fmt.fmt_pct(pct_ok))}</b></div>
            <div class="progress"><div style="width:{(pct_ok if pct_ok == pct_ok else 0) * 100:.1f}%"></div></div>
            <div class="muted">{fmt.fmt_int(ok_n)} confirmados · {fmt.fmt_int(n - ok_n)} pendientes</div>
          </div>
        </div>""",
        unsafe_allow_html=True,
    )


# ---------------------------------------------------------------------------
# Operaciones en curso: marítimos, riesgo y tablas de SLA por grupo
# ---------------------------------------------------------------------------
def maritimos_en_curso(df: pd.DataFrame) -> pd.DataFrame:
    """Marítimos en curso (los embarques que empiezan con AIR son aéreos y se excluyen)."""
    es_air = df["embarque"].astype(str).str.strip().str.upper().str.startswith("AIR")
    return df[(df["grupo_modo"] == "Marítimo") & ~es_air]


def riesgo_maritimo(mar: pd.DataFrame) -> pd.DataFrame:
    """Consolidación proyectada fuera de SLA (Atención o Fuera) y todavía sin ETD OK FFWW."""
    from utils import calculations as calc
    return mar[mar["estado_consolidacion"].isin([calc.SEMAFORO_WARN, calc.SEMAFORO_BAD])
               & ~mar["etd_ok"].fillna(False).astype(bool)]


def sla_por_grupo(d: pd.DataFrame, by: str, estado_col: str, by_label: str,
                  estructuras: bool = False, extra: list[str] | None = None, extra_col: str = "",
                  extra_label: str = "", sla: bool = True) -> str:
    """Tabla HTML: por grupo, operaciones, % y cuántas dentro / fuera del SLA.

    Fuera = Atención + Fuera de SLA. Sin dato = sin fechas para calcular o sin SLA.
    estructuras=True abre monoproveedor / consolidado. extra = columnas de conteo por valor de extra_col.
    """
    import html as _h

    from utils import calculations as calc
    ok_v, bad_v = calc.SEMAFORO_OK, (calc.SEMAFORO_WARN, calc.SEMAFORO_BAD)
    est_list = ["Monoproveedor", "Consolidado"] if estructuras else []
    extra = extra or []
    total_ops = len(d)

    def counts(g):
        ok = int((g[estado_col] == ok_v).sum())
        bad = int(g[estado_col].isin(bad_v).sum())
        return len(g), ok, bad, len(g) - ok - bad

    head1 = [f'<th rowspan="2">{_h.escape(by_label)}</th>', '<th rowspan="2">Ops</th>', '<th rowspan="2">% ops</th>']
    head2 = []
    for e in est_list:
        head1.append(f'<th colspan="3" style="text-align:center">{e}</th>')
        head2 += ["<th>Ops</th>", "<th>Dentro</th>", "<th>Fuera</th>"]
    if extra:
        head1.append(f'<th colspan="{len(extra)}" style="text-align:center">{_h.escape(extra_label)}</th>')
        head2 += [f"<th>{_h.escape(str(x))}</th>" for x in extra]
    if sla:
        head1.append('<th colspan="4" style="text-align:center">SLA</th>')
        head2 += ["<th>Dentro</th>", "<th>Fuera</th>", "<th>Sin dato</th>", "<th>% dentro</th>"]

    groups = d[by].astype(object).where(d[by].notna(), "Sin asignar")
    order = groups.value_counts().index.tolist()
    rows = []
    for key in order + ["Total"]:
        g = d if key == "Total" else d[groups == key]
        n, ok, bad, sin = counts(g)
        con = ok + bad
        style = " style='font-weight:600'" if key == "Total" else ""
        cells = [f"<th class='rowh'>{_h.escape(str(key))}</th>", f"<td>{fmt.fmt_int(n)}</td>",
                 f"<td>{fmt.fmt_pct(n / total_ops if total_ops else float('nan'))}</td>"]
        for e in est_list:
            ge = g[g["estructura"] == e]
            ne, oke, bade, _ = counts(ge)
            cells += [f"<td>{fmt.fmt_int(ne)}</td>", f"<td>{fmt.fmt_int(oke)}</td>",
                      f"<td>{fmt.fmt_int(bade)}</td>"]
        for x in extra:
            v = int((g[extra_col] == x).sum())
            cells.append(f"<td>{fmt.fmt_int(v) if v else '—'}</td>")
        pct = ok / con if con else float("nan")
        dot = ("ok" if pct >= 0.5 else "bad") if con else ""
        dot_html = f'<i class="dot {dot}"></i>' if dot else ""
        cells += [] if not sla else [f"<td>{fmt.fmt_int(ok)}</td>", f"<td>{fmt.fmt_int(bad)}</td>", f"<td>{fmt.fmt_int(sin)}</td>",
                  f"<td style='text-align:left'>{dot_html}{fmt.fmt_pct(pct)}</td>"]
        rows.append(f"<tr{style}>" + "".join(cells) + "</tr>")
    return ('<div class="scorecard compact"><table><thead><tr>' + "".join(head1) + "</tr><tr>" + "".join(head2)
            + f'</tr></thead><tbody>{"".join(rows)}</tbody></table></div>')
