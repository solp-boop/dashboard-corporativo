"""Carga, normalización y validación de datos.

Flujo:  fuente -> resolver encabezados -> tipar -> normalizar -> derivar -> calidad

`build_bundle(source)` es puro (sin Streamlit) para poder testearlo.
`get_data()` es la versión cacheada que usa la app.
"""
from __future__ import annotations

import datetime as dt
import re
from dataclasses import dataclass, field
from zoneinfo import ZoneInfo

import numpy as np
import pandas as pd
import streamlit as st

from config import mappings, settings
from config.schema import SCHEMAS, VALIDACIONES_SLA_ANCHOR, DatasetSchema
from services.google_sheets import SheetSource, SourceError, find_tab
from utils import calculations as calc
from utils import data_cleaning as dc
from utils.logger import get_logger

log = get_logger("loader")

# Campos categóricos que se unifican entre todos los datasets.
SHARED_CATEGORIES = ["empresa", "destino", "puerto", "forwarder", "tipo_carga",
                     "shipper", "responsable", "tipo_demora", "estructura", "booking"]

# Campos que se controlan en "Calidad de datos" (etiqueta legible).
KEY_FIELDS = {
    "reservas": {"etd": "ETD", "puerto": "Puerto", "forwarder": "Forwarder",
                 "f_packeo_min": "Fecha packeo mín.", "f_instruccion": "Fecha de instrucción",
                 "m3": "M3", "estructura": "Mono/Consolidado"},
    "historicas": {"etd": "ETD", "eta": "ETA", "puerto": "Puerto", "forwarder": "Forwarder",
                   "f_packeo_min": "Fecha packeo mín.", "f_instruccion": "Fecha de instrucción",
                   "estructura": "Mono/Consolidado"},
    "aereos": {"etd": "ETD", "eta": "ETA", "f_packeo_min": "Fecha packeo mín.",
               "f_ingreso_wh": "Ingreso WH", "eta_caldas": "ETA Caldas", "forwarder": "Forwarder"},
    "planif": {"etd": "ETD", "puerto": "Puerto de salida", "proveedor": "Proveedor", "m3": "M3"},
    "emb_hist": {"fin_produccion": "Fecha fin de producción real"},
    "cot_sin_negociar": {"flete": "Valor flete", "tipo_ctnr": "Tipo contenedor", "validez_desde": "Validez desde"},
    "cotizaciones": {"flete": "Valor flete", "puerto": "POL", "tipo_ctnr": "Tipo contenedor",
                     "validez_desde": "Validez desde", "validez_hasta": "Validez hasta"},
}


# ---------------------------------------------------------------------------
@dataclass
class DatasetQuality:
    key: str
    title: str
    tab: str = ""
    available: bool = False
    message: str = ""
    rows_raw: int = 0
    rows_empty: int = 0
    rows_filler: int = 0
    duplicates: int = 0
    rows_final: int = 0
    missing_required: list[str] = field(default_factory=list)
    missing_optional: list[str] = field(default_factory=list)
    invalid_values: dict[str, int] = field(default_factory=dict)      # col -> n
    out_of_range: dict[str, int] = field(default_factory=dict)        # col -> n
    missing_key_fields: dict[str, int] = field(default_factory=dict)  # etiqueta -> n
    complete_rows: int = 0
    # celdas con error de fórmula (#N/A, #REF!, #VALUE!…): columna -> (celdas, valores, ejemplos de registro)
    error_cells: dict[str, tuple[int, str, str]] = field(default_factory=dict)
    # filas de la planilla (columna «_fila» de cada dataset) con cada problema: (tipo, columna) -> [filas]
    # tipo: "error" | "invalido" | "rango". Sirve para acotar los controles (desde 2026, ETD OK, etc.).
    issue_rows: dict[tuple[str, str], list[int]] = field(default_factory=dict)
    # filas con datos cuya referencia (Embarque / SO) es un error de fórmula (#N/A…): se descartan, pero se avisan
    ref_errores: list[dict] = field(default_factory=list)

    @property
    def complete_pct(self) -> float:
        return self.complete_rows / self.rows_final if self.rows_final else 0.0


@dataclass
class DataBundle:
    datasets: dict[str, pd.DataFrame]
    sla_puertos: pd.DataFrame
    quality: dict[str, DatasetQuality]
    errors: list[str]
    loaded_at: dt.datetime
    source_name: str
    source_modified: dict[str, dt.datetime | None] = field(default_factory=dict)
    stale: bool = False  # True si son datos de una carga anterior (la última falló)
    code_version: str = ""

    def get(self, key: str) -> pd.DataFrame | None:
        return self.datasets.get(key)

    def available(self, key: str) -> bool:
        q = self.quality.get(key)
        return bool(q and q.available and key in self.datasets)


