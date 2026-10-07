"""Salud de datos: controles automáticos sobre la planilla (health check).

Cada control devuelve los casos concretos a corregir, con la solapa donde se corrige y la
acción sugerida. Los usan la página Salud de datos, el semáforo del encabezado, la Bandeja
de acción y el Panorama. Sin Streamlit, para poder testearlo.

Los controles no dependen de los filtros de la barra lateral: miran la planilla entera.
"""
from __future__ import annotations

from dataclasses import dataclass, field

import numpy as np
import pandas as pd

from config import settings
from config.mappings import MODOS_MARITIMOS
from utils.data_cleaning import id_key

COLS = ["solapa", "registro", "fecha", "responsable", "detalle"]


@dataclass
class Control:
    clave: str
    nombre: str
    detecta: str
    donde: str
    accion: str
    severidad: str = "warn"          # "bad" (dato roto) | "warn" (incompleto o a revisar)
    casos: pd.DataFrame = field(default_factory=lambda: pd.DataFrame(columns=COLS))
    disponible: bool = True          # False si falta la solapa para correrlo

    @property
    def n(self) -> int:
        return int(len(self.casos))

    @property
    def estado(self) -> str:
        if not self.disponible:
            return "Sin datos"
        return "OK" if self.n == 0 else ("Roto" if self.severidad == "bad" else "A revisar")


def _casos(df: pd.DataFrame, solapa: str, detalle, fecha: str = "etd", registro: str = "embarque") -> pd.DataFrame:
    if df is None or df.empty:
        return pd.DataFrame(columns=COLS)
    det = df.apply(detalle, axis=1) if callable(detalle) else detalle
    return pd.DataFrame({
        "solapa": solapa,
        "registro": df[registro].astype(str).values if registro in df else "",
        "fecha": df[fecha].values if fecha in df else pd.NaT,
        "responsable": df["responsable"].values if "responsable" in df else None,
        "detalle": det.values if hasattr(det, "values") else det,
    }).reset_index(drop=True)


def _d(v) -> str:
    return pd.Timestamp(v).strftime("%d/%m/%Y") if pd.notna(v) else "—"


def _dias_habiles(edicion: pd.Timestamp, hasta: pd.Timestamp) -> int:
    """Días hábiles completos sin ediciones: desde el día siguiente a la edición hasta ayer."""
    if pd.isna(edicion):
        return 0
    desde = edicion.normalize() + pd.Timedelta(days=1)
    if hasta <= desde:
        return 0
    return int(np.busday_count(desde.date(), hasta.date()))


