"""Calidad de datos: ¿el indicador da mal porque la base está incompleta?"""
from __future__ import annotations

import pandas as pd
import streamlit as st

from components.kpi_cards import KPI, kpi_row
from components.layout import guard, section
from components.tables import ColSpec, data_table
from services.data_loader import KEY_FIELDS
from utils import formatting as fmt
from utils.filters import apply_filters
from views._common import ctx

ORDER = ["reservas", "historicas", "aereos", "planif", "cotizaciones"]


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


def render() -> None:
    bundle, filters = ctx()
    st.caption("Las cifras de «base completa» no dependen de los filtros. "
               "El % completo con filtros ayuda a saber si un KPI puntual está afectado.")
    if bundle.errors:
        with st.container(border=True):
            st.markdown("**Avisos de la carga**")
            for e in bundle.errors:
                st.caption(f"• {e}")

    for key in ORDER:
        q = bundle.quality.get(key)
        if q is None:
            continue
        section(q.title, f"Solapa «{q.tab}»" if q.tab else "")
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

    sla = bundle.sla_puertos
    section("Targets de SLA por puerto (Validaciones)")
    if sla.empty:
        st.warning("No se encontró la tabla de targets; se usan los valores por defecto de config/settings.py.")
    else:
        data_table(sla, [
            ColSpec("puerto", "Puerto"), ColSpec("sla_consolidacion", "Consolidación (d)", "days"),
            ColSpec("sla_tt", "Tránsito (d)", "days"), ColSpec("sla_total", "Total (d)", "days"),
        ], key="dq_sla", filename="targets_sla", search=False)
