import os
import subprocess
import sys

# TRUCO MAESTRO: Si la librería no aparece, la instalamos a la fuerza al arrancar
try:
    from st_gsheets_connection import GSheetsConnection
except ImportError:
    subprocess.check_call([sys.executable, "-m", "pip", "install", "st-gsheets-connection"])
    from st_gsheets_connection import GSheetsConnection

import streamlit as st

# Configuración de la página
st.set_page_config(page_title="Dashboard Corporativo", layout="wide")

st.title("📊 Panel de Control Gerencial")

# Conexión
try:
    conn = st.connection("gsheets", type=GSheetsConnection)
    
    # --- CONFIGURACIÓN DE PESTAÑAS ---
    # Cambia estos nombres por los de tus hojas reales si hace falta
    pestanas_reales = ["Hoja 1", "Hoja 2", "Hoja 3", "Hoja 4"]
    seleccion = st.sidebar.selectbox("Selecciona la pestaña de datos:", pestanas_reales)

    # Leer la hoja seleccionada
    df = conn.read(worksheet=seleccion)
    
    # Mostrar resultados
    st.subheader(f"Mostrando datos de: {seleccion}")
    st.metric("Total Filas", len(df))
    st.dataframe(df, use_container_width=True)

except Exception as e:
    st.error("⚠️ Error de conexión o configuración")
    st.write(f"Detalle: {e}")
    st.info("Revisa los 'Secrets' y que la hoja de Google sea pública.")
