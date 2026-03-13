import streamlit as st
from streamlit_gsheets import GSheetsConnection

# Configuración visual de alta gama
st.set_page_config(page_title="Dashboard Gerencial", layout="wide")

st.title("📊 Panel Control Corporativo")
st.markdown("---")

# Creamos la conexión con Google Sheets
conn = st.connection("gsheets", type=GSheetsConnection)

# --- MENÚ LATERAL ---
with st.sidebar:
    st.image("https://cdn-icons-png.flaticon.com/512/1063/1063196.png", width=100)
    st.header("Navegación")
    
    # IMPORTANTE: Aquí escribe los nombres EXACTOS de tus pestañas de Google Sheets
    # Por ejemplo: ["Ventas", "Gastos", "Inventario"]
    opciones = ["Hoja 1", "Hoja 2", "Hoja 3", "Hoja 4"]
    
    seleccion = st.selectbox("Selecciona la pestaña:", opciones)
    st.info("La información se actualiza en tiempo real desde la fuente.")

# --- CUERPO DEL DASHBOARD ---
try:
    # Leemos la pestaña seleccionada
    df = conn.read(worksheet=seleccion)
    
    # Mostramos métricas rápidas si hay datos
    if not df.empty:
        st.subheader(f"📂 Datos de: {seleccion}")
        
        # Una pequeña ayuda visual: total de filas
        st.metric(label="Total de Registros", value=len(df))
        
        # Mostramos la tabla interactiva
        st.dataframe(df, use_container_width=True)
    else:
        st.warning("La pestaña seleccionada está vacía.")

except Exception as e:
    st.error("⚠️ Error de conexión")
    st.write("Verifica que los 'Secrets' en Streamlit tengan el link correcto y que la hoja sea pública.")
