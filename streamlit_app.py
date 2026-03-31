import streamlit as st
import pandas as pd
import plotly.express as px
from datetime import datetime, timedelta
import time

# --- 1. CONFIGURACIÓN DE PÁGINA ---
st.set_page_config(page_title="BIDCOM | Dashboard Ejecutivo", layout="wide")

# --- 2. DISEÑO BIDCOM IMPACTO TOTAL (CSS) ---
st.markdown("""
    <style>
    .block-container { padding: 1rem 2rem; }
    .main { background-color: #040911; color: #ffffff; }
    .stTabs [data-baseweb="tab-list"] { justify-content: center !important; gap: 30px; margin-bottom: 40px; }
    .bidcom-header {
        background: linear-gradient(135deg, #001f3f 0%, #003366 100%);
        padding: 30px; border-radius: 20px; border: 1px solid #004080;
        text-align: center; margin-bottom: 30px;
        box-shadow: 0 0 30px rgba(0, 168, 255, 0.3);
    }
    .bidcom-header h1 { font-size: 60px; letter-spacing: 10px; color: #ffffff; font-weight: 900; margin: 0; text-shadow: 2px 2px 15px rgba(0, 168, 255, 0.8); }
    .bidcom-subtitle { font-size: 18px; color: #00a8ff; letter-spacing: 4px; text-transform: uppercase; font-weight: 600; margin-top: 5px; }
    .metric-container { text-align: center; padding: 20px; }
    .label-massive { font-size: 24px; color: #00a8ff; letter-spacing: 5px; text-transform: uppercase; font-weight: 800; margin-bottom: 5px; }
    .value-massive { font-size: 120px; font-weight: 900; color: #00a8ff; line-height: 1; margin: 0; text-shadow: 0 0 30px rgba(0,168,255,0.5); }
    .stButton>button {
        border-radius: 15px !important; color: white !important;
        width: 100%; height: 140px; font-weight: 800 !important; font-size: 18px !important;
        background: rgba(255, 255, 255, 0.03) !important; border: 1px solid rgba(255, 255, 255, 0.1) !important;
        transition: all 0.3s ease-in-out !important;
    }
    .stButton>button:hover { background-color: rgba(0, 168, 255, 0.2) !important; border-color: #00a8ff !important; color: #00a8ff !important; box-shadow: 0 0 20px rgba(0, 168, 255, 0.4) !important; }
    .chart-title { text-align: center; letter-spacing: 2px; color: #00a8ff; font-weight: 900; font-size: 20px; margin: 25px 0 15px 0; text-transform: uppercase; }
    
    /* Estilos para KPI de Reservas */
    .reserva-box {
        background: rgba(0, 168, 255, 0.05);
        padding: 15px;
        border-radius: 12px;
        border: 1px solid #004080;
        text-align: center;
    }
    </style>
    """, unsafe_allow_html=True)

