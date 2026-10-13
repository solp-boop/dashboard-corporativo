"""Buscador Comex: por SO, embarque o producto (SKU / código, descripción o modelo).

Busca en todas las fuentes (Planif cargas, Reservas, Históricas, Aéreos y Embarques Históricos) y
cruza la información: una SO muestra su embarque, un embarque muestra sus SO y un SKU muestra en qué SO y
embarques viajó. Se usa en la página «Buscar» y en la ventana «Buscador Comex» de la barra lateral.
Ignora los filtros de la barra lateral a propósito (se busca siempre en todo).

Coincidencia tolerante: "38529", "so 38529", "SO-38529" y "so38529" encuentran
la misma SO; "2679" encuentra "FCL 2679" pero no "FCL 26790".
"""
from __future__ import annotations

import re
from urllib.parse import quote

import pandas as pd
import streamlit as st

from components.kpi_cards import KPI, kpi_row
from components.layout import empty, esc, guard, section
from components.tables import ColSpec, data_table
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


PRODUCTO_COLS = ["codigo", "descripcion", "marca", "so", "embarque", "cantidad", "etd", "eta", "estado", "fuente"]


def _productos(bundle, query: str) -> pd.DataFrame:
    """Líneas de producto que coinciden por código (SKU), descripción o modelo: Planif cargas (una fila por SO ×
    producto) y Embarques Históricos (solo código). Una fila por código × SO × embarque."""
    partes = []
    planif = bundle.get("planif")
    if planif is not None and "codigo" in planif:
        m = pd.Series(False, index=planif.index)
        for c in ("codigo", "descripcion", "descripcion_master", "modelo"):
            if c in planif:
                m |= matches(planif[c], query)
        p = planif[m]
        if len(p):
            desc = p["descripcion"] if "descripcion" in p else pd.Series(index=p.index, dtype=object)
            if "descripcion_master" in p:
                desc = desc.fillna(p["descripcion_master"])
            partes.append(pd.DataFrame({
                "codigo": p["codigo"], "descripcion": desc, "marca": p.get("marca"), "so": p["so"],
                "embarque": p["embarque"], "cantidad": p.get("cantidad"), "etd": p.get("etd"), "eta": p.get("eta"),
                "estado": p.get("status_final"), "fuente": "Planif cargas"}))
    eh = bundle.get("emb_hist")
    if eh is not None and "codigo" in eh:
        e = eh[matches(eh["codigo"], query)]
        if len(e):
            partes.append(pd.DataFrame({
                "codigo": e["codigo"], "descripcion": None, "marca": None, "so": e["so"], "embarque": e["embarque"],
                "cantidad": None, "etd": e.get("etd"), "eta": None, "estado": "Embarcado",
                "fuente": "Embarques Históricos"}))
    if not partes:
        return pd.DataFrame(columns=PRODUCTO_COLS)
    d = pd.concat(partes, ignore_index=True)
    # Completa la descripción de lo histórico con la de Planif (mismo código) y saca duplicados (Planif primero).
    for c in ("descripcion", "marca"):
        nombres = d.dropna(subset=[c]).drop_duplicates("codigo").set_index("codigo")[c]
        d[c] = d[c].fillna(d["codigo"].map(nombres))
    d["_k"] = d["codigo"].map(_key) + "|" + d["so"].map(_key) + "|" + d["embarque"].map(lambda v: _key(v) if v == v else "")
    d = d.drop_duplicates("_k").drop(columns="_k")
    return d[PRODUCTO_COLS].reset_index(drop=True)


