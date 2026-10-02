"""Agentes (forwarders): quién demora y dónde intervenir."""
from __future__ import annotations

import numpy as np
import pandas as pd
import streamlit as st

from components import charts
from components.kpi_cards import KPI, cert_status, cert_sub, kpi_row
from components.layout import chart_title, empty, filter_notes, guard, require, section
from components.tables import ColSpec, data_table
from config import settings
from config.mappings import MODOS_MARITIMOS
from utils import calculations as calc
from utils import formatting as fmt
from views._common import ctx, filtered, stat_sub, today


def _group(df: pd.DataFrame, by: str) -> pd.DataFrame:
    rows = []
    for key, d in df.groupby(by):
        pct, n = calc.cumplimiento(d["dias_consolidacion"], d["sla_consolidacion"])
        pagado = d.loc[d["flete_pagado"] > 0, "flete_pagado"].sum()
        cert = d.loc[d["flete_pagado"] > 0, "flete_certificado"].sum()
        rows.append({
            by: key, "embarques": len(d), "contenedores": d["contenedores"].sum(), "m3": d["m3"].sum(),
            "agente": d["dias_agente"].median(), "n_agente": int(d["dias_agente"].notna().sum()),
            "consolidacion": d["dias_consolidacion"].median(), "cumple": pct if n else np.nan,
            "desvio": d["desvio_etd"].median(),
            "in_advance": (d["booking"] == "In advance").mean() if d["booking"].notna().any() else np.nan,
            "certificacion": cert / pagado if pagado else np.nan,
        })
    return pd.DataFrame(rows).sort_values("embarques", ascending=False) if rows else pd.DataFrame()


def render() -> None:
    bundle, filters = ctx()
    base = require(bundle, "historicas")
    if base is None:
        return
    df = filtered(bundle, "historicas", filters)
    df = df[df["modo"].isin(MODOS_MARITIMOS) & (df["etd"] <= today())]
    filter_notes(base, filters, "Reservas Históricas")
    if df.empty:
        empty()
        return

    section("Forwarders", "Embarques marítimos zarpados en el período.")
    with guard("KPIs de agentes"):
        ag = calc.describe(df["dias_agente"])
        des = calc.describe(df["desvio_etd"])
        pagado = df.loc[df["flete_pagado"] > 0, "flete_pagado"].sum()
        cert = df.loc[df["flete_pagado"] > 0, "flete_certificado"].sum()
        n_cert = int((df["flete_pagado"] > 0).sum())
        pct_cert = cert / pagado if pagado else np.nan
        stt, badge = (cert_status(pct_cert)
                      if n_cert >= settings.MIN_SAMPLE else ("", ""))
        kpi_row([
            KPI("Embarques", fmt.fmt_int(len(df)), sub=f"<b>{fmt.fmt_int(df['contenedores'].sum())}</b> contenedores"),
            KPI("Instrucción → ETD (mediana)", fmt.fmt_int(ag.median) if ag.enough else "—", unit="d",
                sub=stat_sub(ag)),
            KPI("Desvío ETD real vs estimada", fmt.fmt_int(des.median) if des.enough else "—", unit="d",
                sub=stat_sub(des)),
            KPI("Flete certificado", fmt.fmt_pct(pct_cert) if n_cert >= settings.MIN_SAMPLE else "—",
                status=stt, badge=badge,
                sub=cert_sub() + " · "
                    f"datos en <b>{fmt.fmt_int(n_cert)}</b> de {fmt.fmt_int(len(df))} embarques"),
        ])

    by_ffww = _group(df, "forwarder")
    c1, c2 = st.columns(2, gap="medium")
    with c1, guard("Instrucción a ETD por forwarder"):
        chart_title("Instrucción → ETD por forwarder",
                    f"Mediana en días · forwarders con ≥ {settings.MIN_SAMPLE} embarques con dato")
        g = by_ffww[by_ffww["n_agente"] >= settings.MIN_SAMPLE].sort_values("agente", ascending=False)
        if g.empty:
            empty()
        else:
            fig = charts.hbar(g["forwarder"], g["agente"],
                              text=[f"{fmt.fmt_int(v)} d · n={n}" for v, n in zip(g["agente"], g["n_agente"])],
                              hover="%{y}: %{x:.0f} d<extra></extra>", x_title="días",
                              ref_value=ag.median if ag.enough else None, ref_label="Mediana general")
            charts.show(fig, key="ag_instr_etd")
    with c2, guard("Cumplimiento por forwarder"):
        chart_title("Cumplimiento de SLA de consolidación por forwarder",
                    f"% de embarques dentro de SLA · ≥ {settings.MIN_SAMPLE} embarques")
        g = by_ffww[(by_ffww["embarques"] >= settings.MIN_SAMPLE) & by_ffww["cumple"].notna()] \
            .sort_values("cumple")
        if g.empty:
            empty()
        else:
            fig = charts.hbar(g["forwarder"], g["cumple"] * 100,
                              text=[fmt.fmt_pct(v) for v in g["cumple"]],
                              hover="%{y}: %{x:.0f} %<extra></extra>", x_title="%", x_suffix=" %")
            charts.show(fig, key="ag_cumple")

    with guard("Tabla de forwarders"):
        data_table(by_ffww, [
            ColSpec("forwarder", "Forwarder"), ColSpec("embarques", "Embarques", "int"),
            ColSpec("contenedores", "Cont.", "int"), ColSpec("m3", "M3", "int"),
            ColSpec("agente", "Instr.→ETD (d)", "days"), ColSpec("consolidacion", "Consolidación (d)", "days"),
            ColSpec("cumple", "% SLA consol.", "pct"), ColSpec("desvio", "Desvío ETD (d)", "days"),
            ColSpec("in_advance", "% in advance", "pct"), ColSpec("certificacion", "% flete certificado", "pct"),
        ], key="ag_ffww", filename="forwarders", search=False,
            caption="Medianas en días. Desvío ETD = ETD real − ETD estimada")
