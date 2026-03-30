import streamlit as st
import pandas as pd

# Configuración de página
st.set_page_config(page_title="Tablero de Gestión Logística Internacional", layout="wide")

# --- ESTILO CORPORATIVO (Ejecutivo) ---
st.markdown("""
    <style>
    /* Fondo y alineación general */
    .main { background-color: #0e1117; }
    h1, h2, h3 { font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; font-weight: 600; text-align: center; }
    
    /* Títulos de secciones */
    .section-title { font-size: 14px; letter-spacing: 2px; color: #808495; text-transform: uppercase; margin-bottom: 20px; text-align: center; }
    
    /* Métricas principales */
    div[data-testid="stMetricValue"] { font-size: 48px !important; font-weight: 700; color: #ffffff; justify-content: center; display: flex; }
    div[data-testid="stMetricLabel"] { font-size: 13px !important; letter-spacing: 1.5px; color: #808495; text-transform: uppercase; justify-content: center; display: flex; }
    
    /* Tabs ejecutivos */
    .stTabs [data-baseweb="tab-list"] { justify-content: center; border-bottom: 1px solid #31333f; }
    .stTabs [data-baseweb="tab"] { font-size: 14px; padding: 10px 30px; }
    
    /* Tabla */
    [data-testid="stDataFrame"] { display: flex; justify-content: center; padding: 20px; }
    hr { border-top: 1px solid #31333f; }
    </style>
    """, unsafe_allow_html=True)

try:
    # 1. Obtención de datos
    base_url = "https://docs.google.com/spreadsheets/d/1uDV3-CK5aeb-PI81uNc54t4L50HhscHe5xkp-pL9SyI"
    GID_HOJA = "0" 
    csv_url = f"{base_url}/export?format=csv&gid={GID_HOJA}"
    
    df = pd.read_csv(csv_url)
    df.columns = df.columns.str.strip()

    # --- LIMPIEZA Y CÁLCULOS ---
    if 'M3 Total' in df.columns:
        df['M3 Total'] = df['M3 Total'].astype(str).str.replace('.', '', regex=False).str.replace(',', '.', regex=False)
        df['M3 Total'] = pd.to_numeric(df['M3 Total'], errors='coerce').fillna(0)
    
    # Lógica de Instrucción (Columna U)
    df['Instruido'] = df['Fecha de Instruccion'].notna() & (df['Fecha de Instruccion'].astype(str).str.upper() != 'SIN INSTRUCCION')

    # --- ENCABEZADO ---
    st.title("TABLERO DE GESTIÓN LOGÍSTICA INTERNACIONAL")
    st.markdown("<p class='section-title'>Resumen de Operaciones Globales</p>", unsafe_allow_html=True)
    st.markdown("<hr>", unsafe_allow_html=True)

    # --- NAVEGACIÓN ---
    tab1, tab2, tab3 = st.tabs(["ORIGEN", "EN TRÁNSITO", "DESTINO FINAL"])

    with tab1:
        # Métricas de Volumen y SO
        m3_totales = df['M3 Total'].sum()
        cant_so = df['SO'].nunique() if 'SO' in df.columns else len(df)
        
        st.markdown("<br>", unsafe_allow_html=True)
        c1, c2 = st.columns(2)
        c1.metric("CANTIDAD DE SO", f"{int(cant_so)}")
        c2.metric("VOLUMEN TOTAL (M3)", f"{int(m3_totales):,}")

        st.markdown("<br><hr>", unsafe_allow_html=True)

        # Análisis de Instrucción
        st.markdown("<p class='section-title'>Estado de Instrucción de Carga</p>", unsafe_allow_html=True)
        
        instruidos_m3 = df[df['Instruido'] == True]['M3 Total'].sum()
        perc_instruido = (instruidos_m3 / m3_totales * 100) if m3_totales > 0 else 0
        perc_pendiente = 100 - perc_instruido

        i1, i2 = st.columns(2)
        i1.metric("CONSOLIDADO INSTRUIDO", f"{int(perc_instruido)}%")
        i2.metric("PENDIENTE DE INSTRUCCIÓN", f"{int(perc_pendiente)}%")

        st.markdown("<br><hr>", unsafe_allow_html=True)

        # Distribución Geográfica
        if 'Pais Destino' in df.columns:
            st.markdown("<p class='section-title'>Distribución por País de Destino</p>", unsafe_allow_html=True)
            
            resumen = df.groupby('Pais Destino').agg({
                'SO': 'count',
                'M3 Total': 'sum'
            }).rename(columns={'SO': 'CANT. SO', 'M3 Total': 'M3 ORIGEN'})
            
            resumen['% TOTAL'] = ((resumen['M3 ORIGEN'] / m3_totales) * 100).round(0)
            resumen = resumen.sort_values(by='M3 ORIGEN', ascending=False)

            # Fila de Total
            total_row = pd.DataFrame({
                'CANT. SO': [resumen['CANT. SO'].sum()],
                'M3 ORIGEN': [resumen['M3 ORIGEN'].sum()],
                '% TOTAL': [100]
            }, index=['TOTAL GENERAL'])

            resumen_final = pd.concat([resumen, total_row])
            
            # Tabla ejecutiva (Redondeada y limpia)
            st.dataframe(
                resumen_final.style.format({
                    'CANT. SO': '{:,.0f}',
                    'M3 ORIGEN': '{:,.0f}',
                    '% TOTAL': '{:.0f}%'
                }), 
                use_container_width=True
            )

    with tab2:
        st.markdown("<p class='section-title'>Seguimiento de Unidades en Tránsito Marítimo/Aéreo</p>", unsafe_allow_html=True)

    with tab3:
        st.markdown("<p class='section-title'>Reporte de Arribos y Entregas en Destino</p>", unsafe_allow_html=True)

except Exception as e:
    st.error(f"Fallo en la sincronización de datos: {e}")
