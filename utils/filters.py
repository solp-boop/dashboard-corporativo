"""Filtros: un único estado y una única función para aplicarlos.

- FilterState guarda el período y las selecciones.
- apply_filters(df, filters) es la ÚNICA función que filtra datos en todo el
  dashboard. KPIs, gráficos, tablas y exportaciones usan su resultado.
- dependent_options() calcula las opciones de un filtro según los filtros
  anteriores de la cascada (Empresa → Destino → Modo → Puerto → Forwarder…).
"""
from __future__ import annotations

import datetime as dt
from dataclasses import dataclass, field

import pandas as pd

# Orden de la cascada: cada filtro depende de los anteriores.
FILTER_FIELDS: list[tuple[str, str]] = [
    ("empresa", "Empresa"),
    ("destino", "Destino"),
    ("modo", "Modo de transporte"),
    ("puerto", "Puerto de origen"),
    ("forwarder", "Forwarder"),
    ("estructura", "Estructura de carga"),
    ("responsable", "Responsable"),
]
FIELD_LABELS = dict(FILTER_FIELDS)
_NOT_IN_DATASET = "__no_aplica__"


@dataclass
class FilterState:
    start: dt.date | None = None
    end: dt.date | None = None
    selections: dict[str, list[str]] = field(default_factory=dict)

    @property
    def active_fields(self) -> list[str]:
        return [f for f, _ in FILTER_FIELDS if self.selections.get(f)]

    @property
    def has_period(self) -> bool:
        return self.start is not None or self.end is not None

    def without_period(self) -> "FilterState":
        return FilterState(None, None, dict(self.selections))

    def describe(self) -> str:
        parts = []
        if self.has_period:
            a = self.start.strftime("%d/%m/%Y") if self.start else "…"
            b = self.end.strftime("%d/%m/%Y") if self.end else "…"
            parts.append(f"Período {a} – {b}")
        for f in self.active_fields:
            vals = self.selections[f]
            parts.append(f"{FIELD_LABELS[f]}: {', '.join(vals[:3])}{'…' if len(vals) > 3 else ''}")
        return " · ".join(parts) if parts else "Sin filtros"


def apply_filters(df: pd.DataFrame, filters: FilterState, date_col: str = "fecha_ref",
                  use_period: bool = True) -> pd.DataFrame:
    """Aplica período + selecciones. Siempre devuelve una copia.

    - Si el dataset no tiene la columna de un filtro, ese filtro se ignora
      (ver not_applicable()).
    - Con período activo, los registros sin fecha quedan afuera.
    """
    if df is None:
        return pd.DataFrame()
    mask = pd.Series(True, index=df.index)
    if use_period and filters.has_period and date_col in df:
        d = pd.to_datetime(df[date_col], errors="coerce")
        if filters.start:
            mask &= d >= pd.Timestamp(filters.start)
        if filters.end:
            mask &= d <= pd.Timestamp(filters.end)
    for f in filters.active_fields:
        if f in df:
            mask &= df[f].isin(filters.selections[f])
    return df.loc[mask].copy()


def not_applicable(df: pd.DataFrame, filters: FilterState) -> list[str]:
    """Filtros activos que no aplican a este dataset (etiquetas)."""
    return [FIELD_LABELS[f] for f in filters.active_fields if f not in df]


def undated_count(df: pd.DataFrame, filters: FilterState, date_col: str = "fecha_ref") -> int:
    """Registros que el filtro de período excluye por no tener fecha."""
    if not filters.has_period or df is None or date_col not in df:
        return 0
    sub = apply_filters(df, filters.without_period(), date_col)
    return int(sub[date_col].isna().sum())


def dependent_options(dims: pd.DataFrame, filters: FilterState, field_name: str) -> list[str]:
    """Opciones compatibles con las selecciones de los filtros ANTERIORES en la cascada."""
    if dims is None or dims.empty or field_name not in dims:
        return []
    order = [f for f, _ in FILTER_FIELDS]
    upstream = order[: order.index(field_name)]
    mask = pd.Series(True, index=dims.index)
    for f in upstream:
        sel = filters.selections.get(f)
        if sel and f in dims:
            # Filas de datasets que no tienen ese campo no restringen la cascada.
            mask &= dims[f].isin(sel) | (dims[f] == _NOT_IN_DATASET)
    vals = dims.loc[mask, field_name].dropna().astype(str)
    vals = vals[vals != _NOT_IN_DATASET]
    return sorted(vals.unique().tolist(), key=lambda s: s.lower())


def build_dimensions(datasets: dict[str, pd.DataFrame], filters: FilterState | None = None) -> pd.DataFrame:
    """Tabla con los campos de filtro de todos los datasets (para las opciones)."""
    cols = [f for f, _ in FILTER_FIELDS]
    parts = []
    for df in datasets.values():
        if df is None or df.empty:
            continue
        sub = df[[c for c in cols + ["fecha_ref"] if c in df]]
        if filters is not None and filters.has_period:
            sub = apply_filters(sub, FilterState(filters.start, filters.end, {}))
        sub = sub.reindex(columns=cols)
        for c in cols:
            if c not in df:
                sub[c] = _NOT_IN_DATASET
        parts.append(sub)
    if not parts:
        return pd.DataFrame(columns=cols)
    return pd.concat(parts, ignore_index=True).drop_duplicates()
