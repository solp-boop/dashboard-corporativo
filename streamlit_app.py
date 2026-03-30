import streamlit as st
import pandas as pd
import plotly.express as px

# --- CONFIGURACIÓN DE PÁGINA (CORREGIDA) ---
st.set_page_config(page_title="BIDCOM | Dashboard Ejecutivo", layout="wide")

# --- DISEÑO BIDCOM DE MÁXIMO IMPACTO (CSS CUSTOM) ---
st.markdown("""
    <style>
    .main { background-color: #040911; color: #ffffff; }
    
    /* Header Principal */
    .bidcom-header {
        background: linear-gradient(135deg, #001f3f 0%, #003366 100%);
        padding: 40px; border-radius: 20px; border: 1px solid #004080;
        text-align: center; margin-bottom: 30px;
    }
    .bidcom-header h1 { font-size: 55px; letter-spacing: 10px; color: #ffffff; font-weight: 900; margin:0; }
    
    /* Centrado de Tabs */
    .stTabs [data-baseweb="tab-list"] { justify-content: center; gap: 30px; margin-bottom: 40px; }

    /* --- CONTENEDOR DE MÉTRICAS GIGANTES --- */
    .big-metric-card {
        background: rgba(255, 255, 255, 0.03);
        border: 1px solid rgba(255, 255, 255, 0.1);
        border-radius: 25px;
        padding: 40px 20px;
        text-align: center;
        box-shadow: 0 10px 30px rgba(0,0,0,0.5);
    }
    
    .label-massive { 
        font-size: 18px; 
        color: #808495; 
        letter-spacing: 5px; 
        text-transform: uppercase; 
        font-weight: 700;
        margin-bottom: 10px;
    }
    .value-massive { 
        font-size: 130px; /* Tamaño masivo para llamar la atención */
        font-weight: 900; 
        color: #ffffff; 
        line-height: 1; 
        margin: 0;
        text-shadow: 0 0 40px rgba(0,168,255,0.3);
    }
    .unit-massive { font-size: 35px; color: #00a8ff; font-weight: 400; }

    /* Botones Interactivos (Instruido / Pendiente) */
    .stButton { display: flex; justify-content: center; }
    .stButton>button {
        border-radius: 20px !important; color: white !important;
        width: 100%; height: 180px; transition: all 0.3s ease;
        font-weight: 800 !important; font-size: 26px !important;
        background: rgba(255, 255, 255, 0.03) !important;
        border: 1px solid rgba(255, 255, 255, 0.1) !important;
    }
    .stButton>button:hover {
        background-color: #003366 !important; 
        border: 2px solid #00a8ff !important;
    }
    
    /* Indicadores de color en botones */
    div[data-testid="column"]:nth-child(1) .stButton > button { border-bottom: 8px solid #00ff88 !important; }
    div[data-testid="column"]:nth-child(2) .stButton > button { border-bottom: 8px solid #ff4b4b !important; }

    </style>
    """, unsafe_allow_html=True)

