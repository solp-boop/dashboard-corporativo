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


# ---------------------------------------------------------------------------
# Tránsito marítimo y líneas
# ---------------------------------------------------------------------------
_LINEAS = {"maersk": "MAERSK", "msk": "MAERSK", "hapag": "HAPAG", "hapag lloyd": "HAPAG", "cosco": "COSCO",
           "zim": "ZIM", "cma": "CMA CGM", "cma cgm": "CMA CGM", "cma-cgm": "CMA CGM", "pil": "PIL", "pill": "PIL",
           "one": "ONE", "hmm": "HMM", "msc": "MSC", "emc": "EVERGREEN", "evergreen": "EVERGREEN", "oocl": "OOCL",
           "occl": "OOCL", "yang ming": "YANG MING"}


def linea(v) -> str:
    """Nombre unificado de la línea marítima (MSC, MAERSK, HAPAG…); vacío → «Sin dato»."""
    from utils.data_cleaning import fold
    if not isinstance(v, str) or not v.strip():
        return "Sin dato"
    f = fold(v)
    return _LINEAS.get(f, v.strip().upper())


def solo_argentina(d: pd.DataFrame) -> pd.DataFrame:
    """Destino Argentina (o sin destino cargado): afuera lo que va a otro país."""
    if d is None or "destino" not in d:
        return d
    return d[d["destino"].isna() | (d["destino"] == "Argentina")]


def tt_mes(d: pd.DataFrame) -> pd.DataFrame:
    """Por mes de ETA (solo llegados): embarques, % en objetivo, mínimo, mediana y máximo de tránsito + total (NaT)."""
    x = d.dropna(subset=["eta", "dias_tt"])
    if x.empty:
        return pd.DataFrame(columns=["mes", "n", "pct_obj", "tt_min", "tt_med", "tt_max"])
    x = x.assign(mes=calc.month_start(x["eta"]))

    def fila(g):
        con = g.dropna(subset=["obj_tt"]) if "obj_tt" in g else g.iloc[0:0]
        return {"n": len(g), "pct_obj": float((con["dias_tt"] <= con["obj_tt"]).mean()) if len(con) else np.nan,
                "tt_min": float(g["dias_tt"].min()), "tt_med": float(g["dias_tt"].median()),
                "tt_max": float(g["dias_tt"].max())}
    rows = [{"mes": m, **fila(g)} for m, g in x.groupby("mes")] + [{"mes": pd.NaT, **fila(x)}]
    return pd.DataFrame(rows)


def lineas_mes(d: pd.DataFrame, fecha: str = "eta") -> pd.DataFrame:
    """Línea × mes de `fecha`: embarques, contenedores, % de los contenedores del mes y mediana de tránsito
    (la mediana solo con los que ya tienen tránsito calculado)."""
    x = d.dropna(subset=[fecha])
    if x.empty:
        return pd.DataFrame(columns=["linea", "mes", "n", "cont", "pct", "tt_med"])
    x = x.assign(mes=calc.month_start(x[fecha]), linea=x["linea"].map(linea) if "linea" in x else "Sin dato",
                 _c=x["contenedores"].fillna(1).clip(lower=1) if "contenedores" in x else 1.0)
    g = x.groupby(["linea", "mes"]).agg(n=("embarque", "nunique"), cont=("_c", "sum"),
                                        tt_med=("dias_tt", "median")).reset_index()
    g["pct"] = g["cont"] / g.groupby("mes")["cont"].transform("sum")
    return g


def subas_tt(d: pd.DataFrame, umbral: int = 7) -> pd.DataFrame:
    """Embarques llegados cuyo tránsito superó el objetivo de su puerto o la mediana de su línea en los 3 meses
    anteriores (por ETA) en `umbral` días o más. Para avisar a ventas / preventas."""
    x = d.dropna(subset=["eta", "dias_tt"]).copy()
    if x.empty:
        return x
    x["linea_u"] = x["linea"].map(linea) if "linea" in x else "Sin dato"
    x["mes"] = calc.month_start(x["eta"])
    ref = {}
    for (ln, mes), _ in x.groupby(["linea_u", "mes"]):
        prev = x[(x["linea_u"] == ln) & (x["mes"] < mes) & (x["mes"] >= mes - pd.DateOffset(months=3))]["dias_tt"]
        ref[(ln, mes)] = float(prev.median()) if len(prev) >= 3 else np.nan
    x["ref_linea"] = [ref.get((a, b), np.nan) for a, b in zip(x["linea_u"], x["mes"])]
    x["vs_linea"] = x["dias_tt"] - x["ref_linea"]
    x["vs_obj"] = x["dias_tt"] - x["obj_tt"] if "obj_tt" in x else np.nan
    m = (x["vs_obj"] > 0) | (x["vs_linea"] >= umbral)
    return x[m].sort_values("eta", ascending=False)