# ---------------------------------------------------------------------------
# Resolución de encabezados
# ---------------------------------------------------------------------------
def resolve_columns(schema: DatasetSchema, headers: list) -> tuple[dict[str, int], list, list]:
    """Mapea columna canónica -> índice. Devuelve (mapa, faltan_obligatorias, faltan_opcionales)."""
    folded = [dc.fold(h) for h in headers]
    found, miss_req, miss_opt = {}, [], []
    for col in schema.columns:
        idx = None
        for alias in col.aliases:
            k = dc.fold(alias)
            if k in folded:
                idx = folded.index(k)
                break
        if idx is None:
            (miss_req if col.required else miss_opt).append(col.display)
        else:
            found[col.name] = idx
    return found, miss_req, miss_opt


def grid_to_frame(schema: DatasetSchema, grid: list[list], colmap: dict[str, int]) -> pd.DataFrame:
    body = grid[1:] if grid else []
    data = {}
    for col in schema.columns:
        idx = colmap.get(col.name)
        if idx is None:
            data[col.name] = [None] * len(body)
        else:
            data[col.name] = [(r[idx] if idx < len(r) else None) for r in body]
    return pd.DataFrame(data, dtype=object)


# ---------------------------------------------------------------------------
# Tipado
# ---------------------------------------------------------------------------
def _filas(mask) -> list[int]:
    """Número de fila de la planilla (encabezado = fila 1) de las filas marcadas."""
    if mask is None:
        return []
    return [int(i) + FILA_OFFSET for i in mask[mask.fillna(False).astype(bool)].index]


FILA_OFFSET = 2   # grid_to_frame: índice 0 = fila 2 de la solapa


def type_columns(df: pd.DataFrame, schema: DatasetSchema, q: DatasetQuality) -> pd.DataFrame:
    out = pd.DataFrame(index=df.index)
    for col in schema.columns:
        s = df[col.name]
        try:
            if col.kind == "date":
                out[col.name], st_ = dc.parse_dates(s)
                if st_.invalid:
                    q.invalid_values[col.display] = st_.invalid
                    q.issue_rows[("invalido", col.display)] = _filas(st_.invalid_mask)
                if st_.out_of_range:
                    q.out_of_range[col.display] = st_.out_of_range
                    q.issue_rows[("rango", col.display)] = _filas(st_.range_mask)
            elif col.kind == "number":
                out[col.name], st_ = dc.parse_numbers(s)
                if st_.invalid:
                    q.invalid_values[col.display] = st_.invalid
                    q.issue_rows[("invalido", col.display)] = _filas(st_.invalid_mask)
            elif col.kind == "flag":
                out[col.name] = dc.parse_flags(s)
            elif col.kind == "category":
                out[col.name] = dc.apply_aliases(s, mappings.VALUE_ALIASES.get(col.name))
            else:  # id / text
                out[col.name] = dc.clean_text(s)
        except Exception:  # nunca romper la carga por una columna
            log.exception("Error convirtiendo %s.%s", schema.key, col.name)
            q.invalid_values[col.display] = int(s.notna().sum())
            out[col.name] = pd.Series([None] * len(s), index=s.index, dtype=object)
    return out


# ---------------------------------------------------------------------------
# Derivaciones
# ---------------------------------------------------------------------------
def derive_modo(df: pd.DataFrame) -> pd.Series:
    tc = df.get("tipo_carga", pd.Series(index=df.index, dtype=object))
    emb = df.get("embarque", pd.Series(index=df.index, dtype=object))

    def one(t, e):
        m = mappings.MODO_POR_TIPO_CARGA.get(dc.fold(t)) if t else None
        if m:
            return m
        if e:
            prefix = str(e).strip().split(" ")[0].upper()
            return mappings.MODO_POR_PREFIJO.get(prefix)
        return None

    return pd.Series([one(t, e) for t, e in zip(tc, emb)], index=df.index, dtype=object)


def normalize_estructura(s: pd.Series) -> pd.Series:
    return s.map(lambda v: v if v in mappings.ESTRUCTURA_VALIDAS else None).astype(object)


def normalize_booking(s: pd.Series) -> pd.Series:
    return s.map(lambda v: v if v in ("In advance", "Spot") else None).astype(object)


