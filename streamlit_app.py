import streamlit as st
import pandas as pd

# Configuración de página
st.set_page_config(page_title="BICOM - Tablero Logística Internacional", layout="wide")

# --- IDENTIDAD CORPORATIVA BICOM (CSS CUSTOM) ---
st.markdown("""
    <style>
    /* Fondo General */
    .main { background-color: #f8f9fa; color: #1e1e1e; }
    
    /* Encabezado Principal */
    .main-header {
        background: linear-gradient(90deg, #003366 0%, #00509d 100%);
        color: white;
        padding: 2rem;
        border-radius: 10px;
        text-align: center;
        margin-bottom: 2rem;
        box-shadow: 0 4px 6px rgba(0,0,0,0.1);
    }

    /* Estilo de las Solapas (Tabs) */
    .stTabs [data-baseweb="tab-list"] {
        gap: 10px;
        justify-content: center;
    }
    .stTabs [data-baseweb="tab"] {
        background-color: #e9ecef;
        border-radius: 5px 5px 0 0;
        padding: 10px 25px;
        font-weight: 600;
        color: #003366;
    }
    .stTabs [aria-selected="true"] {
        background-color: #003366 !important;
        color: white !important;
    }

    /* Tarjetas de Métricas */
    div[data-testid="stMetric"] {
        background-color: white;
        padding: 20px;
        border-radius: 10px;
        box-shadow: 0 2px 4px rgba(0,0,0,0.05);
        border-left: 5px solid #d90429; /* Acento rojo Bicom */
    }
    div[data-testid="stMetricValue"] { color: #003366; font-size: 38px !important; }
    div[data-testid="stMetricLabel"] { color: #6c757d; font-weight: 700; text-transform: uppercase; }

    /* Títulos de Sección */
    .section-title {
        color: #003366;
        border-bottom: 2px solid #003366;
        padding-bottom: 5px;
        margin-top: 20px;
        margin-bottom: 20px;
        font-weight: 700;
    }
    </style>
    """, unsafe_allow_html=True)

try:
    # 1. Obtención de Datos
    base_url = "https://docs.google.com/spreadsheets/d/1uDV3-CK5aeb-PI81uNc54t4L50HhscHe5xkp-pL9SyI"
    GID_HOJA = "0" 
    csv_url = f"{base_url}/export?format=csv&gid={GID_HOJA}"
    
    df = pd.read_csv(csv_url)
    df.columns = df.columns.str.strip()

    # Limpieza M3
    if 'M3 Total' in df.columns:
        df['M3 Total'] = df['M3 Total'].astype(str).str.replace('.', '', regex=False).str.replace(',', '.', regex=False)
        df['M3 Total'] = pd.to_numeric(df['M3 Total'], errors='coerce').fillna(0)
    
    # Lógica Instrucción
    df['Instruido'] = df['Fecha de Instruccion'].notna() & (df['Fecha de Instruccion'].astype(str).str.upper() != 'SIN INSTRUCCION')

    # --- ENCABEZADO BICOM ---
    st.markdown("<div class='main-header'><h1>BICOM</h1><h3>TABLERO DE GESTIÓN LOGÍSTICA INTERNACIONAL</h3></div>", unsafe_allow_html=True)

    # --- NAVEGACIÓN POR SOLAPAS (TABS) ---
    tab_origen, tab_status, tab_indicadores, tab_agentes, tab_analistas, tab_fletes = st.tabs([
        "ORIGEN", "STATUS CARGAS", "INDICADORES", "PERFORMANCE AGENTES", "PERFORMANCE ANALISTAS", "SITUACIÓN FLETES"
    ])

    with tab_origen:
        st.markdown("<h3 class='section-title'>Consolidado de Origen</h3>", unsafe_allow_html=True)
        m3_totales = df['M3 Total'].sum()
        cant_so = df['SO'].nunique() if 'SO' in df.columns else len(df)
        
        c1, c2 = st.columns(2)
        c1.metric("CANTIDAD DE SO", f"{int(cant_so)}")
        c2.metric("VOLUMEN TOTAL (M3)", f"{int(m3_totales):,}")

    with tab_status:
        st.markdown("<h3 class='section-title'>Status Cargas en Curso</h3>", unsafe_allow_html=True)
        instruidos_m3 = df[df['Instruido'] == True]['M3 Total'].sum()
        perc_instruido = (instruidos_m3 / m3_totales * 100) if m3_totales > 0 else 0
        perc_pendiente = 100 - perc_instruido

        i1, i2 = st.columns(2)
        i1.metric("CONSOLIDADO INSTRUIDO", f"{int(perc_instruido)}%")
        i2.metric("PENDIENTE DE INSTRUCCIÓN", f"{int(perc_pendiente)}%")

    with tab_indicadores:
        st.markdown("<h3 class='section-title'>Indicadores Importantes</h3>", unsafe_allow_html=True)
        if 'Pais Destino' in df.columns:
            resumen = df.groupby('Pais Destino').agg({
                'SO': 'count',
                'M3 Total': 'sum'
            }).rename(columns={'SO': 'CANT. SO', 'M3 Total': 'M3 ORIGEN'})
            
            resumen['% TOTAL'] = ((resumen['M3 ORIGEN'] / m3_totales) * 100).round(0)
            resumen = resumen.sort_values(by='M3 ORIGEN', ascending=False)
            
            total_row = pd.DataFrame({
                'CANT. SO': [resumen['CANT. SO'].sum()],
                'M3 ORIGEN': [resumen['M3 ORIGEN'].sum()],
                '% TOTAL': [100]
            }, index=['TOTAL GENERAL'])
            
            resumen_final = pd.concat([resumen, total_row])
            st.dataframe(resumen_final.style.format({'CANT. SO': '{:,.0f}', 'M3 ORIGEN': '{:,.0f}', '% TOTAL': '{:.0f}%'}), use_container_width=True)

    with tab_agentes:
        st.markdown("<h3 class='section-title'>Performance Agentes</h3>", unsafe_allow_html=True)
        st.info("Información en proceso de consolidación por Agente de Carga.")

    with tab_analistas:
        st.markdown("<h3 class='section-title'>Performance Analistas</h3>", unsafe_allow_html=True)
        st.info("Seguimiento de tiempos de respuesta por Analista responsable.")

    with tab_fletes:
        st.markdown("<h3 class='section-title'>Situación Fletes</h3>", unsafe_allow_html=True)
        st.warning("Sección pendiente de integración con base de tarifas.")

except Exception as e:
    st.error(f"Error de sistema: {e}")
