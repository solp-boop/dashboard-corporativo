"""Dashboard Ejecutivo · Comercio Exterior / Logística Internacional.

Punto de entrada. Ejecutar con:  streamlit run streamlit_app.py
"""
from __future__ import annotations

import streamlit as st

st.set_page_config(
    page_title="Dashboard Ejecutivo · Comex",
    page_icon="🚢",
    layout="wide",
    initial_sidebar_state="expanded",
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
from components.layout import guard, load_css, page_header  # noqa: E402
from services.data_loader import SourceError, clear_cache, get_data  # noqa: E402
from utils.logger import get_logger  # noqa: E402
from views import (  # noqa: E402
    accion, buscar, calidad, costos, lead_times, operacion, panorama,
)

log = get_logger("app")
load_css()

PAGE_BUSCAR = st.Page(buscar.render, title="Buscar SO / embarque", icon=":material/search:", url_path="buscar")
PAGES = {
    "General": [
        st.Page(panorama.render, title="Panorama", icon=":material/dashboard:", url_path="panorama", default=True),
    ],
    "Análisis": [
        st.Page(lead_times.render, title="Tiempos", icon=":material/timer:", url_path="sla"),
        st.Page(costos.render, title="Costos y captura", icon=":material/payments:", url_path="fletes"),
        st.Page(operacion.render, title="Operación en curso", icon=":material/directions_boat:", url_path="embarques"),
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
    # Buscador fijo: lleva a la ficha de la operación desde cualquier página.
    def _buscar_global():
        q = (st.session_state.get("global_q") or "").strip()
        if q:
            st.session_state["search_q"] = q
            st.session_state["_ir_a_buscar"] = True

    st.text_input("Buscar SO / embarque", key="global_q", placeholder="SO-12345 o FCL 2544",
                  label_visibility="collapsed", on_change=_buscar_global)
    if st.session_state.pop("_ir_a_buscar", False) and pg.url_path != "buscar":
        st.switch_page(PAGE_BUSCAR)
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

page_header(pg.title, bundle, filters)
with guard(pg.title):  # red de seguridad: un error inesperado nunca muestra un traceback
    pg.run()