try:
    # 1. Carga de Datos
    base_url = "https://docs.google.com/spreadsheets/d/1uDV3-CK5aeb-PI81uNc54t4L50HhscHe5xkp-pL9SyI"
    GID_HOJA = "0" 
    csv_url = f"{base_url}/export?format=csv&gid={GID_HOJA}"
    df = pd.read_csv(csv_url)
    df.columns = df.columns.str.strip()

    # Procesamiento de M3
    if 'M3 Total' in df.columns:
        df['M3 Total'] = df['M3 Total'].astype(str).str.replace('.', '', regex=False).str.replace(',', '.', regex=False)
        df['M3 Total'] = pd.to_numeric(df['M3 Total'], errors='coerce').fillna(0)
    
    # Lógica de Instrucción
    df['Es_Instruido'] = df['Fecha de Instruccion'].notna() & (df['Fecha de Instruccion'].astype(str).str.upper() != 'SIN INSTRUCCION')
    
    # Cálculos masivos
    m3_totales = df['M3 Total'].sum()
    cant_so = df['SO'].nunique() if 'SO' in df.columns else len(df)
    cant_proveedores = df['Proveedor'].nunique() if 'Proveedor' in df.columns else 0

    # --- HEADER BIDCOM ---
    st.markdown("<div class='bidcom-header'><h1>BIDCOM</h1><p style='color:#00a8ff; letter-spacing:3px;'>OPERACIONES LOGÍSTICAS INTERNACIONALES</p></div>", unsafe_allow_html=True)

    tabs = st.tabs(["ORIGEN", "STATUS CARGAS", "INDICADORES", "AGENTES", "ANALISTAS", "FLETES"])

    with tabs[0]:
        # --- BLOQUE SUPERIOR MASIVO ---
        m1, m2, m3 = st.columns(3)
        
        with m1:
            st.markdown(f"<div class='big-metric-card'><p class='label-massive'>Cantidad de SO</p><p class='value-massive'>{int(cant_so)}</p></div>", unsafe_allow_html=True)
        with m2:
            st.markdown(f"<div class='big-metric-card'><p class='label-massive'>Volumen Total</p><p class='value-massive'>{int(m3_totales):,}<span class='unit-massive'> M3</span></p></div>", unsafe_allow_html=True)
        with m3:
            st.markdown(f"<div class='big-metric-card'><p class='label-massive'>Proveedores</p><p class='value-massive'>{int(cant_proveedores)}</p></div>", unsafe_allow_html=True)

        st.markdown("<br><br>", unsafe_allow_html=True)

        # --- BOTONES DE ACCIÓN (Centrados) ---
        _, b1_col, b2_col, _ = st.columns([0.5, 2, 2, 0.5])
        
        instruidos_m3 = df[df['Es_Instruido'] == True]['M3 Total'].sum()
        perc_instruido = (instruidos_m3 / m3_totales * 100) if m3_totales > 0 else 0
        perc_pendiente = 100 - perc_instruido

        with b1_col:
            if st.button(f"CONSOLIDADO INSTRUIDO \n {int(perc_instruido)}%"):
                st.session_state.filtro = None if st.session_state.get('filtro') == 'instruido' else 'instruido'
        with b2_col:
            if st.button(f"PENDIENTE INSTRUCCIÓN \n {int(perc_pendiente)}%"):
                st.session_state.filtro = None if st.session_state.get('filtro') == 'pendiente' else 'pendiente'

        # Toggle Detalle
        filtro = st.session_state.get('filtro')
        if filtro:
            st.markdown("---")
            if filtro == "instruido":
                st.subheader("Cargas con Instrucción Consolidada")
                st.dataframe(df[df['Es_Instruido'] == True][['SO', 'Pais Destino', 'M3 Total', 'Fecha de Instruccion']], use_container_width=True)
            else:
                st.subheader("Cargas Pendientes de Instrucción")
                st.dataframe(df[df['Es_Instruido'] == False][['SO', 'Pais Destino', 'M3 Total', 'Status Pago']], use_container_width=True)

        st.markdown("<br><br>", unsafe_allow_html=True)

        # --- CUADRO DE PARTICIPACIÓN ---
        st.markdown("<p style='text-align:center; letter-spacing:2px; color:#808495; font-weight:bold;'>PARTICIPACIÓN POR PAÍS DE DESTINO</p>", unsafe_allow_html=True)
        resumen = df.groupby('Pais Destino').agg({'SO': 'count', 'M3 Total': 'sum'}).rename(columns={'SO': 'CANT. SO', 'M3 Total': 'M3'})
        resumen['%'] = ((resumen['M3'] / m3_totales) * 100).round(0)
        resumen = resumen.sort_values(by='M3', ascending=False)
        
        df_total = pd.DataFrame({'CANT. SO': [resumen['CANT. SO'].sum()], 'M3': [resumen['M3'].sum()], '%': [100]}, index=['TOTAL GENERAL'])
        resumen_final = pd.concat([resumen, df_total])
        
        def highlight_total(s):
            return ['background-color: #003366; font-weight: bold; color: white' if s.name == 'TOTAL GENERAL' else '' for _ in s]

        st.dataframe(resumen_final.style.apply(highlight_total, axis=1).format({'CANT. SO': '{:,.0f}', 'M3': '{:,.0f}', '%': '{:.0f}%'}), use_container_width=True)

        # --- GRÁFICO PUERTOS ---
        st.markdown("<br><p style='text-align:center; letter-spacing:2px; color:#ffffff; font-weight:bold; font-size:22px;'>DISTRIBUCIÓN POR PUERTO DE SALIDA</p>", unsafe_allow_html=True)
        col_puerto = 'Puerto de Salida' if 'Puerto de Salida' in df.columns else df.columns[41]
        df[col_puerto] = df[col_puerto].fillna('SIN DEFINIR').replace('', 'SIN DEFINIR')
        puertos_df = df.groupby(col_puerto).agg({'M3 Total': 'sum'}).reset_index().sort_values(by='M3 Total')

        fig = px.bar(puertos_df, y=col_puerto, x='M3 Total', orientation='h', text_auto=',.0f', color_discrete_sequence=['#00a8ff'], template='plotly_dark')
        fig.update_layout(xaxis_title="M3", yaxis_title=None, paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)')
        fig.update_traces(textfont_size=20, textposition='outside')
        st.plotly_chart(fig, use_container_width=True)

except Exception as e:
    st.error(f"Fallo en la carga de componentes: {e}")
