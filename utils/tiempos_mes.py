"""Tiempos mes a mes (mes de ETD): por tipo de negocio aéreo, por tramo y por etapa marítima.

Sin Streamlit, para poder testearlo. Todo por mediana.
"""
from __future__ import annotations

import numpy as np
import pandas as pd

from utils import calculations as calc


def _mes(d: pd.DataFrame) -> pd.Series:
    return calc.month_start(d["etd"])


def tipo_por_mes(a: pd.DataFrame, total: str = "dias_aereo", sla: str = "sla_aereo",
                 tipo: str = "tipo_label") -> pd.DataFrame:
    """Una fila por tipo × mes: n, mediana de días, SLA del tipo, n dentro del SLA y % dentro.

    Incluye una fila «Todos» por mes (el % compara cada embarque con el SLA de su tipo)."""
    cols = ["tipo", "mes", "n", "mediana", "sla", "dentro", "pct"]
    d = a.dropna(subset=["etd", total])
    if d.empty:
        return pd.DataFrame(columns=cols)
    d = d.assign(mes=_mes(d), _sla=d[sla] if sla in d else np.nan)
    d["_ok"] = (d[total] <= d["_sla"]).where(d["_sla"].notna())
    rows = []
    for (tp, mes), g in list(d.groupby([tipo, "mes"])) + [(("Todos", m), g) for m, g in d.groupby("mes")]:
        con = g["_ok"].dropna()
        rows.append({"tipo": tp, "mes": mes, "n": len(g), "mediana": float(g[total].median()),
                     "sla": float(g["_sla"].median()) if tp != "Todos" and g["_sla"].notna().any() else np.nan,
                     "dentro": int(con.sum()), "pct": float(con.mean()) if len(con) else np.nan})
    return pd.DataFrame(rows, columns=cols)


def por_mes(d: pd.DataFrame, columnas: list[str], llegados: list[str] | None = None,
            today: pd.Timestamp | None = None) -> pd.DataFrame:
    """Una fila por mes de ETD con la mediana de cada columna (días) y n.

    `llegados`: columnas que solo cuentan embarques con ETA ≤ today (tránsito, total)."""
    x = d.dropna(subset=["etd"])
    if x.empty:
        return pd.DataFrame(columns=["mes", "n"] + columnas)
    x = x.assign(mes=_mes(x))
    rows = []
    for mes, g in x.groupby("mes"):
        r = {"mes": mes, "n": len(g)}
        for c in columnas:
            if c not in g:
                r[c] = np.nan
                continue
            s = g
            if llegados and c in llegados and today is not None and "eta" in g:
                s = g[g["eta"] <= today]
            v = s[c].clip(lower=0).dropna()
            r[c] = float(v.median()) if len(v) else np.nan
            r[f"{c}_n"] = int(len(v))
        rows.append(r)
    return pd.DataFrame(rows)