def parse_sla_table(grid: list[list]) -> pd.DataFrame:
    """Tabla de targets por puerto de la solapa Validaciones."""
    cols = ["puerto", "sla_consolidacion", "sla_tt", "sla_total"]
    if not grid:
        return pd.DataFrame(columns=cols + ["puerto_key"])
    header = [dc.fold(h) for h in grid[0]]
    anchors = {dc.fold(a) for a in VALIDACIONES_SLA_ANCHOR}
    idx = next((i for i, h in enumerate(header) if h in anchors), None)
    if idx is None or idx == 0:
        return pd.DataFrame(columns=cols + ["puerto_key"])
    rows = []
    for r in grid[1:]:
        r = list(r) + [None] * 4
        port = dc.clean_text_value(r[idx - 1])
        if not port:
            continue
        vals = [dc.parse_number_value(r[idx + k])[0] for k in range(3)]
        rows.append([port, *vals])
    out = pd.DataFrame(rows, columns=cols)
    # «Ningbo-Monoproducto»: targets propios para monoproveedor (tránsito y total). La clave es
    # «<puerto> monoproducto», con el puerto unificado igual que el resto («Nangtong» → «Nantong»).
    mono = out["puerto"].astype(str).str.contains(r"(?i)-\s*monoproducto\s*$", regex=True)
    base = out["puerto"].astype(str).str.replace(r"(?i)\s*-\s*monoproducto\s*$", "", regex=True)
    base = dc.apply_aliases(base, mappings.VALUE_ALIASES.get("puerto"))
    out["puerto"] = np.where(mono, base + "-Monoproducto", base)
    out["puerto_key"] = base.map(dc.fold) + np.where(mono, " monoproducto", "")
    return out.drop_duplicates("puerto_key")


def add_sla(df: pd.DataFrame, sla: pd.DataFrame, cons_fijo: bool = False) -> pd.DataFrame:
    """SLA por puerto (Validaciones). cons_fijo=True: consolidación con el tope fijo de la empresa
    (25 d consolidado / 15 d monoproveedor), sin mirar el puerto. Se usa para lo que está en curso."""
    key = df["puerto"].map(lambda v: dc.fold(v) if v else "")
    lookup = sla.set_index("puerto_key") if not sla.empty else pd.DataFrame(
        columns=["sla_consolidacion", "sla_tt", "sla_total"])
    port_cons = key.map(lookup["sla_consolidacion"]) if not sla.empty else np.nan
    port_tt = key.map(lookup["sla_tt"]) if not sla.empty else np.nan
    port_total = key.map(lookup["sla_total"]) if not sla.empty else np.nan

    es_mono = df["estructura"] == "Monoproveedor"
    if not sla.empty:
        # Monoproveedor: tránsito y total del renglón «<puerto>-Monoproducto» de Validaciones, si existe.
        key_mono = key.map(lambda k: f"{k} monoproducto" if k else "")
        tiene_mono = es_mono & key_mono.isin(lookup.index)
        port_tt = pd.Series(port_tt, index=df.index).where(~tiene_mono, key_mono.map(lookup["sla_tt"]))
        port_total = pd.Series(port_total, index=df.index).where(~tiene_mono, key_mono.map(lookup["sla_total"]))
    df["sla_puerto_definido"] = key.isin(lookup.index) if not sla.empty else False
    cons = pd.Series(port_cons, index=df.index, dtype=float).fillna(settings.SLA_CONSOLIDACION_DEFAULT)
    mono_sla = calc.sla_mono(df["etd"]).values
    # SLA de consolidación por puerto (lo que corresponde una vez zarpado), aunque en curso se use el tope fijo.
    df["sla_cons_puerto"] = np.where(es_mono, mono_sla, cons)
    if cons_fijo:
        cons = pd.Series(float(settings.SLA_CONSOLIDACION_DEFAULT), index=df.index)
    df["sla_consolidacion"] = np.where(es_mono, mono_sla, cons)
    df["sla_tt"] = pd.Series(port_tt, index=df.index, dtype=float).fillna(settings.SLA_TT_DEFAULT)
    df["sla_total"] = pd.Series(port_total, index=df.index, dtype=float).fillna(settings.SLA_TOTAL_DEFAULT)
    df["estado_consolidacion"] = calc.semaforo(df["dias_consolidacion"], df["sla_consolidacion"])
    df["estado_total"] = calc.semaforo(df["dias_total"], df["sla_total"])
    df["cumple_consolidacion"] = (df["dias_consolidacion"] <= df["sla_consolidacion"]).where(
        df["dias_consolidacion"].notna())
    return df


def add_durations(df: pd.DataFrame, specs: dict[str, tuple[str, str]], q: DatasetQuality) -> pd.DataFrame:
    for metric, (end, start) in specs.items():
        if end not in df or start not in df:
            df[metric] = np.nan
            continue
        df[metric], bad = calc.days_between(df[end], df[start], metric)
        if bad:
            label = f"Tiempo: {METRIC_LABELS.get(metric, metric)}"
            q.out_of_range[label] = bad
            if "_fila" in df:
                crudo = (pd.to_datetime(df[end]) - pd.to_datetime(df[start])).dt.days
                q.issue_rows[("rango", label)] = df.loc[crudo.notna() & df[metric].isna(), "_fila"].astype(int).tolist()
    return df


METRIC_LABELS = {
    "dias_comex": "packeo → instrucción", "dias_agente": "instrucción → ETD",
    "dias_consolidacion": "consolidación (packeo → ETD)", "dias_tt": "tránsito (ETD → ETA)",
    "dias_total": "total (fin de producción → ETA)", "desvio_etd": "desvío ETD vs estimada",
    "dias_espera": "espera (packeo mín. → máx.)", "dias_packeo_wh": "packeo → WH",
    "dias_wh_etd": "WH → ETD", "dias_wh_instr": "WH → instrucción", "dias_instr_etd": "instrucción → ETD",
    "dias_etd_eta": "ETD → ETA", "dias_eta_caldas": "ETA → Caldas",
    "dias_total_aereo": "total aéreo (packeo → Caldas)",
}

