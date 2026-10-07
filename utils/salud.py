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

COLS = ["solapa", "registro", "fila", "fecha", "responsable", "detalle"]


@dataclass
class Control:
    clave: str
    nombre: str
    detecta: str
    donde: str                       # solapa(s) donde se corrige, con el nombre real de la planilla
    accion: str
    severidad: str = "warn"          # "bad" (dato roto) | "warn" (incompleto o a revisar)
    casos: pd.DataFrame = field(default_factory=lambda: pd.DataFrame(columns=COLS))
    disponible: bool = True          # False si falta la solapa para correrlo
    columna: str = ""                # columna(s) a mirar

    @property
    def solapas(self) -> str:
        """Solapas con casos (o la prevista si no hay casos)."""
        if self.n and "solapa" in self.casos:
            return " · ".join(dict.fromkeys(self.casos["solapa"].dropna().astype(str)))
        return self.donde

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
        "fila": df["_fila"].values if "_fila" in df else None,
        "fecha": df[fecha].values if fecha in df else pd.NaT,
        "responsable": df["responsable"].values if "responsable" in df else None,
        "detalle": det.values if hasattr(det, "values") else det,
    }).reset_index(drop=True)


def solapa(bundle, key: str) -> str:
    """Nombre real de la solapa en la planilla (p. ej. «Reservas Historicas», «SEGUIMIENTO AEREOS»)."""
    q = getattr(bundle, "quality", {}).get(key)
    if q is not None and q.tab:
        return q.tab
    return settings.DATASET_SOURCES.get(key, ("", key))[1]


def alcance(key: str, df: pd.DataFrame) -> tuple[pd.Series, pd.Series]:
    """(filas para campos clave, filas para problemas de formato).

    Todo: fecha de referencia desde settings.SALUD_DESDE (o sin fecha, que también es un problema).
    Reservas: campos clave solo con la instrucción enviada; problemas de formato solo con «ETD OK FFWW».
    """
    if df is None or df.empty:
        vacio = pd.Series(dtype=bool)
        return vacio, vacio
    f = df["fecha_ref"] if "fecha_ref" in df else pd.Series(pd.NaT, index=df.index)
    base = f.isna() | (f >= pd.Timestamp(settings.SALUD_DESDE))
    campos, problemas = base, base
    if key == "reservas":
        if "f_instruccion" in df:
            campos = base & df["f_instruccion"].notna()
        if "etd_ok" in df:
            problemas = base & df["etd_ok"].fillna(False).astype(bool)
    return campos, problemas


TIPOS_FORMATO = {"error": "Error de fórmula", "invalido": "Valor no convertible", "rango": "Fuera de rango"}


def _lista_filas(filas: list[int], n: int = 8) -> str:
    if not filas:
        return ""
    txt = ", ".join(str(f) for f in filas[:n])
    return f"fila{'s' if len(filas) > 1 else ''} {txt}" + (f" y {len(filas) - n} más" if len(filas) > n else "")


