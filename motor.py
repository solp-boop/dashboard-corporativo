import streamlit as st
from st_gsheets_connection import GSheetsConnection

# Configuración de la página
st.set_page_config(page_title="Dashboard Corporativo", layout="wide")

st.title("📊 Panel de Control Gerencial")

# Conexión
conn = st.connection("gsheets", type=GSheetsConnection)

# --- CONFIGURACIÓN DE PESTAÑAS ---
# IMPORTANTE: Si tus hojas tienen nombres distintos, cámbialos aquí:
pestanas_reales = ["Hoja 1", "Hoja 2", "Hoja 3", "Hoja 4"]
seleccion = st.sidebar.selectbox("Selecciona la pestaña de datos:", pestanas_reales)

try:
    # Leer la hoja seleccionada
    df = conn.read(worksheet=seleccion)
    
    # Mostrar resultados
    st.subheader(f"Mostrando datos de: {seleccion}")
    st.metric("Total Filas", len(df))
    st.dataframe(df, use_container_width=True)

except Exception as e:
    st.error("⚠️ Error al conectar con Google Sheets")
    st.info("Asegúrate de que el enlace en 'Secrets' sea el correcto y que el archivo de Google sea público.")