MARITIME_DURATIONS = {
    "dias_comex": ("f_instruccion", "f_packeo_min"),
    "dias_agente": ("etd", "f_instruccion"),
    "dias_consolidacion": ("etd", "f_packeo_min"),
    "dias_tt": ("eta", "etd"),
    "dias_total": ("eta", "f_fin_produccion"),
    "desvio_etd": ("etd", "etd_estimada"),
    "dias_espera": ("f_packeo_max", "f_packeo_min"),
}
AIR_DURATIONS = {
    "dias_packeo_wh": ("f_ingreso_wh", "f_packeo_min"),
    "dias_wh_etd": ("etd", "f_ingreso_wh"),
    "dias_wh_instr": ("f_instruccion", "f_ingreso_wh"),
    "dias_instr_etd": ("etd", "f_instruccion"),
    "dias_etd_eta": ("eta", "etd"),
    "dias_eta_caldas": ("eta_caldas", "eta"),
    "dias_total_aereo": ("eta_caldas", "f_packeo_min"),
}


def add_freight(df: pd.DataFrame) -> pd.DataFrame:
    """Costos por contenedor y por m³ de cada embarque (Reservas Históricas).

    En la planilla, Flete Int PAGADO, Gastos Locales y Total Gastos Origen son
    por embarque; se dividen por la cantidad de contenedores.
    """
    cont = df["contenedores"].where(df["contenedores"] > 0)
    pagado = df["flete_pagado"].where(df["flete_pagado"] > 0)
    unit = df["flete_unitario"].where(df["flete_unitario"] > 0)
    df["flete_por_ctnr"] = unit.fillna(pagado / cont)
    df["locales_por_ctnr"] = df["gastos_locales"].where(df["gastos_locales"] > 0) / cont
    df["origen_por_ctnr"] = df["gastos_origen"].where(df["gastos_origen"] > 0) / cont
    df["costo_total"] = (pagado.fillna(0) + df["gastos_locales"].fillna(0).clip(lower=0)
                         + df["gastos_origen"].fillna(0).clip(lower=0)).where(pagado.notna())
    m3 = df["m3"].where(df["m3"] > 0)
    df["costo_por_m3"] = df["costo_total"] / m3
    df["tipo_ctnr"] = df["tipo_carga"].map(
        lambda v: mappings.CTNR_POR_TIPO_CARGA.get(dc.fold(v)) if v else None)
    return df


def add_air_sla(df: pd.DataFrame, q: DatasetQuality) -> pd.DataFrame:
    """SLA aéreo: columna Total contra el objetivo de su tipo de negocio."""
    lo, hi = settings.DURATION_RANGES["dias_total_aereo"]
    tot = df["total_dias"]
    bad = tot.notna() & ((tot < lo) | (tot > hi))
    if bad.any():
        q.out_of_range["Total aéreo (días)"] = int(bad.sum())
        if "_fila" in df:
            q.issue_rows[("rango", "Total aéreo (días)")] = df.loc[bad, "_fila"].astype(int).tolist()
    df["dias_aereo"] = tot.mask(bad)
    targets = {k.upper(): v for k, v in settings.SLA_AEREO_POR_TIPO.items()}
    alias = {k.upper(): v.upper() for k, v in settings.SLA_AEREO_ALIAS.items()}

    def tipo_sla(v):
        if not v:
            return None
        k = dc.fold(v).upper()
        k = alias.get(k, k)
        return k if k in targets else None

    df["tipo_sla"] = df["tipo_negocio"].map(tipo_sla)
    df["sla_aereo"] = df["tipo_sla"].map(targets).astype(float)
    df["sla_vigente"] = df["etd"] >= pd.Timestamp(settings.SLA_AEREO_DESDE)
    df["estado_aereo"] = calc.semaforo(df["dias_aereo"], df["sla_aereo"])
    return df