def buscar(bundle, query: str) -> dict:
    """{found: [(fila, fuente)], so_hits: Planif de las SO, productos: líneas de producto (SKU)}."""
    planif = bundle.get("planif")
    so_hits = pd.DataFrame()
    if planif is not None:
        so_hits = planif[matches(planif["so"], query) | matches(planif["embarque"], query)]
    productos = _productos(bundle, query)
    # Embarques a mostrar: los que coinciden, los de las SO encontradas y los de los productos encontrados.
    emb = {_key(e) for e in so_hits["embarque"].dropna()} if len(so_hits) else set()
    emb |= {_key(e) for e in productos["embarque"].dropna()}
    ship_ids = set()
    found: list[tuple[pd.Series, str]] = []
    for key, label in [("reservas", "En curso (Reservas)"), ("aereos", "Aéreo (Seguimiento)"),
                       ("historicas", "Histórico")]:
        d = bundle.get(key)
        if d is None:
            continue
        hits = d[matches(d["embarque"], query)]
        if emb:
            hits = pd.concat([hits, d[d["embarque"].map(_key).isin(emb)]]).drop_duplicates("embarque")
        if "etd" in hits:
            hits = hits.sort_values("etd", ascending=False)
        for _, r in hits.iterrows():
            k = _key(r["embarque"])
            if k in ship_ids:
                continue  # ya mostrado desde una fuente más actual
            ship_ids.add(k)
            found.append((r, label))
    # SO de los embarques encontrados (si se buscó por embarque).
    if planif is not None and ship_ids and productos.empty:
        extra = planif[planif["embarque"].map(_key).isin(ship_ids)]
        so_hits = pd.concat([so_hits, extra]).drop_duplicates()
    if len(productos) and found:
        # ETD / ETA del embarque cuando la línea de producto no las trae (Embarques Históricos suele venir vacío).
        fechas = {_key(r["embarque"]): (r.get("etd"), r.get("eta")) for r, _ in found}
        k = productos["embarque"].map(lambda v: _key(v) if v == v else "")
        productos["etd"] = productos["etd"].fillna(k.map(lambda x: fechas.get(x, (None, None))[0]))
        productos["eta"] = productos["eta"].fillna(k.map(lambda x: fechas.get(x, (None, None))[1]))
    if len(productos):
        productos = productos.sort_values("etd", ascending=False, na_position="first").reset_index(drop=True)
    return {"found": found, "so_hits": so_hits, "productos": productos}


def _tabla_productos(prod: pd.DataFrame, key: str) -> None:
    data_table(prod, [
        ColSpec("codigo", "Código (SKU)"), ColSpec("descripcion", "Descripción", width="medium"),
        ColSpec("marca", "Marca"), ColSpec("so", "SO"), ColSpec("embarque", "Embarque"),
        ColSpec("cantidad", "Cantidad", "int"), ColSpec("etd", "ETD", "date"), ColSpec("eta", "ETA", "date"),
        ColSpec("estado", "Estado"), ColSpec("fuente", "Fuente"),
    ], key=key, filename="busqueda_producto", search=len(prod) > 12, height=min(420, 38 + 35 * len(prod)))


AYUDA = ("Escribí un número de SO (38529, SO-38529), un embarque (FCL 2679, AIR 199) o un producto: código / SKU "
         "(RCDJI070), modelo o parte de la descripción (osmo action). Busca en todo, sin los filtros de la barra "
         "lateral.")


@st.dialog("🔎 Buscador Comex", width="large")
def dialogo() -> None:
    """Ventana de búsqueda rápida (se abre desde la barra lateral). Resultados resumidos y enlace a la ficha."""
    bundle, _ = ctx()
    st.caption(AYUDA)
    q = st.text_input("¿Qué buscás?", key="bc_q", placeholder="SO, embarque, SKU o producto…",
                      label_visibility="collapsed")
    if not q or len(_key(q)) < 2:
        return
    with guard("Buscador"):
        r = buscar(bundle, q)
        found, so_hits, prod = r["found"], r["so_hits"], r["productos"]
        n_so = so_hits["so"].nunique() if len(so_hits) else 0
        n_sku = prod["codigo"].nunique() if len(prod) else 0
        if not found and not n_so and not n_sku:
            empty(f"No encontré «{q}». Probá solo con los números o con otra parte del nombre.")
            return
        st.markdown(f"**{fmt.plural(len(found), 'embarque')}** · **{fmt.plural(n_so, 'SO', 'SO')}** · "
                    f"**{fmt.plural(n_sku, 'producto')}** — "
                    f"<a href='buscar?q={quote(q)}' target='_self'>abrir la ficha completa →</a>",
                    unsafe_allow_html=True)
        if n_sku:
            st.markdown("**Productos**")
            _tabla_productos(prod.head(200), "bc_prod")
        if found:
            st.markdown("**Embarques**")
            lineas = []
            for row, origen in found[:MAX_SHIPMENTS]:
                partes = [f"**{esc(row['embarque'])}**", esc(origen)]
                if row.get("estadio"):
                    partes.append(esc(row.get("estadio")))
                partes.append(f"ETD {fmt.fmt_date(row.get('etd'))}")
                partes.append(f"ETA {fmt.fmt_date(row.get('eta'))}")
                if row.get("puerto"):
                    partes.append(esc(row.get("puerto")))
                if row.get("forwarder"):
                    partes.append(esc(row.get("forwarder")))
                lineas.append("- " + " · ".join(partes))
            st.markdown("\n".join(lineas))
            if len(found) > MAX_SHIPMENTS:
                st.caption(f"Se muestran {MAX_SHIPMENTS} de {len(found)}; el resto en la ficha completa.")
        if n_so and not n_sku:
            st.markdown("**SO**")
            data_table(so_hits.sort_values(["so"]), [
                ColSpec("so", "SO"), ColSpec("embarque", "Embarque"), ColSpec("proveedor", "Proveedor"),
                ColSpec("etd", "ETD", "date"), ColSpec("eta", "ETA", "date"), ColSpec("status_final", "Status"),
            ], key="bc_so", filename="busqueda_so", search=False, height=min(320, 38 + 35 * len(so_hits)))


