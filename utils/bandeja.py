"""Bandeja de acción: todos los casos que piden intervención, con su acción sugerida.

Una fila por caso (un embarque puede tener más de uno). Reúne:
- en curso: ETD sin confirmar, zarpados sin documentación, instruidos sin ETD,
  consolidación marítima proyectada fuera de SLA y aéreos proyectados fuera del SLA de su tipo;
- cerrados: embarques fuera de SLA sin causa cargada;
- datos: los casos por registro de Salud de datos.

Sin Streamlit, para poder testearlo.
"""
from __future__ import annotations

import numpy as np
import pandas as pd

from config import settings
from utils import calculations as calc
from utils.data_cleaning import id_key

COLUMNAS = ["prioridad", "tipo", "situacion", "accion", "embarque", "so", "proveedor", "agente", "responsable",
            "modo", "f_packeo", "etd", "dias", "sla", "excedido", "causa", "solapa"]
PRIORIDADES = ["Alta", "Media", "Baja"]
TIPOS = {"forwarder": "Confirmar o reclamar al forwarder", "sla": "Riesgo de SLA",
         "cerrado": "Cerrado sin causa", "dato": "Dato a corregir"}

# Controles de Salud de datos que se resuelven por registro (los de columna van solo a Salud de datos).
CONTROLES_POR_REGISTRO = ("llego_en_reservas", "packeo_post_etd", "eta_antes_etd", "sin_so", "duplicado", "criticos")


def _base(df: pd.DataFrame, **cols) -> pd.DataFrame:
    """Arma filas de la bandeja desde un DataFrame de operaciones (columnas faltantes = vacías)."""
    out = pd.DataFrame(index=df.index)
    src = {"embarque": "embarque", "agente": "forwarder", "responsable": "responsable", "modo": "grupo_modo",
           "f_packeo": "f_packeo_min", "etd": "etd", "causa": "tipo_demora"}
    for dst, s in src.items():
        out[dst] = df[s] if s in df else None
    for k, v in cols.items():
        out[k] = v
    return out


def _dias_a(df: pd.DataFrame, today: pd.Timestamp) -> pd.Series:
    return (df["etd"] - today).dt.days


