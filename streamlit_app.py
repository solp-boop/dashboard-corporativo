import streamlit as st
import pandas as pd

# Configuración de página
st.set_page_config(page_title="BICOM | Logística Internacional", layout="wide")

# --- DISEÑO DE ALTO IMPACTO (CSS) ---
st.markdown("""
    <style>
    .main { background-color: #040911; color: #ffffff; }
    .bicom-header {
        background: linear-gradient(135deg, #001f3f 0%, #003366 100%);
        padding: 40px; border-radius: 15px; border: 1px solid #004080;
        text-align: center; margin-bottom: 30px;
    }
    .bicom-header h1 { font-size: 50px; letter-spacing: 5px; color: #ffffff; font-weight: 800; }
    
    /* Estilo para convertir botones en tarjetas métricas */
    .stButton>button {
        background: rgba(255, 255, 255, 0.03) !important;
        border: 1px solid rgba(255, 255, 255, 0.1) !important;
        border-radius: 20px !important;
        color: white !important;
        width: 100%;
        height: 150px;
        transition: all 0.3s ease;
    }
    .stButton>button:hover {
        border: 1px solid #00a8ff !important;
        background: rgba(0, 168, 255, 0.1) !important;
        transform: translateY(-5px);
    }
    
    .metric-label { font-size: 14px; color: #808495; letter-spacing: 2px; text-transform: uppercase; margin-bottom: 5px;}
    .metric-value-big { font-size: 45px; font-weight: 800; color: #ffffff; }
    
    .stTabs [data-baseweb="tab-list"] { justify-content: center; }
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
    
    df['Instruido'] = df['Fecha de Instruccion'].notna() & (df['Fecha de Instruccion'].astype(str).str.upper() != 'SIN INSTRUCCION')
    m3_totales = df['M3 Total'].sum()
    cant_so = df['SO'].nunique() if 'SO' in df.columns else len(df)

    # --- HEADER ---
    st.markdown("<div class='bicom-header'><h1>BICOM</h1><p style='color:#00a8ff; letter-spacing:3px;'>GESTIÓN LOGÍSTICA INTERNACIONAL</p></div>", unsafe_allow_html=True)

    t1, t2, t3, t4, t5, t6 = st.tabs(["ORIGEN", "STATUS CARGAS", "INDICADORES", "AGENTES", "ANALISTAS", "FLETES"])

    with t1:
        st.markdown("<br>", unsafe_allow_html=True)
        
        # --- FILA 1: BOTONES MÉTRICOS ---
        c1, c2 = st.columns(2)
        
        with c1:
            if st.button(f"CANTIDAD DE SO \n\n {int(cant_so)}"):
                st.session_state.detalle = "so"
        with c2:
            if st.button(f"VOLUMEN TOTAL (M3) \n\n {int(m3_totales):,}"):
                st.session_state.detalle = "m3"

        # Espacio para mostrar info si hacen click
        if 'detalle' in st.session_state:
            with st.expander("DETALLE SELECCIONADO", expanded=True):
                if st.session_state.detalle == "so":
                    st.write("### Desglose por Tipo de Operación (SO)")
                    # Aquí podrías poner un gráfico o tabla específica
                    st.dataframe(df[['SO', 'Pais Destino', 'Status Pago']].head(10))
                else:
                    st.write("### Análisis de Volumen Crítico")
                    st.bar_chart(df.groupby('Pais Destino')['M3 Total'].sum())

        st.markdown("<br>", unsafe_allow_html=True)
        
        # --- FILA 2: STATUS ---
        i1, i2 = st.columns(2)
        instruidos_m3 = df[df['Instruido'] == True]['M3 Total'].sum()
        perc_instruido = (instruidos_m3 / m3_totales * 100) if m3_totales > 0 else 0
        perc_pendiente = 100 - perc_instruido

        st.markdown(f"""
        <div style='display: flex; gap: 20px; justify-content: center;'>
            <div style='background: rgba(0,255,136,0.05); border: 1px solid #00ff88; padding: 20px; border-radius: 15px; width: 45%; text-align: center;'>
                <p style='color: #808495; font-size: 12px;'>CONSOLIDADO INSTRUIDO</p>
                <p style='color: #00ff88; font-size: 35px; font-weight: 800;'>{int(perc_instruido)}%</p>
            </div>
            <div style='background: rgba(255,75,75,0.05); border: 1px solid #ff4b4b; padding: 20px; border-radius: 15px; width: 45%; text-align: center;'>
                <p style='color: #808495; font-size: 12px;'>PENDIENTE INSTRUCCIÓN</p>
                <p style='color: #ff4b4b; font-size: 35px; font-weight: 800;'>{int(perc_pendiente)}%</p>
            </div>
        </div>
        """, unsafe_allow_html=True)

        st.markdown("<br><br>", unsafe_allow_html=True)

        # --- TABLA DE DESTINOS CON TOTALES ---
        st.markdown("<p style='text-align:center; letter-spacing:2px; color:#808495;'>PARTICIPACIÓN POR PAÍS DE DESTINO</p>", unsafe_allow_html=True)
        
        resumen = df.groupby('Pais Destino').agg({'SO': 'count', 'M3 Total': 'sum'}).rename(columns={'SO': 'CANT. SO', 'M3 Total': 'M3'})
        resumen['%'] = ((resumen['M3'] / m3_totales) * 100).round(0)
        resumen = resumen.sort_values(by='M3', ascending=False)
        
        # AGREGAR FILA DE TOTALES
        total_so = resumen['CANT. SO'].sum()
        total_m3 = resumen['M3'].sum()
        
        # Crear la fila de total
        df_total = pd.DataFrame({
            'CANT. SO': [total_so],
            'M3': [total_m3],
            '%': [100]
        }, index=['TOTAL GENERAL'])
        
        resumen_final = pd.concat([resumen, df_total])
        
        st.dataframe(
            resumen_final.style.format({
                'CANT. SO': '{:,.0f}', 
                'M3': '{:,.0f}', 
                '%': '{:.0f}%'
            }), 
            use_container_width=True
        )

except Exception as e:
    st.error(f"Error de sistema: {e}")
