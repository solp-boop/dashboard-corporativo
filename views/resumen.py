"""Resumen ejecutivo: ¿cómo estamos?, ¿cumplimos SLA?, ¿qué requiere atención?"""
from __future__ import annotations

import numpy as np
import pandas as pd
import streamlit as st

from components import sla as sla_view
from components.layout import chart_title, empty, guard, require, section
from components.tables import ColSpec, data_table
from config import settings
from utils import calculations as calc
from utils import formatting as fmt
from utils import productos, sla
from views._common import ctx, en_curso, filtered, kpis_en_curso, periodo_txt, today


def alerts(res: pd.DataFrame) -> pd.DataFrame:
    """Embarques en curso que requieren acción, con el motivo."""
    t = today()
    horizon = t + pd.Timedelta(days=settings.ALERT_HORIZON_DAYS)
    upcoming = res["etd"].between(t, horizon)
    reasons = pd.Series([[] for _ in range(len(res))], index=res.index)

    def add(mask, text):
        for i in res.index[mask.fillna(False)]:
            reasons[i] = reasons[i] + [text if isinstance(text, str) else text(res.loc[i])]

    mar = res["grupo_modo"] == "Marítimo" if "grupo_modo" in res else pd.Series(True, index=res.index)
    add(upcoming & ~res["etd_ok"], "ETD sin confirmar por el forwarder")
    docs_missing = mar & ((res["draft_bl"].fillna("NO").astype(str).str.upper() != "SI") |
                          (res["pl_final"].fillna("NO").astype(str).str.upper() != "SI"))
    sailed = res["etd"].between(t - pd.Timedelta(days=30), t - pd.Timedelta(days=3))
    add(sailed & docs_missing, "Zarpó hace más de 3 días sin Draft BL / Packing list final")
    future = res["etd"] >= t
    add(future & mar & (res["estado_consolidacion"] == calc.SEMAFORO_BAD),
        lambda r: f"Consolidación proyectada {fmt.fmt_int(r['dias_consolidacion'])} d "
                  f"(SLA {fmt.fmt_int(r['sla_consolidacion'])} d)")
    add(res["etd"].isna() & res["f_instruccion"].notna(), "Instruido sin ETD cargado")

    out = res[reasons.map(len) > 0].copy()
    out["motivo"] = reasons[out.index].map(" · ".join)
    out["n_motivos"] = reasons[out.index].map(len)
    days_to = (out["etd"] - t).dt.days
    out["prioridad"] = np.where(days_to.le(3) | (out["n_motivos"] >= 2), "Alta", "Media")
    return out.sort_values(["prioridad", "etd"], ascending=[True, True])


def render() -> None:
    bundle, filters = ctx()

    # ------------------------------------------------------------------ hoy
    section("¿Cómo estamos hoy?")
    res = None
    with guard("Operación en curso"):
        res, info = en_curso(bundle, filters)
        if res.empty:
            empty()
        else:
            kpis_en_curso(res, info)

    # ------------------------------------------------------------------ SLA
    periodo = periodo_txt(filters)
    section("¿Estamos cumpliendo SLA?",
            f"Embarques que zarparon {periodo}, mes a mes. El mes en curso se muestra rayado porque está "
            f"incompleto. Objetivo de cumplimiento: {fmt.fmt_pct(settings.CUMPLIMIENTO_OBJETIVO)}. "
            "La apertura por mes cerrado, estructura, puerto y forwarder está en Lead times y SLA.")
    c_mar, c_aer = st.columns(2, gap="medium")
    with c_mar:
        st.markdown('<div class="row-label">Marítimo</div>', unsafe_allow_html=True)
        if require(bundle, "historicas") is not None:
            with guard("SLA marítimo"):
                t = today()
                hist = filtered(bundle, "historicas", filters)
                z = sla.zarpados(hist, t)
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
                t = today()
                a = sla_view.air_zarpados(filtered(bundle, "aereos", filters), t)
                vig = a[a["sla_vigente"] & a["sla_aereo"].notna()]
                pct_a, n_a = calc.cumplimiento(vig["dias_aereo"], vig["sla_aereo"])
                ok_a = int((vig["dias_aereo"] <= vig["sla_aereo"]).sum())
                st.markdown(
                    f'<div class="panel"><div class="panel-title">Cumplimiento SLA aéreo · desde '
                    f'{settings.SLA_AEREO_DESDE:%d/%m/%Y}</div>'
                    f'<div class="mode-head"><span class="big">'
                    f'{fmt.fmt_pct(pct_a) if n_a >= settings.MIN_SAMPLE else "—"}</span>'
                    f'<span class="lbl">{fmt.fmt_int(ok_a)} de {fmt.fmt_int(n_a)} embarques dentro del SLA · '
                    f'mediana del año {fmt.fmt_int(a["dias_aereo"].median())} d</span></div></div>',
                    unsafe_allow_html=True)
                chart_title("Tiempo total mes a mes",
                            "Mediana de la columna Total (días). En gris, los meses anteriores al SLA")
                sla_view.air_chart(a, t, key="res_sla_aer")

    # ------------------------------------------------------------------ objetivo −15 %
    if bundle.get("emb_hist") is not None:
        section("Objetivo −15 % · consolidación de SKU nuevos y top ranking",
                "Tiempo de consolidación por SO, separado en monoproveedor y consolidado. "
                "La evolución mes a mes está en Lead times y SLA.")
        with guard("Objetivo −15 %"):
            d = productos.base_lines(bundle.get("emb_hist"), today())
            sla_view.productos_table(productos.summary(d, today()))

    # ------------------------------------------------------------------ atención
    section("¿Qué operaciones requieren atención?",
            f"ETD en los próximos {settings.ALERT_HORIZON_DAYS} días sin confirmar, zarpados sin documentación, "
            "consolidación proyectada fuera de SLA o instruidos sin ETD.")
    if res is not None:
        with guard("Alertas"):
            al = alerts(res)
            if al.empty:
                empty("No hay alertas para los filtros seleccionados.")
            else:
                data_table(al, [
                    ColSpec("prioridad", "Prioridad"),
                    ColSpec("embarque", "Embarque"),
                    ColSpec("grupo_modo", "Modo"),
                    ColSpec("motivo", "Motivo", width="large"),
                    ColSpec("etd", "ETD", "date"),
                    ColSpec("forwarder", "Forwarder"),
                    ColSpec("puerto", "Puerto"),
                    ColSpec("responsable", "Responsable"),
                    ColSpec("m3", "M3", "num"),
                    ColSpec("estado_consolidacion", "Consolidación", "status"),
                ], key="alertas", filename="alertas_embarques")
