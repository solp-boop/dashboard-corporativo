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


def problem_rows(key: str, df: pd.DataFrame) -> pd.DataFrame:
    """Registros con campos clave vacíos, con la lista de lo que falta."""
    fields = {c: lbl for c, lbl in KEY_FIELDS.get(key, {}).items() if c in df}
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
                           "estado": ESTADO_ICONO[c.estado], "donde": c.donde, "accion": c.accion,
                           "_orden": {"Roto": 0, "A revisar": 1, "OK": 2, "Sin datos": 3}[c.estado]} for c in ctrls])
    tabla = tabla.sort_values(["_orden", "casos"], ascending=[True, False])
    data_table(tabla, [
        ColSpec("estado", "Estado"), ColSpec("control", "Control"), ColSpec("casos", "Casos", "int"),
        ColSpec("detecta", "Qué detecta", width="large"), ColSpec("donde", "Dónde se corrige"),
        ColSpec("accion", "Acción"),
    ], key="salud_controles", filename="salud_de_datos_controles", search=False)
    con_casos = sorted([c for c in ctrls if c.disponible and c.n], key=lambda c: (c.severidad != "bad", -c.n))
    if not con_casos:
        return
    nombres = {c.clave: f"{ESTADO_ICONO[c.estado]} · {c.nombre} · {fmt.plural(c.n, 'caso')}" for c in con_casos}
    elegido = st.selectbox("Ver casos de", list(nombres), format_func=nombres.get, key="salud_ver")
    c = next(x for x in con_casos if x.clave == elegido)
    data_table(c.casos, [
        ColSpec("solapa", "Solapa"), ColSpec("registro", "Registro / columna"), ColSpec("fecha", "Fecha", "date"),
        ColSpec("responsable", "Responsable"), ColSpec("detalle", "Detalle", width="large"),
    ], key=f"salud_{c.clave}", filename=f"salud_{c.clave}", search=c.n > 15,
        caption=f"Acción: {c.accion} · se corrige en {c.donde}")


def render() -> None:
    bundle, filters = ctx()
    if bundle.errors:
        with st.container(border=True):
            st.markdown("**Avisos de la carga**")
            for e in bundle.errors:
                st.caption(f"• {e}")

    with guard("Salud de datos"):
        _health_check(bundle)

    section("Completitud por solapa", "Registros leídos, excluidos y % con todos los campos clave. Las cifras de «base "
            "completa» no dependen de los filtros.")
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
                f = apply_filters(df, filters)
                fields = [c for c in KEY_FIELDS.get(key, {}) if c in f]
                complete_f = f[fields].notna().all(axis=1).mean() if len(f) and fields else float("nan")
                total_leido = q.rows_raw - q.rows_empty
                kpi_row([
                    KPI("Registros leídos", fmt.fmt_int(total_leido),
                        sub=f"{fmt.fmt_int(q.rows_empty)} filas vacías ignoradas"),
                    KPI("Excluidos", fmt.fmt_int(q.rows_filler + q.duplicates),
                        sub=f"<b>{fmt.fmt_int(q.rows_filler)}</b> sin datos / proyección · "
                            f"<b>{fmt.fmt_int(q.duplicates)}</b> duplicados"),
                    KPI("Registros válidos", fmt.fmt_int(q.rows_final)),
                    KPI("% completos (base)", fmt.fmt_pct(q.complete_pct),
                        status="ok" if q.complete_pct >= .9 else ("warn" if q.complete_pct >= .7 else "bad"),
                        sub="Con todos los campos clave"),
                    KPI("% completos (filtros)", fmt.fmt_pct(complete_f), sub=f"{fmt.fmt_int(len(f))} registros filtrados"),
                ])
                c1, c2 = st.columns(2, gap="medium")
                with c1:
                    rows = [{"campo": k, "faltan": v, "pct": v / q.rows_final if q.rows_final else 0}
                            for k, v in q.missing_key_fields.items()]
                    data_table(pd.DataFrame(rows).sort_values("faltan", ascending=False), [
                        ColSpec("campo", "Campo clave"), ColSpec("faltan", "Registros sin dato", "int"),
                        ColSpec("pct", "% sin dato", "pct"),
                    ], key=f"dq_fields_{key}", filename=f"calidad_campos_{key}", search=False)
                with c2:
                    issues = [{"tipo": "Valor no convertible", "campo": k, "n": v} for k, v in q.invalid_values.items()]
                    issues += [{"tipo": "Fuera de rango", "campo": k, "n": v} for k, v in q.out_of_range.items()]
                    issues += [{"tipo": "Columna opcional faltante", "campo": c, "n": None} for c in q.missing_optional]
                    issues = [{"tipo": f"Error de fórmula ({v})", "campo": c, "n": n}
                              for c, (n, v, _) in q.error_cells.items()] + issues
                    if issues:
                        data_table(pd.DataFrame(issues), [
                            ColSpec("tipo", "Problema"), ColSpec("campo", "Columna / cálculo"),
                            ColSpec("n", "Registros", "int"),
                        ], key=f"dq_issues_{key}", filename=f"calidad_problemas_{key}", search=False,
                            caption="Los valores no convertibles y fuera de rango se tratan como vacíos")
                    else:
                        st.caption("Sin problemas de formato detectados.")
                prob = problem_rows(key, df)
                if len(prob):
                    with st.expander(f"Ver {fmt.fmt_int(len(prob))} registros con campos clave vacíos"):
                        data_table(prob, [
                            ColSpec("id", "Registro"), ColSpec("etd", "ETD", "date"),
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
