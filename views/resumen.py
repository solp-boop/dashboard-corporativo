"""Resumen: nuestro año, velocidad, eficiencia operativa, costos y captura, cargas especiales."""
from __future__ import annotations

import html

import numpy as np
import pandas as pd
import streamlit as st

from components import sla as sla_view
from components.layout import block, chart_title, empty, guard, require, subsection
from config import settings
from utils import calculations as calc
from utils import formatting as fmt
from utils import productos, sla
from components.kpi_cards import KPI, kpi_row
from components.tables import ColSpec, data_table
from utils import anio
from utils import resumen_kpis as rk
from views._common import ctx, en_curso, filtered, maritimos_en_curso, periodo_txt, split_html, today


def _record_txt(tab: pd.DataFrame) -> str:
    m = tab[tab["mes"].notna()]
    if m.empty or not m["m3"].gt(0).any():
        return ""
    r = m.loc[m["m3"].idxmax()]
    return f"Récord: <b>{fmt.fmt_month(r['mes'], long=True).lower()}</b> · {fmt.fmt_int(r['m3'])} m³"


def render_anio(bundle, filters) -> None:
    """Nuestro año: lo embarcado en el año calendario, total y mes a mes."""
    t = today()
    hist = filtered(bundle, "historicas", filters, use_period=False)
    block(1, f"Nuestro {t.year}", "¿Cuánto movimos? Operaciones embarcadas.")
    if hist is None or hist.empty:
        empty()
        return
    d = anio.del_anio(hist, t.year)
    if d.empty:
        empty(f"Sin embarques con ETD en {t.year} para los filtros seleccionados.")
        return
    tab = anio.mensual(d)
    tot = tab.iloc[-1]
    kpi_row([
        KPI("Embarques", fmt.fmt_int(tot["embarques"])),
        KPI("Contenedores", fmt.fmt_int(tot["contenedores"]), sub="marítimos"),
        KPI("FOB SIMI", fmt.fmt_usd(tot["fob_simi"])),
        KPI("Volumen", fmt.fmt_int(tot["m3"]), unit="m³", sub=_record_txt(tab)),
    ])
    colors = dict(zip(anio.MEDIOS, settings.SERIES + ["#8A8F98"]))
    medios = split_html([(m, int((d["medio"] == m).sum()), colors[m],
                          f" · {fmt.fmt_int(d.loc[d['medio'] == m, 'cnt_mar'].sum())} cont." if m == "Marítimo" else "")
                         for m in anio.medios_presentes(d)])
    est = split_html([(e, int((d["estructura"] == e).sum()), c, "")
                      for e, c in zip(anio.ESTRUCTURAS, (settings.SERIES[0], settings.SERIES[2]))])
    st.markdown(f"""<div class="today-grid even">
          <div class="panel"><div class="panel-title">Medio de envío</div>{medios}</div>
          <div class="panel"><div class="panel-title">Estructura</div>{est}</div>
        </div>""", unsafe_allow_html=True)

    show = tab.copy()
    this_month = t.to_period("M").to_timestamp()
    show["mes_txt"] = [f"Total {t.year}" if pd.isna(m) else
                       fmt.fmt_month(m, long=True) + (" · en curso" if m == this_month else "")
                       for m in show["mes"]]
    cols = [ColSpec("mes_txt", "Mes", width="medium"), ColSpec("embarques", "Embarques", "int"),
            ColSpec("contenedores", "Contenedores", "int"), ColSpec("fob_simi", "FOB SIMI (USD)", "usd"),
            ColSpec("m3", "M3", "num"), ColSpec("pct_mono", "% Mono", "pct"), ColSpec("pct_cons", "% Consolidado", "pct")]
    cols += [ColSpec(f"pct_{m}", f"% {m}", "pct") for m in anio.medios_presentes(d)]
    meses = show[show["mes"].notna()]
    rec = meses["m3"].idxmax() if meses["m3"].gt(0).any() else None
    styles = pd.Series("", index=show.index)
    styles.iloc[-1] = "font-weight: 600; background-color: rgba(120,130,150,0.10)"
    if rec is not None:
        show.loc[rec, "mes_txt"] = "★ " + show.loc[rec, "mes_txt"] + " · récord m³"
        styles.loc[rec] = "font-weight: 600; background-color: rgba(36,86,166,0.14)"
    data_table(show, cols, key="anio", filename=f"embarques_{t.year}", search=False, row_styles=styles)


def _tt_cards(tt: rk.TT, umbral_txt: str) -> None:
    if not tt.n:
        empty("Sin embarques con ETD y ETA válidas.")
        return
    if tt.comparable:
        diff = tt.med_act - tt.med_prev
        flecha = "▲" if diff > 0 else "▼" if diff < 0 else "="
        comp = (f"{tt.q_act[:2]}: <b>{fmt.fmt_int(tt.med_act)} d</b> vs {tt.q_prev[:2]} {fmt.fmt_int(tt.med_prev)} d "
                f"({flecha} {fmt.fmt_int(abs(diff))} d)")
    else:
        comp = "Sin trimestres cerrados comparables"
    kpi_row([
        KPI("Transit time (mediana)", fmt.fmt_int(tt.mediana) if tt.enough else "—", unit="d",
            sub=f"n={fmt.fmt_int(tt.n)} · {comp}"),
        KPI("P90", fmt.fmt_int(tt.p90) if tt.enough else "—", unit="d",
            sub="el 10 % más lento tarda más que esto"),
        KPI(f"Más de {umbral_txt}", fmt.fmt_pct(tt.pct_sobre) if tt.enough else "—",
            status=("warn" if tt.pct_sobre > 0.10 else "ok") if tt.enough else "",
            sub=f"<b>{fmt.fmt_int(tt.n_sobre)}</b> de {fmt.fmt_int(tt.n)} casos"),
    ])