def formato(bundle) -> pd.DataFrame:
    """Errores de fórmula, valores no convertibles y fuera de rango, dentro del alcance de cada solapa.

    Columnas: key, solapa, tipo, tipo_txt, campo, n, filas (lista de filas de la planilla)."""
    rows = []
    for key, q in getattr(bundle, "quality", {}).items():
        df = bundle.get(key)
        ok = None
        if df is not None and "_fila" in df:
            _, prob = alcance(key, df)
            ok = set(df.loc[prob, "_fila"].astype(int))
        fuentes = [("error", c, n, v) for c, (n, v, _) in q.error_cells.items()]
        fuentes += [("invalido", c, n, None) for c, n in q.invalid_values.items()]
        fuentes += [("rango", c, n, None) for c, n in q.out_of_range.items()]
        for tipo, campo, n, valores in fuentes:
            filas = q.issue_rows.get((tipo, campo))
            if filas is not None and ok is not None:
                filas = sorted(set(filas) & ok)
                n = len(filas)
            else:
                filas = []
            if not n:
                continue
            rows.append({"key": key, "solapa": q.tab or q.title, "tipo": tipo,
                         "tipo_txt": TIPOS_FORMATO[tipo] + (f" ({valores})" if valores else ""),
                         "campo": campo, "n": int(n), "filas": filas})
    return pd.DataFrame(rows, columns=["key", "solapa", "tipo", "tipo_txt", "campo", "n", "filas"])


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
    S = {k: solapa(bundle, k) for k in ("reservas", "historicas", "aereos", "planif", "emb_hist")}
    fm = formato(bundle)
    out: list[Control] = []

    # 1 · Errores de fórmula
    rows = [{"solapa": r["solapa"], "registro": f"Columna «{r['campo']}»", "fecha": pd.NaT, "responsable": None,
             "detalle": f"{r['n']} celdas con {r['tipo_txt'].split('(')[-1].rstrip(')')} · {_lista_filas(r['filas'])}".rstrip(" ·")}
            for _, r in fm[fm["tipo"] == "error"].iterrows()]
    out.append(Control("formula", "Errores de fórmula", "#N/A, #REF!, #VALUE!, #DIV/0!, #NAME? en columnas que usa el tablero",
                       "Según el caso", "Corregir la fórmula en la planilla", "bad",
                       pd.DataFrame(rows, columns=COLS), columna="La indicada en cada caso"))

    # 2 · Llegó y sigue en Reservas
    c = Control("llego_en_reservas", "Llegó y sigue en Reservas", "Embarque en Reservas con ETA ya pasada: debería estar en Reservas Históricas",
                f"{S['reservas']} → {S['historicas']}", f"Pasar a {S['historicas']}", "warn", disponible=res is not None,
                columna="ETA")
    if res is not None:
        d = res[res["eta"].notna() & (res["eta"] < today)]
        c.casos = _casos(d, S["reservas"], lambda r: f"Llegó el {_d(r['eta'])} (ETA) y sigue en Reservas")
    out.append(c)

    desde = pd.Timestamp(settings.SALUD_DESDE)

    # 3 · Packeo posterior a la ETD (desde SALUD_DESDE)
    partes = []
    for df, sol in ((hist, S["historicas"]), (res, S["reservas"])):
        if df is not None:
            d = df[df["f_packeo_min"].notna() & df["etd"].notna() & (df["f_packeo_min"] > df["etd"])
                   & (df["etd"] >= desde)]
            partes.append(_casos(d, sol, lambda r: f"Packeo {_d(r['f_packeo_min'])} posterior a la ETD {_d(r['etd'])}"))
    out.append(Control("packeo_post_etd", "Packeo posterior a la ETD", f"Fecha de packeo mínima después de la ETD: no puede haber salido antes de packear (ETD desde {desde:%Y})",
                       f"{S['reservas']} · {S['historicas']}", "Corregir la fecha de packeo o la ETD", "bad",
                       pd.concat(partes, ignore_index=True) if partes else pd.DataFrame(columns=COLS),
                       columna="F.Packeo Min · ETD"))

    # 4 · ETA anterior a la ETD
    partes = []
    for df, sol, col in ((hist, S["historicas"], "eta"), (res, S["reservas"], "eta"),
                         (aer, S["aereos"], "eta_caldas")):
        if df is not None and col in df:
            d = df[df[col].notna() & df["etd"].notna() & (df[col] < df["etd"]) & (df["etd"] >= desde)]
            partes.append(_casos(d, sol, lambda r, c=col: f"{'ETA Caldas' if c == 'eta_caldas' else 'ETA'} {_d(r[c])} anterior a la ETD {_d(r['etd'])}"))
    out.append(Control("eta_antes_etd", "Llegada antes de la salida", f"ETA (o ETA Caldas) anterior a la ETD (ETD desde {desde:%Y})",
                       f"{S['reservas']} · {S['historicas']} · {S['aereos']}", "Corregir la ETA o la ETD", "bad",
                       pd.concat(partes, ignore_index=True) if partes else pd.DataFrame(columns=COLS),
                       columna="ETA (ETA Caldas en aéreos) · ETD"))

    # 5 · Embarque sin SO en Embarques Históricos
    c = Control("sin_so", "Embarque sin SO", f"Embarque de {today.year} zarpado hace más de {settings.SALUD_DIAS_SIN_SO} días que no figura en Embarques Históricos",
                S["emb_hist"], "Cargar las SO del embarque", "warn",
                disponible=hist is not None and eh is not None, columna="Embarque · SO")
    if hist is not None and eh is not None:
        claves = set(id_key(eh["embarque"].dropna()))
        d = hist[(hist["etd"].dt.year == today.year) & (hist["etd"] <= today - pd.Timedelta(days=settings.SALUD_DIAS_SIN_SO))]
        d = d[~id_key(d["embarque"]).isin(claves)]
        c.casos = _casos(d, S["emb_hist"], "Sin SO cargadas")
    out.append(c)

    # 6 · Duplicado entre solapas
    c = Control("duplicado", "Duplicado entre solapas", "El mismo embarque está en Reservas y en Reservas Históricas",
                S["reservas"], "Dejarlo en una sola solapa", "warn", disponible=res is not None and hist is not None,
                columna="Embarque")
    if res is not None and hist is not None:
        d = res[id_key(res["embarque"]).isin(set(id_key(hist["embarque"])))]
        c.casos = _casos(d, S["reservas"], f"También está en {S['historicas']}")
    out.append(c)

    # 7 · Fuera de SLA sin causa
    c = Control("sin_causa", "Fuera de SLA sin causa", f"Embarque marítimo de {today.year} fuera del SLA de consolidación sin «Tipo de demora»",
                S["historicas"], "Cargar la causa («Tipo de demora»)", "warn", disponible=hist is not None,
                columna="Tipo de demora")
    if hist is not None:
        d = hist[hist["modo"].isin(MODOS_MARITIMOS) & (hist["etd"].dt.year == today.year) & (hist["etd"] <= today)
                 & (hist["dias_consolidacion"] > hist["sla_consolidacion"]) & hist["tipo_demora"].isna()]
        c.casos = _casos(d, S["historicas"],
                         lambda r: f"Consolidación {r['dias_consolidacion']:.0f} d (SLA {r['sla_consolidacion']:.0f} d)")
    out.append(c)

    # 8 · Columnas con fórmula sin referencia
    rows = []
    if hist is not None and "dif_mercado_planilla" in hist and "flete_economico" in hist:
        con = hist[hist["dif_mercado_planilla"].notna() & (hist["etd"].dt.year == today.year)]
        if len(con) >= settings.MIN_SAMPLE and (con["flete_economico"].fillna(0) > 0).mean() < 0.05:
            rows.append({"solapa": S["historicas"], "registro": "Columna «Dif pagado vs mercado»",
                         "fecha": pd.NaT, "responsable": None,
                         "detalle": f"«Flete int + economico» está vacía, así que la diferencia repite el flete pagado "
                                    f"({len(con)} filas de {today.year}). El tablero calcula el vs mercado con las cotizaciones."})
    if eh is not None and "motivo_eh" in eh and "category" in eh:
        both = eh[eh["motivo_eh"].notna() & eh["category"].notna()]
        if len(both) >= settings.MIN_SAMPLE:
            cats = set(eh["category"].dropna().astype(str))
            share = both["motivo_eh"].astype(str).isin(cats).mean()
            if share >= 0.5:
                rows.append({"solapa": S["emb_hist"], "registro": "Columna «Motivo»", "fecha": pd.NaT,
                             "responsable": None,
                             "detalle": f"El {share:.0%} de los valores son nombres de category managers (iguales a «Category»): "
                                        "posible columna corrida."})
    out.append(Control("columnas", "Columnas sospechosas", "Columnas cuya fórmula o contenido no corresponde a su título",
                       "Según el caso", "Revisar la fórmula o el contenido de la columna", "warn",
                       pd.DataFrame(rows, columns=COLS), columna="La indicada en cada caso"))

    # 9 · Valores imposibles o no convertibles
    rows = []
    for _, r in fm[fm["tipo"] != "error"].iterrows():
        que = "valores fuera de rango" if r["tipo"] == "rango" else "valores que no son fecha o número"
        rows.append({"solapa": r["solapa"], "registro": f"Columna «{r['campo']}»", "fecha": pd.NaT, "responsable": None,
                     "detalle": f"{r['n']} {que} (se toman como vacíos) · {_lista_filas(r['filas'])}".rstrip(" ·")})
    out.append(Control("valores", "Valores imposibles",
                       f"Días negativos o fuera de rango, fechas o números con texto (registros desde "
                       f"{pd.Timestamp(settings.SALUD_DESDE):%Y}; en Reservas, solo con ETD OK del agente)",
                       "Según el caso", "Corregir el valor", "warn", pd.DataFrame(rows, columns=COLS),
                       columna="La indicada en cada caso"))

    # 10 · Campos críticos vacíos en lo que está en curso
    partes = []
    if res is not None:
        crit = {"etd": "ETD", "forwarder": "Forwarder", "f_packeo_min": "Fecha packeo mín.", "estructura": "Mono/Consolidado"}
        # Igual que «en curso»: los AIR de Reservas se controlan en Seguimiento Aéreos; sin responsable no es operación.
        es_air = res["embarque"].astype(str).str.strip().str.upper().str.startswith("AIR")
        r = res[~es_air & res["responsable"].notna()] if "responsable" in res else res[~es_air]
        d = r[r[list(crit)].isna().any(axis=1)]
        partes.append(_casos(d, S["reservas"], lambda r: "Falta: " + ", ".join(v for k, v in crit.items() if pd.isna(r[k]))))
    if aer is not None:
        act = aer[aer["activo"]] if "activo" in aer else aer
        crit = {"etd": "ETD", "forwarder": "Forwarder", "f_packeo_min": "Fecha packeo mín."}
        d = act[act[list(crit)].isna().any(axis=1)]
        partes.append(_casos(d, S["aereos"], lambda r: "Falta: " + ", ".join(v for k, v in crit.items() if pd.isna(r[k]))))
    out.append(Control("criticos", "Campos críticos vacíos", "Operaciones en curso sin ETD, forwarder, packeo o estructura",
                       f"{S['reservas']} · {S['aereos']}", "Completar el dato", "warn",
                       pd.concat(partes, ignore_index=True) if partes else pd.DataFrame(columns=COLS),
                       columna="ETD · Forwarder · F.Packeo Min · ¿ES MONOPROVEEDOR?"))

    out.append(_packeo_sin_fechas(bundle, S, res, hist, aer))

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
                       disponible=mod is not None, columna="—"))
    return out


