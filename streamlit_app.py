import streamlit as st
import pandas as pd

# Configuración de página
st.set_page_config(page_title="BICOM | Gestión Logística", layout="wide")

# --- DISEÑO UNIFICADO DE ALTO IMPACTO (CSS) ---
st.markdown("""
    <style>
    .main { background-color: #040911; color: #ffffff; }
    .bicom-header {
        background: linear-gradient(135deg, #001f3f 0%, #003366 100%);
        padding: 30px; border-radius: 15px; border: 1px solid #004080;
        text-align: center; margin-bottom: 20px;
    }
    
    /* Estilo para los TABS centrados */
    .stTabs [data-baseweb="tab-list"] { justify-content: center; gap: 20px; }

    /* FORMATO UNIFICADO DE TARJETAS (Estáticas y Botones) */
    .metric-box {
        background: rgba(255, 255, 255, 0.03);
        border: 1px solid rgba(255, 255, 255, 0.1);
        padding: 30px;
        border-radius: 20px;
        text-align: center;
        height: 180px;
        display: flex;
        flex-direction: column;
        justify-content: center;
        align-items: center;
    }

    /* Estilo para que los botones parezcan tarjetas métricas */
    .stButton>button {
        background: rgba(255, 255, 255, 0.03) !important;
        border: 1px solid rgba(255, 255, 255, 0.1) !important;
        border-radius: 20px !important;
        color: white !important;
        width: 100%;
        height: 180px;
        transition: all 0.3s ease;
        display: flex;
        flex-direction: column;
        justify-content: center;
    }
    
    /* Colores de acento para los botones interactivos */
    div[data-testid="column"]:nth-child(1) .stButton > button { border-bottom: 4px solid #00ff88 !important; }
    div[data-testid="column"]:nth-child(2) .stButton > button { border-bottom: 4px solid #ff4b4b !important; }
    
    .stButton>button:hover { border: 1px solid #00a8ff !important; background: rgba(0, 168, 255, 0.05) !important; transform: translateY(-5px); }
    
    .label-text { font-size: 12px; color: #808495; letter-spacing: 2px; text-transform: uppercase; margin-bottom: 10px; }
    .value-text { font-size: 50px; font-weight: 800; color: #ffffff; margin: 0; }
    </style>
    """, unsafe_allow_html=True)

try:
    # 1. Datos
    base_url = "https://docs.google.com/spreadsheets/d/1uDV3-CK5aeb-PI81uNc54t4L50HhscHe5xkp-pL9SyI"
    GID_HOJA = "0" 
    csv_url = f"{base_url}/export?format=csv&gid={GID_HOJA}"
    df = pd.read_csv(csv_url)
    df.columns = df.columns.str.strip()

    if 'M3 Total' in df.columns:
        df['M3 Total'] = df['M3 Total'].astype(str).str.replace('.', '', regex=False).str.replace(',', '.', regex=False)
        df['M3 Total'] = pd.to_numeric(df['M3 Total'], errors='coerce').fillna(0)
    
    df['Es_Instruido'] = df['Fecha de Instruccion'].notna() & (df['Fecha de Instruccion'].astype(str).str.upper() != 'SIN INSTRUCCION')
    
    m3_totales = df['M3 Total'].sum()
    cant_so = df['SO'].nunique() if 'SO' in df.columns else len(df)
    instruidos_m3 = df[df['Es_Instruido'] == True]['M3 Total'].sum()
    perc_instruido = (instruidos_m3 / m3_totales * 100) if m3_totales > 0 else 0
    perc_pendiente = 100 - perc_instruido

    # --- HEADER ---
    st.markdown("<div class='bicom-header'><h1>BICOM</h1><p style='color:#00a8ff; letter-spacing:2px; margin:0;'>LOGÍSTICA INTERNACIONAL</p></div>", unsafe_allow_html=True)

    tabs = st.tabs(["ORIGEN", "STATUS CARGAS", "INDICADORES", "AGENTES", "ANALISTAS", "FLETES"])

    with tabs[0]:
        st.markdown("<br>", unsafe_allow_html=True)
        
        # --- FILA 1: MÉTRICAS ESTÁTICAS ---
        c1, c2 = st.columns(2)
        with c1:
            st.markdown(f"<div class='metric-box'><p class='label-text'>CANTIDAD DE SO</p><p class='value-text'>{int(cant_so)}</p></div>", unsafe_allow_html=True)
        with c2:
            st.markdown(f"<div class='metric-box'><p class='label-text'>VOLUMEN TOTAL</p><p class='value-text'>{int(m3_totales):,}<span style='font-size:20px;'> M3</span></p></div>", unsafe_allow_html=True)

        st.markdown("<br>", unsafe_allow_html=True)

        # --- FILA 2: BOTONES MÉTRICOS (INSTRUIDO VS PENDIENTE) ---
        b1, b2 = st.columns(2)
        
        with b1:
            # El botón ahora tiene el mismo formato visual de texto que las tarjetas estáticas
            if st.button(f"CONSOLIDADO INSTRUIDO \n {int(perc_instruido)}%"):
                st.session_state.filtro = None if st.session_state.get('filtro') == 'instruido' else 'instruido'
        
        with b2:
            if st.button(f"PENDIENTE INSTRUCCIÓN \n {int(perc_pendiente)}%"):
                st.session_state.filtro = None if st.session_state.get('filtro') == 'pendiente' else 'pendiente'

        # Desglose interactivo
        filtro = st.session_state.get('filtro')
        if filtro:
            st.markdown("<br>", unsafe_allow_html=True)
            if filtro == "instruido":
                st.markdown("<h3 style='text-align:center; color:#00ff88;'>Detalle de Cargas Instruidas</h3>", unsafe_allow_html=True)
                detalle = df[df['Es_Instruido'] == True][['SO', 'Pais Destino', 'M3 Total', 'Fecha de Instruccion']]
                st.dataframe(detalle.style.format({'M3 Total': '{:,.0f}'}), use_container_width=True)
            elif filtro == "pendiente":
                st.markdown("<h3 style='text-align:center; color:#ff4b4b;'>Urgente: Cargas Pendientes de Instrucción</h3>", unsafe_allow_html=True)
                detalle = df[df['Es_Instruido'] == False][['SO', 'Pais Destino', 'M3 Total', 'Status Pago']]
                st.dataframe(detalle.style.format({'M3 Total': '{:,.0f}'}), use_container_width=True)

        st.markdown("<br><hr style='opacity:0.1'><br>", unsafe_allow_html=True)

        # TABLA DE DESTINOS
        st.markdown("<p style='text-align:center; letter-spacing:2px; color:#808495;'>PARTICIPACIÓN POR PAÍS DE DESTINO</p>", unsafe_allow_html=True)
        resumen = df.groupby('Pais Destino').agg({'SO': 'count', 'M3 Total': 'sum'}).rename(columns={'SO': 'CANT. SO', 'M3 Total': 'M3'})
        resumen['%'] = ((resumen['M3'] / m3_totales) * 100).round(0)
        resumen = resumen.sort_values(by='M3', ascending=False)
        
        df_total = pd.DataFrame({'CANT. SO': [resumen['CANT. SO'].sum()], 'M3': [resumen['M3'].sum()], '%': [100]}, index=['TOTAL GENERAL'])
        resumen_final = pd.concat([resumen, df_total])
        
        st.dataframe(resumen_final.style.format({'CANT. SO': '{:,.0f}', 'M3': '{:,.0f}', '%': '{:.0f}%'}), use_container_width=True)

except Exception as e:
    st.error(f"Error: {e}")
