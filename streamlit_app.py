"""Dashboard Ejecutivo · Comercio Exterior / Logística Internacional.

Punto de entrada. Ejecutar con:  streamlit run streamlit_app.py
"""
from __future__ import annotations


def _limitar_arenas_malloc() -> None:
    """Causa real de «la app superó sus límites de recursos» en Streamlit Cloud.

    Streamlit corre cada ejecución en un hilo nuevo y glibc le da a cada hilo su propia «arena» de memoria; lo
    que pandas libera queda repartido en esas arenas y el proceso nunca lo devuelve (medido: +50 MB por cada
    recorrida de páginas, sin techo). Con 2 arenas la memoria queda plana (≈325 MB). Equivale a la variable de
    entorno MALLOC_ARENA_MAX=2, que Streamlit Cloud no permite fijar antes de arrancar el proceso.
    """
    import ctypes
    try:
        libc = ctypes.CDLL("libc.so.6")
        libc.mallopt(-8, 2)            # M_ARENA_MAX: solo sirve si todavía no se crearon hilos
        libc.mallopt(-3, 64 * 1024)    # M_MMAP_THRESHOLD: bloques ≥64 KB (arrays de pandas) van por mmap y se devuelven al liberarse
    except Exception:  # noqa: BLE001 · fuera de Linux/glibc no existe; no es un error
        pass


_limitar_arenas_malloc()

import streamlit as st  # noqa: E402

st.set_page_config(
    page_title="Dashboard · Comex",
    page_icon="🚢",
    layout="wide",
    initial_sidebar_state="auto",   # abierta en compu, cerrada en el celular
)


def _reload_si_cambio_el_codigo() -> None:
    """Streamlit Cloud baja el código nuevo pero no siempre recarga los módulos ya importados.

    Si cambió algún .py del proyecto desde la última ejecución, se recargan (config → utils →
    services → components → views) para que el cambio se vea sin reiniciar la app.
    """
    import hashlib
    import importlib
    import pathlib
    import sys

    root = pathlib.Path(__file__).parent
    pkgs = ("config", "utils", "services", "components", "views")
    h = hashlib.md5()
    for pkg in pkgs:
        for f in sorted((root / pkg).glob("*.py")):
            h.update(f.name.encode())
            h.update(str(f.stat().st_mtime_ns).encode())
    firma = h.hexdigest()
    store = sys.modules.setdefault("_firma_codigo", type(sys)("_firma_codigo"))
    if getattr(store, "valor", None) not in (None, firma):
        for pkg in pkgs:
            for name in sorted(n for n in list(sys.modules) if n == pkg or n.startswith(pkg + ".")):
                try:
                    importlib.reload(sys.modules[name])
                except Exception:  # noqa: BLE001 — un módulo que no recarga no debe tirar la app
                    pass
    store.valor = firma


_reload_si_cambio_el_codigo()

from components.filters import render_filters  # noqa: E402
from components.layout import guard, load_css, page_header, theme_switch  # noqa: E402
from services.data_loader import SourceError, clear_cache, get_data  # noqa: E402
from utils.logger import get_logger  # noqa: E402
from views import (  # noqa: E402
    accion, buscar, calidad, costos, equipo, lead_times, operacion, panorama,
)

log = get_logger("app")
load_css()



PAGE_BUSCAR = st.Page(buscar.render, title="Buscador Comex", icon=":material/search:", url_path="buscar")
PAGES = {
    "General": [
        st.Page(panorama.render, title="Panorama", icon=":material/dashboard:", url_path="panorama", default=True),
    ],
    "Análisis": [
        st.Page(lead_times.render, title="Tiempos", icon=":material/timer:", url_path="sla"),
        st.Page(costos.render, title="Costos y captura", icon=":material/payments:", url_path="fletes"),
        st.Page(operacion.render, title="Operación en curso", icon=":material/directions_boat:", url_path="embarques"),
        st.Page(equipo.render, title="Equipo y agentes", icon=":material/groups:", url_path="equipo"),
    ],
    "Acción": [
        st.Page(accion.render, title="Bandeja de acción", icon=":material/task_alt:", url_path="accion"),
        PAGE_BUSCAR,
        st.Page(calidad.render, title="Salud de datos", icon=":material/health_and_safety:", url_path="calidad"),
    ],
}

pg = st.navigation(PAGES, position="sidebar")

with st.sidebar:
    st.markdown('<div class="side-brand">BIDCOM · Comex</div>'
                '<div class="side-sub">Logística internacional</div>', unsafe_allow_html=True)
    theme_switch()
    # Buscador Comex: desde cualquier página abre una ventana con los resultados (SO, embarque o producto / SKU).
    def _buscar_global():
        q = (st.session_state.get("global_q") or "").strip()
        if q:
            st.session_state["bc_q"] = q
            st.session_state["_abrir_buscador"] = True

    st.markdown('<div class="side-label">🔎 Buscador Comex</div>', unsafe_allow_html=True)
    st.text_input("Buscador Comex", key="global_q", placeholder="SO, embarque, SKU o producto…",
                  label_visibility="collapsed", on_change=_buscar_global,
                  help="Ej.: 38529 · FCL 2679 · AIR 199 · RCDJI070 · osmo action. Enter para buscar.")
    if st.button("Abrir buscador", icon=":material/search:", width="stretch"):
        st.session_state["_abrir_buscador"] = True
    if st.button("↻  Actualizar datos", width="stretch", type="primary",
                 help="Vuelve a consultar la planilla (los datos se refrescan solos cada 10 minutos)."):
        clear_cache()
        st.rerun()

try:
    bundle = get_data()
except SourceError as exc:
    page_header(pg.title, None, None)
    st.error(f"No se pudieron cargar los datos. {exc}")
    st.caption("Probá con «Actualizar datos». Si el problema sigue, revisá la configuración de "
               "credenciales (ver README).")
    st.stop()

with st.sidebar:
    filters = render_filters(bundle)
    if bundle.errors:
        with st.expander("Avisos de la carga", expanded=False):
            for e in bundle.errors:
                st.caption(f"• {e}")

if st.session_state.pop("_abrir_buscador", False):
    with guard("Buscador Comex"):
        buscar.dialogo()

page_header(pg.title, bundle, filters)
with guard(pg.title):  # red de seguridad: un error inesperado nunca muestra un traceback
    pg.run()


def _liberar_memoria() -> None:
    """Devuelve al sistema la memoria que pandas ya liberó. Sin esto, en Streamlit Cloud (≈1 GB) la memoria del
    proceso solo crece con cada interacción y la app se cae por «superó sus límites de recursos»."""
    import ctypes
    import gc
    gc.collect()
    try:
        ctypes.CDLL("libc.so.6").malloc_trim(0)
    except Exception:  # noqa: BLE001 · fuera de Linux no existe; no es un error
        pass


_liberar_memoria()
