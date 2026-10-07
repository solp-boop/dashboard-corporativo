"""Salud de datos: controles automáticos (health check) y completitud de cada solapa."""
from __future__ import annotations

import pandas as pd
import streamlit as st

from components.kpi_cards import KPI, kpi_row
from components.layout import guard, section
from components.tables import ColSpec, data_table
from services.data_loader import KEY_FIELDS
from utils import formatting as fmt
from utils.filters import apply_filters
from views._common import ctx, today
from config import settings
from utils import salud
from zoneinfo import ZoneInfo

ORDER = ["reservas", "historicas", "aereos", "planif", "emb_hist", "cotizaciones"]


def problem_rows(key: str, df: pd.DataFrame, fields: dict | None = None) -> pd.DataFrame:
    """Registros con campos clave vacíos, con la lista de lo que falta."""
    fields = {c: lbl for c, lbl in (fields if fields is not None else KEY_FIELDS.get(key, {})).items() if c in df}
    if not fields:
        return pd.DataFrame()
    id_col = "embarque" if "embarque" in df else ("so" if "so" in df else None)
    miss = df[list(fields)].isna()
    has = miss.any(axis=1)
    out = pd.DataFrame({
        "id": df.loc[has, id_col] if id_col else df.index[has],
        "faltan": miss[has].apply(lambda r: ", ".join(fields[c] for c in r.index if r[c]), axis=1),
        "n": miss[has].sum(axis=1),
    })
    if "etd" in df:
        out["etd"] = df.loc[has, "etd"]
    out["fila"] = df.loc[has, "_fila"].map(lambda v: str(int(v)) if pd.notna(v) else "") if "_fila" in df else ""
    return out.sort_values("n", ascending=False)


ESTADO_ICONO = {"OK": "🟢 OK", "A revisar": "🟡 A revisar", "Roto": "🔴 Roto", "Sin datos": "⚪ Sin datos"}


def _health_check(bundle) -> None:
    t = today()
    ctrls = salud.controles_cache(bundle, t)
    estado, n_mal, casos = salud.resumen(ctrls)
    disp = [c for c in ctrls if c.disponible]
    mod = bundle.source_modified.get("tablero") if bundle.source_modified else None
    section("¿Podemos confiar en los números?",
            "Controles automáticos sobre toda la planilla (no dependen de los filtros). Los casos también aparecen en "
            "la Bandeja de acción.")
    kpi_row([
        KPI("Estado general", {"ok": "Sano", "warn": "A revisar", "bad": "Hay datos rotos"}[estado],
            status=estado, help="Rojo si algún control encuentra datos rotos (fórmulas, fechas imposibles); "
                                "ámbar si solo hay datos incompletos o a revisar."),
        KPI("Controles con problemas", f"{n_mal} de {len(disp)}", status=estado),
        KPI("Casos a corregir", fmt.fmt_int(casos), status=estado if casos else "ok"),
        KPI("Última edición de la planilla",
            fmt.fmt_datetime(mod.astimezone(ZoneInfo(settings.TIMEZONE))).split()[0] if mod else "—"),
    ])
    tabla = pd.DataFrame([{"control": c.nombre, "detecta": c.detecta, "casos": c.n if c.disponible else None,
                           "estado": ESTADO_ICONO[c.estado], "solapa": c.solapas, "columna": c.columna,
                           "accion": c.accion,
                           "_orden": {"Roto": 0, "A revisar": 1, "OK": 2, "Sin datos": 3}[c.estado]} for c in ctrls])
    tabla = tabla.sort_values(["_orden", "casos"], ascending=[True, False])
    data_table(tabla, [
        ColSpec("estado", "Estado"), ColSpec("control", "Control"), ColSpec("casos", "Casos", "int"),
        ColSpec("solapa", "Solapa a corregir", width="medium"), ColSpec("columna", "Columna", width="medium"),
        ColSpec("accion", "Acción"), ColSpec("detecta", "Qué detecta", width="large"),
    ], key="salud_controles", filename="salud_de_datos_controles", search=False)
    con_casos = sorted([c for c in ctrls if c.disponible and c.n], key=lambda c: (c.severidad != "bad", -c.n))
    if not con_casos:
        return
    nombres = {c.clave: f"{ESTADO_ICONO[c.estado]} · {c.nombre} · {fmt.plural(c.n, 'caso')}" for c in con_casos}
    elegido = st.selectbox("Ver casos de", list(nombres), format_func=nombres.get, key="salud_ver")
    c = next(x for x in con_casos if x.clave == elegido)
    casos = c.casos.assign(fila=c.casos["fila"].map(lambda v: str(int(v)) if pd.notna(v) else ""))
    data_table(casos, [
        ColSpec("solapa", "Solapa"), ColSpec("registro", "Registro / columna"), ColSpec("fila", "Fila"),
        ColSpec("fecha", "Fecha", "date"), ColSpec("responsable", "Responsable"),
        ColSpec("detalle", "Detalle", width="large"),
    ], key=f"salud_{c.clave}", filename=f"salud_{c.clave}", search=c.n > 15,
        caption=f"Acción: {c.accion} · solapa {c.solapas}" + (f" · columna {c.columna}" if c.columna not in ("", "—") else "")
                + " · Fila = número de fila en la solapa")


def render() -> None:
    bundle, filters = ctx()
    if bundle.errors:
        with st.container(border=True):
            st.markdown("**Avisos de la carga**")
            for e in bundle.errors:
                st.caption(f"• {e}")

    with guard("Salud de datos"):
        _health_check(bundle)

    section("Completitud por solapa",
            f"Registros con fecha desde {pd.Timestamp(settings.SALUD_DESDE):%Y} (o sin fecha). En Reservas, los campos "
            "clave se controlan solo con la instrucción enviada y los problemas de formato solo con «ETD OK FFWW». "
            "Fila = número de fila en la solapa.")
    _completitud(bundle, filters)


