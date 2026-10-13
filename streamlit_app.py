"""El dashboard anterior se dio de baja: este enlace ahora lleva al dashboard nuevo.

El código anterior quedó en _dashboard_anterior/ (y en el historial de git) por si hace falta consultarlo.
"""
import streamlit as st

NUEVO = "https://dashboard-comex.streamlit.app/"

st.set_page_config(page_title="Dashboard Comex · se mudó", page_icon="🚢", layout="centered")
st.title("El dashboard se mudó")
st.write("Este dashboard se reemplazó por la versión nueva de **Comercio Exterior · Logística Internacional**, "
         "con la información actualizada.")
st.link_button("Ir al dashboard nuevo", NUEVO, type="primary")
st.caption(f"Guardá este enlace: {NUEVO}")
# Redirección automática (si el navegador la permite; si no, queda el botón).
st.html(f"<script>try {{ window.top.location.replace('{NUEVO}'); }} catch (e) {{}}</script>",
        unsafe_allow_javascript=True)
