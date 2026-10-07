"""Piezas de layout: cabecera, secciones, avisos y manejo seguro de errores."""
from __future__ import annotations

import html
from contextlib import contextmanager
from pathlib import Path

import streamlit as st

from services.data_loader import DataBundle
from utils import formatting as fmt
from utils.filters import FilterState, not_applicable
from utils.logger import get_logger

log = get_logger("ui")
ASSETS = Path(__file__).resolve().parent.parent / "assets"


def load_css() -> None:
    css = (ASSETS / "styles.css").read_text(encoding="utf-8")
    st.markdown(f"<style>{css}</style>", unsafe_allow_html=True)


def esc(v) -> str:
    return html.escape(str(v))


def _salud_html(bundle) -> str:
    """Semáforo de salud de datos para el encabezado (enlaza a Salud de datos). Nunca rompe la página."""
    try:
        import pandas as pd
        from utils import salud
        estado, n_mal, casos = salud.resumen(salud.controles_cache(bundle, pd.Timestamp.today().normalize()))
    except Exception:
        return ""
    txt = ("Datos: sin problemas" if estado == "ok" else
           f"Datos: {n_mal} {'control' if n_mal == 1 else 'controles'} con problemas · {fmt.fmt_int(casos)} casos")
    return f'<br><a class="health {estado}" href="calidad" target="_self"><i></i>{esc(txt)}</a>'


def page_header(page_title: str, bundle: DataBundle | None, filters: FilterState | None) -> None:
    meta = ""
    if bundle is not None:
        modified = bundle.source_modified.get("tablero")
        mod_txt = ""
        if modified is not None:
            from zoneinfo import ZoneInfo
            from config import settings

            mod_txt = (f"<br>Última edición de la planilla: <b>"
                       f"{fmt.fmt_datetime(modified.astimezone(ZoneInfo(settings.TIMEZONE)))}</b>")
        meta = (f"Última actualización de datos: <b>{fmt.fmt_datetime(bundle.loaded_at)}</b>"
                f"{mod_txt}{_salud_html(bundle)}")
    ftxt = f'<div class="filters">{esc(filters.describe())}</div>' if filters else ""
    st.markdown(
        f"""<div class="dash-header">
              <div>
                <p class="eyebrow">Comercio Exterior · Logística Internacional</p>
                <h1>Dashboard Ejecutivo <span class="page">· {esc(page_title)}</span></h1>
              </div>
              <div class="meta">{meta}{ftxt}</div>
            </div>""",
        unsafe_allow_html=True,
    )
    if bundle is not None and bundle.stale:
        st.warning("No se pudo consultar la planilla. Se muestran los últimos datos cargados. "
                   + " ".join(bundle.errors[:1]))


def section(title: str, subtitle: str = "") -> None:
    st.markdown(f'<div class="section-title">{esc(title)}</div>', unsafe_allow_html=True)
    if subtitle:
        st.markdown(f'<div class="section-sub">{esc(subtitle)}</div>', unsafe_allow_html=True)


def block(num: int, title: str, subtitle: str = "") -> None:
    """Bloque principal de una página larga (Resumen): número + título con separador."""
    st.markdown(f'<div class="block-title"><span class="block-num">{num}</span>{esc(title)}</div>',
                unsafe_allow_html=True)
    if subtitle:
        st.markdown(f'<div class="section-sub">{esc(subtitle)}</div>', unsafe_allow_html=True)


def subsection(title: str, subtitle: str = "") -> None:
    """Sub-bloque dentro de una sección."""
    st.markdown(f'<div class="subsection-title">{esc(title)}</div>', unsafe_allow_html=True)
    if subtitle:
        st.markdown(f'<div class="section-sub">{esc(subtitle)}</div>', unsafe_allow_html=True)


def chart_title(title: str, subtitle: str = "") -> None:
    st.markdown(f'<div class="chart-title">{esc(title)}</div>'
                + (f'<div class="chart-sub">{esc(subtitle)}</div>' if subtitle else ""),
                unsafe_allow_html=True)


def empty(msg: str = "No hay datos para los filtros seleccionados.") -> None:
    st.markdown(f'<div class="empty">{esc(msg)}</div>', unsafe_allow_html=True)


def coverage(n: int, total: int, what: str = "operaciones", detail: str = "") -> None:
    """'Datos disponibles: 3 de 50 operaciones' (resaltado si la cobertura es baja)."""
    from config import settings

    low = total > 0 and (n < settings.MIN_SAMPLE or n / total < settings.MIN_COVERAGE)
    extra = f" · {esc(detail)}" if detail else ""
    cls = "coverage low" if low else "coverage"
    icon = "⚠ " if low else ""
    st.markdown(f'<div class="{cls}">{icon}Datos disponibles: {fmt.fmt_int(n)} de '
                f'{fmt.fmt_int(total)} {esc(what)}{extra}</div>', unsafe_allow_html=True)


def semaforo_legend() -> None:
    st.markdown(
        '<div class="legend-inline"><span><i class="dot ok"></i>Dentro de SLA</span>'
        '<span><i class="dot warn"></i>Atención (hasta +20 %)</span>'
        '<span><i class="dot bad"></i>Fuera de SLA</span></div>',
        unsafe_allow_html=True,
    )


def filter_notes(df, filters: FilterState, dataset_label: str) -> None:
    """Aclara qué filtros no aplican a este dataset."""
    na = not_applicable(df, filters)
    notes = []
    if na:
        notes.append(f"{dataset_label} no tiene {', '.join(na)}: ese filtro no se aplica acá.")
    # Los registros sin fecha se informan en Calidad de datos, no arriba de cada página.
    if notes:
        st.caption(" ".join(notes))


def require(bundle: DataBundle, key: str):
    """Devuelve el dataset o muestra un mensaje claro y devuelve None."""
    q = bundle.quality.get(key)
    if bundle.available(key):
        return bundle.get(key)
    title = q.title if q else key
    msg = (q.message if q and q.message else "El dataset no está disponible.")
    st.info(f"**{title}**: no se pueden mostrar estos indicadores. {msg}")
    return None


@contextmanager
def guard(name: str):
    """Aísla una sección: si falla, muestra un aviso amable y sigue el resto."""
    try:
        yield
    except KeyError as exc:
        log.exception("Sección '%s': columna faltante %s", name, exc)
        st.info(f"No se pudo calcular «{name}» porque falta la columna {exc} en la planilla.")
    except Exception as exc:  # noqa: BLE001
        log.exception("Sección '%s' falló", name)
        st.info(f"No se pudo mostrar «{name}». El error quedó registrado ({type(exc).__name__}).")
