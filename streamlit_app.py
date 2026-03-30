import streamlit as st
import pandas as pd

# Configuración de página
st.set_page_config(page_title="BICOM | Gestión Logística", layout="wide")

# --- DISEÑO PREMIUM (CSS) ---
st.markdown("""
    <style>
    .main { background-color: #040911; color: #ffffff; }
    .bicom-header {
        background: linear-gradient(135deg, #001f3f 0%, #003366 100%);
        padding: 30px; border-radius: 15px; border: 1px solid #004080;
        text-align: center; margin-bottom: 20px;
    }
    .bicom-header h1 { font-size: 45px; letter-spacing: 4px; color: #ffffff; font-weight: 800; margin:0; }
    
    /* Métricas Estáticas */
    .static-metric {
        background: rgba(255, 255, 255, 0.02);
        border: 1px solid rgba(255, 255, 255, 0.05);
        padding: 20px; border-radius: 15px; text-align: center;
    }

    /* Botones de Acción (Instruido/Pendiente) */
    .stButton>button {
        border-radius: 15px !important;
        color: white !important;
        width: 100%;
        height: 120px;
        transition: all 0.3s ease;
        font-weight: 700 !important;
    }
    /* Estilo específico para Instruido (Verde) */
    div.stButton > button:first-child { border: 1px solid #00ff88 !important; background: rgba(0, 255, 136, 0.05) !important; }
    /* Estilo específico para Pendiente (Rojo) */
    div[data-testid="column"]:nth-child(2) .stButton > button { border: 1px solid #ff4b4b !important; background: rgba(255, 75, 75, 0.05) !important; }
    
    .stButton>button:hover { transform: scale(1.02); box-shadow: 0 0 20px rgba(255,255,255,0.1); }
    
    [data-testid="stDataFrame"] { border-radius: 10px; overflow: hidden; }
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
    
    # Lógica Instrucción (Columna U)
    df['Es_Instruido'] = df['Fecha de Instruccion'].notna() & (df['Fecha de Instruccion'].astype(str).str.upper() != 'SIN INSTRUCCION')
    
    m3_totales = df['M3 Total'].sum()
    cant_so = df['SO'].nunique() if 'SO' in df.columns else len(df)
    
    instruidos_m3 = df[df['Es_Instruido'] == True]['M3 Total'].sum()
    perc_instruido = (instruidos_m3 / m3_totales * 100) if m3_totales > 0 else 0
    perc_pendiente = 100 - perc_instruido

    # --- HEADER ---
    st.markdown("<div class='bicom-header'><h1>BICOM</h1><p style='color:#00a8ff; letter-spacing:2px; margin:0;'>LOGÍSTICA INTERNACIONAL</p></div>", unsafe_allow_html=True)

    t1, t2, t3, t4, t5, t6 = st.tabs(["ORIGEN", "STATUS CARGAS", "INDICADORES", "AGENTES", "ANALISTAS", "FLETES"])

    with t1:
        st.markdown("<br>", unsafe_allow_html=True)
        
        # --- FILA 1: MÉTRICAS ESTÁTICAS (GRANDES) ---
        c1, c2 = st.columns(2)
        with c1:
            st.markdown(f"<div class='static-metric'><p style='color:#808495; font-size:12px; letter-spacing:2px;'>CANTIDAD DE SO</p><p style='font-size:45px; font-weight:800; margin:0;'>{int(cant_so)}</p></div>", unsafe_allow_html=True)
        with c2:
            st.markdown(f"<div class='static-metric'><p style='color:#808495; font-size:12px; letter-spacing:2px;'>VOLUMEN TOTAL</p><p style='font-size:45px; font-weight:800; margin:0;'>{int(m3_totales):,}<span style='font-size:18px; color:#00a8ff;'> M3</span></p></div>", unsafe_allow_html=True)

        st.markdown("<br><hr style='opacity:0.1'><br>", unsafe_allow_html=True)

        # --- FILA 2: BOTONES DE ACCIÓN (INSTRUIDO VS PENDIENTE) ---
        st.markdown("<p style='text-align:center; color:#808495; font-size:11px; letter-spacing:2px; margin-bottom:15px;'>SELECCIONE PARA VER DESGLOSE</p>", unsafe_allow_html=True)
        b1, b2 = st.columns(2)
        
        with b1:
            if st.button(f"CONSOLIDADO INSTRUIDO \n\n {int(perc_instruido)}%"):
                st.session_state.filtro = "instruido"
        with b2:
            if st.button(f"PENDIENTE INSTRUCCIÓN \n\n {int(perc_pendiente)}%"):
                st.session_state.filtro = "pendiente"

        # Área de resultados del botón
        if 'filtro' in st.session_state:
            with st.container():
                st.markdown("---")
                if st.session_state.filtro == "instruido":
                    st.subheader("Detalle de Cargas Instruidas")
                    detalle = df[df['Es_Instruido'] == True][['SO', 'Pais Destino', 'M3 Total', 'Fecha de Instruccion']]
                    st.dataframe(detalle.style.format({'M3 Total': '{:,.0f}'}), use_container_width=True)
                else:
                    st.subheader("⚠️ Urgente: Cargas Pendientes de Instrucción")
                    detalle = df[df['Es_Instruido'] == False][['SO', 'Pais Destino', 'M3 Total', 'Status Pago']]
                    st.dataframe(detalle.style.format({'M3 Total': '{:,.0f}'}), use_container_width=True)

        st.markdown("<br><br>", unsafe_allow_html=True)

        # --- TABLA DE DESTINOS CON TOTAL GENERAL ---
        st.markdown("<p style='text-align:center; letter-spacing:2px; color:#808495;'>PARTICIPACIÓN POR PAÍS DE DESTINO</p>", unsafe_allow_html=True)
        resumen = df.groupby('Pais Destino').agg({'SO': 'count', 'M3 Total': 'sum'}).rename(columns={'SO': 'CANT. SO', 'M3 Total': 'M3'})
        resumen['%'] = ((resumen['M3'] / m3_totales) * 100).round(0)
        resumen = resumen.sort_values(by='M3', ascending=False)
        
        # Fila de Totales
        df_total = pd.DataFrame({'CANT. SO': [resumen['CANT. SO'].sum()], 'M3': [resumen['M3'].sum()], '%': [100]}, index=['TOTAL GENERAL'])
        resumen_final = pd.concat([resumen, df_total])
        
        st.dataframe(resumen_final.style.format({'CANT. SO': '{:,.0f}', 'M3': '{:,.0f}', '%': '{:.0f}%'}), use_container_width=True)

except Exception as e:
    st.error(f"Error de sistema: {e}")
