"""Formato de números, fechas y unidades (convención es-AR)."""
from __future__ import annotations

import datetime as dt
import math

import pandas as pd

NA = "—"


def _isnan(v) -> bool:
    try:
        return v is None or pd.isna(v) or (isinstance(v, float) and math.isnan(v))
    except (TypeError, ValueError):
        return False


def _es(num_str: str) -> str:
    """'1,234.5' -> '1.234,5'."""
    return num_str.replace(",", "§").replace(".", ",").replace("§", ".")


def fmt_int(v) -> str:
    return NA if _isnan(v) else _es(f"{round(float(v)):,.0f}")


def fmt_num(v, decimals: int = 1) -> str:
    if _isnan(v):
        return NA
    v = float(v)
    if decimals and v == round(v):
        decimals = 0
    return _es(f"{v:,.{decimals}f}")


def fmt_usd(v, compact: bool = True) -> str:
    """USD 18,2 M · USD 812 K · USD 950."""
    if _isnan(v):
        return NA
    v = float(v)
    a = abs(v)
    if compact and a >= 1_000_000:
        return f"USD {fmt_num(v / 1_000_000, 1)} M"
    if compact and a >= 10_000:
        return f"USD {fmt_num(v / 1_000, 0)} K"
    return f"USD {fmt_int(v)}"


def fmt_pct(v, decimals: int = 0, signed: bool = False) -> str:
    if _isnan(v):
        return NA
    s = _es(f"{float(v) * 100:,.{decimals}f}")
    if signed and float(v) > 0:
        s = "+" + s
    return f"{s} %"


def fmt_days(v) -> str:
    return NA if _isnan(v) else f"{fmt_int(v)} d"


def fmt_m3(v) -> str:
    return NA if _isnan(v) else f"{fmt_int(v)} m³"


def fmt_date(v) -> str:
    if _isnan(v):
        return NA
    return pd.Timestamp(v).strftime("%d/%m/%Y")


def fmt_datetime(v: dt.datetime | None) -> str:
    if v is None:
        return NA
    return v.strftime("%d/%m/%Y %H:%M")


MESES = ["ene", "feb", "mar", "abr", "may", "jun", "jul", "ago", "sep", "oct", "nov", "dic"]
MESES_LARGOS = ["Enero", "Febrero", "Marzo", "Abril", "Mayo", "Junio", "Julio", "Agosto",
                "Septiembre", "Octubre", "Noviembre", "Diciembre"]


def fmt_month(v, long: bool = False) -> str:
    if _isnan(v):
        return NA
    t = pd.Timestamp(v)
    return f"{MESES_LARGOS[t.month - 1]} {t.year}" if long else f"{MESES[t.month - 1]} {t.strftime('%y')}"


def plural(n: int, singular: str, plural_: str | None = None) -> str:
    return f"{fmt_int(n)} {singular if n == 1 else (plural_ or singular + 's')}"
