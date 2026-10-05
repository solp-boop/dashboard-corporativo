"""Cálculos de negocio reutilizables (sin Streamlit).

Regla general para tiempos: la MEDIANA es el indicador principal; P25 y P75
dan el rango típico. El promedio solo se usa como dato secundario.
"""
from __future__ import annotations

from dataclasses import dataclass

import numpy as np
import pandas as pd

from config import settings

SEMAFORO_OK = "Dentro de SLA"
SEMAFORO_WARN = "Atención"
SEMAFORO_BAD = "Fuera de SLA"
SEMAFORO_ORDER = [SEMAFORO_OK, SEMAFORO_WARN, SEMAFORO_BAD]


@dataclass
class Stat:
    n: int            # registros con dato válido
    total: int        # registros considerados
    median: float = np.nan
    p25: float = np.nan
    p75: float = np.nan
    mean: float = np.nan

    @property
    def coverage(self) -> float:
        return self.n / self.total if self.total else 0.0

    @property
    def enough(self) -> bool:
        return self.n >= settings.MIN_SAMPLE

    @property
    def low_coverage(self) -> bool:
        return self.total > 0 and self.coverage < settings.MIN_COVERAGE


def describe(values: pd.Series, total: int | None = None) -> Stat:
    s = pd.to_numeric(values, errors="coerce")
    total = int(len(s)) if total is None else int(total)
    v = s.dropna()
    if v.empty:
        return Stat(n=0, total=total)
    return Stat(
        n=int(v.size), total=total,
        median=float(v.median()), p25=float(v.quantile(0.25)),
        p75=float(v.quantile(0.75)), mean=float(v.mean()),
    )


def days_between(end: pd.Series, start: pd.Series, metric: str) -> tuple[pd.Series, int]:
    """Diferencia en días; valores fuera del rango válido -> NaN (y se cuentan)."""
    d = (pd.to_datetime(end) - pd.to_datetime(start)).dt.days.astype(float)
    lo, hi = settings.DURATION_RANGES.get(metric, (-10_000, 10_000))
    bad = d.notna() & ((d < lo) | (d > hi))
    return d.mask(bad), int(bad.sum())


def sla_mono(etd: pd.Series) -> pd.Series:
    """SLA de consolidación monoproveedor según la fecha de ETD (vigencias en settings).

    Sin ETD se usa el vigente hoy.
    """
    fechas = pd.to_datetime(pd.Series(etd))
    out = pd.Series(float(settings.SLA_MONO_VIGENCIAS[-1][1]), index=fechas.index)
    for desde, dias in settings.SLA_MONO_VIGENCIAS:
        out = out.mask(fechas >= pd.Timestamp(desde), float(dias))
    return out


def sla_mono_txt() -> str:
    """'12 d desde 01/10/2026 (antes 10 d desde 01/03/2026, 15 d)'."""
    v = settings.SLA_MONO_VIGENCIAS
    actual = f"{v[-1][1]} d desde {pd.Timestamp(v[-1][0]):%d/%m/%Y}"
    previas = [f"{d} d desde {pd.Timestamp(f):%d/%m/%Y}" if i else f"{d} d"
               for i, (f, d) in enumerate(v[:-1])][::-1]
    return actual + (f" (antes {', '.join(previas)})" if previas else "")


def semaforo(values: pd.Series, sla: pd.Series | float) -> pd.Series:
    v = pd.to_numeric(values, errors="coerce")
    s = sla if isinstance(sla, pd.Series) else pd.Series(sla, index=v.index)
    s = pd.to_numeric(s, errors="coerce")
    out = pd.Series(pd.NA, index=v.index, dtype=object)
    ok = v <= s
    warn = (v > s) & (v <= s * (1 + settings.SLA_WARNING_TOLERANCE))
    bad = v > s * (1 + settings.SLA_WARNING_TOLERANCE)
    out[ok] = SEMAFORO_OK
    out[warn] = SEMAFORO_WARN
    out[bad] = SEMAFORO_BAD
    return out


def pct_true(mask: pd.Series) -> tuple[float, int]:
    """% de True sobre los no nulos. Devuelve (pct, n)."""
    m = mask.dropna()
    if m.empty:
        return np.nan, 0
    return float(m.astype(bool).mean()), int(m.size)


def cumplimiento(values: pd.Series, sla: pd.Series) -> tuple[float, int]:
    v = pd.to_numeric(values, errors="coerce")
    s = pd.to_numeric(sla, errors="coerce")
    valid = v.notna() & s.notna()
    if not valid.any():
        return np.nan, 0
    return float((v[valid] <= s[valid]).mean()), int(valid.sum())


def month_start(dates: pd.Series) -> pd.Series:
    return pd.to_datetime(dates).dt.to_period("M").dt.to_timestamp()


def week_start(dates: pd.Series) -> pd.Series:
    d = pd.to_datetime(dates)
    return (d - pd.to_timedelta(d.dt.weekday, unit="D")).dt.normalize()


def pct_change(curr: float, prev: float) -> float:
    if prev is None or pd.isna(prev) or prev == 0 or pd.isna(curr):
        return np.nan
    return (curr - prev) / abs(prev)


def median_by(df: pd.DataFrame, by: str | list[str], value: str, min_n: int = 1) -> pd.DataFrame:
    """Mediana, P25, P75 y n por grupo."""
    g = df.dropna(subset=[value]).groupby(by, observed=True)[value]
    out = g.agg(n="count", mediana="median",
                p25=lambda s: s.quantile(0.25), p75=lambda s: s.quantile(0.75)).reset_index()
    return out[out["n"] >= min_n]


def last_closed_months(dates: pd.Series, today: pd.Timestamp | None = None) -> tuple[pd.Timestamp, pd.Timestamp]:
    """(mes cerrado más reciente, mes anterior) como inicio de mes."""
    today = pd.Timestamp.today().normalize() if today is None else today
    this_month = today.to_period("M").to_timestamp()
    last = this_month - pd.offsets.MonthBegin(1)
    prev = last - pd.offsets.MonthBegin(1)
    return last, prev