def prepare_emb_hist(eh: pd.DataFrame, hist: pd.DataFrame | None) -> None:
    """Marca SKU nuevo y top ranking y toma la estructura (mono/consolidado) de Reservas Históricas."""
    lo, hi = settings.DURATION_RANGES["tiempo_consolidacion_so"]
    t = eh["tiempo_consolidacion"]
    eh["tiempo_consolidacion"] = t.where(t.between(lo, hi))
    nuevo = eh["sku_nuevo"].map(lambda v: dc.fold(v) if v else "")
    # La columna trae "SI"/"NO" o, en los SKU nuevos, el código del producto.
    eh["es_nuevo"] = (nuevo == "si") | ~nuevo.isin(["", "no", "si"])
    rank = pd.to_numeric(eh["ranking"], errors="coerce")
    eh["ranking_pos"] = rank
    eh["es_top"] = rank.between(1, settings.TOP_RANKING_MAX)
    est_eh = eh["estructura_eh"].map(lambda v: {"consolidado": "Consolidado",
                                                "monoproveedor": "Monoproveedor"}.get(dc.fold(v)) if v else None)
    key = dc.id_key(eh["embarque"])
    if hist is not None and not hist.empty and "estructura" in hist:
        h = hist.assign(_k=dc.id_key(hist["embarque"]))
        h_est = h.dropna(subset=["estructura"]).drop_duplicates("_k").set_index("_k")["estructura"]
        est_h = key.map(h_est)
        est_h = est_h.map(lambda v: {"consolidado": "Consolidado", "monoproveedor": "Monoproveedor"}.get(dc.fold(v), v)
                          if isinstance(v, str) else None)
        eh["estructura"] = est_h.where(est_h.notna(), est_eh)
    else:
        eh["estructura"] = est_eh
    eh["maritimo"] = eh["embarque"].map(lambda v: str(v).strip().upper().startswith(("FCL", "LCL")))


def attach_fin_produccion(frames: dict[str, pd.DataFrame]) -> None:
    """Agrega a Reservas e Históricas la fecha de fin de producción de cada embarque.

    Viene de Embarques Historicos (una fila por SO). Se toma la fecha MÁS
    TEMPRANA entre las SO del embarque, igual que la consolidación usa el
    packeo mínimo.
    """
    eh = frames.get("emb_hist")
    if eh is not None and not eh.empty:
        prepare_emb_hist(eh, frames.get("historicas"))
    if eh is None or eh.empty:
        for key in ("reservas", "historicas"):
            if key in frames:
                frames[key]["f_fin_produccion"] = pd.NaT
        return
    fp = (eh.dropna(subset=["fin_produccion"])
            .assign(_k=lambda d: dc.id_key(d["embarque"]))
            .groupby("_k")["fin_produccion"].min())
    for key in ("reservas", "historicas"):
        if key in frames:
            df = frames[key]
            df["f_fin_produccion"] = pd.to_datetime(dc.id_key(df["embarque"]).map(fp), errors="coerce")


def tipo_negocio_planif(row_marca, row_clase) -> str:
    c = dc.fold(row_clase)
    if "muestra" in c:
        return "Muestras"
    if c == "repuestos":
        return "Repuestos"
    m = dc.fold(row_marca)
    if not m:
        return "Sin marca"
    if "gadnic" in m or m in {"rieti", "vetra"}:
        return "GADNIC"
    if m.startswith("dji"):
        return "DJI"
    return "Otras marcas"


def estado_instruccion(raw) -> str:
    ts, state = dc.parse_date_value(raw)
    if ts is not None:
        return "Instruida"
    f = dc.fold(raw)
    if "sin instruccion" in f or f in {"pendiente", "no"}:
        return "Pendiente"
    return "Sin clasificar"


def finish_dataset(key: str, df: pd.DataFrame, sla: pd.DataFrame, q: DatasetQuality) -> pd.DataFrame:
    """Reglas específicas de cada dataset (después de unificar categorías)."""
    if "estructura" in df:
        df["estructura"] = normalize_estructura(df["estructura"])
    if "booking" in df:
        df["booking"] = normalize_booking(df["booking"])
    if "tipo_carga" in df or "embarque" in df:
        df["modo"] = derive_modo(df)

    if key == "historicas":
        df = add_freight(df)
    if key in ("reservas", "historicas"):
        df = add_durations(df, MARITIME_DURATIONS, q)
        df = add_sla(df, sla, cons_fijo=(key == "reservas" and settings.SLA_EN_CURSO_FIJO))
        fob_real = df["fob_real"] if "fob_real" in df else pd.Series(np.nan, index=df.index)
        df["fob"] = fob_real.where(fob_real > 0, df["fob_simi"])
    if key == "reservas":
        df["etd_ok"] = df["etd_ok"].fillna(False).astype(bool)
    if key == "aereos":
        df = add_durations(df, AIR_DURATIONS, q)
        df["activo"] = ~df["estadio"].map(lambda v: dc.fold(v).upper()).isin(
            {e.upper() for e in mappings.ESTADIOS_CERRADOS})
        df["fob"] = df["fob_simi"]
        df["modo"] = df["modo"].fillna("Aéreo")
        df["etd_ok"] = df["etd_ok"].fillna(False).astype(bool)
        df = add_air_sla(df, q)
    if key == "planif":
        df["estado_instruccion"] = df["f_instruccion_raw"].map(estado_instruccion)
        df["f_instruccion"] = df["f_instruccion_raw"].map(lambda v: dc.parse_date_value(v)[0])
        df["f_instruccion"] = pd.to_datetime(df["f_instruccion"], errors="coerce")
        df["tipo_negocio"] = [tipo_negocio_planif(m, c) for m, c in zip(df["marca"], df["clase"])]
        # FOB del pipeline: siempre "Fob total Origen" (definición del área).
        df["fob"] = df["fob_origen"] if "fob_origen" in df else pd.Series(np.nan, index=df.index)
    if key in ("cotizaciones", "cot_sin_negociar"):
        def pod_country(v):
            f = dc.fold(v)
            return next((c for k, c in mappings.DESTINO_POR_POD if k in f), None) if f else None
        df["destino"] = df["pod"].map(pod_country)
        df["tipo_ctnr"] = df["tipo_ctnr"].map(
            lambda v: mappings.VALUE_ALIASES["tipo_ctnr"].get(dc.fold(v), v) if v else v)
        bad = df["flete"].notna() & (df["flete"] < 100)   # p. ej. "2,7" cargado en miles
        if bad.any():
            q.out_of_range["Valor Flete < USD 100"] = int(bad.sum())
            q.issue_rows[("rango", "Valor Flete < USD 100")] = df.loc[bad, "_fila"].astype(int).tolist()
        df = df[df["flete"] >= 100].copy()

    schema = SCHEMAS[key]
    df["fecha_ref"] = pd.to_datetime(df[schema.date_ref], errors="coerce")
    return df