def _ocupacion_table(r: pd.DataFrame) -> None:
    head = ["Tipo", "Capacidad", "Contenedores", "Ocupación (mediana)",
            f"≥ {fmt.fmt_pct(settings.OCUPACION_UMBRAL)}", f"< {fmt.fmt_pct(settings.OCUPACION_UMBRAL)}"]
    rows = []
    for _, x in r.iterrows():
        tot = x["tipo"] == "Total"
        cap = "—" if tot else f"{fmt.fmt_int(x['cap'])} m³"
        style = " style='font-weight:600'" if tot else ""
        rows.append(
            f"<tr{style}><th class='rowh'>{html.escape(x['tipo'])}</th><td>{cap}</td>"
            f"<td>{fmt.fmt_int(x['contenedores'])}</td><td>{fmt.fmt_pct(x['mediana'])}</td>"
            f"<td>{fmt.fmt_int(x['ok'])}<span class='n'>{fmt.fmt_pct(x['pct_ok'])}</span></td>"
            f"<td>{fmt.fmt_int(x['bajo'])}<span class='n'>{fmt.fmt_pct(1 - x['pct_ok'])}</span></td></tr>")
    st.markdown('<div class="scorecard compact"><table><thead><tr>' + "".join(f"<th>{h}</th>" for h in head)
                + f'</tr></thead><tbody>{"".join(rows)}</tbody></table></div>', unsafe_allow_html=True)


def _especial_cards(e: rk.Especial, modo: str) -> None:
    mar = modo == "Marítimo"
    nombre = "IMO" if mar else "DG"
    if not e.total:
        empty()
        return
    if e.n < settings.MIN_SAMPLE:
        kpi_row([KPI(f"{'Embarques' if mar else 'Cargas'} {nombre}", fmt.fmt_int(e.n),
                     sub=f"{fmt.fmt_pct(e.pct)} de {fmt.fmt_int(e.total)} · volumen insuficiente para comparar")])
        return
    unidad = "por contenedor" if mar else "por kg chargeable"
    costo_v = (fmt.fmt_usd(e.costo, compact=False) if mar else f"USD {fmt.fmt_num(e.costo, 1)}") if e.n_costo else "—"
    if e.costo_comparable:
        extra = (fmt.fmt_usd(e.extra, compact=False) if mar else f"USD {fmt.fmt_num(e.extra, 1)}")
        signo = "+" if e.extra > 0 else ""
        costo_sub = (f"<b>{signo}{extra}</b> ({fmt.fmt_pct(e.extra_pct, signed=True)}) vs "
                     f"{'no IMO' if mar else 'aéreo estándar'} comparable · n={fmt.fmt_int(e.n_pares)}")
    else:
        costo_sub = f"Sin volumen comparable suficiente (n={fmt.fmt_int(e.n_pares)})"
    if e.tt_comparable:
        d = e.tt - e.tt_ref
        tt_sub = (f"<b>{('+' if d > 0 else '') + fmt.fmt_int(d) + ' d' if round(d) else '='}</b> vs {'no IMO' if mar else 'no DG'} "
                  f"({fmt.fmt_int(e.tt_ref)} d) · n={fmt.fmt_int(e.n_tt)}")
    else:
        tt_sub = f"Sin volumen comparable suficiente (n={fmt.fmt_int(e.n_tt)})"
    kpi_row([
        KPI(f"{'Embarques' if mar else 'Cargas'} {nombre}", fmt.fmt_int(e.n),
            sub=f"<b>{fmt.fmt_pct(e.pct)}</b> de {fmt.fmt_int(e.total)} {'marítimos' if mar else 'aéreos'}"),
        KPI(f"{'Flete' if mar else 'USD/kg'} {nombre} (mediana)", costo_v, sub=f"{unidad} · {costo_sub}"),
        KPI(f"Transit time {nombre}", fmt.fmt_int(e.tt) if e.n_tt else "—", unit="d", sub=tt_sub),
    ])


UNIFORME_CSS = """<style>
/* Resumen: todas las tarjetas con el mismo alto */
.kpi-grid { align-items: stretch; }
.kpi-grid .kpi { min-height: 8.6rem; box-sizing: border-box; }
.kpi-grid .panel.span-3 { grid-column: span 3; min-height: 8.6rem; box-sizing: border-box; margin: 0; }
</style>"""


