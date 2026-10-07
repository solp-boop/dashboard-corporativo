"""Limpieza y conversión de tipos.

Todas las funciones son tolerantes: nunca lanzan excepción por un valor mal
cargado. Lo que no se puede convertir queda vacío (NaN/NaT) y se cuenta para
el reporte de Calidad de datos.

Para que sea rápido, cada columna se convierte sobre sus valores únicos y
después se mapea (las planillas tienen muchos valores repetidos).
"""
from __future__ import annotations

import datetime as dt
import math
import re
import unicodedata
from dataclasses import dataclass

import numpy as np
import pandas as pd

from config import settings

_WS = re.compile(r"\s+")
_NON_ALNUM = re.compile(r"[^0-9a-z]+")
_DMY = re.compile(
    r"^(\d{1,2})[/\-.](\d{1,2})[/\-.](\d{2}|\d{4})(?:[ T]+(\d{1,2}):(\d{2})(?::(\d{2}))?)?$"
)
_ISO = re.compile(r"^(\d{4})-(\d{1,2})-(\d{1,2})(?:[ T].*)?$")
_JS = re.compile(r"^[A-Za-z]{3},?\s+([A-Za-z]{3})\s+(\d{1,2}),?\s+(\d{4})")
_MONTHS_EN = {m: i for i, m in enumerate(
    ["jan", "feb", "mar", "apr", "may", "jun", "jul", "aug", "sep", "oct", "nov", "dec"], start=1)}
_THOUSANDS_DOT = re.compile(r"^-?\d{1,3}(\.\d{3})+$")
_CURRENCY = re.compile(r"(?i)u\$s|us\$|usd|ars|\$|€")
_EXCEL_EPOCH = dt.datetime(1899, 12, 30)


# ---------------------------------------------------------------------------
# Texto
# ---------------------------------------------------------------------------
def fold(value) -> str:
    """Clave de comparación: minúsculas, sin acentos, sin signos, un espacio."""
    if value is None or (isinstance(value, float) and math.isnan(value)):
        return ""
    s = unicodedata.normalize("NFKD", str(value))
    s = "".join(ch for ch in s if not unicodedata.combining(ch)).lower()
    return _NON_ALNUM.sub(" ", s).strip()


def _is_blank(value) -> bool:
    if value is None:
        return True
    if isinstance(value, float) and math.isnan(value):
        return True
    if value is pd.NaT:
        return True
    try:
        if pd.isna(value):
            return True
    except (TypeError, ValueError):
        pass
    return False


def is_null_token(value) -> bool:
    if _is_blank(value):
        return True
    s = str(value).strip().lower()
    return s in settings.NULL_TOKENS


def clean_text_value(value):
    if is_null_token(value):
        return None
    if isinstance(value, float) and value.is_integer():
        value = int(value)
    s = _WS.sub(" ", str(value)).strip()
    return s or None


def clean_text(series: pd.Series) -> pd.Series:
    uniques = pd.unique(series.astype(object))
    mapping = {u: clean_text_value(u) for u in uniques}
    return series.astype(object).map(mapping).astype(object)


# ---------------------------------------------------------------------------
# Fechas
# ---------------------------------------------------------------------------
@dataclass
class ParseStats:
    invalid: int = 0        # texto no vacío que no es fecha/número
    out_of_range: int = 0   # fecha/número detectado pero fuera de rango
    invalid_mask: pd.Series | None = None   # qué filas (para acotar los controles de calidad)
    range_mask: pd.Series | None = None

    def __add__(self, other: "ParseStats") -> "ParseStats":
        return ParseStats(self.invalid + other.invalid, self.out_of_range + other.out_of_range)


def _date_bounds() -> tuple[pd.Timestamp, pd.Timestamp]:
    lo = pd.Timestamp(settings.DATE_MIN)
    hi = pd.Timestamp(dt.date.today() + dt.timedelta(days=settings.DATE_MAX_DAYS_AHEAD))
    return lo, hi


def _to_ts(y: int, m: int, d: int):
    try:
        return pd.Timestamp(year=y, month=m, day=d)
    except (ValueError, OverflowError):
        return None


def parse_date_value(value):
    """Devuelve (Timestamp | None, estado) con estado en {'ok','empty','invalid'}."""
    if is_null_token(value):
        return None, "empty"
    if isinstance(value, bool):
        return None, "invalid"
    if isinstance(value, (pd.Timestamp, dt.datetime)):
        return pd.Timestamp(value).normalize(), "ok"
    if isinstance(value, dt.date):
        return pd.Timestamp(value), "ok"
    if isinstance(value, (int, float, np.integer, np.floating)):
        v = float(value)
        if 20000 <= v <= 80000:  # número de serie de Sheets/Excel
            return pd.Timestamp(_EXCEL_EPOCH + dt.timedelta(days=int(v))), "ok"
        return None, "invalid"

    s = str(value).strip()
    s = re.sub(r"/{2,}", "/", s)
    m = _DMY.match(s)
    if m:
        d, mo, y = int(m.group(1)), int(m.group(2)), int(m.group(3))
        if y < 100:
            y += 2000
        ts = _to_ts(y, mo, d)
        return (ts, "ok") if ts is not None else (None, "invalid")
    m = _ISO.match(s)
    if m:
        ts = _to_ts(int(m.group(1)), int(m.group(2)), int(m.group(3)))
        return (ts, "ok") if ts is not None else (None, "invalid")
    m = _JS.match(s)
    if m:
        mo = _MONTHS_EN.get(m.group(1).lower())
        ts = _to_ts(int(m.group(3)), mo, int(m.group(2))) if mo else None
        return (ts, "ok") if ts is not None else (None, "invalid")
    try:
        v = float(s.replace(",", "."))
        return parse_date_value(v)
    except ValueError:
        return None, "invalid"


