"""Diagnóstico (nivel 2): ¿qué explica el desvío? Corte por dimensión y contribución.

Para un conjunto de operaciones con un tiempo (`valor`) y su límite (`limite`), arma por cada
valor de una dimensión: operaciones, mediana, P90, cuántas se pasan, qué parte del desvío total
explica (contribución) y la variación de la mediana contra un período de comparación.

Una operación puede pertenecer a varios valores de una dimensión (un embarque consolidado tiene
varios proveedores): en ese caso cuenta en cada uno, y la contribución se calcula sobre esos conteos.
Sin Streamlit, para poder testearlo.
"""
from __future__ import annotations

from dataclasses import dataclass

import numpy as np
import pandas as pd

from utils.data_cleaning import id_key

SIN_DATO = "Sin dato"


@dataclass(frozen=True)
class Dimension:
    clave: str        # columna del DataFrame (puede tener listas)
    nombre: str       # cómo se muestra
    multiple: bool = False


def _expandir(df: pd.DataFrame, col: str) -> pd.DataFrame:
    d = df.copy()
    v = d[col]
    d[col] = v.map(lambda x: x if isinstance(x, (list, tuple, set)) and len(x) else
                   ([x] if isinstance(x, str) and x.strip() else [SIN_DATO]))
    d = d.explode(col)
    d[col] = d[col].map(lambda x: SIN_DATO if x is None or (isinstance(x, float) and np.isnan(x))
                        or str(x).strip(' "') == "" else str(x).strip(' "'))
    return d


def explicar(df: pd.DataFrame, dim: str, valor: str, limite: str | None, id_col: str = "embarque",
             prev: pd.DataFrame | None = None) -> pd.DataFrame:
    """Una fila por valor de `dim`, ordenada por contribución al desvío (y operaciones).

    - fuera: operaciones con valor > límite (sin límite: no hay fuera ni contribución).
    - contrib: fuera del grupo / fuera totales (sobre operaciones sin repetir cuando la dimensión es simple).
    - exceso: mediana de (valor − límite) de las que se pasan.
    - delta: mediana del grupo − mediana del mismo grupo en `prev`.
    """
    cols = ["grupo", "ops", "mediana", "p90", "fuera", "pct_fuera", "contrib", "exceso", "mediana_prev", "delta"]
    if df is None or df.empty or dim not in df:
        return pd.DataFrame(columns=cols)
    d = _expandir(df[df[valor].notna()], dim)
    if d.empty:
        return pd.DataFrame(columns=cols)
    tiene_lim = limite is not None and limite in d
    d["_fuera"] = (d[valor] > d[limite]) if tiene_lim else False
    d["_exc"] = (d[valor] - d[limite]).where(d["_fuera"]) if tiene_lim else np.nan
    total_fuera = int(d["_fuera"].sum())
    g = d.groupby(dim).agg(ops=(id_col, "nunique") if id_col in d else (valor, "size"),
                           mediana=(valor, "median"), p90=(valor, lambda s: s.quantile(.9)),
                           fuera=("_fuera", "sum"), exceso=("_exc", "median"))
    if tiene_lim:
        con_lim = d[d[limite].notna()]
        n_lim = (con_lim.groupby(dim)[id_col].nunique() if id_col in con_lim else con_lim.groupby(dim).size())
        g["con_objetivo"] = n_lim.reindex(g.index).fillna(0)
        g["pct_fuera"] = (g["fuera"] / g["con_objetivo"]).where(g["con_objetivo"] > 0)
    else:
        g["pct_fuera"] = np.nan
    g["contrib"] = g["fuera"] / total_fuera if total_fuera else np.nan
    if prev is not None and len(prev) and dim in prev:
        p = _expandir(prev[prev[valor].notna()], dim)
        g["mediana_prev"] = p.groupby(dim)[valor].median().reindex(g.index)
    else:
        g["mediana_prev"] = np.nan
    g["delta"] = g["mediana"] - g["mediana_prev"]
    g = g.reset_index().rename(columns={dim: "grupo"})
    g["_sd"] = g["grupo"] == SIN_DATO
    orden = ["contrib", "ops"] if total_fuera else ["ops"]
    g = g.sort_values(["_sd"] + orden, ascending=[True] + [False] * len(orden))
    return g[cols].reset_index(drop=True)


def casos(df: pd.DataFrame, dim: str, grupo: str) -> pd.DataFrame:
    """Operaciones de un valor de la dimensión (respeta dimensiones con varios valores por operación)."""
    if df is None or df.empty or dim not in df:
        return df.iloc[0:0] if df is not None else pd.DataFrame()
    v = df[dim]
    if grupo == SIN_DATO:
        m = v.map(lambda x: (not isinstance(x, (list, tuple, set)) and (x is None or (isinstance(x, float) and np.isnan(x))
                                                                     or str(x).strip() == "")) or
                  (isinstance(x, (list, tuple, set)) and not len(x)))
    else:
        m = v.map(lambda x: grupo in [str(i).strip(' "') for i in x] if isinstance(x, (list, tuple, set))
                  else str(x).strip(' "') == grupo if isinstance(x, str) else False)
    return df[m]


def indice_emb_hist(eh: pd.DataFrame | None) -> pd.DataFrame | None:
    """Embarque (id_key) → listas de SO, proveedores y category managers. Es lo lento de unir_emb_hist: conviene
    calcularlo una vez por carga de datos y pasarlo como `indice`."""
    if eh is None or eh.empty or "embarque" not in eh:
        return None
    e = eh.dropna(subset=["embarque"])
    k = id_key(e["embarque"])

    def lista(s):
        return sorted({v for v in (str(x).strip(' "') for x in s.dropna()) if v})

    cols = {"so": "so", "proveedor": "proveedor", "category": "category"}
    out = {}
    for src in cols:
        if src in e:
            out[src] = e[src].groupby(k.values).agg(lista)
    return pd.DataFrame(out) if out else None


def unir_emb_hist(ops: pd.DataFrame, eh: pd.DataFrame | None, indice: pd.DataFrame | None = None) -> pd.DataFrame:
    """Suma a cada embarque sus SO, proveedores y category managers (listas) desde Embarques Históricos."""
    out = ops.copy()
    g = indice if indice is not None else indice_emb_hist(eh)
    if g is None:
        for c in ("sos", "proveedores", "categories"):
            out[c] = [[] for _ in range(len(out))]
        return out
    k = id_key(out["embarque"].astype(str))
    for src, dst in (("so", "sos"), ("proveedor", "proveedores"), ("category", "categories")):
        out[dst] = k.map(g[src]).tolist() if src in g else [[] for _ in range(len(out))]
        out[dst] = out[dst].map(lambda x: x if isinstance(x, list) else [])
    return out


def texto_lista(x, limite: int = 3) -> str:
    if not isinstance(x, (list, tuple, set)) or not len(x):
        return ""
    vals = list(x)
    return ", ".join(vals[:limite]) + (f" +{len(vals) - limite}" if len(vals) > limite else "")
