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


# Marca <html data-theme="dark|light"> según el fondo que pinta Streamlit (claro u oscuro, lo elige cada usuario o
# su sistema). Así el CSS propio (tarjetas, matrices, gráficos) sigue al tema aunque se cambie desde ⋮ → Settings.
_TEMA_JS = """<script>(() => {
  if (window.__temaBidcom) return; window.__temaBidcom = true;
  const fijar = () => {
    const a = document.querySelector('.stApp'); if (!a) return;
    const m = getComputedStyle(a).backgroundColor.match(/[0-9.]+/g); if (!m) return;
    const t = (0.299 * m[0] + 0.587 * m[1] + 0.114 * m[2]) < 128 ? 'dark' : 'light';
    if (document.documentElement.dataset.theme !== t) document.documentElement.dataset.theme = t;
  };
  fijar(); setInterval(fijar, 700);
})();</script>"""


# Selector de tema a la vista (antes solo estaba en ⋮ → Settings). Escribe la misma preferencia que guarda Streamlit
# (localStorage «stActiveTheme-<ruta>-v2» = "Light" | "Dark" | "System") y recarga la página para aplicarla.
_TEMA_SWITCH = """<div class="tema-switch" id="tema-switch">
  <span class="tema-lbl">Tema</span>
  <button data-t="Light" title="Fondo blanco">☀ Claro</button>
  <button data-t="Dark" title="Fondo negro">☾ Oscuro</button>
  <button data-t="System" title="Igual que tu compu o celular">Auto</button>
</div>
<script>(() => {
  const PAGINAS = ["panorama", "sla", "fletes", "embarques", "equipo", "accion", "buscar", "calidad"];
  const ruta = window.location.pathname;
  const partes = ruta.replace(/\/+$/, "").split("/");
  const base = PAGINAS.includes(partes[partes.length - 1]) ? partes.slice(0, -1).join("/") + "/" : ruta;
  const rutas = new Set([ruta, base, base.replace(/\/+$/, "")]);
  PAGINAS.forEach(p => rutas.add(base + p));
  const clave = r => `stActiveTheme-${r}-v2`;
  let actual = "System";
  try { actual = JSON.parse(localStorage.getItem(clave(ruta))) || "System"; } catch (e) {}
  const caja = document.getElementById("tema-switch"); if (!caja || caja.dataset.listo) return;
  caja.dataset.listo = "1";
  caja.querySelectorAll("button").forEach(b => {
    if (b.dataset.t === actual) b.classList.add("on");
    b.addEventListener("click", () => {
      try { rutas.forEach(r => localStorage.setItem(clave(r), JSON.stringify(b.dataset.t))); } catch (e) {}
      window.location.reload();
    });
  });
})();</script>"""


def theme_switch() -> None:
    st.html(_TEMA_SWITCH, unsafe_allow_javascript=True)


def load_css() -> None:
    css = (ASSETS / "styles.css").read_text(encoding="utf-8")
    oscuro = (ASSETS / "dark.css").read_text(encoding="utf-8")
    por_atributo = oscuro.replace("__VARS__", 'html[data-theme="dark"]').replace("__SEL__", 'html[data-theme="dark"]')
    por_sistema = oscuro.replace("__VARS__", 'html:not([data-theme="light"])') \
        .replace("__SEL__", 'html:not([data-theme="light"])')
    st.html(f"<style>{css}\n{por_atributo}\n@media (prefers-color-scheme: dark) {{\n{por_sistema}\n}}</style>"
            + _TEMA_JS, unsafe_allow_javascript=True)


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
                <h1>Dashboard <span class="page">· {esc(page_title)}</span></h1>
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