def casos_en_curso(res: pd.DataFrame, today: pd.Timestamp) -> list[pd.DataFrame]:
    """res = embarques en curso (Reservas marítimo/camión + aéreos activos), como lo arma views._common.en_curso."""
    if res is None or res.empty:
        return []
    out = []
    es_air = res["embarque"].astype(str).str.strip().str.upper().str.startswith("AIR")
    mar = (res["grupo_modo"] == "Marítimo") & ~es_air if "grupo_modo" in res else ~es_air
    etd_ok = res["etd_ok"].fillna(False).astype(bool) if "etd_ok" in res else pd.Series(False, index=res.index)
    dias_a = _dias_a(res, today)

    # 1 · ETD en los próximos días sin confirmar
    m = res["etd"].between(today, today + pd.Timedelta(days=settings.ALERT_HORIZON_DAYS)) & ~etd_ok
    d = res[m]
    if len(d):
        out.append(_base(d, tipo=TIPOS["forwarder"],
                         situacion=d["etd"].map(lambda v: f"ETD {v:%d/%m} sin confirmar por el forwarder"),
                         accion=d["forwarder"].map(lambda f: f"Pedir confirmación de ETD a {f}" if isinstance(f, str)
                                                   else "Pedir confirmación de ETD al forwarder"),
                         prioridad=np.where(dias_a[m] <= 3, "Alta", "Media")))

    # 2 · Zarpó sin documentación (marítimo)
    if "draft_bl" in res and "pl_final" in res:
        falta = ((res["draft_bl"].fillna("NO").astype(str).str.upper() != "SI")
                 | (res["pl_final"].fillna("NO").astype(str).str.upper() != "SI"))
        m = mar & falta & (res["etd"] < today - pd.Timedelta(days=3))
        d = res[m]
        if len(d):
            out.append(_base(d, tipo=TIPOS["forwarder"],
                             situacion=d["etd"].map(lambda v: f"Zarpó el {v:%d/%m} sin Draft BL / packing list final"),
                             accion=d["forwarder"].map(lambda f: f"Reclamar Draft BL y packing list a {f}"
                                                       if isinstance(f, str) else "Reclamar Draft BL y packing list"),
                             prioridad="Alta", dias=(today - d["etd"]).dt.days))

    # 3 · Instruido sin ETD
    if "f_instruccion" in res:
        m = res["etd"].isna() & res["f_instruccion"].notna()
        d = res[m]
        if len(d):
            out.append(_base(d, tipo=TIPOS["forwarder"], situacion="Instruido sin ETD cargada",
                             accion="Pedir booking / ETD al forwarder", prioridad="Media"))

    # 4 · Consolidación marítima proyectada fuera de SLA, todavía sin salir y sin ETD OK (hay margen)
    if "estado_consolidacion" in res:
        por_salir = res["etd"].isna() | (res["etd"] >= today)
        m = mar & res["estado_consolidacion"].isin([calc.SEMAFORO_WARN, calc.SEMAFORO_BAD]) & ~etd_ok & por_salir
        d = res[m]
        if len(d):
            exc = d["dias_consolidacion"] - d["sla_consolidacion"]
            # Alta: hoy ya pasó el SLA desde el packeo, o sale en la próxima semana
            ya_pasado = (today - d["f_packeo_min"]).dt.days > d["sla_consolidacion"]
            pronto = dias_a[m].between(0, settings.ALERT_HORIZON_DAYS)
            out.append(_base(d, tipo=TIPOS["sla"],
                             situacion=[f"Consolidación proyectada {a:.0f} d (SLA {b:.0f} d)" for a, b in
                                        zip(d["dias_consolidacion"], d["sla_consolidacion"])],
                             accion=np.where(d["f_packeo_min"].isna() | (d["f_packeo_min"] > today),
                                             "Escalar al proveedor / category manager: packeo pendiente",
                                             "Adelantar la salida con el forwarder"),
                             prioridad=np.where(ya_pasado.fillna(False) | pronto.fillna(False), "Alta", "Media"),
                             dias=d["dias_consolidacion"], sla=d["sla_consolidacion"], excedido=exc.clip(lower=0)))
    return out


def casos_aereos(riesgo_aereo: pd.DataFrame, today: pd.Timestamp) -> list[pd.DataFrame]:
    """riesgo_aereo = aéreos activos proyectados fuera del SLA de su tipo (views.aereos.riesgo_aereo)."""
    if riesgo_aereo is None or riesgo_aereo.empty:
        return []
    d = riesgo_aereo
    # Solo lo que todavía no salió (después de la ETD queda poco por hacer) y con SLA vigente para su ETD.
    d = d[d["etd"].isna() | (d["etd"] >= today)]
    if "sla_vigente" in d:
        d = d[d["sla_vigente"].fillna(True).astype(bool)]
    if d.empty:
        return []
    exc = d["dias_proyectados"] - d["sla_aereo"]
    ya_pasado = (today - d["f_packeo_min"]).dt.days > d["sla_aereo"]
    return [_base(d, tipo=TIPOS["sla"], modo="Aéreo",
                  situacion=[f"Punta a punta proyectado {a:.0f} d (SLA {b:.0f} d)" for a, b in
                             zip(d["dias_proyectados"], d["sla_aereo"])],
                  accion=d["forwarder"].map(lambda f: f"Revisar tramos con {f} para recuperar días"
                                            if isinstance(f, str) else "Revisar tramos con el agente"),
                  prioridad=np.where(ya_pasado.fillna(False) | _dias_a(d, today).between(0, 3).fillna(False),
                                     "Alta", "Media"),
                  dias=d["dias_proyectados"], sla=d["sla_aereo"], excedido=exc.clip(lower=0))]


