"""Objetivo −15 % contra el año anterior, por estructura (monoproveedor y consolidado), mes a mes.

Criterio (acordado con el jefe de Comex):
- Cada estructura se compara contra sí misma: objetivo del mes = mediana del mismo mes del año anterior × 0,85.
  Así la estacionalidad (Año Nuevo chino, fin de año) se cancela y mono no se mezcla con conso.
- Acumulado: enero → último mes cerrado del año contra los mismos meses del año anterior (mediana de todo el tramo).
- Total = promedio de las variaciones de mono y conso ponderado por el volumen de ESTE año. No se usa la mediana
  total de cada año: si cambia la mezcla (más mono, que es más rápido), el total bajaría sin mejorar nada.
- Un mes solo se califica si los dos años tienen al menos OBJ_MIN_N casos; si no, se muestra sin color. Una
  estructura con muestra chica en el acumulado tampoco entra al total ponderado.
- Siempre mediana. La unidad la decide quien llama (embarque en consolidación, SO por envío en time to market).
"""
from __future__ import annotations

import numpy as np
import pandas as pd

from config import settings

ESTRUCTURAS = ["Monoproveedor", "Consolidado"]


def _estado(var: float, n0: int, n1: int) -> str:
    if var != var:
        return ""
    if n0 < settings.OBJ_MIN_N or n1 < settings.OBJ_MIN_N:
        return "Muestra chica"
    if var <= -settings.REDUCCION_OBJETIVO:
        return "Cumple"
    return "Reduce, sin llegar" if var < 0 else "No reduce"


def _fila(v0: pd.Series, v1: pd.Series) -> dict:
    m0 = float(v0.median()) if len(v0) else np.nan
    m1 = float(v1.median()) if len(v1) else np.nan
    var = m1 / m0 - 1 if m0 == m0 and m0 and m1 == m1 else np.nan
    return {"ant": m0, "n_ant": int(len(v0)), "objetivo": m0 * (1 - settings.REDUCCION_OBJETIVO) if m0 == m0 else np.nan,
            "act": m1, "n_act": int(len(v1)), "var": var, "estado": _estado(var, len(v0), len(v1))}


def vs_anio_anterior(d: pd.DataFrame, today: pd.Timestamp, fecha: str = "etd", valor: str = "valor") -> dict:
    """d = una fila por unidad con `fecha`, `valor` (días) y `estructura`.

    Devuelve {"mensual": filas (estructura, mes 1..mes actual), "acumulado": una fila por estructura,
              "total": variación ponderada, "meses": (primer, último mes cerrado), "anio": año}."""
    y = today.year
    x = d.dropna(subset=[fecha, valor]).copy() if d is not None and len(d) else pd.DataFrame(
        columns=[fecha, valor, "estructura"])
    x = x[x["estructura"].isin(ESTRUCTURAS)] if len(x) else x
    x["_y"] = pd.to_datetime(x[fecha]).dt.year if len(x) else []
    x["_m"] = pd.to_datetime(x[fecha]).dt.month if len(x) else []
    x = x[x["_y"].isin([y - 1, y])] if len(x) else x
    ult = today.month - 1                                    # último mes cerrado
    rows, acum = [], []
    for e in ESTRUCTURAS:
        s = x[x["estructura"] == e] if len(x) else x
        for m in range(1, today.month + 1):
            v0 = s[(s["_y"] == y - 1) & (s["_m"] == m)][valor] if len(s) else pd.Series(dtype=float)
            v1 = s[(s["_y"] == y) & (s["_m"] == m)][valor] if len(s) else pd.Series(dtype=float)
            if not len(v0) and not len(v1):
                continue
            r = _fila(v0, v1)
            if m == today.month:                             # mes en curso: se muestra, no se califica
                r["estado"] = "En curso" if r["var"] == r["var"] else ""
            rows.append({"estructura": e, "mes": m, "en_curso": m == today.month, **r})
        if ult >= 1 and len(s):
            v0 = s[(s["_y"] == y - 1) & (s["_m"] <= ult)][valor]
            v1 = s[(s["_y"] == y) & (s["_m"] <= ult)][valor]
            acum.append({"estructura": e, **_fila(v0, v1)})
    mensual = pd.DataFrame(rows, columns=["estructura", "mes", "en_curso", "ant", "n_ant", "objetivo", "act", "n_act",
                                          "var", "estado"])
    acumulado = pd.DataFrame(acum, columns=["estructura", "ant", "n_ant", "objetivo", "act", "n_act", "var", "estado"])
    ok = acumulado.dropna(subset=["var"])
    # Una estructura con muestra chica (menos de OBJ_MIN_N casos en algún año) no entra al total: con 1 caso
    # en el año anterior arrastraría el total sin representar nada (ej. aéreo monoproveedor 2025).
    ok = ok[(ok["n_act"] >= settings.OBJ_MIN_N) & (ok["n_ant"] >= settings.OBJ_MIN_N)]
    total = float((ok["var"] * ok["n_act"]).sum() / ok["n_act"].sum()) if len(ok) else np.nan
    n0 = int(acumulado["n_ant"].sum()) if len(acumulado) else 0
    n1 = int(ok["n_act"].sum()) if len(ok) else 0
    return {"mensual": mensual, "acumulado": acumulado, "anio": y, "ult_mes": ult,
            "total": {"var": total, "n_act": n1, "n_ant": n0, "estado": _estado(total, n0, n1),
                      "pesos": dict(zip(ok["estructura"], ok["n_act"] / n1)) if n1 else {}}}


def objetivo_por_fila(d: pd.DataFrame, res: dict, fecha: str = "etd") -> pd.Series:
    """Objetivo (días) de cada fila de d: el de su estructura y su mes (mediana del mismo mes del año anterior −15 %)."""
    m = res["mensual"]
    if m.empty or d.empty:
        return pd.Series(np.nan, index=d.index)
    mapa = m.set_index(["estructura", "mes"])["objetivo"]
    k = list(zip(d["estructura"], pd.to_datetime(d[fecha]).dt.month))
    return pd.Series([mapa.get(i, np.nan) for i in k], index=d.index)
