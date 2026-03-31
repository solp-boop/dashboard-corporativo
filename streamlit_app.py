import streamlit as st
import pandas as pd
import plotly.express as px
from datetime import datetime

# --- CONFIGURACIÓN DE PÁGINA ---
st.set_page_config(page_title="BIDCOM | Dashboard Ejecutivo", layout="wide")

# --- DISEÑO BIDCOM (CSS) ---
st.markdown("""
    <style>
    .block-container { padding: 1rem 2rem; }
    .main { background-color: #040911; color: #ffffff; }
    .stButton>button {
        border-radius: 15px !important; color: white !important;
        width: 100%; height: 120px; font-weight: 800 !important; font-size: 18px !important;
        background: rgba(255, 255, 255, 0.03) !important; border: 1px solid rgba(255, 255, 255, 0.1) !important;
    }
    .stButton>button:hover { background-color: #003366 !important; border-color: #00a8ff !important; }
    .chart-title { text-align: center; letter-spacing: 2px; font-weight: bold; text-transform: uppercase; margin: 15px 0; }
    </style>
    """, unsafe_allow_html=True)

try:
    # 1. Carga de Datos
    base_url = "https://docs.google.com/spreadsheets/d/1uDV3-CK5aeb-PI81uNc54t4L50HhscHe5xkp-pL9SyI"
    GID_HOJA = "0" 
    csv_url = f"{base_url}/export?format=csv&gid={GID_HOJA}"
    df = pd.read_csv(csv_url)
    df.columns = df.columns.str.strip()

    # --- LIMPIEZA Y PROCESAMIENTO ---
    # Convertir M3 Total (Columna de volumen)
    if 'M3 Total' in df.columns:
        df['M3 Total'] = df['M3 Total'].astype(str).str.replace('.', '', regex=False).str.replace(',', '.', regex=False)
        df['M3 Total'] = pd.to_numeric(df['M3 Total'], errors='coerce').fillna(0)
    
    # Procesar Ranking Utilidad (Columna B / Índice 1)
    col_ranking = df.columns[1] # "Demanda Efectiva -Ranking Utilidad Total"
    df[col_ranking] = pd.to_numeric(df[col_ranking], errors='coerce')
    
    # Identificar Columnas Específicas
    col_so = df.columns[0]          # Columna A: SO
    col_fecha_prior = df.columns[99] # Columna CV: Fecha prioritaria (Aprox índice 99)
    col_monoprov = df.columns[93]    # Columna CP: ¿ES MONOPROVEEDOR? (Aprox índice 93)

    # Lógica de Fechas Proyecciones
    df['ETD'] = pd.to_datetime(df.iloc[:, 23], errors='coerce')
    df['ETA'] = pd.to_datetime(df.iloc[:, 24], errors='coerce')
    hoy = pd.Timestamp(datetime.now().date())
    
    # --- INTERFAZ ---
    st.markdown("<h1 style='text-align: center; color: #ffffff;'>BIDCOM</h1>", unsafe_allow_html=True)
    tabs = st.tabs(["ORIGEN", "STATUS CARGAS", "INDICADORES", "AGENTES", "ANALISTAS", "FLETES"])

    with tabs[0]:
        # Métricas principales (simplificadas para este ejemplo)
        m1, m2, m3 = st.columns(3)
        m1.metric("CANTIDAD DE SO", len(df))
        m2.metric("VOLUMEN TOTAL", f"{int(df['M3 Total'].sum()):,} M3")
        m3.metric("PROVEEDORES", df['Proveedor'].nunique() if 'Proveedor' in df.columns else 0)

        st.markdown("<br>", unsafe_allow_html=True)

        # --- BOTONES DE ACCIÓN ---
        # Añadimos el tercer botón para el Ranking Top 100
        b1, b2, b3 = st.columns(3)
        
        with b1:
            if st.button("CONSOLIDADO \n INSTRUIDO"):
                st.session_state.vista = 'instruido'
        with b2:
            if st.button("PENDIENTE \n INSTRUCCIÓN"):
                st.session_state.vista = 'pendiente'
        with b3:
            if st.button("🔥 PRODUCTOS \n TOP RANKING (1-100)"):
                st.session_state.vista = 'ranking'

        # --- LÓGICA DE DESPLIEGUE DE TABLAS ---
        if 'vista' in st.session_state:
            st.markdown("---")
            if st.session_state.vista == 'ranking':
                st.subheader("🚀 Top 100 SO: Prioridad Máxima de Salida")
                
                # Filtrar Top 100 por Utilidad (Columna B entre 1 y 100)
                df_top = df[(df[col_ranking] >= 1) & (df[col_ranking] <= 100)].copy()
                df_top = df_top.sort_values(by=col_ranking)
                
                # Seleccionar solo las columnas solicitadas
                columnas_ver = [col_so, col_ranking, col_fecha_prior, 'M3 Total', col_monoprov]
                # Asegurar que existan en el DF para evitar errores
                columnas_ver = [c for c in columnas_ver if c in df_top.columns]
                
                st.dataframe(df_top[columnas_ver].style.background_gradient(subset=[col_ranking], cmap='Reds_r'), use_container_width=True)
            
            elif st.session_state.vista == 'instruido':
                # (Lógica existente para instruidos)
                st.write("Mostrando Consolidados Instruidos...")
            
            elif st.session_state.vista == 'pendiente':
                # (Lógica existente para pendientes)
                st.write("Mostrando Pendientes de Instrucción...")

        # --- GRÁFICOS INFERIORES ---
        st.markdown("<br>", unsafe_allow_html=True)
        g1, g2, g3 = st.columns([1.2, 1, 1])
        # (Aquí iría el código de los gráficos de Puertos, ETD y ETA ajustado antes)

except Exception as e:
    st.error(f"Error al procesar el Ranking: {e}. Verifique que las columnas A, B, CP y CV existan en la base.")
