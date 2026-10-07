"""SLA marítimo: series mensuales y tabla de cierre (año / mes cerrado / mes en curso).

Sin Streamlit, para poder testearlo. Lo usan Resumen y Lead times y SLA.
"""
from __future__ import annotations

from dataclasses import dataclass

import numpy as np
import pandas as pd

from config import settings
from config.mappings import MODOS_MARITIMOS
from utils import calculations as calc
from utils import data_cleaning as dc

INDICADORES = [
    # clave, etiqueta, columna de valor, columna de SLA, tipo
    ("cumplimiento", "Cumplimiento SLA consolidación", "dias_consolidacion", "sla_consolidacion", "pct"),
    ("mono", "Consolidación monoproveedor", "dias_consolidacion", "sla_consolidacion", "days"),
    ("cons", "Consolidación consolidado", "dias_consolidacion", "sla_consolidacion", "days"),
    ("total", "Fin de producción → ETA", "dias_total", "sla_total", "days"),
]


def zarpados(hist: pd.DataFrame, today: pd.Timestamp) -> pd.DataFrame:
    """Embarques marítimos ya zarpados (Reservas Históricas)."""
    return hist[hist["modo"].isin(MODOS_MARITIMOS) & (hist["etd"] <= today)]


def monthly_compliance(d: pd.DataFrame) -> pd.DataFrame:
    """% de embarques dentro del SLA de consolidación por mes de ETD."""
    x = d.dropna(subset=["dias_consolidacion", "etd"]).copy()
    if x.empty:
        return pd.DataFrame(columns=["mes", "pct", "n"])
    x["mes"] = calc.month_start(x["etd"])
    x["ok"] = x["dias_consolidacion"] <= x["sla_consolidacion"]
    return x.groupby("mes").agg(pct=("ok", "mean"), n=("ok", "size")).reset_index()


def zarpados_con_reservas(hist: pd.DataFrame, reservas: pd.DataFrame | None, today: pd.Timestamp) -> pd.DataFrame:
    """Marítimos ya zarpados: Reservas Históricas + los que zarparon y siguen en Reservas (ETD ≤ hoy).

    Un embarque queda en Reservas después de zarpar hasta que se pasa a Históricas; si figura en las
    dos solapas, se usa el de Históricas.
    """
    real = zarpados(hist, today)
    if reservas is None or reservas.empty:
        return real
    r = reservas[reservas["modo"].isin(MODOS_MARITIMOS) & (reservas["etd"] <= today)]
    if "responsable" in r:
        r = r[r["responsable"].notna()]
    r = r[~dc.id_key(r["embarque"]).isin(set(dc.id_key(real["embarque"])))]
    if len(r) and "sla_cons_puerto" in r:
        # Ya zarpó: se mide contra el SLA del puerto (en curso se usa el tope fijo de 25 d).
        r = r.assign(sla_consolidacion=r["sla_cons_puerto"])
        r = r.assign(estado_consolidacion=calc.semaforo(r["dias_consolidacion"], r["sla_consolidacion"]))
    return pd.concat([real, r], ignore_index=True, sort=False) if len(r) else real


def projected_month(hist: pd.DataFrame, reservas: pd.DataFrame | None, month: pd.Timestamp,
                    today: pd.Timestamp) -> pd.DataFrame:
    """Mes en curso proyectado: zarpados del mes + Reservas marítimas con ETD en el mes.

    Las Reservas ya tienen fecha de packeo y ETD prevista, así que su
    consolidación proyectada se puede calcular. Si un embarque figura en las
    dos solapas, se usa el de Históricas (dato real).
    """
    m_end = month + pd.offsets.MonthBegin(1)
    real = zarpados_con_reservas(hist, reservas, today)
    real = real[(real["etd"] >= month) & (real["etd"] < m_end)].assign(origen="Zarpado")
    if reservas is None or reservas.empty:
        return real
    r = reservas[reservas["modo"].isin(MODOS_MARITIMOS) & (reservas["etd"] >= month) & (reservas["etd"] < m_end)]
    if "responsable" in r:
        r = r[r["responsable"].notna()]
    ya = set(dc.id_key(real["embarque"]))
    r = r[~dc.id_key(r["embarque"]).isin(ya)].assign(origen="Proyectado")
    return pd.concat([real, r], ignore_index=True, sort=False)