def parse_dates(series: pd.Series) -> tuple[pd.Series, ParseStats]:
    lo, hi = _date_bounds()
    obj = series.astype(object)
    mapping, state = {}, {}
    for u in pd.unique(obj):
        key = u if not _is_blank(u) else None
        ts, st_ = parse_date_value(u)
        if ts is not None and not (lo <= ts <= hi):
            ts, st_ = None, "range"
        mapping[key] = ts
        state[key] = st_
    keys = obj.map(lambda v: None if _is_blank(v) else v)
    out = pd.to_datetime(keys.map(mapping), errors="coerce")
    states = keys.map(state)
    stats = ParseStats(invalid=int((states == "invalid").sum()),
                       out_of_range=int((states == "range").sum()),
                       invalid_mask=states == "invalid", range_mask=states == "range")
    return out, stats


# ---------------------------------------------------------------------------
# Números
# ---------------------------------------------------------------------------
def parse_number_value(value):
    """Devuelve (float | nan, estado)."""
    if is_null_token(value):
        return np.nan, "empty"
    if isinstance(value, bool):
        return np.nan, "invalid"
    if isinstance(value, (int, float, np.integer, np.floating)):
        v = float(value)
        return (v, "ok") if math.isfinite(v) else (np.nan, "empty")
    if isinstance(value, (pd.Timestamp, dt.date)):
        return np.nan, "invalid"

    s = str(value).strip().replace("\xa0", "").replace(" ", "")
    s = _CURRENCY.sub("", s)
    neg = False
    if s.startswith("(") and s.endswith(")"):
        neg, s = True, s[1:-1]
    pct = s.endswith("%")
    if pct:
        s = s[:-1]
    if "," in s and "." in s:
        if s.rfind(",") > s.rfind("."):
            s = s.replace(".", "").replace(",", ".")
        else:
            s = s.replace(",", "")
    elif "," in s:
        s = s.replace(",", "") if s.count(",") > 1 else s.replace(",", ".")
    elif "." in s and _THOUSANDS_DOT.match(s):
        s = s.replace(".", "")
    try:
        v = float(s)
    except ValueError:
        return np.nan, "invalid"
    if not math.isfinite(v):
        return np.nan, "invalid"
    if neg:
        v = -v
    if pct:
        v = v / 100
    return v, "ok"


def parse_numbers(series: pd.Series) -> tuple[pd.Series, ParseStats]:
    obj = series.astype(object)
    mapping, state = {}, {}
    for u in pd.unique(obj):
        key = u if not _is_blank(u) else None
        v, st_ = parse_number_value(u)
        mapping[key], state[key] = v, st_
    keys = obj.map(lambda v: None if _is_blank(v) else v)
    out = pd.to_numeric(keys.map(mapping), errors="coerce").astype(float)
    states = keys.map(state)
    stats = ParseStats(invalid=int((states == "invalid").sum()), invalid_mask=states == "invalid")
    return out, stats


# ---------------------------------------------------------------------------
# Flags
# ---------------------------------------------------------------------------
_TRUE = {"si", "ok", "yes", "true", "x", "1", "verdadero", "listo", "confirmado"}
_FALSE = {"no", "false", "0", "falso", "pendiente"}


def parse_flag_value(value):
    if is_null_token(value):
        return None
    f = fold(value)
    if f in _TRUE:
        return True
    if f in _FALSE:
        return False
    return None


def parse_flags(series: pd.Series) -> pd.Series:
    obj = series.astype(object)
    mapping = {u: parse_flag_value(u) for u in pd.unique(obj)}
    return obj.map(mapping).astype("boolean")


# ---------------------------------------------------------------------------
# Categorías
# ---------------------------------------------------------------------------
def apply_aliases(series: pd.Series, aliases: dict[str, str] | None) -> pd.Series:
    """Limpia texto y reemplaza por alias (comparando claves plegadas)."""
    cleaned = clean_text(series)
    if not aliases:
        return cleaned
    folded_aliases = {fold(k): v for k, v in aliases.items()}
    mapping = {}
    for u in pd.unique(cleaned):
        if u is None:
            mapping[u] = None
            continue
        mapping[u] = folded_aliases.get(fold(u), u)
    return cleaned.map(mapping).astype(object)


def canonical_spelling(values: list[pd.Series]) -> dict[str, str]:
    """Para cada clave plegada, la escritura más frecuente entre todas las series."""
    parts = [v.dropna() for v in values if v is not None]
    if not parts:
        return {}
    combined = pd.concat(parts, ignore_index=True)
    if combined.empty:
        return {}
    counts = combined.value_counts()
    best: dict[str, tuple[int, str]] = {}
    for spelling, n in counts.items():
        k = fold(spelling)
        if not k:
            continue
        # Desempate: la escritura con más mayúsculas "de título" gana sobre TODO MAYÚSCULA.
        score = (int(n), sum(1 for ch in spelling if ch.islower()))
        if k not in best or score > best[k][0]:
            best[k] = (score, spelling)
    return {k: v[1] for k, v in best.items()}


def unify(series: pd.Series, canon: dict[str, str]) -> pd.Series:
    mapping = {u: (canon.get(fold(u), u) if u is not None else None) for u in pd.unique(series.astype(object))}
    return series.astype(object).map(mapping).astype(object)


def id_key(series: pd.Series) -> pd.Series:
    """Clave de identificador para deduplicar y buscar ("FCL  2552 " -> "fcl 2552")."""
    return series.astype(object).map(lambda v: fold(v) if v is not None else "")
