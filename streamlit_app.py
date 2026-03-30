import streamlit as st
import pandas as pd

# Configuración de página
st.set_page_config(page_title="Tablero Logística Internacional", layout="wide")

# --- ESTILO CUSTOM (Centrado y tamaños grandes) ---
st.markdown("""
    <style>
    .main { text-align: center; }
    div[data-testid="stMetricValue"] { font-size: 55px !important; font-weight: bold; color: #1E88E5; justify-content: center; display: flex; }
    div[data-testid="stMetricLabel"] { font-size: 20px !important; justify-content: center; display: flex; }
    .stTabs [data-baseweb="tab-list"] { justify-content: center; }
    h1 { text-align: center; color: #ffffff; }
    h3 { text-align: center; }
    [data-testid="stDataFrame"] { display: flex; justify-content: center; }
    </style>
    """, unsafe_allow_html=True)

try:
    # 1. Obtención de datos
    base_url = "https://docs.google.com/spreadsheets/d/1uDV3-CK5aeb-PI81uNc54t4L50HhscHe5xkp-pL9SyI"
    GID_HOJA = "0" 
    csv_url = f"{base_url}/export?format=csv&gid={GID_HOJA}"
    
    df = pd.read_csv(csv_url)
    df.columns = df.columns.str.strip()

    # --- LIMPIEZA DE DATOS ---
    # Limpiar M3
    if 'M3 Total' in df.columns:
        df['M3 Total'] = df['M3 Total'].astype(str).str.replace('.', '', regex=False).str.replace(',', '.', regex=False)
        df['M3 Total'] = pd.to_numeric(df['M3 Total'], errors='coerce').fillna(0)
    
    # Lógica de Instrucción (Columna U)
    # Si la columna U no está vacía y no dice 'SIN INSTRUCCION', está instruido
    df['Instruido'] = df['Fecha de Instruccion'].notna() & (df['Fecha de Instruccion'].astype(str).str.upper() != 'SIN INSTRUCCION')

    # --- TÍTULO GENÉRICO ---
    st.title("🚢 Tablero Logística Internacional")
    st.markdown("---")

    # --- SOLAPAS ---
    tab1, tab2, tab3 = st.tabs(["🏗️ Origen", "🚢 En Tránsito", "🏁 Destino Final"])

    with tab1:
        st.subheader("Estado de Carga en Origen")
        
        # Totales Generales
        m3_totales = df['M3 Total'].sum()
        cant_so = df['SO'].nunique() if 'SO' in df.columns else len(df)
        
        # Métricas Grandes y Centradas
        c1, c2 = st.columns(2)
        c1.metric("📦 CANTIDAD DE SO", f"{int(cant_so)}")
        c2.metric("📐 VOLUMEN TOTAL", f"{int(m3_totales):,} m³")

        st.markdown("---")

        # --- ANÁLISIS DE INSTRUCCIÓN ---
        st.subheader("Resumen de Instrucción")
        
        instruidos_m3 = df[df['Instruido'] == True]['M3 Total'].sum()
        no_instruidos_m3 = df[df['Instruido'] == False]['M3 Total'].sum()
        
        perc_instruido = (instruidos_m3 / m3_totales * 100) if m3_totales > 0 else 0
        perc_pendiente = 100 - perc_instruido

        i1, i2 = st.columns(2)
        i1.metric("✅ INSTRUIDO", f"{int(perc_instruido)}%")
        i2.metric("⏳ PENDIENTE", f"{int(perc_pendiente)}%")

        st.markdown("---")

        # --- TABLA POR PAÍS (REDONDEADA Y CON TOTAL) ---
        if 'Pais Destino' in df.columns:
            st.subheader("Participación por Destino")
            
            resumen = df.groupby('Pais Destino').agg({
                'SO': 'count',
                'M3 Total': 'sum'
            }).rename(columns={'SO': 'Cant. SO', 'M3 Total': 'M3 en Origen'})
            
            resumen['% del Total'] = ((resumen['M3 en Origen'] / m3_totales) * 100).round(0)
            resumen = resumen.sort_values(by='M3 en Origen', ascending=False)

            # Fila de Total
            total_row = pd.DataFrame({
                'Cant. SO': [resumen['Cant. SO'].sum()],
                'M3 en Origen': [resumen['M3 en Origen'].sum()],
                '% del Total': [100]
            }, index=['TOTAL'])

            resumen_final = pd.concat([resumen, total_row])
            
            # Formatear números a enteros (redondeados)
            st.dataframe(
                resumen_final.style.format({
                    'Cant. SO': '{:,.0f}',
                    'M3 en Origen': '{:,.0f}',
                    '% del Total': '{:.0f}%'
                }), 
                use_container_width=True
            )

except Exception as e:
    st.error(f"Error en la carga de datos: {e}")
