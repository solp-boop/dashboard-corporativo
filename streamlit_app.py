import streamlit as st
import pandas as pd

# Configuración de página
st.set_page_config(page_title="BICOM | Logística Internacional", layout="wide")

# --- DISEÑO DE ALTO IMPACTO (CSS) ---
st.markdown("""
    <style>
    /* Estética Dark Premium */
    .main { background-color: #040911; color: #ffffff; }
    
    /* Header Bicom con degradado sutil */
    .bicom-header {
        background: linear-gradient(135deg, #001f3f 0%, #003366 100%);
        padding: 40px;
        border-radius: 15px;
        border: 1px solid #004080;
        text-align: center;
        margin-bottom: 30px;
    }
    .bicom-header h1 { font-size: 50px; letter-spacing: 5px; margin: 0; color: #ffffff; font-weight: 800; }
    .bicom-header p { font-size: 14px; letter-spacing: 3px; color: #00a8ff; text-transform: uppercase; margin-top: 10px; }

    /* Solapas (Tabs) Estilo Moderno */
    .stTabs [data-baseweb="tab-list"] { gap: 15px; justify-content: center; background-color: transparent; }
    .stTabs [data-baseweb="tab"] {
        height: 50px;
        background-color: #0d1b2a;
        border-radius: 8px;
        color: #ffffff;
        border: 1px solid #1b263b;
        padding: 0 25px;
        font-weight: 500;
        transition: all 0.3s;
    }
    .stTabs [aria-selected="true"] {
        background-color: #0056b3 !important;
        border: 1px solid #00a8ff !important;
        box-shadow: 0 0 15px rgba(0, 168, 255, 0.4);
    }

    /* Tarjetas "Glass" de Origen */
    .metric-card {
        background: rgba(255, 255, 255, 0.03);
        border: 1px solid rgba(255, 255, 255, 0.1);
        padding: 30px;
        border-radius: 20px;
        text-align: center;
        transition: transform 0.3s;
    }
    .metric-card:hover { transform: translateY(-5px); border: 1px solid #00a8ff; }
    .metric-title { font-size: 12px; color: #808495; letter-spacing: 2px; text-transform: uppercase; margin-bottom: 10px; }
    .metric-value { font-size: 60px; font-weight: 800; color: #ffffff; margin: 0; }
    .metric-sub { font-size: 18px; color: #00a8ff; font-weight: 600; }

    /* Tabla Estilizada */
    .stDataFrame { border: 1px solid rgba(255, 255, 255, 0.1); border-radius: 15px; }
    </style>
    """, unsafe_allow_html=True)

try:
    # 1. Datos
    base_url = "https://docs.google.com/spreadsheets/d/1uDV3-CK5aeb-PI81uNc54t4L50HhscHe5xkp-pL9SyI"
    GID_HOJA = "0" 
    csv_url = f"{base_url}/export?format=csv&gid={GID_HOJA}"
    df = pd.read_csv(csv_url)
    df.columns = df.columns.str.strip()

    # Limpieza M3
    if 'M3 Total' in df.columns:
        df['M3 Total'] = df['M3 Total'].astype(str).str.replace('.', '', regex=False).str.replace(',', '.', regex=False)
        df['M3 Total'] = pd.to_numeric(df['M3 Total'], errors='coerce').fillna(0)
    
    # Lógica Instruido
    df['Instruido'] = df['Fecha de Instruccion'].notna() & (df['Fecha de Instruccion'].astype(str).str.upper() != 'SIN INSTRUCCION')
    m3_totales = df['M3 Total'].sum()
    cant_so = df['SO'].nunique() if 'SO' in df.columns else len(df)

    # --- HEADER ---
    st.markdown("""
        <div class='bicom-header'>
            <h1>BICOM</h1>
            <p>Tablero de Gestión Logística Internacional</p>
        </div>
    """, unsafe_allow_html=True)

    # --- TABS ---
    t1, t2, t3, t4, t5, t6 = st.tabs(["ORIGEN", "STATUS CARGAS", "INDICADORES", "AGENTES", "ANALISTAS", "FLETES"])

    with t1:
        st.markdown("<br>", unsafe_allow_html=True)
        
        # FILA 1: Totales Grandes
        c1, c2 = st.columns(2)
        with c1:
            st.markdown(f"""<div class='metric-card'><p class='metric-title'>Cantidad de SO</p><p class='metric-value'>{int(cant_so)}</p></div>""", unsafe_allow_html=True)
        with c2:
            st.markdown(f"""<div class='metric-card'><p class='metric-title'>Volumen Total</p><p class='metric-value'>{int(m3_totales):,}</p><p class='metric-sub'>M3</p></div>""", unsafe_allow_html=True)
        
        st.markdown("<br>", unsafe_allow_html=True)
        
        # FILA 2: Instruido vs Pendiente (En tarjetas separadas)
        i1, i2 = st.columns(2)
        instruidos_m3 = df[df['Instruido'] == True]['M3 Total'].sum()
        perc_instruido = (instruidos_m3 / m3_totales * 100) if m3_totales > 0 else 0
        perc_pendiente = 100 - perc_instruido

        with i1:
            st.markdown(f"""<div class='metric-card' style='border-left: 4px solid #00ff88;'><p class='metric-title'>Consolidado Instruido</p><p class='metric-value' style='color:#00ff88;'>{int(perc_instruido)}%</p></div>""", unsafe_allow_html=True)
        with i2:
            st.markdown(f"""<div class='metric-card' style='border-left: 4px solid #ff4b4b;'><p class='metric-title'>Pendiente Instrucción</p><p class='metric-value' style='color:#ff4b4b;'>{int(perc_pendiente)}%</p></div>""", unsafe_allow_html=True)

        st.markdown("<br><hr style='opacity:0.1'><br>", unsafe_allow_html=True)

        # TABLA DE DESTINOS
        st.markdown("<p style='text-align:center; letter-spacing:2px; color:#808495;'>PARTICIPACIÓN POR PAÍS DE DESTINO</p>", unsafe_allow_html=True)
        resumen = df.groupby('Pais Destino').agg({'SO': 'count', 'M3 Total': 'sum'}).rename(columns={'SO': 'CANT. SO', 'M3 Total': 'M3'})
        resumen['%'] = ((resumen['M3'] / m3_totales) * 100).round(0)
        resumen = resumen.sort_values(by='M3', ascending=False)
        
        st.dataframe(resumen.style.format({'CANT. SO': '{:,.0f}', 'M3': '{:,.0f}', '%': '{:.0f}%'}), use_container_width=True)

    with t2:
        st.info("Visualización de cargas en curso.")

    # Resto de pestañas vacías para mantener estructura...

except Exception as e:
    st.error(f"Error de sistema: {e}")
