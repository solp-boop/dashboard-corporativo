"""Cargas marítimas a Argentina por importador y mes de ETA (Reservas + Reservas Históricas).

Un embarque que está en las dos solapas se cuenta una vez (gana Reservas, que es la más actual).
FOB: el del dataset (Reservas: FOB real, si no SIMI · Históricas: FOB SIMI). Sin Streamlit, para poder testearlo.
"""
from __future__ import annotations

import pandas as pd

from config.mappings import MODOS_MARITIMOS
from utils import calculations as calc
from utils.data_cleaning import id_key


def base(res: pd.DataFrame | None, hist: pd.DataFrame | None, anio: int, empresas: list[str]) -> pd.DataFrame:
    partes = [x for x in (res, hist) if x is not None and len(x)]
    if not partes:
        return pd.DataFrame(columns=["empresa", "embarque", "eta", "mes", "contenedores", "fob"])
    d = pd.concat(partes, ignore_index=True, sort=False)
    d = d.assign(_k=id_key(d["embarque"])).drop_duplicates("_k").drop(columns="_k")
    d = d[(d["eta"].dt.year == anio) & d["modo"].isin(MODOS_MARITIMOS) & (d["destino"] == "Argentina")
          & d["empresa"].isin(empresas)]
    return d.assign(mes=calc.month_start(d["eta"]), contenedores=d["contenedores"].fillna(0),
                    fob=d["fob"].fillna(0))[["empresa", "embarque", "eta", "mes", "contenedores", "fob"]]


def resumen(d: pd.DataFrame, empresas: list[str]) -> pd.DataFrame:
    """Una fila por empresa (en el orden dado, aunque no tenga cargas) + total (empresa None)."""
    g = d.groupby("empresa").agg(cargas=("embarque", "nunique"), fcl=("contenedores", "sum"), fob=("fob", "sum"))
    g = g.reindex(empresas).fillna(0).reset_index()
    tot = {"empresa": None, "cargas": int(d["embarque"].nunique()), "fcl": float(d["contenedores"].sum()),
           "fob": float(d["fob"].sum())}
    return pd.concat([g, pd.DataFrame([tot])], ignore_index=True)


def por_mes(d: pd.DataFrame, empresas: list[str], medida: str) -> pd.DataFrame:
    """Empresa × mes de ETA con la medida (cargas | fcl | fob) + columna y fila de total."""
    col = {"cargas": ("embarque", "nunique"), "fcl": ("contenedores", "sum"), "fob": ("fob", "sum")}[medida]
    p = d.pivot_table(index="empresa", columns="mes", values=col[0], aggfunc=col[1], fill_value=0)
    p = p.reindex(empresas).fillna(0)
    p.loc["Total"] = p.sum()
    p["Total"] = p.sum(axis=1)
    if medida == "cargas":   # el total de cargas no se repite entre empresas
        p.loc["Total", "Total"] = d["embarque"].nunique()
    return p