# ---------------------------------------------------------------------------
def _is_filler(key: str, df: pd.DataFrame) -> pd.Series:
    """Filas que tienen ID pero ningún dato de negocio (reservas vacías, proyecciones)."""
    emb = df.get("embarque")
    non_op = emb.map(lambda v: dc.fold(v) in mappings.EMBARQUES_NO_OPERATIVOS) if emb is not None \
        else pd.Series(False, index=df.index)
    if key in ("reservas", "historicas", "aereos"):
        business = [c for c in ("empresa", "puerto", "forwarder", "etd") if c in df]
        no_data = df[business].isna().all(axis=1)
        if "m3" in df:
            no_data &= ~(df["m3"] > 0)
        if "estadio" in df:  # aéreos: con estadio cargado ya es una operación
            no_data &= df["estadio"].isna()
        return non_op | no_data
    return non_op


# Errores de fórmula de Sheets / Excel, en inglés y en español (#N/A, #N/D, #REF!, #¡REF!, #VALUE!, #¡VALOR!…).
_ERROR_CELDA = re.compile(r"^#(N/?A|N/D|[¡]?(REF|VALUE|VALOR|DIV/0|NUM|NULL|NULO|ERROR|SPILL|CALC)!?|[¿]?(NAME|NOMBRE)\??)$",
                          re.IGNORECASE)


def scan_error_cells(raw: pd.DataFrame, schema, q: DatasetQuality) -> None:
    """Cuenta celdas con error de fórmula por columna (solo filas con registro)."""
    rows = raw[raw[schema.id_column].notna()] if schema.id_column and schema.id_column in raw else raw
    if rows.empty:
        return
    display = {c.name: c.display for c in schema.columns}
    for col in rows.columns:
        s = rows[col]
        txt = s[s.map(lambda v: isinstance(v, str))].str.strip()
        bad = txt[txt.str.match(_ERROR_CELDA)]
        if bad.empty:
            continue
        valores = ", ".join(sorted(bad.str.upper().unique()))
        q.issue_rows[("error", display.get(col, col))] = [int(i) + FILA_OFFSET for i in bad.index]
        ids = (rows.loc[bad.index, schema.id_column].astype(str).head(5).tolist()
               if schema.id_column and schema.id_column in rows and col != schema.id_column else [])
        q.error_cells[display.get(col, col)] = (int(len(bad)), valores, ", ".join(ids))


def process_dataset(key: str, raw: pd.DataFrame, q: DatasetQuality) -> pd.DataFrame:
    schema = SCHEMAS[key]
    q.rows_raw = len(raw)
    try:
        scan_error_cells(raw, schema, q)
    except Exception:
        log.exception("Error buscando celdas con error en %s", key)
    df = type_columns(raw, schema, q)

    # Filas totalmente vacías (la planilla trae grillas de 1.000 filas).
    empty = df.isna().all(axis=1)
    if schema.id_column:
        empty = empty | df[schema.id_column].isna()
        try:
            ref = raw[schema.id_column].map(lambda v: isinstance(v, str) and bool(_ERROR_CELDA.match(v.strip())))
            con_datos = df.drop(columns=[schema.id_column]).notna().any(axis=1)
            for i in df.index[ref & con_datos]:
                q.ref_errores.append({"fila": int(i) + FILA_OFFSET, "valor": str(raw.at[i, schema.id_column]).strip(),
                                      **{c: df.at[i, c] for c in ("f_packeo_min", "etd", "eta", "responsable")
                                         if c in df}})
        except Exception:
            log.exception("Error buscando referencias con error en %s", key)
    q.rows_empty = int(empty.sum())
    df = df[~empty]

    filler = _is_filler(key, df)
    q.rows_filler = int(filler.sum())
    df = df[~filler]

    before = len(df)
    if key in ("reservas", "historicas", "aereos"):
        df = df.assign(_k=dc.id_key(df["embarque"])).drop_duplicates("_k").drop(columns="_k")
    else:
        df = df.drop_duplicates()
    q.duplicates = before - len(df)
    df["_fila"] = df.index + FILA_OFFSET   # fila de la planilla, para decir dónde corregir
    return df.reset_index(drop=True)