@dataclass
class Celda:
    valor: float = np.nan
    n: int = 0
    sla: float = np.nan
    tipo: str = "days"

    @property
    def estado(self) -> str:
        """'ok' / 'warn' / 'bad' / '' (sin color si la muestra es chica)."""
        if self.n < settings.MIN_SAMPLE or self.valor != self.valor:
            return ""
        if self.tipo == "pct":
            if settings.CUMPLIMIENTO_OBJETIVO is None:
                return ""
            minimo = settings.CUMPLIMIENTO_MINIMO or settings.CUMPLIMIENTO_OBJETIVO
            return ("ok" if self.valor >= settings.CUMPLIMIENTO_OBJETIVO else
                    "warn" if self.valor >= minimo else "bad")
        if self.sla != self.sla:
            return ""
        tol = settings.SLA_WARNING_TOLERANCE
        return "ok" if self.valor <= self.sla else ("warn" if self.valor <= self.sla * (1 + tol) else "bad")


def celda(d: pd.DataFrame, key: str) -> Celda:
    _, _, col, sla_col, tipo = next(i for i in INDICADORES if i[0] == key)
    if key == "mono":
        d = d[d["estructura"] == "Monoproveedor"]
    elif key == "cons":
        d = d[d["estructura"] == "Consolidado"]
    if key == "cumplimiento":
        pct, n = calc.cumplimiento(d[col], d[sla_col])
        return Celda(pct, n, np.nan, "pct")
    v = d[col].dropna()
    sla = float(d[sla_col].median()) if len(d) else np.nan
    return Celda(float(v.median()) if len(v) else np.nan, int(v.size), sla, "days")


@dataclass
class Cierre:
    columnas: list[str]            # encabezados legibles
    filas: list[tuple[str, list]]  # (indicador, [Celda | str])


def scorecard(hist: pd.DataFrame, reservas: pd.DataFrame | None, period: pd.DataFrame,
              today: pd.Timestamp, mes_label) -> Cierre:
    """Tabla: período | mes anterior | mes cerrado | variación | mes en curso (zarpado / proyectado).

    Zarpado = Históricas + lo que ya salió y sigue en Reservas. El total (fin de producción → ETA) solo
    cuenta embarques que ya llegaron (una ETA futura es estimada)."""
    z = zarpados_con_reservas(hist, reservas, today)

    def celda_(d, key):
        if key == "total" and "eta" in d:
            d = d[d["eta"] <= today]
        return celda(d, key)
    this_month = today.to_period("M").to_timestamp()
    last = this_month - pd.offsets.MonthBegin(1)
    prev = last - pd.offsets.MonthBegin(1)
    mz = calc.month_start(z["etd"])
    d_last, d_prev = z[mz == last], z[mz == prev]
    d_cur = z[mz == this_month]
    d_proj = projected_month(hist, reservas, this_month, today)

    cols = ["Período", mes_label(prev), f"{mes_label(last)} (cerrado)", "Variación",
            f"{mes_label(this_month)} · zarpados", f"{mes_label(this_month)} · proyectado"]
    filas = []
    for key, label, *_ in INDICADORES:
        c_last, c_prev = celda_(d_last, key), celda_(d_prev, key)
        if c_last.valor == c_last.valor and c_prev.valor == c_prev.valor:
            diff = c_last.valor - c_prev.valor
            if key == "cumplimiento":
                var = f"{'▲' if diff > 0 else '▼' if diff < 0 else '='} {abs(round(diff * 100))} pts"
            else:
                var = f"{'▲' if diff > 0 else '▼' if diff < 0 else '='} {abs(round(diff))} d"
        else:
            var = "—"
        filas.append((label, [celda_(period, key), c_prev, c_last, var,
                              celda_(d_cur, key), celda(d_proj, key)]))
    return Cierre(cols, filas)
