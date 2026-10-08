"""Bandeja de acción (nivel 3): las operaciones sobre las que hay que actuar, con la acción sugerida."""
from __future__ import annotations

import pandas as pd
import streamlit as st

from components.kpi_cards import KPI, kpi_row
from components.layout import empty, guard, section
from components.tables import ColSpec, data_table
from config import settings
from utils import bandeja, salud
from utils import formatting as fmt
from views import aereos
from views._common import ctx, en_curso, filtered, today


def casos(bundle, filters) -> pd.DataFrame:
    """Todos los casos de la bandeja. Los de en curso y cerrados respetan los filtros (salvo el período);
    los de datos miran la planilla entera."""
    t = today()
    partes = []
    res, _ = en_curso(bundle, filters)
    partes += bandeja.casos_en_curso(res, t)
    if res is not None and len(res):
        partes += bandeja.casos_impo2(res[res["fuente"] == "Reservas"] if "fuente" in res else res, t,
                                      salud.solapa(bundle, "reservas"))
    if bundle.get("aereos") is not None:
        todos = filtered(bundle, "aereos", filters, use_period=False)
        act = todos[todos["activo"]]
        partes += bandeja.casos_aereos(aereos.riesgo_aereo(act, t) if len(act) else None, t)
    if bundle.get("historicas") is not None:
        h = filtered(bundle, "historicas", filters, use_period=False)
        partes += bandeja.casos_cerrados(h, t)
        partes += bandeja.casos_impo2(h, t, salud.solapa(bundle, "historicas"), requiere_ok=False)
    partes += bandeja.casos_datos(salud.controles_cache(bundle, t))
    df = bandeja.armar(partes)
    return bandeja.enriquecer(df, bundle.get("planif"), bundle.get("emb_hist"))


COLS = [
    ColSpec("prioridad", "Prioridad"), ColSpec("situacion", "Situación", width="large"),
    ColSpec("accion", "Acción sugerida", width="large"), ColSpec("embarque", "Embarque"), ColSpec("so", "SO"),
    ColSpec("proveedor", "Proveedor"), ColSpec("agente", "Agente"), ColSpec("responsable", "Responsable"),
    ColSpec("f_packeo", "Packeo", "date"), ColSpec("etd", "ETD", "date"), ColSpec("dias", "Días", "days"),
    ColSpec("sla", "SLA (d)", "days"), ColSpec("excedido", "Excedidos (d)", "days"), ColSpec("causa", "Causa"),
    ColSpec("tipo", "Tipo"),
]