def quality_fields(key: str, df: pd.DataFrame, q: DatasetQuality) -> None:
    fields = KEY_FIELDS.get(key, {})
    present = [c for c in fields if c in df]
    for c in present:
        q.missing_key_fields[fields[c]] = int(df[c].isna().sum())
    q.rows_final = len(df)
    q.complete_rows = int(df[present].notna().all(axis=1).sum()) if present else len(df)


# ---------------------------------------------------------------------------
def build_bundle(source: SheetSource, datasets: dict[str, tuple[str, str]] | None = None) -> DataBundle:
    datasets = datasets or settings.DATASET_SOURCES
    errors: list[str] = []
    quality: dict[str, DatasetQuality] = {}
    frames: dict[str, pd.DataFrame] = {}
    sla = parse_sla_table([])
    modified: dict[str, dt.datetime | None] = {}

    by_book: dict[str, dict[str, str]] = {}
    for key, (book, tab) in datasets.items():
        by_book.setdefault(book, {})[key] = tab

    for book, keys in by_book.items():
        try:
            titles = source.tab_titles(book)
        except SourceError as exc:
            errors.append(str(exc))
            for key in keys:
                if key in SCHEMAS:
                    quality[key] = DatasetQuality(key, SCHEMAS[key].title, message=str(exc))
            continue
        except Exception as exc:
            log.exception("Error listando solapas de %s", book)
            msg = f"No se pudo leer la planilla '{book}' ({type(exc).__name__})."
            errors.append(msg)
            for key in keys:
                if key in SCHEMAS:
                    quality[key] = DatasetQuality(key, SCHEMAS[key].title, message=msg)
            continue

        modified[book] = source.last_modified(book)
        resolved: dict[str, str] = {}
        for key, wanted in keys.items():
            tab = find_tab(titles, wanted)
            if tab is None:
                msg = f"No se encontró la solapa '{wanted}' en la planilla."
                log.warning(msg)
                if key in SCHEMAS:
                    quality[key] = DatasetQuality(key, SCHEMAS[key].title, message=msg)
                else:
                    errors.append(msg)
                continue
            resolved[key] = tab

        try:
            headers = source.read_headers(book, [resolved[k] for k in resolved if k in SCHEMAS])
            request: dict[str, list[int] | None] = {}
            colmaps: dict[str, dict[str, int]] = {}
            for key, tab in resolved.items():
                if key not in SCHEMAS:
                    request[tab] = None  # Validaciones: se lee entera
                    continue
                schema = SCHEMAS[key]
                colmap, miss_req, miss_opt = resolve_columns(schema, headers.get(tab, []))
                q = DatasetQuality(key, schema.title, tab=tab,
                                   missing_required=miss_req, missing_optional=miss_opt)
                quality[key] = q
                if miss_opt:
                    log.warning("%s: faltan columnas opcionales %s", tab, miss_opt)
                if miss_req:
                    q.message = ("Faltan columnas obligatorias en la solapa "
                                 f"'{tab}': {', '.join(miss_req)}.")
                    log.error(q.message)
                    continue
                colmaps[key] = colmap
                request[tab] = sorted(set(colmap.values()))
            grids = source.read_tables(book, request)
        except SourceError as exc:
            errors.append(str(exc))
            continue
        except Exception as exc:
            log.exception("Error leyendo datos de %s", book)
            errors.append(f"Error leyendo la planilla '{book}' ({type(exc).__name__}).")
            continue

        for key, tab in resolved.items():
            if key == "validaciones":
                try:
                    sla = parse_sla_table(grids.get(tab, []))
                    if sla.empty:
                        errors.append("No se encontró la tabla de SLA por puerto en Validaciones; "
                                      "se usan los SLA por defecto.")
                except Exception:
                    log.exception("Error leyendo SLA")
                    errors.append("No se pudo leer la tabla de SLA; se usan los SLA por defecto.")
                continue
            if key not in colmaps:
                continue
            q = quality[key]
            try:
                raw = grid_to_frame(SCHEMAS[key], grids.get(tab, []), colmaps[key])
                frames[key] = process_dataset(key, raw, q)
            except Exception as exc:
                log.exception("Error procesando %s", key)
                q.message = f"No se pudo procesar la solapa '{tab}' ({type(exc).__name__})."

    # Unificar escrituras entre datasets (Hong Kong / HONG KONG, etc.).
    for fieldname in SHARED_CATEGORIES:
        series = [f[fieldname] for f in frames.values() if fieldname in f]
        if fieldname == "puerto" and not sla.empty:
            series.append(sla["puerto"])
        canon = dc.canonical_spelling(series)
        for f in frames.values():
            if fieldname in f:
                f[fieldname] = dc.unify(f[fieldname], canon)
        if fieldname == "puerto" and not sla.empty:
            sla["puerto"] = dc.unify(sla["puerto"], canon)

    attach_fin_produccion(frames)

    for key in list(frames):
        q = quality[key]
        try:
            frames[key] = finish_dataset(key, frames[key], sla, q)
            quality_fields(key, frames[key], q)
            q.available = True
        except Exception as exc:
            log.exception("Error derivando %s", key)
            q.message = f"No se pudieron calcular los indicadores de '{q.title}' ({type(exc).__name__})."
            frames.pop(key)

    loaded_at = dt.datetime.now(ZoneInfo(settings.TIMEZONE))
    log.info("Carga completa: %s", {k: len(v) for k, v in frames.items()})
    return DataBundle(datasets=frames, sla_puertos=sla, quality=quality, errors=errors,
                      loaded_at=loaded_at, source_name=source.name, source_modified=modified)


