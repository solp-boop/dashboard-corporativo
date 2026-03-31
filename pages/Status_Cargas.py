import streamlit as st
import pandas as pd
import time

# 1. Configuración de página (Esto debe ser lo primero)
st.set_page_config(page_title="BIDCOM | Status Cargas", layout="wide")

# 2. Estilo BIDCOM
st.markdown("""
    <style>
    .main { background-color: #040911; color: #ffffff; }
    .metric-container { text-align: center; padding: 20px; }
    .label-massive { font-size: 24px; color: #00a8ff; letter-spacing: 5px; text-transform: uppercase; font-weight: 800; }
    .value-massive { font-size: 100px; font-weight: 900; color: #00a8ff; text-shadow: 0 0 30px rgba(0,168,255,0.5); }
    .bidcom-header {
        background: linear-gradient(135deg, #001f3f 0%, #003366 100%);
        padding: 30px; border-radius: 20px; text-align: center; margin-bottom: 30px;
    }
    </style>
    """, unsafe_allow_html=True)

# 3. Carga de Datos (Usando el GID de Reservas que pasaste)
try:
    base_url = "https://docs.google.com/spreadsheets/d/1uDV3-CK5aeb-PI81uNc54t4L50HhscHe5xkp-pL9SyI"
    
    # Cargamos Hoja 1 (Instrucciones) y Hoja 2 (Reservas)
    # Agregamos nocache para forzar la actualización
    df_inst = pd.read_csv(f"{base_url}/export?format=csv&gid=0&nocache={time.time()}")
    df_reserva = pd.read_csv(f"{base_url}/export?format=csv&gid=276804813&nocache={time.time()}")
    
    # Limpieza rápida de columnas
    df_inst.columns = df_inst.columns.str.strip()
    df_reserva.columns = df_reserva.columns.str.strip()

    # Procesar M3 de Instrucciones (Hoja 0)
    if 'M3 Total' in df_inst.columns:
        df_inst['M3 Total'] = df_inst['M3 Total'].astype(str).str.replace('.', '', regex=False).str.replace(',', '.', regex=False)
        df_inst['M3 Total'] = pd.to_numeric(df_inst['M3 Total'], errors='coerce').fillna(0)

    # Filtrar lo Instruido (Tiene fecha)
    df_inst['Fecha_Inst_DT'] = pd.to_datetime(df_inst['Fecha de Instruccion'], errors='coerce')
    df_valido = df_inst[df_inst['Fecha_Inst_DT'].notna()].copy()

    # --- RENDERIZADO ---
    st.markdown("<div class='bidcom-header'><h1>BIDCOM</h1><div style='color:#00a8ff; letter-spacing:5px;'>STATUS DE CARGAS</div></div>", unsafe_allow_html=True)

    # Métricas de Instrucción (Hoja 0)
    m1, m2, m3 = st.columns(3)
    with m1:
        st.markdown(f"<div class='metric-container'><p class='label-massive'>CANTIDAD DE SO</p><p class='value-massive'>{len(df_valido)}</p></div>", unsafe_allow_html=True)
    with m2:
        st.markdown(f"<div class='metric-container'><p class='label-massive'>VOLUMEN TOTAL</p><p class='value-massive'>{int(df_valido['M3 Total'].sum()):,}</p></div>", unsafe_allow_html=True)
    with m3:
        st.markdown(f"<div class='metric-container'><p class='label-massive'>PROVEEDORES</p><p class='value-massive'>{df_valido['Proveedor'].nunique()}</p></div>", unsafe_allow_html=True)

    st.markdown("<br><hr style='opacity:0.1'><br>", unsafe_allow_html=True)

    # Tabla de Reservas (Hoja 276804813)
    st.markdown("<h3 style='text-align:center; color:#00a8ff;'>DETALLE HOJA DE RESERVAS</h3>", unsafe_allow_html=True)
    st.dataframe(df_reserva, use_container_width=True)

except Exception as e:
    st.error(f"Error de conexión: {e}")