def render() -> None:
    bundle, filters = ctx()
    st.markdown(UNIFORME_CSS, unsafe_allow_html=True)
    t = today()
    periodo = periodo_txt(filters)
    hist = filtered(bundle, "historicas", filters) if bundle.get("historicas") is not None else None
    z = sla.zarpados(hist, t) if hist is not None else pd.DataFrame()
    aer = filtered(bundle, "aereos", filters) if bundle.get("aereos") is not None else None
    aer_z = aer[aer["etd"] <= t] if aer is not None else pd.DataFrame()

    # ================================================================== 1 · Nuestro año
    with guard("Nuestro año"):
        render_anio(bundle, filters)

    # ================================================================== 2 · Velocidad
    block(2, "Velocidad", f"¿Cuánto tardamos? Embarques que zarparon {periodo}. Tiempos por mediana; n = casos con dato. "
            "El detalle por mes cerrado, puerto y forwarder está en Lead times y SLA.")
    subsection("SLA", f"El mes en curso se muestra rayado porque está incompleto. "
               f"Objetivo de cumplimiento: {fmt.fmt_pct(settings.CUMPLIMIENTO_OBJETIVO)}.")
    c_mar, c_aer = st.columns(2, gap="medium")
    with c_mar:
        st.markdown('<div class="row-label">Marítimo</div>', unsafe_allow_html=True)
        if require(bundle, "historicas") is not None:
            with guard("SLA marítimo"):
                pct, n = calc.cumplimiento(z["dias_consolidacion"], z["sla_consolidacion"])
                n_ok = int((z["dias_consolidacion"] <= z["sla_consolidacion"]).sum())
                last = t.to_period("M").to_timestamp() - pd.offsets.MonthBegin(1)
                cl = sla.celda(z[calc.month_start(z["etd"]) == last], "cumplimiento")
                st.markdown(
                    f'<div class="panel"><div class="panel-title">Cumplimiento SLA de consolidación · período</div>'
                    f'<div class="mode-head"><span class="big">'
                    f'{fmt.fmt_pct(pct) if n >= settings.MIN_SAMPLE else "—"}</span>'
                    f'<span class="lbl">{fmt.fmt_int(n_ok)} de {fmt.fmt_int(n)} embarques dentro del SLA · '
                    f'{fmt.fmt_month(last, long=True).split()[0].lower()}: {fmt.fmt_pct(cl.valor)}</span></div></div>',
                    unsafe_allow_html=True)
                chart_title("Cumplimiento mes a mes", "% de embarques con consolidación dentro del SLA")
                sla_view.compliance_chart(sla.monthly_compliance(z), t, key="res_sla_mar")
    with c_aer:
        st.markdown('<div class="row-label">Aéreo</div>', unsafe_allow_html=True)
        if require(bundle, "aereos") is not None:
            with guard("SLA aéreo"):
                a = sla_view.air_zarpados(aer, t)
                vig = a[a["sla_vigente"] & a["sla_aereo"].notna()]
                pct_a, n_a = calc.cumplimiento(vig["dias_aereo"], vig["sla_aereo"])
                ok_a = int((vig["dias_aereo"] <= vig["sla_aereo"]).sum())
                st.markdown(
                    f'<div class="panel"><div class="panel-title">Cumplimiento SLA aéreo · desde '
                    f'{settings.SLA_AEREO_DESDE:%d/%m/%Y}</div>'
                    f'<div class="mode-head"><span class="big">'
                    f'{fmt.fmt_pct(pct_a) if n_a >= settings.MIN_SAMPLE else "—"}</span>'
                    f'<span class="lbl">{fmt.fmt_int(ok_a)} de {fmt.fmt_int(n_a)} embarques dentro del SLA · '
                    f'cada embarque contra el SLA de su tipo</span></div></div>',
                    unsafe_allow_html=True)
                chart_title("Cumplimiento mes a mes",
                            "% de embarques dentro del SLA de su tipo de negocio. En gris, meses anteriores "
                            "al SLA (referencia)")
                sla_view.air_compliance_chart(a, t, key="res_sla_aer")

    subsection("Transit time · ETD → ETA",
               "Mediana, P90 (dispersión) y casos largos. La comparación es el último trimestre cerrado contra el anterior.")
    c_mar, c_aer = st.columns(2, gap="medium")
    with c_mar, guard("Transit time marítimo"):
        st.markdown('<div class="row-label">Marítimo</div>', unsafe_allow_html=True)
        if len(z):
            _tt_cards(rk.transit_time(z, "dias_tt", settings.TT_MARITIMO_UMBRAL, t),
                      f"{settings.TT_MARITIMO_UMBRAL} días")
        else:
            empty()
    with c_aer, guard("Transit time aéreo"):
        st.markdown('<div class="row-label">Aéreo · sin courier</div>', unsafe_allow_html=True)
        if len(aer_z):
            _tt_cards(rk.transit_time(aer_z[aer_z["modo"] == "Aéreo"], "dias_etd_eta", settings.TT_AEREO_UMBRAL, t),
                      f"{settings.TT_AEREO_UMBRAL} días")
        else:
            empty()

    # ================================================================== 3 · Eficiencia operativa
    block(3, "Eficiencia operativa", "¿Qué tan eficientemente usamos los recursos? Tope GADNIC, consolidación en curso, objetivo −15 % y uso de la capacidad "
            "de los contenedores.")
    lim = settings.SLA_AEREO_POR_TIPO.get("GADNIC", 24)
    subsection(f"GADNIC · tope de {lim} días",
               f"Crítico para la compañía. Aéreos GADNIC: tiempo total (packeo mínimo → ETA Caldas, columna «Total»), "
               f"zarpados {periodo} y activos proyectados.")
    with guard("GADNIC"):
        if aer is None or aer.empty:
            empty("Sin datos de Seguimiento Aéreos.")
        else:
            from views import aereos as aereos_view
            gz = aer_z[(aer_z["tipo_sla"] == "GADNIC") & aer_z["dias_aereo"].notna()]
            todos = filtered(bundle, "aereos", filters, use_period=False)
            act = todos[todos["activo"] & (todos["tipo_sla"] == "GADNIC")]
            proy = aereos_view.riesgo(act, t) if len(act) else act
            n_g = len(gz)
            ok_g = int((gz["dias_aereo"] <= lim).sum())
            st_g = calc.describe(gz["dias_aereo"])
            pct_g = ok_g / n_g if n_g else np.nan
            obj = settings.CUMPLIMIENTO_OBJETIVO
            n_riesgo = int((proy["dias_proyectados"] > lim).sum()) if len(proy) else 0
            kpi_row([
                KPI(f"Dentro de {lim} días", fmt.fmt_pct(pct_g) if n_g >= settings.MIN_SAMPLE else "—",
                    status=("ok" if pct_g >= obj else "bad") if n_g >= settings.MIN_SAMPLE else "",
                    sub=f"<b>{fmt.fmt_int(ok_g)}</b> de {fmt.fmt_int(n_g)} embarques"),
                KPI("Tiempo total (mediana)", fmt.fmt_int(st_g.median) if st_g.enough else "—", unit="d",
                    status=("ok" if st_g.median <= lim else "bad") if st_g.enough else "",
                    sub=f"P90 <b>{fmt.fmt_int(gz['dias_aereo'].quantile(.9)) if n_g else '—'} d</b> · n={fmt.fmt_int(n_g)}"),
                KPI(f"Más de {lim} días", fmt.fmt_int(n_g - ok_g), status="bad" if n_g - ok_g else "ok",
                    sub="embarques zarpados en el período"),
                KPI("Activos en riesgo", fmt.fmt_int(n_riesgo), status="bad" if n_riesgo else "ok",
                    sub=f"de <b>{fmt.fmt_int(len(act))}</b> GADNIC activos con tiempo proyectado > {lim} d"),
            ])

    lim_cons, lim_mono = settings.SLA_CONSOLIDACION_DEFAULT, settings.SLA_CONSOLIDACION_MONO
    subsection("Consolidación marítima en curso",
               f"Cómo vienen los tiempos de consolidación de los marítimos en curso (packeo mínimo → ETD proyectada). "
               f"Tope: {lim_cons} días para consolidados y {lim_mono} para monoproveedor. La gran mayoría lleva GADNIC.")
    with guard("Consolidación marítima en curso"):
        from utils.data_cleaning import id_key
        res_c, _ = en_curso(bundle, filters)
        mar = maritimos_en_curso(res_c) if len(res_c) else pd.DataFrame()
        if mar.empty:
            empty("Sin marítimos en curso.")
        else:
            gk = rk.gadnic_embarques(bundle.get("planif"))
            n_gad = int(id_key(mar["embarque"]).isin(gk).sum()) if gk else 0
            lim_row = np.where(mar["estructura"] == "Monoproveedor", lim_mono, lim_cons)
            sobre = mar["dias_consolidacion"] > lim_row
            es_cons, es_mono = mar["estructura"] == "Consolidado", mar["estructura"] == "Monoproveedor"
            con_dato = mar["dias_consolidacion"].notna()
            cons_all = calc.describe(mar["dias_consolidacion"])
            med_c = calc.describe(mar.loc[es_cons, "dias_consolidacion"])
            med_m = calc.describe(mar.loc[es_mono, "dias_consolidacion"])
            n_c, n_m = int((es_cons & con_dato).sum()), int((es_mono & con_dato).sum())
            s_c, s_m = int((sobre & es_cons).sum()), int((sobre & es_mono).sum())
            margen = int((sobre & ~mar["etd_ok"].fillna(False).astype(bool)).sum())
            kpi_row([
                KPI("Cargas activas", fmt.fmt_int(len(mar)),
                    sub=f"<b>{fmt.fmt_int(n_gad)}</b> con GADNIC ({fmt.fmt_pct(n_gad / len(mar))})"),
                KPI("Consolidación proyectada (mediana)", fmt.fmt_int(cons_all.median) if cons_all.enough else "—",
                    unit="d", sub=(f"consolidado <b>{fmt.fmt_int(med_c.median)} d</b> · "
                                   f"mono <b>{fmt.fmt_int(med_m.median)} d</b> · n={fmt.fmt_int(cons_all.n)}")),
                KPI(f"Consolidados > {lim_cons} d", fmt.fmt_int(s_c), status="bad" if s_c else "ok",
                    sub=f"<b>{fmt.fmt_pct(s_c / n_c if n_c else np.nan)}</b> de {fmt.fmt_int(n_c)} con dato"),
                KPI(f"Monoproveedor > {lim_mono} d", fmt.fmt_int(s_m), status="bad" if s_m else "ok",
                    sub=f"<b>{fmt.fmt_pct(s_m / n_m if n_m else np.nan)}</b> de {fmt.fmt_int(n_m)} con dato"),
                KPI("Con margen de acción", fmt.fmt_int(margen), status="bad" if margen else "ok",
                    sub="pasados del tope y todavía sin ETD OK FFWW · detalle en Control → Alertas"),
            ])
            sin = int((~con_dato).sum())
            if sin:
                st.caption(f"{fmt.fmt_int(sin)} cargas activas sin fecha de packeo o ETD para proyectar la consolidación.")

    if bundle.get("emb_hist") is not None:
        subsection("Objetivo −15 % · consolidación de SKU nuevos y top ranking",
                   f"Mediana de días de consolidación por SO, por trimestre de {t.year}. La base es Q1 y el objetivo "
                   "es bajarla un 15 %: se compara el último trimestre cerrado contra Q1. "
                   "La apertura mes a mes está en Lead times y SLA.")
        with guard("Objetivo −15 %"):
            d = productos.base_lines(bundle.get("emb_hist"), t)
            summ = productos.summary(d, t)
            g1, g2 = st.columns(2, gap="medium")
            for col, (grupo, label) in zip((g1, g2), productos.GRUPOS.items()):
                with col:
                    chart_title(label, "Mediana por trimestre · línea punteada = objetivo (Q1 −15 %)")
                    sla_view.productos_q_chart(summ, label, t, key=f"res_prod_{grupo}")
            sla_view.productos_table(summ, t)

    umbral = fmt.fmt_pct(settings.OCUPACION_UMBRAL)
    subsection("Utilización de contenedores",
               f"Ocupación = m³ cargados / (contenedores × capacidad del tipo). Embarques FCL que zarparon {periodo}; "
               "cada contenedor cuenta con la ocupación de su embarque.")
    occ = pd.DataFrame()
    with guard("Utilización de contenedores"):
        occ = rk.ocupacion(z) if len(z) else pd.DataFrame()
        r = rk.ocupacion_resumen(occ) if len(occ) else pd.DataFrame()
        if r.empty:
            empty("Sin embarques FCL con m³ y tipo de contenedor.")
        else:
            tot = r[r["tipo"] == "Total"].iloc[0]
            c1, c2 = st.columns([2, 3], gap="medium")
            with c1:
                kpi_row([
                    KPI("Ocupación (mediana)", fmt.fmt_pct(tot["mediana"]),
                        sub=f"{fmt.fmt_int(tot['contenedores'])} contenedores"),
                    KPI(f"Contenedores ≥ {umbral}", fmt.fmt_int(tot["ok"]), status="ok",
                        sub=f"<b>{fmt.fmt_pct(tot['pct_ok'])}</b> del total"),
                    KPI(f"Contenedores < {umbral}", fmt.fmt_int(tot["bajo"]),
                        status="warn" if tot["bajo"] else "ok",
                        sub=f"<b>{fmt.fmt_pct(1 - tot['pct_ok'])}</b> del total"),
                ], columns=1)
            with c2:
                _ocupacion_table(r)

    subsection("Uso de 20 ST",
               f"Un 20 ST con ocupación menor al {umbral} no es necesariamente una mala decisión: se considera "
               "justificado si el embarque lleva SKU nuevos o top ranking (Embarques Históricos).")
    with guard("Uso de 20 ST"):
        justif = rk.justificaciones_producto(bundle.get("emb_hist"))
        u = rk.uso_20st(occ, justif) if len(occ) else rk.Uso20()
        if not u.total:
            empty("Sin 20 ST en el período.")
        else:
            motivos = " · ".join(f"{k}: <b>{fmt.fmt_int(v)}</b>" for k, v in u.por_motivo.items())
            pct = u.pct_justificados
            kpi_row([
                KPI("20 ST utilizados", fmt.fmt_int(u.total)),
                KPI(f"Con ocupación < {umbral}", fmt.fmt_int(u.bajos),
                    sub=f"<b>{fmt.fmt_pct(u.bajos / u.total)}</b> de los 20 ST"),
                KPI("Justificados", fmt.fmt_int(u.justificados) if u.tiene_campo else "—",
                    sub=(motivos + " (un embarque puede tener los dos)") if u.tiene_campo else "Sin datos suficientes"),
                KPI("% de 20 ST bajos justificados", fmt.fmt_pct(pct) if pct == pct else "—",
                    status=("ok" if pct >= 0.5 else "warn") if pct == pct else "",
                    sub=f"KPI principal · sin justificar: <b>{fmt.fmt_int(u.bajos - u.justificados)}</b>"),
            ])
            if len(u.detalle):
                with st.expander(f"Ver los {fmt.fmt_int(len(u.detalle))} embarques en 20 ST con baja ocupación"):
                    data_table(u.detalle.sort_values("etd"), [
                        ColSpec("embarque", "Embarque"), ColSpec("etd", "ETD", "date"),
                        ColSpec("forwarder", "Forwarder"), ColSpec("puerto", "Puerto"),
                        ColSpec("contenedores", "Cont.", "int"), ColSpec("m3", "M3", "num"),
                        ColSpec("ocupacion", "Ocupación", "pct"), ColSpec("justificacion", "Justificación"),
                    ], key="res_20st", filename="20st_baja_ocupacion", search=False)

    # ================================================================== 4 · Costos y captura
    if bundle.get("historicas") is not None:
        render_fletes(bundle, filters)

    # ================================================================== 5 · Cargas especiales
    block(5, "Cargas especiales", f"¿Qué impacto tienen las cargas IMO / DG? Embarques que zarparon {periodo}. "
            "Costos y tiempos por mediana, comparados solo contra carga comparable (mismo mes y tipo de "
            "contenedor / origen).")
    c_mar, c_aer = st.columns(2, gap="medium")
    with c_mar, guard("IMO marítimo"):
        st.markdown('<div class="row-label">Marítimo · IMO</div>', unsafe_allow_html=True)
        if len(z) and "dg" in z:
            _especial_cards(rk.imo_maritimo(z), "Marítimo")
            st.caption("Columna «DG» de Reservas Históricas. Comparable: mismo tipo de contenedor, mes de ETD y destino.")
        else:
            empty("Sin columna DG en Reservas Históricas.")
    with c_aer, guard("DG aéreo"):
        st.markdown('<div class="row-label">Aéreo · DG</div>', unsafe_allow_html=True)
        if len(aer_z) and "dg" in aer_z:
            _especial_cards(rk.dg_aereo(aer_z), "Aéreo")
            st.caption("Columna «CARGA IMO» de Seguimiento Aéreos, sin courier. USD/kg = flete total / chargeable. "
                       "Comparable: mismo mes de ETD y origen.")
        else:
            empty("Sin columna CARGA IMO en Seguimiento Aéreos.")