def casos_cerrados(hist: pd.DataFrame, today: pd.Timestamp) -> list[pd.DataFrame]:
    """Embarques marítimos del año zarpados fuera del SLA de consolidación y sin «Tipo de demora»."""
    from config.mappings import MODOS_MARITIMOS
    if hist is None or hist.empty:
        return []
    m = (hist["modo"].isin(MODOS_MARITIMOS) & (hist["etd"].dt.year == today.year) & (hist["etd"] <= today)
         & (hist["dias_consolidacion"] > hist["sla_consolidacion"]) & hist["tipo_demora"].isna())
    d = hist[m]
    if d.empty:
        return []
    return [_base(d, tipo=TIPOS["cerrado"], modo="Marítimo",
                  situacion=[f"Cerró fuera de SLA: {a:.0f} d (SLA {b:.0f} d)" for a, b in
                             zip(d["dias_consolidacion"], d["sla_consolidacion"])],
                  accion="Cargar la causa en «Tipo de demora»", prioridad="Baja", solapa="Reservas Históricas",
                  dias=d["dias_consolidacion"], sla=d["sla_consolidacion"],
                  excedido=d["dias_consolidacion"] - d["sla_consolidacion"])]


def casos_datos(ctrls) -> list[pd.DataFrame]:
    out = []
    for c in ctrls:
        if c.clave not in CONTROLES_POR_REGISTRO or not c.disponible or c.casos.empty:
            continue
        d = c.casos
        out.append(pd.DataFrame({
            "tipo": TIPOS["dato"], "situacion": d["detalle"].values, "accion": f"{c.accion} ({c.donde})",
            "embarque": d["registro"].values, "responsable": d["responsable"].values, "etd": d["fecha"].values,
            "solapa": d["solapa"].values, "prioridad": "Media" if c.severidad == "bad" else "Baja",
        }))
    return out


def enriquecer(df: pd.DataFrame, planif: pd.DataFrame | None, eh: pd.DataFrame | None) -> pd.DataFrame:
    """Suma SO y proveedor de cada embarque: Planificación (en curso) y Embarques Históricos (cerrados)."""
    if df.empty:
        return df
    partes = []
    for src in (planif, eh):
        if src is not None and len(src) and "embarque" in src and "so" in src:
            cols = ["embarque", "so"] + (["proveedor"] if "proveedor" in src else [])
            partes.append(src[cols].dropna(subset=["embarque"]))
    if not partes:
        return df
    m = pd.concat(partes, ignore_index=True)
    m["_k"] = id_key(m["embarque"])

    def junta(s, limite=3):
        vals = sorted({str(v) for v in s.dropna() if str(v).strip()})
        if not vals:
            return None
        return ", ".join(vals[:limite]) + (f" +{len(vals) - limite}" if len(vals) > limite else "")

    agg = {"so": junta}
    if "proveedor" in m:
        agg["proveedor"] = junta
    g = m.groupby("_k").agg(agg)
    k = id_key(df["embarque"].astype(str))
    df = df.copy()
    df["so"] = k.map(g["so"])
    if "proveedor" in g:
        df["proveedor"] = k.map(g["proveedor"])
    return df


def armar(partes: list[pd.DataFrame]) -> pd.DataFrame:
    partes = [p for p in partes if p is not None and len(p)]
    if not partes:
        return pd.DataFrame(columns=COLUMNAS)
    df = pd.concat(partes, ignore_index=True, sort=False)
    for c in COLUMNAS:
        if c not in df:
            df[c] = None
    df["prioridad"] = pd.Categorical(df["prioridad"], categories=PRIORIDADES, ordered=True)
    df = df.sort_values(["prioridad", "etd"], na_position="last").reset_index(drop=True)
    df["prioridad"] = df["prioridad"].astype(str)
    return df[COLUMNAS]


def resumen_situaciones(df: pd.DataFrame) -> pd.DataFrame:
    """Casos por tipo de acción, ordenados por cantidad (para la franja «Necesita atención»)."""
    if df.empty:
        return pd.DataFrame(columns=["tipo", "casos", "alta"])
    g = df.groupby("tipo").agg(casos=("tipo", "size"), alta=("prioridad", lambda s: int((s == "Alta").sum())))
    return g.sort_values(["alta", "casos"], ascending=False).reset_index()