def _packeo_sin_fechas(bundle, S, res, hist, aer) -> Control:
    """Embarque con fecha de packeo mínima pero sin ETD o ETA (vacía o con #N/A), o con la referencia en #N/A."""
    desde = pd.Timestamp(settings.SALUD_DESDE)
    partes = []
    for df, key in ((res, "reservas"), (hist, "historicas"), (aer, "aereos")):
        if df is None or df.empty or "f_packeo_min" not in df:
            continue
        q = bundle.quality.get(key)
        d = df
        if key == "reservas":
            d = d[~d["embarque"].astype(str).str.strip().str.upper().str.startswith("AIR")]
        else:
            d = d[d["f_packeo_min"] >= desde]
        faltan = {c: lbl for c, lbl in (("etd", "ETD"), ("eta", "ETA")) if c in d}
        d = d[d["f_packeo_min"].notna() & d[list(faltan)].isna().any(axis=1)]
        err: dict = {}
        if q is not None:
            txt = {"error": "con #N/A o error de fórmula", "invalido": "con un valor que no es fecha",
                   "rango": "con una fecha imposible"}
            for (tipo, campo), filas in q.issue_rows.items():
                if campo.upper() in ("ETD", "ETA"):
                    err.update({(f, campo.upper()): txt[tipo] for f in filas})

        def det(r, faltan=faltan, err=err):
            vacias = [lbl for c, lbl in faltan.items() if pd.isna(r[c])]
            fila = int(r["_fila"]) if "_fila" in r and pd.notna(r["_fila"]) else None
            partes_ = [f"{lbl} {err.get((fila, lbl), 'vacía')}" for lbl in vacias]
            return f"Packeo {_d(r['f_packeo_min'])}: " + ", ".join(partes_)
        partes.append(_casos(d, S[key], det, fecha="f_packeo_min"))
        if q is not None:
            for e in q.ref_errores:
                if pd.isna(e.get("f_packeo_min")) or (key != "reservas" and e["f_packeo_min"] < desde):
                    continue
                partes.append(pd.DataFrame([{
                    "solapa": S[key], "registro": e["valor"], "fila": e["fila"], "fecha": e.get("f_packeo_min"),
                    "responsable": e.get("responsable"),
                    "detalle": f"Referencia (Embarque) con {e['valor']}: la fila no se toma en el tablero"}]))
    casos = pd.concat([p for p in partes if len(p)], ignore_index=True) if any(len(p) for p in partes) \
        else pd.DataFrame(columns=COLS)
    return Control("packeo_sin_fechas", "Packeo sin ETD / ETA",
                   f"Embarque con fecha de packeo mínima pero con la ETD o la ETA vacía o en #N/A, o con la referencia "
                   f"en #N/A (Reservas: todos; resto: packeo desde {desde:%Y})",
                   f"{S['reservas']} · {S['historicas']} · {S['aereos']}", "Completar la ETD / ETA o corregir la fórmula",
                   "bad", casos, disponible=res is not None or hist is not None, columna="ETD · ETA · Embarque")


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