def render_fletes(bundle, filters) -> None:
    """¿Cuánto pagamos y cuánto capturamos? Resumen de la gestión de fletes."""
    import plotly.graph_objects as go

    from components import charts
    from components.kpi_cards import KPI, cert_status, cert_sub, kpi_row
    from config.mappings import MODOS_MARITIMOS
    from utils import freight

    periodo = periodo_txt(filters)
    block(4, "Costos y captura",
            f"¿Cuánto nos costó, cuánto pesa sobre lo que compramos y cuánto capturamos? Embarques que zarparon {periodo}. El detalle por forwarder y "
            "por embarque está en Fletes y gastos pagados; las tarifas, en Cotizaciones.")
    with guard("Fletes y gastos"):
        t = today()
        cot = bundle.get("cotizaciones")
        h = filtered(bundle, "historicas", filters)
        h = h[h["modo"].isin(MODOS_MARITIMOS) & (h["etd"] <= t) & (h["flete_pagado"] > 0)]
        h = freight.add_market_reference(h, cot)
        a = bundle.get("aereos")
        a = filtered(bundle, "aereos", filters) if a is not None else pd.DataFrame()
        if len(a):
            a = a[(a["etd"] <= t) & (a["flete_pagado"] > 0)]

        def costos(d):
            if not len(d):
                return 0.0, 0.0, 0.0
            return (float(d["flete_pagado"].sum()), float(d["gastos_origen"].clip(lower=0).sum()),
                    float(d["gastos_locales"].clip(lower=0).sum()))

        fm, om, dm = costos(h)
        fa, oa, da = costos(a)
        tot_m, tot_a = fm + om + dm, fa + oa + da
        total = tot_m + tot_a

        ahorro = freight.savings_vs_market(h)
        n_ref = int(ahorro.notna().sum())
        ah_total = float(ahorro.sum())
        mercado_total = float((h["mercado_mes"] * h["contenedores"]).sum())
        ah_pct = ah_total / mercado_total if mercado_total else np.nan

        def cert_de(d):
            ok = d["flete_pagado"] > 0 if len(d) else pd.Series(dtype=bool)
            return (float(d.loc[ok, "flete_certificado"].sum() / d.loc[ok, "flete_pagado"].sum())
                    if len(d) and ok.any() else np.nan)

        cert_m, cert_a = cert_de(h), cert_de(a)
        nor = freight.nor_savings(h)
        nor_ok = nor.dropna(subset=["ahorro"]) if len(nor) else nor

        # ---- Total: lo comercial es cuánto pesa la logística sobre el FOB embarcado
        def costo_fila(d):
            return (d["flete_pagado"].clip(lower=0).fillna(0) + d["gastos_origen"].clip(lower=0).fillna(0)
                    + d["gastos_locales"].clip(lower=0).fillna(0))

        def incidencia(d):
            """Costo logístico / FOB, solo embarques con FOB cargado. (incidencia, fob, n con fob)."""
            if not len(d) or "fob" not in d:
                return np.nan, 0.0, 0
            ok = d["fob"] > 0
            fob = float(d.loc[ok, "fob"].sum())
            return (float(costo_fila(d[ok]).sum()) / fob if fob else np.nan), fob, int(ok.sum())

        inc_m, fob_m, _ = incidencia(h)
        inc_a, fob_a, _ = incidencia(a)
        both = pd.concat([x for x in (h, a) if len(x)], ignore_index=True, sort=False) if (len(h) or len(a)) \
            else pd.DataFrame()
        inc_t, fob_t, n_fob = incidencia(both)
        last = t.to_period("M").to_timestamp() - pd.offsets.MonthBegin(1)
        prev = last - pd.offsets.MonthBegin(1)
        mb = calc.month_start(both["etd"]) if len(both) else pd.Series(dtype="datetime64[ns]")
        inc_last, _, n_last = incidencia(both[mb == last]) if len(both) else (np.nan, 0, 0)
        inc_prev, _, _ = incidencia(both[mb == prev]) if len(both) else (np.nan, 0, 0)
        if inc_last == inc_last and inc_prev == inc_prev:
            d_pts = (inc_last - inc_prev) * 100
            var_txt = (f"{'▲' if d_pts > 0 else '▼' if d_pts < 0 else '='} {fmt.fmt_num(abs(d_pts), 1)} pts vs "
                       f"{fmt.fmt_month(prev, long=True).split()[0].lower()} ({fmt.fmt_pct(inc_prev, 1)})")
        else:
            var_txt = "Sin mes anterior para comparar"
        st.markdown('<div class="row-label">Total · marítimo + aéreo</div>', unsafe_allow_html=True)
        kpi_row([
            KPI("Costo logístico pagado", fmt.fmt_usd(total), sub=f"<b>{fmt.fmt_int(len(h) + len(a))}</b> embarques"),
            KPI("FOB embarcado", fmt.fmt_usd(fob_t),
                sub=f"de los <b>{fmt.fmt_int(n_fob)}</b> embarques con FOB cargado"),
            KPI("Incidencia logística", fmt.fmt_pct(inc_t, 1),
                sub=f"costo / FOB · marítimo <b>{fmt.fmt_pct(inc_m, 1)}</b> · aéreo <b>{fmt.fmt_pct(inc_a, 1)}</b>"),
            KPI(f"Incidencia {fmt.fmt_month(last, long=True).lower()}", fmt.fmt_pct(inc_last, 1),
                status=("bad" if inc_last > inc_prev else "ok") if inc_last == inc_last and inc_prev == inc_prev else "",
                sub=var_txt),
        ])

        # ---- Marítimo
        st.markdown('<div class="row-label">Marítimo</div>', unsafe_allow_html=True)
        kpi_row([
            KPI("Costo pagado", fmt.fmt_usd(tot_m),
                sub=f"<b>{fmt.fmt_pct(inc_m, 1)}</b> del FOB · {fmt.fmt_int(len(h))} embarques"),
            KPI("Ahorro vs mercado", fmt.fmt_usd(ah_total) if n_ref else "—",
                status=("ok" if ah_total >= 0 else "bad") if n_ref >= settings.MIN_SAMPLE else "",
                sub=(f"Flete {fmt.fmt_pct(-ah_pct, signed=True)} vs mediana de mercado · "
                     f"{fmt.fmt_int(n_ref)} embarques") if n_ref else "Sin cotizaciones para comparar"),
            KPI("Ahorro por usar 40 NOR", fmt.fmt_usd(nor_ok["ahorro"].sum()) if len(nor_ok) else "—",
                status=("ok" if nor_ok["ahorro"].sum() >= 0 else "bad") if len(nor_ok) else "",
                sub=(f"<b>{fmt.fmt_int(nor_ok['contenedores'].sum())}</b> contenedores 40 NOR vs 40 ST/HQ del mismo mes"
                     + (f" · por m³: {fmt.fmt_usd(nor_ok['ahorro_m3'].sum())}" if nor_ok["ahorro_m3"].notna().any() else ""))
                if len(nor_ok) else "Sin embarques en 40 NOR"),
            KPI("Flete certificado", fmt.fmt_pct(cert_m), status=cert_status(cert_m)[0], badge=cert_status(cert_m)[1],
                sub=cert_sub() + " · certificado por fuera / flete pagado"),
        ])
        con_origen = int((h["gastos_origen"] > 0).sum())
        st.caption(f"Gastos en origen cargados en {fmt.fmt_int(con_origen)} de {fmt.fmt_int(len(h))} embarques "
                   "marítimos. «Ahorro vs mercado»: por embarque, (precio de mercado − flete pagado por contenedor) × "
                   "contenedores; el precio de mercado es la mediana de la mejor tarifa de cada forwarder cotizada "
                   "para el mes de ETD, el mismo tipo de contenedor y destino. «Ahorro por usar 40 NOR»: por embarque "
                   "en 40 NOR, (mediana pagada por un 40 ST/HQ ese mes − flete pagado por el 40 NOR) × contenedores.")

        # ---- Aéreo
        st.markdown('<div class="row-label">Aéreo</div>', unsafe_allow_html=True)
        if not len(a):
            empty("Sin aéreos con flete pagado en el período.")
        else:
            kg = a["chargeable"] if "chargeable" in a else pd.Series(np.nan, index=a.index)
            usd_kg = calc.describe((a["flete_pagado"] / kg).where(kg > 0))
            kpi_row([
                KPI("Costo pagado", fmt.fmt_usd(tot_a),
                    sub=f"<b>{fmt.fmt_pct(inc_a, 1)}</b> del FOB · {fmt.fmt_int(len(a))} embarques"),
                KPI("USD por kg chargeable", f"USD {fmt.fmt_num(usd_kg.median, 1)}" if usd_kg.enough else "—",
                    sub=(f"Mediana · P25–P75 USD {fmt.fmt_num(usd_kg.p25, 1)}–{fmt.fmt_num(usd_kg.p75, 1)} · "
                         f"n={fmt.fmt_int(usd_kg.n)}") if usd_kg.enough else "Sin chargeable cargado"),
                KPI("Flete certificado", fmt.fmt_pct(cert_a), status=cert_status(cert_a)[0],
                    badge=cert_status(cert_a)[1], sub=cert_sub() + " · certificado por fuera / flete pagado"),
            ], columns=4)

        c1, c2 = st.columns(2, gap="medium")
        with c1:
            chart_title("Costo pagado e incidencia por mes",
                        "USD por mes de ETD · arriba de cada barra, % del FOB embarcado ese mes")
            medio = st.segmented_control("Medio", ["Total", "Marítimo", "Aéreo"], default="Total",
                                         key="res_costo_medio", label_visibility="collapsed") or "Total"
            fuentes = {"Total": (h, a), "Marítimo": (h,), "Aéreo": (a,)}[medio]
            parts = []
            for df_ in fuentes:
                if len(df_):
                    x_ = df_.assign(mes=calc.month_start(df_["etd"]))
                    x_["costo_fob"] = costo_fila(x_).where(x_["fob"] > 0, 0) if "fob" in x_ else 0
                    x_["fob_ok"] = x_["fob"].where(x_["fob"] > 0, 0) if "fob" in x_ else 0
                    parts.append(x_[["mes", "flete_pagado", "gastos_origen", "gastos_locales", "costo_fob", "fob_ok"]])
            if not parts:
                empty()
            else:
                mm = pd.concat(parts).groupby("mes").sum(min_count=1).clip(lower=0).sort_index().tail(12)
                x = [fmt.fmt_month(m) for m in mm.index]
                fig = go.Figure()
                for i, (col, lab) in enumerate((("flete_pagado", "Flete"), ("gastos_origen", "Gastos en origen"),
                                                ("gastos_locales", "Gastos en destino"))):
                    fig.add_bar(x=x, y=mm[col].fillna(0), name=lab, marker=dict(color=settings.SERIES[i], cornerradius=3),
                                hovertemplate=f"%{{x}} · {lab}: USD %{{y:,.0f}}<extra></extra>")
                tot_mes = mm[["flete_pagado", "gastos_origen", "gastos_locales"]].fillna(0).sum(axis=1)
                inc_mes = (mm["costo_fob"] / mm["fob_ok"]).where(mm["fob_ok"] > 0)
                fig.add_scatter(x=x, y=tot_mes.values, mode="text", showlegend=False, cliponaxis=False,
                                text=[fmt.fmt_pct(v, 1) if v == v else "" for v in inc_mes.values],
                                textposition="top center", textfont=dict(size=11, color=settings.COLORS["slate"]),
                                customdata=inc_mes.values * 100,
                                hovertemplate="%{x} · incidencia %{customdata:.1f} % del FOB<extra></extra>")
                fig.update_layout(barmode="stack")
                charts.theme(fig, height=300, y_title="USD")
                fig.update_yaxes(range=[0, float(tot_mes.max()) * 1.15 if tot_mes.max() else 1])
                charts.show(fig, key="res_costo_mes")
        with c2:
            chart_title("Ahorro vs mercado por mes · marítimo", "USD · flete marítimo. Positivo = pagamos menos que la mediana de mercado")
            hh = h.assign(ah=ahorro, mes=calc.month_start(h["etd"])).dropna(subset=["ah"])
            if hh.empty:
                empty("Sin cotizaciones para comparar.")
            else:
                g = hh.groupby("mes")["ah"].agg(["sum", "size"]).sort_index().tail(12)
                fig = go.Figure(go.Bar(
                    x=[fmt.fmt_month(m) for m in g.index], y=g["sum"],
                    marker=dict(color=[settings.COLORS["green"] if v >= 0 else settings.COLORS["red"] for v in g["sum"]],
                                cornerradius=3),
                    text=[fmt.fmt_usd(v) for v in g["sum"]], textposition="outside", cliponaxis=False,
                    textfont=dict(size=11, color=settings.COLORS["slate"]), customdata=g["size"],
                    hovertemplate="%{x}<br>USD %{y:,.0f}<br>Embarques: %{customdata}<extra></extra>"))
                charts.theme(fig, height=300, y_title="USD", legend=False)
                fig.update_yaxes(rangemode="normal", zeroline=True, zerolinecolor=settings.COLORS["grey"])
                charts.show(fig, key="res_ahorro_mes")
