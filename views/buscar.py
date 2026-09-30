"""Buscador por SO o por embarque.

Busca en todas las fuentes (Planif cargas, Reservas, Históricas y Aéreos) y
cruza la información: una SO muestra su embarque y un embarque muestra sus SO.
Ignora los filtros de la barra lateral a propósito (se busca siempre en todo).

Coincidencia tolerante: "38529", "so 38529", "SO-38529" y "so38529" encuentran
la misma SO; "2679" encuentra "FCL 2679" pero no "FCL 26790".
"""
from __future__ import annotations

import re

import pandas as pd
import streamlit as st

from components.kpi_cards import KPI, kpi_row
from components.layout import empty, esc, guard, section
from components.tables import ColSpec, data_table
from utils import calculations as calc
from utils import formatting as fmt
from utils.data_cleaning import fold
from views._common import ctx

MAX_SHIPMENTS = 10


def _key(v) -> str:
    """Clave de búsqueda: minúsculas, sin signos y con letras/números separados."""
    s = fold(v)
    s = re.sub(r"(?<=[a-z])(?=\d)|(?<=\d)(?=[a-z])", " ", s)
    return re.sub(r"\s+", " ", s).strip()


def matches(series: pd.Series, query: str) -> pd.Series:
    q = _key(query)
    if not q:
        return pd.Series(False, index=series.index)
    keys = series.map(lambda v: _key(v) if v is not None and v == v else "")
    tokens = q.split(" ")
    mask = pd.Series(True, index=series.index)
    for tok in tokens:
        if tok.isdigit():
            pat = re.compile(rf"(?:^|\s){re.escape(tok)}(?:\s|$)")
        else:
            pat = re.compile(rf"(?:^|\s){re.escape(tok)}")
        mask &= keys.map(lambda k: bool(pat.search(k)))
    return mask


def shipment_card(row: pd.Series, origen: str) -> None:
    est = row.get("estado_consolidacion")
    status = {"Dentro de SLA": "ok", "Atención": "warn", "Fuera de SLA": "bad"}.get(est, "")
    cons = row.get("dias_consolidacion")
    sla = row.get("sla_consolidacion")
    st.markdown(f"**{esc(row['embarque'])}** · {esc(origen)}"
                + (f" · {esc(row.get('estadio'))}" if row.get("estadio") else ""))
    kpi_row([
        KPI("ETD", fmt.fmt_date(row.get("etd")),
            sub=("ETD confirmado" if row.get("etd_ok") is True else
                 ("ETD sin confirmar" if row.get("etd_ok") is False else ""))),
        KPI("ETA", fmt.fmt_date(row.get("eta")),
            sub=f"Caldas: {fmt.fmt_date(row.get('eta_caldas'))}" if "eta_caldas" in row else ""),
        KPI("Origen / Forwarder", str(row.get("puerto") or "—"), sub=esc(row.get("forwarder") or "—")),
        KPI("Carga", f"{fmt.fmt_num(row.get('m3'), 1)} m³",
            sub=f"{fmt.fmt_int(row.get('contenedores'))} cont. · {esc(row.get('tipo_carga') or '')}"
            if "contenedores" in row else esc(row.get("tipo_carga") or "")),
        KPI("Consolidación", fmt.fmt_days(cons) if cons == cons else "—", status=status,
            badge=est if isinstance(est, str) else "",
            sub=f"SLA {fmt.fmt_int(sla)} d" if sla == sla and sla is not None else ""),
    ])
    obs = row.get("observaciones")
    if isinstance(obs, str) and obs:
        st.caption(f"Observaciones: {obs}")


def render() -> None:
    bundle, _ = ctx()
    section("Buscar por SO o embarque", "Ejemplos: 38529 · SO-38529 · FCL 2679 · AIR 199. "
            "La búsqueda ignora los filtros de la barra lateral.")
    query = st.text_input("SO o embarque", key="search_q", placeholder="Escribí un número de SO o de embarque…",
                          label_visibility="collapsed")
    if not query or len(_key(query)) < 2:
        st.caption("Ingresá al menos 2 caracteres.")
        return

    with guard("Búsqueda"):
        planif = bundle.get("planif")
        so_hits = pd.DataFrame()
        if planif is not None:
            so_hits = planif[matches(planif["so"], query) | matches(planif["embarque"], query)]

        ship_ids = set()
        sources = [("reservas", "En curso (Reservas)"), ("aereos", "Aéreo (Seguimiento)"),
                   ("historicas", "Histórico")]
        found: list[tuple[pd.Series, str]] = []
        for key, label in sources:
            d = bundle.get(key)
            if d is None:
                continue
            hits = d[matches(d["embarque"], query)]
            # Embarques de las SO encontradas.
            if not so_hits.empty:
                emb = {_key(e) for e in so_hits["embarque"].dropna()}
                hits = pd.concat([hits, d[d["embarque"].map(_key).isin(emb)]]).drop_duplicates("embarque")
            for _, r in hits.iterrows():
                k = _key(r["embarque"])
                if k in ship_ids:
                    continue  # ya mostrado desde una fuente más actual
                ship_ids.add(k)
                found.append((r, label))

        # SO de los embarques encontrados (si se buscó por embarque).
        if planif is not None and ship_ids:
            extra = planif[planif["embarque"].map(_key).isin(ship_ids)]
            so_hits = pd.concat([so_hits, extra]).drop_duplicates()

        n_so = so_hits["so"].nunique() if len(so_hits) else 0
        st.markdown(f"**{fmt.plural(len(found), 'embarque')}** · **{fmt.plural(n_so, 'SO encontrada', 'SO encontradas')}**")
        if not found and not n_so:
            empty(f"No se encontró «{query}» en ninguna fuente. Revisá el número o probá solo con los dígitos.")
            return

        if found:
            section("Embarques")
            for r, label in found[:MAX_SHIPMENTS]:
                with st.container(border=True):
                    shipment_card(r, label)
            if len(found) > MAX_SHIPMENTS:
                st.caption(f"Se muestran {MAX_SHIPMENTS} de {len(found)}. Refiná la búsqueda para ver el resto.")

        if n_so:
            section("SO relacionadas", "Planificación de cargas (una fila por línea de producto)")
            data_table(so_hits.sort_values(["so"]), [
                ColSpec("so", "SO"), ColSpec("embarque", "Embarque"), ColSpec("estado_instruccion", "Estado"),
                ColSpec("proveedor", "Proveedor", width="medium"), ColSpec("marca", "Marca"),
                ColSpec("puerto", "Puerto"), ColSpec("f_instruccion", "Instrucción", "date"),
                ColSpec("etd", "ETD", "date"), ColSpec("eta", "ETA", "date"),
                ColSpec("m3", "M3", "num"), ColSpec("fob", "FOB (USD)", "usd"),
                ColSpec("status_final", "Status"), ColSpec("responsable", "Responsable"),
            ], key="search_so", filename="busqueda_so", search=False)
