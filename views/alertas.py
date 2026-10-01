"""Alertas: embarques en curso que requieren acción, con el motivo."""
from __future__ import annotations

import numpy as np
import pandas as pd

from components.kpi_cards import KPI, kpi_row
from components.layout import empty, guard, section
from components.tables import ColSpec, data_table
from config import settings
from utils import calculations as calc
from utils import formatting as fmt
from views._common import ctx, en_curso, today

# Tipos de alerta (clave, título de la tarjeta).
TIPOS = [
    ("etd", "ETD sin confirmar"),
    ("docs", "Zarpados sin documentación"),
    ("cons", "Consolidación fuera de SLA"),
    ("sin_etd", "Instruidos sin ETD"),
]


def alerts(res: pd.DataFrame) -> pd.DataFrame:
    """Embarques en curso que requieren acción, con el motivo y el tipo de alerta."""
    t = today()
    horizon = t + pd.Timedelta(days=settings.ALERT_HORIZON_DAYS)
    upcoming = res["etd"].between(t, horizon)
    reasons = pd.Series([[] for _ in range(len(res))], index=res.index)
    tipos = pd.Series([[] for _ in range(len(res))], index=res.index)

    def add(mask, tipo, text):
        for i in res.index[mask.fillna(False)]:
            reasons[i] = reasons[i] + [text if isinstance(text, str) else text(res.loc[i])]
            tipos[i] = tipos[i] + [tipo]

    mar = res["grupo_modo"] == "Marítimo" if "grupo_modo" in res else pd.Series(True, index=res.index)
    add(upcoming & ~res["etd_ok"].fillna(False).astype(bool), "etd", "ETD sin confirmar por el forwarder")
    docs_missing = mar & ((res["draft_bl"].fillna("NO").astype(str).str.upper() != "SI") |
                          (res["pl_final"].fillna("NO").astype(str).str.upper() != "SI"))
    sailed = res["etd"].between(t - pd.Timedelta(days=30), t - pd.Timedelta(days=3))
    add(sailed & docs_missing, "docs", "Zarpó hace más de 3 días sin Draft BL / Packing list final")
    future = res["etd"] >= t
    add(future & mar & (res["estado_consolidacion"] == calc.SEMAFORO_BAD), "cons",
        lambda r: f"Consolidación proyectada {fmt.fmt_int(r['dias_consolidacion'])} d "
                  f"(SLA {fmt.fmt_int(r['sla_consolidacion'])} d)")
    add(res["etd"].isna() & res["f_instruccion"].notna(), "sin_etd", "Instruido sin ETD cargado")

    out = res[reasons.map(len) > 0].copy()
    out["motivo"] = reasons[out.index].map(" · ".join)
    out["tipos"] = tipos[out.index]
    out["n_motivos"] = reasons[out.index].map(len)
    days_to = (out["etd"] - t).dt.days
    out["prioridad"] = np.where(days_to.le(3) | (out["n_motivos"] >= 2), "Alta", "Media")
    return out.sort_values(["prioridad", "etd"], ascending=[True, True])


def render() -> None:
    bundle, filters = ctx()
    section("Alertas",
            f"Embarques en curso que requieren acción: ETD en los próximos {settings.ALERT_HORIZON_DAYS} días "
            "sin confirmar, zarpados sin documentación, consolidación proyectada fuera de SLA o instruidos sin ETD. "
            "Prioridad alta: sale en 3 días o menos, o tiene más de un motivo.")
    with guard("Alertas"):
        res, _ = en_curso(bundle, filters)
        if res.empty:
            empty()
            return
        al = alerts(res)
        if al.empty:
            empty("No hay alertas para los filtros seleccionados.")
            return

        n_alta = int((al["prioridad"] == "Alta").sum())
        cards = [KPI("Embarques con alerta", fmt.fmt_int(len(al)),
                     sub=f"<b>{fmt.fmt_int(n_alta)}</b> de prioridad alta",
                     status="bad" if n_alta else "warn")]
        for key, label in TIPOS:
            n = int(al["tipos"].map(lambda ts, k=key: k in ts).sum())
            cards.append(KPI(label, fmt.fmt_int(n), status="warn" if n else "ok"))
        kpi_row(cards)

        data_table(al, [
            ColSpec("prioridad", "Prioridad"),
            ColSpec("embarque", "Embarque"),
            ColSpec("grupo_modo", "Modo"),
            ColSpec("motivo", "Motivo", width="large"),
            ColSpec("etd", "ETD", "date"),
            ColSpec("forwarder", "Forwarder"),
            ColSpec("puerto", "Puerto"),
            ColSpec("responsable", "Responsable"),
            ColSpec("m3", "M3", "num"),
            ColSpec("estado_consolidacion", "Consolidación", "status"),
        ], key="alertas", filename="alertas_embarques")