# ---------------------------------------------------------------------------
def controles(bundle, today: pd.Timestamp) -> list[Control]:
    """Todos los controles, en el orden en que se muestran."""
    g = bundle.get
    res, hist, aer, eh = g("reservas"), g("historicas"), g("aereos"), g("emb_hist")
    out: list[Control] = []

    # 1 · Errores de fórmula
    rows = [{"solapa": q.tab or q.title, "registro": ej or "—", "fecha": pd.NaT, "responsable": None,
             "detalle": f"«{col}»: {n} celdas con {v}"}
            for q in bundle.quality.values() for col, (n, v, ej) in q.error_cells.items()]
    out.append(Control("formula", "Errores de fórmula", "#N/A, #REF!, #VALUE!, #DIV/0!, #NAME? en columnas que usa el tablero",
                       "La solapa indicada", "Corregir la fórmula en la planilla", "bad",
                       pd.DataFrame(rows, columns=COLS)))

    # 2 · Llegó y sigue en Reservas
    c = Control("llego_en_reservas", "Llegó y sigue en Reservas", "Embarque en Reservas con ETA ya pasada: debería estar en Reservas Históricas",
                "Reservas → Reservas Históricas", "Pasar a Reservas Históricas", "warn", disponible=res is not None)
    if res is not None:
        d = res[res["eta"].notna() & (res["eta"] < today)]
        c.casos = _casos(d, "Reservas", lambda r: f"Llegó el {_d(r['eta'])} (ETA) y sigue en Reservas")
    out.append(c)

    # 3 · Packeo posterior a la ETD
    partes = []
    for df, sol in ((hist, "Reservas Históricas"), (res, "Reservas")):
        if df is not None:
            d = df[df["f_packeo_min"].notna() & df["etd"].notna() & (df["f_packeo_min"] > df["etd"])]
            partes.append(_casos(d, sol, lambda r: f"Packeo {_d(r['f_packeo_min'])} posterior a la ETD {_d(r['etd'])}"))
    out.append(Control("packeo_post_etd", "Packeo posterior a la ETD", "Fecha de packeo mínima después de la ETD: no puede haber salido antes de packear",
                       "Reservas / Reservas Históricas", "Corregir la fecha de packeo o la ETD", "bad",
                       pd.concat(partes, ignore_index=True) if partes else pd.DataFrame(columns=COLS)))

    # 4 · ETA anterior a la ETD
    partes = []
    for df, sol, col in ((hist, "Reservas Históricas", "eta"), (res, "Reservas", "eta"),
                         (aer, "Seguimiento Aéreos", "eta_caldas")):
        if df is not None and col in df:
            d = df[df[col].notna() & df["etd"].notna() & (df[col] < df["etd"])]
            partes.append(_casos(d, sol, lambda r, c=col: f"{'ETA Caldas' if c == 'eta_caldas' else 'ETA'} {_d(r[c])} anterior a la ETD {_d(r['etd'])}"))
    out.append(Control("eta_antes_etd", "Llegada antes de la salida", "ETA (o ETA Caldas) anterior a la ETD",
                       "La solapa indicada", "Corregir la ETA o la ETD", "bad",
                       pd.concat(partes, ignore_index=True) if partes else pd.DataFrame(columns=COLS)))

    # 5 · Embarque sin SO en Embarques Históricos
    c = Control("sin_so", "Embarque sin SO", f"Embarque de {today.year} zarpado hace más de {settings.SALUD_DIAS_SIN_SO} días que no figura en Embarques Históricos",
                "Embarques Históricos", "Cargar las SO del embarque", "warn",
                disponible=hist is not None and eh is not None)
    if hist is not None and eh is not None:
        claves = set(id_key(eh["embarque"].dropna()))
        d = hist[(hist["etd"].dt.year == today.year) & (hist["etd"] <= today - pd.Timedelta(days=settings.SALUD_DIAS_SIN_SO))]
        d = d[~id_key(d["embarque"]).isin(claves)]
        c.casos = _casos(d, "Embarques Históricos", "Sin SO cargadas")
    out.append(c)

    # 6 · Duplicado entre solapas
    c = Control("duplicado", "Duplicado entre solapas", "El mismo embarque está en Reservas y en Reservas Históricas",
                "Reservas", "Dejarlo en una sola solapa", "warn", disponible=res is not None and hist is not None)
    if res is not None and hist is not None:
        d = res[id_key(res["embarque"]).isin(set(id_key(hist["embarque"])))]
        c.casos = _casos(d, "Reservas", "También está en Reservas Históricas")
    out.append(c)

    # 7 · Fuera de SLA sin causa
    c = Control("sin_causa", "Fuera de SLA sin causa", f"Embarque marítimo de {today.year} fuera del SLA de consolidación sin «Tipo de demora»",
                "Reservas Históricas", "Cargar la causa («Tipo de demora»)", "warn", disponible=hist is not None)
    if hist is not None:
        d = hist[hist["modo"].isin(MODOS_MARITIMOS) & (hist["etd"].dt.year == today.year) & (hist["etd"] <= today)
                 & (hist["dias_consolidacion"] > hist["sla_consolidacion"]) & hist["tipo_demora"].isna()]
        c.casos = _casos(d, "Reservas Históricas",
                         lambda r: f"Consolidación {r['dias_consolidacion']:.0f} d (SLA {r['sla_consolidacion']:.0f} d)")
    out.append(c)

    # 8 · Columnas con fórmula sin referencia
    rows = []
    if hist is not None and "dif_mercado_planilla" in hist and "flete_economico" in hist:
        con = hist[hist["dif_mercado_planilla"].notna() & (hist["etd"].dt.year == today.year)]
        if len(con) >= settings.MIN_SAMPLE and (con["flete_economico"].fillna(0) > 0).mean() < 0.05:
            rows.append({"solapa": "Reservas Históricas", "registro": "Columna «Dif pagado vs mercado»",
                         "fecha": pd.NaT, "responsable": None,
                         "detalle": f"«Flete int + economico» está vacía, así que la diferencia repite el flete pagado "
                                    f"({len(con)} filas de {today.year}). El tablero calcula el vs mercado con las cotizaciones."})
    if eh is not None and "motivo_eh" in eh and "category" in eh:
        both = eh[eh["motivo_eh"].notna() & eh["category"].notna()]
        if len(both) >= settings.MIN_SAMPLE:
            cats = set(eh["category"].dropna().astype(str))
            share = both["motivo_eh"].astype(str).isin(cats).mean()
            if share >= 0.5:
                rows.append({"solapa": "Embarques Históricos", "registro": "Columna «Motivo»", "fecha": pd.NaT,
                             "responsable": None,
                             "detalle": f"El {share:.0%} de los valores son nombres de category managers (iguales a «Category»): "
                                        "posible columna corrida."})
    out.append(Control("columnas", "Columnas sospechosas", "Columnas cuya fórmula o contenido no corresponde a su título",
                       "La solapa indicada", "Revisar la fórmula o el contenido de la columna", "warn",
                       pd.DataFrame(rows, columns=COLS)))

    # 9 · Valores imposibles o no convertibles
    rows = []
    for q in bundle.quality.values():
        for col, n in q.out_of_range.items():
            rows.append({"solapa": q.tab or q.title, "registro": col, "fecha": pd.NaT, "responsable": None,
                         "detalle": f"{n} valores fuera de rango (se toman como vacíos)"})
        for col, n in q.invalid_values.items():
            rows.append({"solapa": q.tab or q.title, "registro": col, "fecha": pd.NaT, "responsable": None,
                         "detalle": f"{n} valores que no son fecha o número (se toman como vacíos)"})
    out.append(Control("valores", "Valores imposibles", "Días negativos o fuera de rango, fechas o números con texto",
                       "La solapa indicada", "Corregir el valor", "warn", pd.DataFrame(rows, columns=COLS)))

    # 10 · Campos críticos vacíos en lo que está en curso
    partes = []
    if res is not None:
        crit = {"etd": "ETD", "forwarder": "Forwarder", "f_packeo_min": "Fecha packeo mín.", "estructura": "Mono/Consolidado"}
        # Igual que «en curso»: los AIR de Reservas se controlan en Seguimiento Aéreos; sin responsable no es operación.
        es_air = res["embarque"].astype(str).str.strip().str.upper().str.startswith("AIR")
        r = res[~es_air & res["responsable"].notna()] if "responsable" in res else res[~es_air]
        d = r[r[list(crit)].isna().any(axis=1)]
        partes.append(_casos(d, "Reservas", lambda r: "Falta: " + ", ".join(v for k, v in crit.items() if pd.isna(r[k]))))
    if aer is not None:
        act = aer[aer["activo"]] if "activo" in aer else aer
        crit = {"etd": "ETD", "forwarder": "Forwarder", "f_packeo_min": "Fecha packeo mín."}
        d = act[act[list(crit)].isna().any(axis=1)]
        partes.append(_casos(d, "Seguimiento Aéreos", lambda r: "Falta: " + ", ".join(v for k, v in crit.items() if pd.isna(r[k]))))
    out.append(Control("criticos", "Campos críticos vacíos", "Operaciones en curso sin ETD, forwarder, packeo o estructura",
                       "La solapa indicada", "Completar el dato", "warn",
                       pd.concat(partes, ignore_index=True) if partes else pd.DataFrame(columns=COLS)))

    # 11 · Planilla desactualizada
    rows = []
    mod = bundle.source_modified.get("tablero") if getattr(bundle, "source_modified", None) else None
    if mod is not None:
        mod_ts = pd.Timestamp(mod)
        if mod_ts.tzinfo is not None:
            mod_ts = mod_ts.tz_convert(settings.TIMEZONE).tz_localize(None)
        dias = _dias_habiles(mod_ts, today)
        if dias > settings.SALUD_DIAS_HABILES_SIN_EDICION:
            rows.append({"solapa": "Tablero LI", "registro": "Última edición", "fecha": mod_ts, "responsable": None,
                         "detalle": f"Sin ediciones hace {dias} días hábiles"})
    out.append(Control("desactualizada", "Planilla desactualizada",
                       f"Sin ediciones en más de {settings.SALUD_DIAS_HABILES_SIN_EDICION} días hábiles",
                       "Tablero LI", "Actualizar la planilla", "warn", pd.DataFrame(rows, columns=COLS),
                       disponible=mod is not None))
    return out


def resumen(ctrls: list[Control]) -> tuple[str, int, int]:
    """(estado general, controles con problemas, casos totales). Estado: ok | warn | bad."""
    con = [c for c in ctrls if c.disponible and c.n]
    estado = "bad" if any(c.severidad == "bad" for c in con) else ("warn" if con else "ok")
    return estado, len(con), sum(c.n for c in con)


_MEMO: dict = {}


def controles_cache(bundle, today: pd.Timestamp) -> list[Control]:
    """Los controles se calculan una vez por carga de datos y por día."""
    key = (id(bundle), getattr(bundle, "loaded_at", None), today)
    if key not in _MEMO:
        _MEMO.clear()
        _MEMO[key] = controles(bundle, today)
    return _MEMO[key]
