import streamlit as st
import pandas as pd

# Configuración de página
st.set_page_config(page_title="Tablero de Gestión Logística Internacional", layout="wide")

# --- DISEÑO EJECUTIVO (CSS) ---
st.markdown("""
    <style>
    /* Alineación central y fuentes */
    .main { background-color: #0e1117; }
    h1 { font-family: 'Helvetica Neue', Helvetica, Arial, sans-serif; font-weight: 700; text-align: center; letter-spacing: 2px; padding-bottom: 20px; color: #ffffff; }
    
    /* Subtítulos de Secciones */
    .section-header { 
        font-family: 'Helvetica Neue', Helvetica, Arial, sans-serif; 
        font-size: 18px; 
        font-weight: 600; 
        color: #ffffff; 
        text-align: center; 
        background-color: #1e2129; 
        padding: 10px; 
        margin-top: 30px; 
        margin-bottom: 20px; 
        letter-spacing: 1px;
        text-transform: uppercase;
    }
    
    /* Métricas */
    div[data-testid="stMetricValue"] { font-size: 42px !important; font-weight: 700; justify-content: center; display: flex; color: #ffffff; }
    div[data-testid="stMetricLabel"] { font-size: 12px !important; justify-content: center; display: flex; color: #808495; letter-spacing: 1px; }
    
    /* Tabs */
    .stTabs [data-baseweb="tab-list"] { justify-content: center; }
    
    /* Ajustes de tabla */
    [data-testid="stDataFrame"] { display: flex; justify-content: center; }
    hr { border-top: 1px solid #31333f; margin: 30px 0; }
    </style>
    """, unsafe_allow_html=True)

try:
    # 1. Obtención y Limpieza de Datos
    base_url = "https://docs.google.com/spreadsheets/d/1uDV3-CK5aeb-PI81uNc54t4L50HhscHe5xkp-pL9SyI"
    GID_HOJA = "0" 
    csv_url = f"{base_url}/export?format=csv&gid={GID_HOJA}"
    
    df = pd.read_csv(csv_url)
    df.columns = df.columns.str.strip()

    if 'M3 Total' in df.columns:
        df['M3 Total'] = df['M3 Total'].astype(str).str.replace('.', '', regex=False).str.replace(',', '.', regex=False)
        df['M3 Total'] = pd.to_numeric(df['M3 Total'], errors='coerce').fillna(0)
    
    df['Instruido'] = df['Fecha de Instruccion'].notna() & (df['Fecha de Instruccion'].astype(str).str.upper() != 'SIN INSTRUCCION')

    # --- TÍTULO PRINCIPAL CENTRADO ---
    st.title("TABLERO DE GESTIÓN LOGÍSTICA INTERNACIONAL")

    # --- SECCIÓN: ORIGEN ---
    st.markdown("<div class='section-header'>Origen</div>", unsafe_allow_html=True)
    
    m3_totales = df['M3 Total'].sum()
    cant_so = df['SO'].nunique() if 'SO' in df.columns else len(df)
    
    c1, c2 = st.columns(2)
    c1.metric("CANTIDAD DE SO", f"{int(cant_so)}")
    c2.metric("VOLUMEN TOTAL (M3)", f"{int(m3_totales):,}")

    # --- SECCIÓN: STATUS CARGAS EN CURSO ---
    st.markdown("<div class='section-header'>Status cargas en curso</div>", unsafe_allow_html=True)
    
    instruidos_m3 = df[df['Instruido'] == True]['M3 Total'].sum()
    perc_instruido = (instruidos_m3 / m3_totales * 100) if m3_totales > 0 else 0
    perc_pendiente = 100 - perc_instruido

    i1, i2 = st.columns(2)
    i1.metric("CONSOLIDADO INSTRUIDO", f"{int(perc_instruido)}%")
    i2.metric("PENDIENTE DE INSTRUCCIÓN", f"{int(perc_pendiente)}%")

    # --- SECCIÓN: INDICADORES IMPORTANTES ---
    st.markdown("<div class='section-header'>Indicadores importantes</div>", unsafe_allow_html=True)
    
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
        
        st.dataframe(
            resumen_final.style.format({'CANT. SO': '{:,.0f}', 'M3 ORIGEN': '{:,.0f}', '% TOTAL': '{:.0f}%'}), 
            use_container_width=True
        )

    # --- SECCIÓN: PERFORMANCE AGENTES ---
    st.markdown("<div class='section-header'>Performance Agentes</div>", unsafe_allow_html=True)
    st.markdown("<p style='text-align:center; color:#808495;'>Datos en proceso de consolidación...</p>", unsafe_allow_html=True)

    # --- SECCIÓN: PERFORMANCE ANALISTAS ---
    st.markdown("<div class='section-header'>Performance Analistas</div>", unsafe_allow_html=True)
    st.markdown("<p style='text-align:center; color:#808495;'>Datos en proceso de consolidación...</p>", unsafe_allow_html=True)

    # --- SECCIÓN: SITUACION FLETES ---
    st.markdown("<div class='section-header'>Situación fletes</div>", unsafe_allow_html=True)
    st.markdown("<p style='text-align:center; color:#808495;'>Pendiente de carga de tarifas y costos transaccionales...</p>", unsafe_allow_html=True)

except Exception as e:
    st.error(f"Error de sistema: {e}")