def render() -> None:
    bundle, filters = ctx()
    section("Bandeja de acción",
            "Las operaciones sobre las que hay que actuar hoy, con la acción sugerida. En curso y cerrados respetan los "
            "filtros (salvo el período); los datos a corregir miran toda la planilla.")
    with guard("Bandeja de acción"):
        df = casos(bundle, filters)
        if df.empty:
            empty("No hay casos abiertos para los filtros seleccionados.")
            return
        n_tipo = df["tipo"].value_counts()
        alta = int((df["prioridad"] == "Alta").sum())
        kpi_row([
            KPI("Casos abiertos", fmt.fmt_int(len(df)), status="bad" if alta else "warn",
                sub=f"<b>{fmt.fmt_int(alta)}</b> de prioridad alta · {fmt.fmt_int(df['embarque'].nunique())} registros",
                help="Prioridad alta: sale en 3 días o menos, zarpó sin documentación, salió hace "
                     f"{settings.IMPO2_DIAS}+ días sin pasar a Impo2 o ya se pasa del SLA."),
            KPI("Confirmar o reclamar al forwarder", fmt.fmt_int(n_tipo.get(bandeja.TIPOS["forwarder"], 0)),
                status="warn" if n_tipo.get(bandeja.TIPOS["forwarder"], 0) else "ok",
                help=f"ETD en los próximos {settings.ALERT_HORIZON_DAYS} días sin «ETD OK FFWW», zarpados hace más de "
                     "3 días sin Draft BL o packing list, e instruidos sin ETD."),
            KPI("Pasar a Impo2", fmt.fmt_int(n_tipo.get(bandeja.TIPOS["impo2"], 0)),
                status="bad" if n_tipo.get(bandeja.TIPOS["impo2"], 0) else "ok",
                help=f"Embarques que salieron hace {settings.IMPO2_DIAS} días o más, con «ETD OK FFWW», y que en "
                     "«Cargado en Importaciones2» todavía no figuran como cargados (Reservas y Reservas Históricas, "
                     "marítimo y camión)."),
            KPI("Riesgo de SLA", fmt.fmt_int(n_tipo.get(bandeja.TIPOS["sla"], 0)),
                status="bad" if n_tipo.get(bandeja.TIPOS["sla"], 0) else "ok",
                help="Marítimos con consolidación proyectada fuera de SLA y aéreos con punta a punta proyectado fuera "
                     "del SLA de su tipo, todavía sin «ETD OK FFWW» (hay margen para actuar)."),
            KPI("Datos a corregir", fmt.fmt_int(n_tipo.get(bandeja.TIPOS["dato"], 0)
                                                + n_tipo.get(bandeja.TIPOS["cerrado"], 0)),
                status="warn",
                help="Cerrados fuera de SLA sin causa cargada y registros con datos rotos o incompletos "
                     "(detalle en Salud de datos)."),
        ])

        c1, c2, c3 = st.columns([2, 3, 2], gap="small")
        resp = c1.selectbox("Responsable", ["Todos"] + sorted(df["responsable"].dropna().astype(str).unique()),
                            key="acc_resp")
        tipos = ["Todos"] + [v for v in bandeja.TIPOS.values() if v in set(df["tipo"])]
        tipo = c2.selectbox("Tipo de acción", tipos, key="acc_tipo")
        prio = c3.multiselect("Prioridad", bandeja.PRIORIDADES, default=bandeja.PRIORIDADES, key="acc_prio")
        v = df
        if resp != "Todos":
            v = v[v["responsable"].astype(str) == resp]
        if tipo != "Todos":
            v = v[v["tipo"] == tipo]
        if prio:
            v = v[v["prioridad"].isin(prio)]
        estilos = v["prioridad"].map({"Alta": "background-color: rgba(192,57,43,0.07)"}).fillna("")
        data_table(v, COLS, key="acc_tabla", filename="bandeja_de_accion", row_styles=estilos,
                   caption="Ordenado por prioridad y ETD · «Excedidos» = días por encima del SLA")

        with st.expander("Casos por responsable"):
            g = (df.assign(responsable=df["responsable"].fillna("Sin responsable"))
                 .groupby("responsable")
                 .agg(casos=("tipo", "size"), alta=("prioridad", lambda s: int((s == "Alta").sum())),
                      forwarder=("tipo", lambda s: int((s == bandeja.TIPOS["forwarder"]).sum())),
                      sla=("tipo", lambda s: int((s == bandeja.TIPOS["sla"]).sum())),
                      impo2=("tipo", lambda s: int((s == bandeja.TIPOS["impo2"]).sum())),
                      datos=("tipo", lambda s: int(s.isin([bandeja.TIPOS["dato"], bandeja.TIPOS["cerrado"]]).sum())))
                 .sort_values(["alta", "casos"], ascending=False).reset_index())
            data_table(g, [
                ColSpec("responsable", "Responsable"), ColSpec("casos", "Casos", "int"), ColSpec("alta", "Alta", "int"),
                ColSpec("forwarder", "Forwarder", "int"), ColSpec("sla", "Riesgo SLA", "int"),
                ColSpec("impo2", "Impo2", "int"), ColSpec("datos", "Datos", "int"),
            ], key="acc_resp_tabla", filename="bandeja_por_responsable", search=False)