def _completitud(bundle, filters) -> None:
    keys = [k for k in ORDER if bundle.quality.get(k) is not None]
    tabs = st.tabs([bundle.quality[k].tab or bundle.quality[k].title for k in keys] + ["Targets de SLA"])
    with tabs[-1]:
        _targets(bundle)
    for key, tab in zip(keys, tabs):
        q = bundle.quality[key]
        with tab:
            st.caption(q.title)
            with guard(f"Calidad {q.title}"):
                if not q.available:
                    st.warning(q.message or "Dataset no disponible.")
                    if q.missing_required:
                        st.caption("Columnas obligatorias faltantes: " + ", ".join(q.missing_required))
                    continue
                df = bundle.get(key)
                en_campos, en_prob = salud.alcance(key, df)
                base = df[en_campos]
                labels = {c: l for c, l in KEY_FIELDS.get(key, {}).items() if c in df}
                if key == "reservas":
                    labels.pop("f_instruccion", None)   # el alcance ya exige la instrucción
                fields = list(labels)
                completo = base[fields].notna().all(axis=1).mean() if len(base) and fields else float("nan")
                f = apply_filters(base, filters)
                complete_f = f[fields].notna().all(axis=1).mean() if len(f) and fields else float("nan")
                total_leido = q.rows_raw - q.rows_empty
                desde = pd.Timestamp(settings.SALUD_DESDE)
                alc = f"desde {desde:%Y}" + (" con instrucción enviada" if key == "reservas" else "")
                kpi_row([
                    KPI("Registros leídos", fmt.fmt_int(total_leido),
                        sub=f"{fmt.fmt_int(q.rows_empty)} filas vacías ignoradas"),
                    KPI("Excluidos", fmt.fmt_int(q.rows_filler + q.duplicates),
                        sub=f"<b>{fmt.fmt_int(q.rows_filler)}</b> sin datos / proyección · "
                            f"<b>{fmt.fmt_int(q.duplicates)}</b> duplicados"),
                    KPI("Controlados", fmt.fmt_int(len(base)), sub=f"de {fmt.fmt_int(q.rows_final)} válidos"),
                    KPI("% completos", fmt.fmt_pct(completo),
                        status="ok" if completo >= .9 else ("warn" if completo >= .7 else "bad"),
                        sub="con todos los campos clave"),
                    KPI("% completos (filtros)", fmt.fmt_pct(complete_f), sub=f"{fmt.fmt_int(len(f))} registros filtrados"),
                ])
                c1, c2 = st.columns([2, 3], gap="medium")
                with c1:
                    n = len(base)
                    rows = [{"campo": lbl, "faltan": int(base[c].isna().sum()),
                             "pct": base[c].isna().mean() if n else 0} for c, lbl in labels.items()]
                    if rows:
                        data_table(pd.DataFrame(rows).sort_values("faltan", ascending=False), [
                            ColSpec("campo", "Campo clave"), ColSpec("faltan", "Registros sin dato", "int"),
                            ColSpec("pct", "% sin dato", "pct"),
                        ], key=f"dq_fields_{key}", filename=f"calidad_campos_{key}", search=False,
                            caption=f"Registros {alc}")
                with c2:
                    fm = salud.formato(bundle)
                    fm = fm[fm["key"] == key]
                    issues = [{"tipo": r["tipo_txt"], "campo": r["campo"], "n": r["n"],
                               "filas": ", ".join(str(x) for x in r["filas"][:6])
                                        + (f" (+{len(r['filas']) - 6})" if len(r["filas"]) > 6 else "")}
                              for _, r in fm.iterrows()]
                    issues += [{"tipo": "Columna opcional faltante", "campo": c, "n": None, "filas": ""}
                               for c in q.missing_optional]
                    alc_p = f"desde {desde:%Y}" + (" con «ETD OK FFWW»" if key == "reservas" else "")
                    if issues:
                        data_table(pd.DataFrame(issues), [
                            ColSpec("tipo", "Problema"), ColSpec("campo", "Columna / cálculo"),
                            ColSpec("n", "Registros", "int"), ColSpec("filas", "Filas en la solapa", width="medium"),
                        ], key=f"dq_issues_{key}", filename=f"calidad_problemas_{key}", search=False,
                            caption=f"Registros {alc_p} · los valores no convertibles y fuera de rango se tratan "
                                    "como vacíos")
                    else:
                        st.caption(f"Sin problemas de formato en los registros {alc_p}.")
                prob = problem_rows(key, base, labels)
                if len(prob):
                    with st.expander(f"Ver {fmt.fmt_int(len(prob))} registros con campos clave vacíos"):
                        data_table(prob, [
                            ColSpec("id", "Registro"), ColSpec("fila", "Fila"), ColSpec("etd", "ETD", "date"),
                            ColSpec("faltan", "Campos vacíos", width="large"), ColSpec("n", "Cantidad", "int"),
                        ], key=f"dq_rows_{key}", filename=f"registros_incompletos_{key}")


def _targets(bundle) -> None:
    sla = bundle.sla_puertos
    st.caption("Targets de SLA por puerto (Validaciones)")
    if sla.empty:
        st.warning("No se encontró la tabla de targets; se usan los valores por defecto de config/settings.py.")
    else:
        data_table(sla, [
            ColSpec("puerto", "Puerto"), ColSpec("sla_consolidacion", "Consolidación (d)", "days"),
            ColSpec("sla_tt", "Tránsito (d)", "days"), ColSpec("sla_total", "Total (d)", "days"),
        ], key="dq_sla", filename="targets_sla", search=False)
