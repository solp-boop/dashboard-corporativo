"""Utilidades compartidas por las vistas."""
from __future__ import annotations

import pandas as pd

from components.filters import current_filters
from services.data_loader import DataBundle, get_data
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


def stat_sub(stat, unit: str = "d") -> str:
    """'P25–P75: 15–31 d · n=120'."""
    if not stat.n:
        return "Sin datos suficientes"
    return (f"P25–P75: <b>{fmt.fmt_int(stat.p25)}–{fmt.fmt_int(stat.p75)} {unit}</b> · "
            f"n={fmt.fmt_int(stat.n)}")