try:
    # --- 3. CARGA DE DATOS ---
    base_url = "https://docs.google.com/spreadsheets/d/1uDV3-CK5aeb-PI81uNc54t4L50HhscHe5xkp-pL9SyI"
    
    # Origen (GID 0)
    df = pd.read_csv(f"{base_url}/export?format=csv&gid=0&nocache={time.time()}")
    df.columns = df.columns.str.strip()

    if 'M3 Total' in df.columns:
        df['M3 Total'] = df['M3 Total'].astype(str).str.replace('.', '', regex=False).str.replace(',', '.', regex=False)
        df['M3 Total'] = pd.to_numeric(df['M3 Total'], errors='coerce').fillna(0)
    
    # Procesamiento Fechas Origen
    df.iloc[:, 23] = df.iloc[:, 23].astype(str).str.strip()
    df.iloc[:, 24] = df.iloc[:, 24].astype(str).str.strip()
    df['ETD_DT'] = pd.to_datetime(df.iloc[:, 23], errors='coerce')
    df['ETA_DT'] = pd.to_datetime(df.iloc[:, 24], errors='coerce')
    df['Fecha_Prior_DT'] = pd.to_datetime(df.iloc[:, 99], errors='coerce') 
    
    hoy = pd.Timestamp(datetime.now().date())
    inicio_mes = hoy.replace(day=1)
    limite_proximo = hoy + timedelta(days=30)

    def label_proyeccion(fecha, pivot):
        if pd.isna(fecha): return "SIN FECHA"
        if fecha.year < 2024: return "PASADO/REALIZADO"
        if fecha < pivot: return "PASADO/REALIZADO"
        return fecha.strftime('%m/%Y')

    df['Mes_ETD_Full'] = df['ETD_DT'].apply(lambda x: label_proyeccion(x, inicio_mes))
    df['Mes_ETA_Full'] = df['ETA_DT'].apply(lambda x: label_proyeccion(x, hoy))

    meses_eta = [m for m in df['Mes_ETA_Full'].unique() if m not in ["PASADO/REALIZADO", "SIN FECHA"]]
    meses_eta_ordenados = sorted(meses_eta, key=lambda x: datetime.strptime(x, '%m/%Y'))
    orden_final_eta = ["PASADO/REALIZADO"] + meses_eta_ordenados + ["SIN FECHA"]
    df['Mes_ETA_Full'] = pd.Categorical(df['Mes_ETA_Full'], categories=orden_final_eta, ordered=True)

    m3_totales_global = round(df['M3 Total'].sum())
    cant_so_global = len(df)
    cant_proveedores_global = df['Proveedor'].nunique() if 'Proveedor' in df.columns else 0

    st.markdown("<div class='bidcom-header'><h1>BIDCOM</h1><div class='bidcom-subtitle'>Tablero Logistica Internacional</div></div>", unsafe_allow_html=True)
    tabs = st.tabs(["ORIGEN", "CONTROL GESTIÓN RESERVAS", "INDICADORES", "AGENTES", "ANALISTAS", "FLETES"])

  # --- SOLAPA 1: ORIGEN ---
    with tabs[0]:
        try:
            # --- CÁLCULOS LOCALES ---
            df['Fecha_Inst_DT'] = pd.to_datetime(df['Fecha de Instruccion'], errors='coerce')
            cond_instruido = df['Fecha_Inst_DT'].notna() & ~(df['Fecha de Instruccion'].astype(str).str.upper().str.contains("SIN INSTRUCCION", na=False))
            cond_critico = (~cond_instruido) & (df['Fecha_Prior_DT'] <= limite_proximo)
            cond_resto = (~cond_instruido) & (~cond_critico)

            df_inst = df[cond_instruido].copy()
            df_criticos = df[cond_critico].copy()
            df_resto = df[cond_resto].copy()

            # Totales y Porcentajes Redondeados
            m3_inst = int(round(df_inst['M3 Total'].sum()))
            m3_crit = int(round(df_criticos['M3 Total'].sum()))
            m3_rest = int(round(df_resto['M3 Total'].sum()))

            p_inst_val = int(round(m3_inst / m3_totales_global * 100)) if m3_totales_global > 0 else 0
            p_crit_val = int(round(m3_crit / m3_totales_global * 100)) if m3_totales_global > 0 else 0
            p_rest_val = int(round(m3_rest / m3_totales_global * 100)) if m3_totales_global > 0 else 0

            # --- BLOQUE 1: KPIs ULTRA MASIVOS ---
            st.markdown("<br>", unsafe_allow_html=True)
            o1, o2, o3 = st.columns(3)
            with o1: st.markdown(f"<div class='metric-container'><p style='font-size: 22px; color: #00a8ff; letter-spacing: 4px; font-weight: 700; margin-bottom: 0;'>CANTIDAD DE SO</p><p style='font-size: 90px; font-weight: 900; color: #00a8ff; line-height: 1; margin: 0; text-shadow: 0 0 25px rgba(0,168,255,0.4);'>{int(cant_so_global)}</p></div>", unsafe_allow_html=True)
            with o2: st.markdown(f"<div class='metric-container'><p style='font-size: 22px; color: #00a8ff; letter-spacing: 4px; font-weight: 700; margin-bottom: 0;'>VOLUMEN TOTAL (M3)</p><p style='font-size: 90px; font-weight: 900; color: #00a8ff; line-height: 1; margin: 0; text-shadow: 0 0 25px rgba(0,168,255,0.4);'>{int(round(m3_totales_global)):,}</p></div>", unsafe_allow_html=True)
            with o3: st.markdown(f"<div class='metric-container'><p style='font-size: 22px; color: #00a8ff; letter-spacing: 4px; font-weight: 700; margin-bottom: 0;'>PROVEEDORES</p><p style='font-size: 90px; font-weight: 900; color: #00a8ff; line-height: 1; margin: 0; text-shadow: 0 0 25px rgba(0,168,255,0.4);'>{int(cant_proveedores_global)}</p></div>", unsafe_allow_html=True)

            st.markdown("<br><hr style='opacity:0.1;'><br>", unsafe_allow_html=True)

         # --- BLOQUE 2: BOTONES DE FILTRADO CON RESALTADO DINÁMICO ---
            b1_col, b2_col, b3_col, b4_col, b5_col = st.columns(5)
            
            # Recuperamos el filtro activo del session_state
            filtro_actual = st.session_state.get('f')

            # Función para aplicar estilo de "Resaltado"
            def get_btn_style(target):
                if filtro_actual == target:
                    return "border: 2px solid #00a8ff; background: rgba(0, 168, 255, 0.1);"
                return "border: 1px solid #1e293b; background: transparent;"

            # Botón 1: MERCADERÍA INSTRUIDA
            with b1_col:
                st.markdown(f"<div style='{get_btn_style('inst')} border-radius:5px;'>", unsafe_allow_html=True)
                if st.button(f"MERCADERIA \n INSTRUIDA {p_inst_val}%", key="btn_inst_o", use_container_width=True):
                    st.session_state.f = 'inst' if filtro_actual != 'inst' else None
                    st.rerun()
                st.markdown("</div>", unsafe_allow_html=True)

            # Botón 2: PRÓXIMA A INSTRUIR
            with b2_col:
                st.markdown(f"<div style='{get_btn_style('crit')} border-radius:5px;'>", unsafe_allow_html=True)
                if st.button(f"PROXIMA A \n INSTRUIR {p_crit_val}%", key="btn_crit_o", use_container_width=True):
                    st.session_state.f = 'crit' if filtro_actual != 'crit' else None
                    st.rerun()
                st.markdown("</div>", unsafe_allow_html=True)

            # Botón 3: LISTA EN +30 DIAS
            with b3_col:
                st.markdown(f"<div style='{get_btn_style('rest')} border-radius:5px;'>", unsafe_allow_html=True)
                if st.button(f"LISTA EN \n +30 DIAS {p_rest_val}%", key="btn_rest_o", use_container_width=True):
                    st.session_state.f = 'rest' if filtro_actual != 'rest' else None
                    st.rerun()
                st.markdown("</div>", unsafe_allow_html=True)

            # Botón 4: TOP 100 RANKING
            with b4_col:
                st.markdown(f"<div style='{get_btn_style('rank')} border-radius:5px;'>", unsafe_allow_html=True)
                if st.button("TOP 100 \n RANKING", key="btn_rank_o", use_container_width=True):
                    st.session_state.f = 'rank' if filtro_actual != 'rank' else None
                    st.rerun()
                st.markdown("</div>", unsafe_allow_html=True)

            # Botón 5: MONOPROVEEDOR / CONSOLIDADO
            with b5_col:
                st.markdown(f"<div style='{get_btn_style('estr')} border-radius:5px;'>", unsafe_allow_html=True)
                if st.button("MONOPROV. / \n CONSOLIDADO", key="btn_estr_o", use_container_width=True):
                    st.session_state.f = 'estr' if filtro_actual != 'estr' else None
                    st.rerun()
                st.markdown("</div>", unsafe_allow_html=True)

            # --- BLOQUE 3: CUADROS DESPLEGABLES (DISEÑO TARJETA RESERVAS) ---
            f = st.session_state.get('f')
            if f:
                st.markdown("<br>", unsafe_allow_html=True)
                
                if f in ["inst", "crit", "rest"]:
                    if f == "inst": titulo, dff, color = "MERCADERIA INSTRUIDA", df_inst, "#00a8ff"
                    elif f == "crit": titulo, dff, color = "PROXIMA A INSTRUIR", df_criticos, "#ff4b4b"
                    elif f == "rest": titulo, dff, color = "LISTA EN +30 DIAS", df_resto, "#8899A6"
                    
                    cant_so_f = len(dff)
                    m3_f = int(round(dff['M3 Total'].sum()))
                    
                    # Diseño de Tarjeta igual a Reservas
                    st.markdown(f"""
                        <div style="background: rgba(255,255,255,0.02); padding: 25px; border-radius: 10px; border-left: 5px solid {color}; margin-bottom: 20px;">
                            <p style="font-weight:700; color:{color}; margin-bottom:15px; font-size:14px; letter-spacing:1px;">{titulo} ({int(round(m3_f/m3_totales_global*100)) if m3_totales_global > 0 else 0}%)</p>
                            <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 20px;">
                                <div><p style="font-size:11px; color:#8899A6; margin:0;">CANTIDAD SO</p><p style="font-size:26px; font-weight:300; margin:0; color:#ffffff;">{cant_so_f}</p></div>
                                <div><p style="font-size:11px; color:#8899A6; margin:0;">VOLUMEN TOTAL</p><p style="font-size:26px; font-weight:300; margin:0; color:#ffffff;">{m3_f:,} M3</p></div>
                            </div>
                        </div>
                    """, unsafe_allow_html=True)
                    st.dataframe(dff[['SO', 'Proveedor', 'M3 Total', 'Fecha de Instruccion' if f=='inst' else df.columns[99]]], use_container_width=True)

                elif f == "rank":
                    col_rank = df.columns[1]
                    col_prior = df.columns[99]
                    df_rank = df[pd.to_numeric(df[col_rank], errors='coerce') <= 100].sort_values(by=col_rank).copy()
                    df_rank['Status'] = df_rank['Fecha_Inst_DT'].apply(lambda x: "✅ OK" if pd.notna(x) else "❌ PEND")
                    
                    st.markdown(f"""
                        <div style="background: rgba(255,255,255,0.02); padding: 25px; border-radius: 10px; border-left: 5px solid #00a8ff; margin-bottom: 20px;">
                            <p style="font-weight:700; color:#00a8ff; margin-bottom:15px; font-size:14px; letter-spacing:1px;">TOP 100 RANKING - RESUMEN</p>
                            <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 20px;">
                                <div><p style="font-size:11px; color:#8899A6; margin:0;">EMBARQUES EN RANGO</p><p style="font-size:26px; font-weight:300; margin:0; color:#ffffff;">{len(df_rank)}</p></div>
                                <div><p style="font-size:11px; color:#8899A6; margin:0;">M3 TOTAL PRIORITARIO</p><p style="font-size:26px; font-weight:300; margin:0; color:#ffffff;">{int(df_rank['M3 Total'].sum()):,} M3</p></div>
                            </div>
                        </div>
                    """, unsafe_allow_html=True)
                    st.dataframe(df_rank[['SO', col_rank, 'Proveedor', col_prior, 'M3 Total', 'Status']], use_container_width=True)

                elif f == "estr":
                    col_cp = df.columns[93]
                    df['Tipo_Carga'] = df[col_cp].apply(lambda x: 'MONOPROVEEDOR' if str(x).upper() == 'SI' else 'CONSOLIDADO')
                    
                    st.markdown("<p style='color:#00a8ff; font-weight:700; letter-spacing:1px; margin-bottom:15px;'>ANALISIS ESTRUCTURA CARGA</p>", unsafe_allow_html=True)
                    e1, e2 = st.columns(2)
                    tipos = ["CONSOLIDADO", "MONOPROVEEDOR"]
                    colores_e = ["#8899A6", "#00a8ff"]
                    
                    for i, t_carga in enumerate(tipos):
                        df_c = df[df['Tipo_Carga'] == t_carga]
                        with [e1, e2][i]:
                            st.markdown(f"""
                                <div style="background: rgba(255,255,255,0.02); padding: 20px; border-radius: 10px; border-left: 5px solid {colores_e[i]};">
                                    <p style="font-weight:700; color:{colores_e[i]}; margin-bottom:10px; font-size:13px;">{t_carga}</p>
                                    <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 10px;">
                                        <div><p style="font-size:10px; color:#8899A6; margin:0;">CANT. SO</p><p style="font-size:22px; font-weight:300; margin:0; color:#ffffff;">{len(df_c)}</p></div>
                                        <div><p style="font-size:10px; color:#8899A6; margin:0;">TOTAL M3</p><p style="font-size:22px; font-weight:300; margin:0; color:#ffffff;">{int(df_c['M3 Total'].sum()):,}</p></div>
                                    </div>
                                </div>
                            """, unsafe_allow_html=True)

            st.markdown("<br><hr style='opacity:0.1'><br>", unsafe_allow_html=True)

 # --- BLOQUE 4: PARTICIPACIÓN POR PAÍS (CON CORRECCIÓN "SIN DEFINIR") ---
            st.markdown("<br>", unsafe_allow_html=True)
            st.markdown("<p style='color:#00a8ff; font-weight:700; letter-spacing:2px; font-size:14px; margin-bottom:20px;'>DISTRIBUCIÓN GEOGRÁFICA DE CARGA</p>", unsafe_allow_html=True)
            
            # Limpieza de datos: Rellenamos vacíos en Pais Destino antes de agrupar
            df['Pais Destino'] = df['Pais Destino'].fillna('SIN DEFINIR').replace('', 'SIN DEFINIR')
            
            res_p = df.groupby('Pais Destino').agg({'SO': 'count', 'M3 Total': 'sum'}).rename(columns={'SO': 'CANT_SO', 'M3 Total': 'M3'}).sort_values(by='M3', ascending=False)
            
            # Totales para la fila final
            total_so_p = res_p['CANT_SO'].sum()
            total_m3_p = res_p['M3'].sum()

            # Encabezado con línea blanca sólida
            h1, h2, h3, h4 = st.columns([1.5, 1, 1, 0.8])
            h1.markdown("<p style='color:#8899A6; font-size:12px; font-weight:700;'>PAÍS DE DESTINO</p>", unsafe_allow_html=True)
            h2.markdown("<p style='color:#8899A6; font-size:12px; font-weight:700; text-align:center;'>VOLUMEN (M3)</p>", unsafe_allow_html=True)
            h3.markdown("<p style='color:#8899A6; font-size:12px; font-weight:700; text-align:center;'>CANTIDAD SO</p>", unsafe_allow_html=True)
            h4.markdown("<p style='color:#8899A6; font-size:12px; font-weight:700; text-align:right;'>SHARE %</p>", unsafe_allow_html=True)
            st.markdown("<hr style='margin:0; border: none; border-top: 2px solid #ffffff; opacity:0.8;'>", unsafe_allow_html=True)

            # Filas de países con líneas divisoras blancas sutiles
            for pais, row in res_p.iterrows():
                m3_v = int(round(row['M3']))
                so_v = int(row['CANT_SO'])
                # Usamos el total calculado de la tabla para que el % sea exacto sobre lo visualizado
                pct_v = int(round((m3_v / total_m3_p * 100))) if total_m3_p > 0 else 0
                
                # Resaltamos "SIN DEFINIR" en un color grisáceo si aparece
                color_texto = "#ffffff" if pais != "SIN DEFINIR" else "#8899A6"
                
                c1, c2, c3, c4 = st.columns([1.5, 1, 1, 0.8])
                c1.markdown(f"<p style='color:{color_texto}; font-weight:700; font-size:16px; margin:12px 0;'>{pais.upper()}</p>", unsafe_allow_html=True)
                c2.markdown(f"<p style='color:#00a8ff; font-weight:300; font-size:22px; text-align:center; margin:8px 0;'>{m3_v:,}</p>", unsafe_allow_html=True)
                c3.markdown(f"<p style='color:{color_texto}; font-weight:300; font-size:22px; text-align:center; margin:8px 0;'>{so_v}</p>", unsafe_allow_html=True)
                c4.markdown(f"<p style='color:#00ff88; font-weight:700; font-size:18px; text-align:right; margin:10px 0;'>{pct_v}%</p>", unsafe_allow_html=True)
                
                st.markdown("<hr style='margin:0; border: none; border-top: 1px solid #ffffff; opacity:0.2;'>", unsafe_allow_html=True)

            # --- FILA DE TOTALES (RESALTADA) ---
            t1, t2, t3, t4 = st.columns([1.5, 1, 1, 0.8])
            t1.markdown("<p style='color:#ffffff; font-weight:900; font-size:18px; margin:15px 0;'>TOTAL GENERAL</p>", unsafe_allow_html=True)
            t2.markdown(f"<p style='color:#00a8ff; font-weight:700; font-size:24px; text-align:center; margin:10px 0;'>{int(round(total_m3_p)):,}</p>", unsafe_allow_html=True)
            t3.markdown(f"<p style='color:#ffffff; font-weight:700; font-size:24px; text-align:center; margin:10px 0;'>{int(total_so_p)}</p>", unsafe_allow_html=True)
            t4.markdown("<p style='color:#00ff88; font-weight:900; font-size:20px; text-align:right; margin:15px 0;'>100%</p>", unsafe_allow_html=True)
            
            st.markdown("<hr style='margin:0; border: none; border-top: 2px solid #ffffff; opacity:0.8;'>", unsafe_allow_html=True)
            st.markdown("<br><br>", unsafe_allow_html=True)

      # --- BLOQUE 5: GRÁFICOS DE PROYECCIÓN Y SALIDA (FORMATO MAXIMIZADO Y CENTRADO) ---
            st.markdown("<br><br>", unsafe_allow_html=True)
            
            # 1. Gráfico de Puertos (Ocupa todo el ancho arriba)
            st.markdown("<p style='color:#00a8ff; font-weight:700; font-size:16px; text-align:center; letter-spacing:1px; margin-bottom:15px;'>DISTRIBUCIÓN POR PUERTO DE SALIDA (M3)</p>", unsafe_allow_html=True)
            col_puerto = df.columns[41]
            p_df = df.groupby(col_puerto).agg({'M3 Total': 'sum'}).reset_index().sort_values(by='M3 Total')
            
            fig_p = px.bar(p_df, y=col_puerto, x='M3 Total', orientation='h', 
                           text_auto=',.0f', color_discrete_sequence=['#00a8ff'], template='plotly_dark')
            fig_p.update_traces(textposition='outside', cliponaxis=False, textfont_size=14, textfont_color="white")
            fig_p.update_layout(
                xaxis_visible=False, 
                yaxis_title=None, 
                height=500, 
                margin=dict(l=150, r=100, t=20, b=20),
                font=dict(size=13),
                paper_bgcolor='rgba(0,0,0,0)',
                plot_bgcolor='rgba(0,0,0,0)'
            )
            st.plotly_chart(fig_p, use_container_width=True)

            st.markdown("<br><br><hr style='opacity:0.1;'><br>", unsafe_allow_html=True)

            # 2. Proyecciones en 2 Columnas con SEPARADOR central
            # El [1, 0.2, 1] crea una columna del 20% de ancho vacía en el medio para separar
            ga, g_sep, gb = st.columns([1, 0.2, 1])
            
            with ga:
                st.markdown("<p style='color:#00ff88; font-weight:700; font-size:15px; text-align:center; margin-bottom:15px;'>PROYECCIÓN MENSUAL ETD</p>", unsafe_allow_html=True)
                etd_p = df.groupby('Mes_ETD_Full').agg({'M3 Total': 'sum'}).reset_index()
                fig_e = px.bar(etd_p, x='Mes_ETD_Full', y='M3 Total', text_auto=',.0f', 
                               color_discrete_sequence=['#00ff88'], template='plotly_dark')
                fig_e.update_traces(textfont_size=14, textposition='outside', textfont_color="white")
                fig_e.update_layout(
                    yaxis_visible=False, 
                    xaxis_title=None, 
                    height=450, 
                    margin=dict(l=20, r=20, t=40, b=20),
                    font=dict(size=12),
                    paper_bgcolor='rgba(0,0,0,0)',
                    plot_bgcolor='rgba(0,0,0,0)'
                )
                st.plotly_chart(fig_e, use_container_width=True)
            
            with gb:
                st.markdown("<p style='color:#ff4b4b; font-weight:700; font-size:15px; text-align:center; margin-bottom:15px;'>PROYECCIÓN MENSUAL ETA</p>", unsafe_allow_html=True)
                eta_p = df.groupby('Mes_ETA_Full', observed=True).agg({'M3 Total': 'sum'}).reset_index()
                fig_a = px.bar(eta_p, x='Mes_ETA_Full', y='M3 Total', text_auto=',.0f', 
                               color_discrete_sequence=['#ff4b4b'], template='plotly_dark')
                fig_a.update_traces(textfont_size=14, textposition='outside', textfont_color="white")
                fig_a.update_layout(
                    yaxis_visible=False, 
                    xaxis_title=None, 
                    height=450, 
                    margin=dict(l=20, r=20, t=40, b=20),
                    font=dict(size=12),
                    paper_bgcolor='rgba(0,0,0,0)',
                    plot_bgcolor='rgba(0,0,0,0)'
                )
                st.plotly_chart(fig_a, use_container_width=True)

        except Exception as e:
            st.error(f"Error en Solapa Origen: {e}")

    # --- SOLAPA 2: CONTROL GESTIÓN RESERVAS ---
    with tabs[1]:
        try:
            url_reserva = f"{base_url}/export?format=csv&gid=276804813&nocache={time.time()}"
            df_reserva = pd.read_csv(url_reserva)
            df_reserva.columns = df_reserva.columns.str.strip()

            # Filtrar solo lo instruido (Columna H)
            df_reserva['Fecha_Inst_H'] = df_reserva.iloc[:, 7].astype(str).str.strip()
            df_gestion = df_reserva[df_reserva['Fecha_Inst_H'].apply(lambda x: len(x) > 4)].copy()

            st.markdown("<h2 style='text-align: center; color: #ffffff;'>CONTROL DE GESTIÓN DE RESERVAS</h2>", unsafe_allow_html=True)
            
            # KPIs Gerenciales
            c1, c2, c3 = st.columns(3)
            with c1: st.markdown(f"<div class='metric-container'><p class='label-massive'>SO INSTRUIDAS</p><p class='value-massive'>{int(len(df_inst))}</p></div>", unsafe_allow_html=True)
            with c2: st.markdown(f"<div class='metric-container'><p class='label-massive'>VOLUMEN (M3)</p><p class='value-massive'>{int(df_inst['M3 Total'].sum()):,}</p></div>", unsafe_allow_html=True)
            with c3: st.markdown(f"<div class='metric-container'><p class='label-massive'>PROVEEDORES</p><p class='value-massive'>{int(df_inst['Proveedor'].nunique())}</p></div>", unsafe_allow_html=True)

            st.markdown("<br><hr style='opacity:0.1'><br>", unsafe_allow_html=True)

            # Clasificación de Transporte (Columna F)
            def clasificar_transporte(x):
                x = str(x).upper()
                if any(m in x for m in ["40 HQ", "40 ST", "20 ST", "40NOR"]): return "MARÍTIMO"
                if any(a in x for a in ["AVION", "COURIER"]): return "AÉREO / COURIER"
                return "OTROS"

            df_gestion['Transporte'] = df_gestion.iloc[:, 5].apply(clasificar_transporte)
            res_t = df_gestion['Transporte'].value_counts()
            
            t1, t2 = st.columns(2)
            with t1: st.metric("EMBARQUES MARÍTIMOS", f"{res_t.get('MARÍTIMO', 0)} Emb.")
            with t2: st.metric("EMBARQUES AÉREO / COURIER", f"{res_t.get('AÉREO / COURIER', 0)} Emb.")

            st.markdown("<br>", unsafe_allow_html=True)

            # Status OK (Columna K)
            df_gestion['ETD_Status_K'] = df_gestion.iloc[:, 10].astype(str).str.upper().str.strip()
            confirmados = df_gestion[df_gestion['ETD_Status_K'] == "OK"].shape[0]
            pendientes = len(df_gestion) - confirmados
            p_ok = round((confirmados / len(df_gestion) * 100)) if len(df_gestion) > 0 else 0

            m_col1, m_col2, m_col3 = st.columns(3)
            m_col1.metric("ETD OK (CONFIRMADOS)", f"{confirmados} Emb.")
            m_col2.metric("SIN ETD OK (PENDIENTES)", f"{pendientes} Emb.")
            m_col3.metric("% GESTIÓN OK", f"{p_ok}%", delta=f"{p_ok}%", delta_color="normal" if confirmados >= pendientes else "inverse")

            st.markdown("<br>", unsafe_allow_html=True)
            st.dataframe(df_gestion.drop(columns=['Transporte', 'ETD_Status_K', 'Fecha_Inst_H']), use_container_width=True)

        except Exception as e:
            st.error(f"Error en Gestión: {e}")

except Exception as e:
    st.error(f"Error crítico: {e}")