def render() -> None:
    bundle, _ = ctx()
    section("Buscador Comex", AYUDA)
    if "q" in st.query_params and st.query_params["q"] != st.session_state.get("_q_url"):
        st.session_state["_q_url"] = st.query_params["q"]
        st.session_state["search_q"] = st.query_params["q"]
    query = st.text_input("SO, embarque o producto", key="search_q",
                          placeholder="SO, embarque, SKU o producto…", label_visibility="collapsed")
    if not query or len(_key(query)) < 2:
        st.caption("Ingresá al menos 2 caracteres.")
        return

    with guard("Búsqueda"):
        r = buscar(bundle, query)
        found, so_hits, prod = r["found"], r["so_hits"], r["productos"]
        n_so = so_hits["so"].nunique() if len(so_hits) else 0
        n_sku = prod["codigo"].nunique() if len(prod) else 0
        st.markdown(f"**{fmt.plural(len(found), 'embarque')}** · "
                    f"**{fmt.plural(n_so, 'SO encontrada', 'SO encontradas')}** · "
                    f"**{fmt.plural(n_sku, 'producto')}**")
        if not found and not n_so and not n_sku:
            empty(f"No se encontró «{query}» en ninguna fuente. Revisá el número o probá solo con los dígitos.")
            return

        if n_sku:
            section("Productos (SKU)", "En qué SO y embarques está cada producto: Planif cargas (con cantidad y "
                                       "estado) y Embarques Históricos.")
            _tabla_productos(prod, "search_prod")

        if found:
            section("Embarques")
            for r_, label in found[:MAX_SHIPMENTS]:
                with st.container(border=True):
                    shipment_card(r_, label)
            if len(found) > MAX_SHIPMENTS:
                st.caption(f"Se muestran {MAX_SHIPMENTS} de {len(found)}. Refiná la búsqueda para ver el resto.")

        if n_so:
            section("SO relacionadas", "Planificación de cargas (una fila por línea de producto)")
            data_table(so_hits.sort_values(["so"]), [
                ColSpec("so", "SO"), ColSpec("embarque", "Embarque"), ColSpec("estado_instruccion", "Estado"),
                ColSpec("proveedor", "Proveedor", width="medium"), ColSpec("marca", "Marca"),
                ColSpec("codigo", "Código (SKU)"), ColSpec("descripcion", "Descripción", width="medium"),
                ColSpec("puerto", "Puerto"), ColSpec("f_instruccion", "Instrucción", "date"),
                ColSpec("etd", "ETD", "date"), ColSpec("eta", "ETA", "date"),
                ColSpec("m3", "M3", "num"), ColSpec("fob", "FOB (USD)", "usd"),
                ColSpec("status_final", "Status"), ColSpec("responsable", "Responsable"),
            ], key="search_so", filename="busqueda_so", search=False)
