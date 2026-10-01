"""Utilidades compartidas por las vistas."""
from __future__ import annotations

import pandas as pd

from components.filters import current_filters
from services.data_loader import DataBundle, get_data
from config.mappings import ESTADIOS_CERRADOS, MODOS_MARITIMOS
from utils.data_cleaning import fold
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


GRUPOS_MODO = ["Marítimo", "Aéreo", "Camión"]


def en_curso(bundle: DataBundle, filters: FilterState) -> tuple[pd.DataFrame, dict]:
    """Embarques en curso = definición única para Resumen y Embarques en curso.

    - Marítimos y camión: solapa Reservas, filas con "Responsable de la carga".
      Los embarques AIR de Reservas se excluyen (se toman de Seguimiento Aéreos).
    - Aéreos: solapa SEGUIMIENTO AEREOS, todo lo que no está ENTREGADO.
    - Se aplican los filtros de la barra lateral, salvo el período: un embarque
      en curso se muestra aunque su ETD esté fuera del rango o vacía.

    Devuelve (DataFrame, info) con info = conteos de lo excluido.
    """
    parts, info = [], {"sin_responsable": 0, "air_en_reservas": 0, "aereos_entregados": 0}
    res = bundle.get("reservas")
    if res is not None and not res.empty:
        is_air = res["embarque"].map(lambda v: fold(v).startswith("air"))
        has_resp = res["responsable"].notna()
        info["air_en_reservas"] = int(is_air.sum())
        info["sin_responsable"] = int((~has_resp & ~is_air).sum())
        r = res[has_resp & ~is_air].copy()
        r["fuente"] = "Reservas"
        parts.append(r)
    aer = bundle.get("aereos")
    if aer is not None and not aer.empty:
        cerrado = aer["estadio"].map(lambda v: fold(v).upper() in {e.upper() for e in ESTADIOS_CERRADOS})
        info["aereos_entregados"] = int(cerrado.sum())
        a = aer[~cerrado].copy()
        a["fuente"] = "Seguimiento Aéreos"
        parts.append(a)
    if not parts:
        return pd.DataFrame(), info
    df = pd.concat(parts, ignore_index=True, sort=False)

    def grupo(row) -> str:
        if row["fuente"] == "Seguimiento Aéreos" or row["modo"] in ("Aéreo", "Courier"):
            return "Aéreo"
        if row["modo"] in MODOS_MARITIMOS:
            return "Marítimo"
        if row["modo"] == "Terrestre":
            return "Camión"
        return "Marítimo" if str(row["embarque"]).upper().startswith(("FCL", "LCL")) else "Otro"

    df["grupo_modo"] = df.apply(grupo, axis=1)
    df["etd_ok"] = df["etd_ok"].fillna(False).astype(bool)
    return apply_filters(df, filters, use_period=False), info


def kpis_en_curso(df: pd.DataFrame, info: dict) -> None:
    """Las dos filas de KPIs de operación en curso (mismas cifras en Resumen y Embarques)."""
    import numpy as np
    import streamlit as st

    from components.kpi_cards import KPI, kpi_row
    from config import settings

    n = len(df)
    t = today()
    week = df["etd"].between(t, t + pd.Timedelta(days=settings.ALERT_HORIZON_DAYS))
    ok_n = int(df["etd_ok"].sum())
    mar = df[df["grupo_modo"] == "Marítimo"]

    def share(g: str) -> KPI:
        sub = df[df["grupo_modo"] == g]
        pct = len(sub) / n if n else np.nan
        extra = (f" · <b>{fmt.fmt_int(sub['contenedores'].sum())}</b> contenedores" if g == "Marítimo" else "")
        return KPI(g, fmt.fmt_pct(pct), sub=f"<b>{fmt.fmt_int(len(sub))}</b> embarques{extra}")

    kpi_row([
        KPI("Embarques en curso", fmt.fmt_int(n),
            sub="Reservas con responsable + aéreos no entregados"),
        share("Marítimo"), share("Aéreo"), share("Camión"),
    ])
    kpi_row([
        KPI("Contenedores (marítimo)", fmt.fmt_int(mar["contenedores"].sum()),
            sub=f"<b>{fmt.fmt_int(len(mar))}</b> embarques marítimos"),
        KPI("Volumen en proceso", fmt.fmt_int(df["m3"].sum()), unit="m³",
            sub=f"Marítimo {fmt.fmt_int(mar['m3'].sum())} · aéreo "
                f"{fmt.fmt_num(df.loc[df['grupo_modo'] == 'Aéreo', 'm3'].sum(), 0)}"),
        KPI("FOB en proceso", fmt.fmt_usd(df["fob"].sum())),
        KPI("ETD confirmado", fmt.fmt_pct(ok_n / n if n else np.nan),
            sub=f"<b>{fmt.fmt_int(ok_n)}</b> OK · <b>{fmt.fmt_int(n - ok_n)}</b> pendientes"),
        KPI(f"Zarpan en {settings.ALERT_HORIZON_DAYS} días", fmt.fmt_int(week.sum()), unit="emb.",
            sub=f"<b>{fmt.fmt_int(df.loc[week, 'm3'].sum())} m³</b> · "
                f"{fmt.fmt_int(df.loc[week & (df['grupo_modo'] == 'Marítimo'), 'contenedores'].sum())} cont."),
    ])
    notas = []
    if info.get("sin_responsable"):
        notas.append(f"{info['sin_responsable']} reservas sin «Responsable de la carga» no se cuentan")
    if info.get("air_en_reservas"):
        notas.append(f"los {info['air_en_reservas']} AIR de Reservas se toman de Seguimiento Aéreos")
    notas.append("el filtro de período no se aplica a lo que está en curso")
    st.caption("Nota: " + "; ".join(notas) + ".")