# ---------------------------------------------------------------------------
# Integración con Streamlit
# ---------------------------------------------------------------------------
def make_source() -> SheetSource:
    """Elige la fuente de datos:

    1. [gcp_service_account] en secrets → API de Google (planillas privadas).
    2. [local_files] o variables DASHBOARD_LOCAL_* → .xlsx local (desarrollo).
    3. Si no hay nada configurado → exportación CSV pública (como la app anterior).
    """
    import os

    from services.google_sheets import GoogleSheetsSource, LocalExcelSource, PublicCsvSource

    try:
        secrets = st.secrets
        has_gcp = "gcp_service_account" in secrets
    except Exception:
        secrets, has_gcp = {}, False

    books = dict(settings.SPREADSHEETS)
    if "sheets" in secrets:
        books.update({k: v for k, v in secrets["sheets"].items() if isinstance(v, str)})

    if has_gcp:
        return GoogleSheetsSource(secrets["gcp_service_account"], books)

    local = {}
    if "local_files" in secrets:
        local = dict(secrets["local_files"])
    for book in books:
        env = os.environ.get(f"DASHBOARD_LOCAL_{book.upper()}")
        if env:
            local[book] = env
    if local:
        return LocalExcelSource(local)
    return PublicCsvSource(books, settings.SHEET_GIDS)


def _code_version() -> str:
    """Huella del código que arma los datos.

    Se usa como parte de la clave de caché: cuando se publica una versión nueva
    que cambia columnas o cálculos, el caché anterior no se reutiliza.
    """
    import hashlib
    from pathlib import Path

    root = Path(__file__).resolve().parent.parent
    files = ["services/data_loader.py", "services/google_sheets.py", "config/schema.py",
             "config/mappings.py", "config/settings.py", "utils/data_cleaning.py", "utils/calculations.py"]
    h = hashlib.sha1()
    for f in files:
        try:
            h.update((root / f).read_bytes())
        except OSError:
            pass
    return h.hexdigest()[:12]


@st.cache_resource(ttl=settings.CACHE_TTL_SECONDS, show_spinner="Cargando datos de la planilla…")
def _load_bundle(code_version: str = "") -> DataBundle:
    """Una sola carga compartida por todos los usuarios hasta que vence el TTL.

    Se usa cache_resource (y no cache_data) para no copiar los DataFrames en
    cada interacción: las vistas nunca modifican estos objetos, solo filtran
    (apply_filters siempre devuelve una copia).
    """
    bundle = build_bundle(make_source())
    bundle.code_version = code_version
    if not bundle.datasets:
        # Una excepción no queda cacheada: se reintenta en la próxima interacción.
        raise SourceError(" ".join(bundle.errors) or "No se pudo cargar ningún dataset.")
    return bundle


@st.cache_resource(show_spinner=False)
def _last_good() -> dict:
    return {}


def get_data() -> DataBundle:
    """Datos normalizados. Si la fuente falla, devuelve la última carga válida."""
    store = _last_good()
    try:
        bundle = _load_bundle(_code_version())
        store["bundle"] = bundle
        return bundle
    except Exception as exc:
        msg = str(exc) if isinstance(exc, SourceError) else f"Error inesperado al cargar los datos ({type(exc).__name__})."
        log.exception("Fallo de carga")
        prev = store.get("bundle")
        if prev is not None and getattr(prev, "code_version", None) == _code_version():
            import copy

            stale = copy.copy(prev)
            stale.stale = True
            stale.errors = [msg] + [e for e in prev.errors if e != msg]
            return stale
        raise SourceError(msg) from exc


def clear_cache() -> None:
    """Botón "Actualizar datos": fuerza una nueva lectura de la fuente."""
    _load_bundle.clear()
