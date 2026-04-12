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
@import url('https://fonts.googleapis.com/css2?family=Outfit:wght@300;400;600;700;900&display=swap');

/* TIPO Y FONDO GENERAL */
html, body, [class*="css"] {
    font-family: 'Outfit', sans-serif !important;
}
.block-container { padding: 2rem 3rem; }
.main { background-color: #020617; color: #f8fafc; }

/* ANIMACIONES */
@keyframes fadeInDown {
    from { opacity: 0; transform: translateY(-40px); }
    to { opacity: 1; transform: translateY(0); }
}
@keyframes fadeInUp {
    from { opacity: 0; transform: translateY(40px); }
    to { opacity: 1; transform: translateY(0); }
}
@keyframes pulseGlow {
    0% { box-shadow: 0 0 20px rgba(0, 168, 255, 0.2); }
    50% { box-shadow: 0 0 40px rgba(0, 168, 255, 0.4); }
    100% { box-shadow: 0 0 20px rgba(0, 168, 255, 0.2); }
}

/* TABS */
.stTabs [data-baseweb="tab-list"] { 
    justify-content: center !important; 
    gap: 20px; 
    margin-bottom: 50px; 
    animation: fadeInUp 0.8s ease-out;
}
.stTabs [data-baseweb="tab"] { 
    background-color: transparent !important;
    border-radius: 8px !important;
    border: 1px solid transparent !important;
    transition: all 0.3s ease;
    padding: 12px 24px;
    color: #475569 !important;
    font-weight: 700 !important;
    letter-spacing: 2px;
}
.stTabs [aria-selected="true"] {
    background: rgba(0, 168, 255, 0.1) !important;
    box-shadow: 0 0 25px rgba(0, 168, 255, 0.2) !important;
    color: #00a8ff !important;
    border: 1px solid rgba(0, 168, 255, 0.3) !important;
}

/* ENCABEZADO */
.bidcom-header {
    background: linear-gradient(135deg, rgba(0,31,63,0.7) 0%, rgba(0,51,102,0.8) 100%);
    backdrop-filter: blur(20px);
    -webkit-backdrop-filter: blur(20px);
    padding: 50px; 
    border-radius: 24px; 
    border: 1px solid rgba(0, 168, 255, 0.2);
    text-align: center; 
    margin-bottom: 40px;
    box-shadow: 0 25px 50px -12px rgba(0,0,0,0.6), inset 0 0 40px rgba(0,168,255,0.1);
    animation: fadeInDown 1s cubic-bezier(0.2, 0.8, 0.2, 1);
}
.bidcom-header h1 { 
    font-size: 80px; 
    letter-spacing: 20px; 
    font-weight: 900; 
    margin: 0; 
    background: linear-gradient(180deg, #ffffff 0%, #00a8ff 150%);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    text-shadow: 0px 10px 40px rgba(0, 168, 255, 0.5); 
}
.bidcom-subtitle { 
    font-size: 22px; 
    color: #00a8ff; 
    letter-spacing: 12px; 
    text-transform: uppercase; 
    font-weight: 600; 
    margin-top: 15px; 
    text-shadow: 0 0 15px rgba(0, 168, 255, 0.4);
}

/* KPIs PRINCIPALES MASIVOS */
.metric-container { 
    text-align: center; 
    padding: 35px 20px; 
    background: linear-gradient(145deg, rgba(255,255,255,0.03) 0%, rgba(255,255,255,0.01) 100%);
    border-radius: 24px;
    border: 1px solid rgba(255,255,255,0.05);
    backdrop-filter: blur(15px);
    -webkit-backdrop-filter: blur(15px);
    box-shadow: 0 10px 30px rgba(0,0,0,0.4);
    transition: all 0.4s cubic-bezier(0.4, 0, 0.2, 1);
    animation: fadeInUp 0.8s backwards;
}
/* .metric-container:hover eliminado por ser no accionable */
.metric-container p:first-child { 
    font-size: 18px !important;
    color: #94a3b8 !important; 
    letter-spacing: 6px !important;
    font-weight: 700 !important;
    margin-bottom: 15px !important;
    text-transform: uppercase;
}
.metric-container p:last-child { 
    font-size: 85px !important; 
    font-weight: 900 !important; 
    color: #fff !important; 
    line-height: 1 !important; 
    margin: 0 !important; 
    text-shadow: 0 0 40px rgba(0,168,255,0.7), 0 0 10px rgba(0,168,255,0.4) !important; 
}

/* TARJETAS GLASSMORPHISM STANDARDS */
.custom-card {
    background: linear-gradient(145deg, rgba(255,255,255,0.04) 0%, rgba(255,255,255,0.01) 100%);
    padding: 30px; 
    border-radius: 20px; 
    backdrop-filter: blur(15px);
    -webkit-backdrop-filter: blur(15px);
    border: 1px solid rgba(255,255,255,0.08); /* DEFAULT */
    box-shadow: 0 10px 35px rgba(0,0,0,0.35);
    transition: all 0.4s ease;
    margin-bottom: 25px;
    animation: fadeInUp 1s backwards;
}
/* .custom-card:hover eliminado por ser no accionable */

.custom-card-title {
    font-weight: 700;
    font-size: 16px;
    letter-spacing: 3px;
    margin-bottom: 20px;
    margin-top: 0;
    text-transform: uppercase;
}
.grid-2 {
    display: grid; 
    grid-template-columns: 1fr 1fr; 
    gap: 20px;
}
.grid-4 {
    display: grid; 
    grid-template-columns: 1fr 1fr 1fr 1fr; 
    gap: 20px;
}
.minicard-title {
    font-size: 11px; 
    color: #94a3b8; 
    letter-spacing: 2px;
    margin: 0 0 5px 0;
    font-weight: 600;
}
.minicard-value {
    font-size: 28px; 
    font-weight: 300; 
    margin: 0; 
    color: #f8fafc;
}

/* BOTONES GLOBALES Y FILTROS */
.stButton>button {
    border-radius: 16px !important; 
    color: #f8fafc !important;
    width: 100%; 
    height: 110px; 
    font-weight: 700 !important; 
    font-size: 15px !important;
    background: rgba(15, 23, 42, 0.4) !important; 
    backdrop-filter: blur(8px);
    border: 1px solid rgba(255, 255, 255, 0.08) !important;
    transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1) !important;
    line-height: 1.4 !important;
    letter-spacing: 1px;
}
.stButton>button:hover { 
    background-color: rgba(0, 168, 255, 0.15) !important; 
    border-color: #00a8ff !important; 
    color: #ffffff !important; 
    box-shadow: 0 10px 30px rgba(0, 168, 255, 0.3), inset 0 0 20px rgba(0, 168, 255, 0.1) !important; 
    transform: translateY(-4px);
}

/* DECORATIVOS: LINEAS DIVISORAS */
.glow-divider {
    border: none;
    height: 2px;
    background: linear-gradient(90deg, transparent, rgba(0,168,255,0.4), transparent);
    margin: 40px 0;
    opacity: 0.6;
}
.white-divider {
    border: none;
    height: 1px;
    background: linear-gradient(90deg, transparent, rgba(255,255,255,0.2), transparent);
    margin: 30px 0;
}
</style>
""", unsafe_allow_html=True)

try:
    # --- 3. CARGA DE DATOS ---
    base_url = "https://docs.google.com/spreadsheets/d/1uDV3-CK5aeb-PI81uNc54t4L50HhscHe5xkp-pL9SyI"

    @st.cache_data(ttl=60)
    def load_main_data(url):
        df = pd.read_csv(url)
        df.columns = df.columns.str.strip()
        return df

    df = load_main_data(f"{base_url}/export?format=csv&gid=0&nocache={time.time()}")

    if 'M3 Total' in df.columns:
        df['M3 Total'] = df['M3 Total'].astype(str).str.replace('.', '', regex=False).str.replace(',', '.', regex=False)
        df['M3 Total'] = pd.to_numeric(df['M3 Total'], errors='coerce').fillna(0)

    if 'Fob total Origen' in df.columns:
        def clean_val(x):
            if isinstance(x, (int, float)): return x
            x = str(x).replace('USD', '').replace('$', '').replace(' ', '')
            num = ''.join(c for c in x if c.isdigit() or c in '.,')
            if ',' in num and '.' in num:
                num = num.replace('.', '').replace(',', '.')
            elif ',' in num:
                num = num.replace(',', '.')
            return pd.to_numeric(num, errors='coerce')
        df['Fob total Origen'] = df['Fob total Origen'].apply(clean_val).fillna(0)

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

    df = df[df['SO'].notna() & (df['SO'].astype(str).str.strip() != "") & (df['SO'].astype(str).str.strip().str.lower() != "nan")]
    m3_totales_global = round(df['M3 Total'].sum())
    cant_so_global = df['SO'].nunique()
    cant_proveedores_global = df['Proveedor'].nunique() if 'Proveedor' in df.columns else 0

    st.markdown("<div class='bidcom-header'><h1>BIDCOM</h1><div class='bidcom-subtitle'>Tablero Logístico Corporativo</div></div>", unsafe_allow_html=True)
    tabs = st.tabs(["ORIGEN", "CONTROL GESTIÓN RESERVAS", "INDICADORES", "AGENTES", "ANALISTAS", "FLETES", "COTIZACIÓN FFWW"])

    # --- SOLAPA 1: ORIGEN ---
    with tabs[0]:
        try:
            df['Fecha_Inst_DT'] = pd.to_datetime(df['Fecha de Instruccion'], errors='coerce')
            col_rank = df.columns[1]
            # Limpiar Ranking (manejo de puntos de miles y comas decimales)
            df['Rank_Num'] = df[col_rank].astype(str).str.replace('.', '', regex=False).str.replace(',', '.', regex=False)
            df['Rank_Num'] = pd.to_numeric(df['Rank_Num'], errors='coerce').fillna(999999)

            # --- CÁLCULOS PREVIOS DE STATUS ---
            col_cp = df.columns[93] # ES MONOPROVEEDOR?
            df['Tipo_Carga'] = df[col_cp].apply(lambda x: 'MONOPROVEEDOR' if str(x).upper() == 'SI' else 'CONSOLIDADO')
            
            # Tipo Repuesto (Gadnic, Muestras, Marcas)
            def get_tipo_repuesto(val):
                val_str = str(val).strip().lower()
                if val_str in ['', 'nan', 'none'] or pd.isna(val) or val_str == 'nan': return "Gadnic"
                if "muestra" in val_str: return "Muestras"
                if "sin planeamiento" in val_str: return "Marcas"
                return "Gadnic"
            df['Tipo_Repuesto'] = df['Repuestos'].apply(get_tipo_repuesto) if 'Repuestos' in df.columns else 'Gadnic'

            # Condiciones de Status
            cond_instruido = df['Fecha_Inst_DT'].notna() & ~(df['Fecha de Instruccion'].astype(str).str.upper().str.contains("SIN INSTRUCCION", na=False))
            cond_pendiente = ~cond_instruido
            
            # Nivel 1: Urgente (Vencida)
            cond_urgente = cond_pendiente & (df['Fecha_Prior_DT'] < hoy)
            
            # Nivel 2: Accionar (Próxima) - Lógica específica por Tipo de Carga
            cond_pd_futura = cond_pendiente & (df['Fecha_Prior_DT'] >= hoy)
            cond_acc_mono = cond_pd_futura & (df['Tipo_Carga'] == 'MONOPROVEEDOR') & (df['Fecha_Prior_DT'] <= hoy + timedelta(days=25))
            cond_acc_consol = cond_pd_futura & (df['Tipo_Carga'] == 'CONSOLIDADO') & (df['Fecha_Prior_DT'] <= hoy + timedelta(days=10))
            cond_accionar = cond_acc_mono | cond_acc_consol
            
            # Nivel 3: Programada (Futura)
            cond_futura = cond_pendiente & (~cond_urgente) & (~cond_accionar)

            # Dataframes de Status
            df_inst = df[cond_instruido].sort_values(by='Rank_Num').copy()
            df_urgente = df[cond_urgente].sort_values(by='Rank_Num').copy()
            df_accionar = df[cond_accionar].sort_values(by='Rank_Num').copy()
            df_futura = df[cond_futura].sort_values(by='Rank_Num').copy()

            # Métricas
            m3_inst = df_inst['M3 Total'].sum()
            m3_urgente = df_urgente['M3 Total'].sum()
            m3_accionar = df_accionar['M3 Total'].sum()
            m3_futura = df_futura['M3 Total'].sum()
            m3_pend_total = m3_urgente + m3_accionar + m3_futura

            p_inst_val = int(round(m3_inst / m3_totales_global * 100)) if m3_totales_global > 0 else 0
            p_pend_val = 100 - p_inst_val
            
            fob_total_global = df['Fob total Origen'].sum()

            # --- BLOQUE: RESUMEN GENERAL ORIGEN ---
            st.markdown("<br>", unsafe_allow_html=True)
            o1, o2, o3, o4 = st.columns(4)
            with o1: st.markdown(f"<div class='metric-container'><p>CANTIDAD DE SO</p><p>{int(cant_so_global)}</p></div>", unsafe_allow_html=True)
            with o2: st.markdown(f"<div class='metric-container'><p>VOLUMEN TOTAL (M3)</p><p>{int(round(m3_totales_global)):,}</p></div>", unsafe_allow_html=True)
            with o3: st.markdown(f"<div class='metric-container'><p>PROVEEDORES</p><p>{int(cant_proveedores_global)}</p></div>", unsafe_allow_html=True)
            with o4: st.markdown(f"<div class='metric-container'><p>FOB TOTAL (USD)</p><p>${int(round(fob_total_global)):,}</p></div>", unsafe_allow_html=True)

            st.markdown("<hr class='glow-divider'>", unsafe_allow_html=True)

            # --- NUEVO PANEL DE CONTROL: STATUS DE MERCADERÍA ---
            st.markdown("<div style='text-align:center; padding: 20px; background: rgba(0, 168, 255, 0.05); border-radius: 20px; margin-bottom: 30px;'><h2 style='color:#00a8ff; font-weight:800; letter-spacing:5px; margin:0;'>CONTROL DE STATUS DE MERCADERÍA</h2></div>", unsafe_allow_html=True)
            
            s1, s2 = st.columns([1.2, 1])
            filtro_actual = st.session_state.get('f')
            
            with s1: # BLOQUE IZQUIERDO: LOGRADO / INSTRUIDA
                st.markdown(f"""
                    <div class="custom-card" style="border-top: 5px solid #00ff88; background: rgba(0,255,136,0.02);">
                        <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 25px;">
                            <p class="custom-card-title" style="color:#00ff88; font-size:18px;">MERCADERÍA INSTRUIDA (LOGRADO)</p>
                            <p style="color:#00ff88; font-weight:900; font-size:32px; margin:0;">{p_inst_val}% <span style="font-size:14px; color:#94a3b8; font-weight:400;">M3</span></p>
                        </div>
                        <div class="grid-2">
                            <div><p class="minicard-title">CANTIDAD SO</p><p class="minicard-value" style="color:#00ff88;">{df_inst['SO'].nunique()}</p></div>
                            <div><p class="minicard-title">VOLUMEN TOTAL</p><p class="minicard-value">{int(round(m3_inst)):,} M3</p></div>
                        </div>
                        <hr style="border:none; border-top:1px solid rgba(255,255,255,0.08); margin:20px 0;">
                        <div class="grid-2">
                            <div>
                                <p class="minicard-title" style="color:#00a8ff;">ESTRUCTURA DE CARGA</p>
                                <p style="font-size:12px; margin:5px 0;">MONO: <b>{df_inst[df_inst['Tipo_Carga']=='MONOPROVEEDOR']['SO'].nunique()} SO</b> ({int(round(df_inst[df_inst['Tipo_Carga']=='MONOPROVEEDOR']['M3 Total'].sum()))} m3)</p>
                                <p style="font-size:12px; margin:5px 0;">CONSOL: <b>{df_inst[df_inst['Tipo_Carga']=='CONSOLIDADO']['SO'].nunique()} SO</b> ({int(round(df_inst[df_inst['Tipo_Carga']=='CONSOLIDADO']['M3 Total'].sum()))} m3)</p>
                            </div>
                            <div>
                                <p class="minicard-title" style="color:#ffaa00;">TIPO DE INGRESO</p>
                                <p style="font-size:12px; margin:5px 0;">GADNIC: <b>{df_inst[df_inst['Tipo_Repuesto']=='Gadnic']['SO'].nunique()} SO</b></p>
                                <p style="font-size:12px; margin:5px 0;">MUESTRAS: <b>{df_inst[df_inst['Tipo_Repuesto']=='Muestras']['SO'].nunique()} SO</b></p>
                            </div>
                        </div>
                """, unsafe_allow_html=True)
                if st.button("VER DETALLE INSTRUIDO", key="btn_inst_new", use_container_width=True):
                    st.session_state.f = 'inst' if filtro_actual != 'inst' else None
                    st.rerun()
                st.markdown("</div>", unsafe_allow_html=True)

            with s2: # BLOQUE DERECHO: PENDIENTE / ACCIONABLE
                df_pend_view = df[cond_pendiente]
                st.markdown(f"""
                    <div class="custom-card" style="border-top: 5px solid #94a3b8;">
                        <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 25px;">
                            <p class="custom-card-title" style="color:#f8fafc; font-size:18px;">MERCADERÍA PENDIENTE</p>
                            <p style="color:#f8fafc; font-weight:900; font-size:32px; margin:0;">{p_pend_val}% <span style="font-size:14px; color:#94a3b8; font-weight:400;">M3</span></p>
                        </div>
                        <div class="grid-2" style="margin-bottom:20px;">
                            <div><p class="minicard-title">CANTIDAD SO</p><p class="minicard-value">{df_pend_view['SO'].nunique()}</p></div>
                            <div><p class="minicard-title">VOLUMEN TOTAL</p><p class="minicard-value">{int(round(m3_pend_total)):,} M3</p></div>
                        </div>
                    </div>
                """, unsafe_allow_html=True)
                
                # NIVEL 1: URGENTE
                if st.button(f"🔴 NIVEL 1: VENCIDA (URGENTE) - {int(df_urgente['SO'].nunique())} SO", key="btn_urg_new", use_container_width=True):
                    st.session_state.f = 'venc' if filtro_actual != 'venc' else None
                    st.rerun()

                # NIVEL 2: ACCIONAR
                if st.button(f"🟠 NIVEL 2: ACCIONAR (PRÓXIMA) - {int(df_accionar['SO'].nunique())} SO", key="btn_acc_new", use_container_width=True):
                    st.session_state.f = 'px25' if filtro_actual != 'px25' else None
                    st.rerun()

                # NIVEL 3: PROGRAMADA
                if st.button(f"🔵 NIVEL 3: PROGRAMADA (FUTURA) - {int(df_futura['SO'].nunique())} SO", key="btn_rest_new", use_container_width=True):
                    st.session_state.f = 'rest' if filtro_actual != 'rest' else None
                    st.rerun()

            # --- BOTONES SECUNDARIOS ---
            st.markdown("<br>", unsafe_allow_html=True)
            c_inf1, c_inf2, c_inf3 = st.columns(3)
            with c_inf1:
                if st.button("TOP 100 RANKING", key="btn_rank_new", use_container_width=True):
                    st.session_state.f = 'rank' if filtro_actual != 'rank' else None
                    st.rerun()
            with c_inf2:
                if st.button("ESTRUCTURA DE CARGA", key="btn_estr_new", use_container_width=True):
                    st.session_state.f = 'estr' if filtro_actual != 'estr' else None
                    st.rerun()
            with c_inf3:
                if st.button("VER TODO (SIN FILTROS)", key="btn_all_new", use_container_width=True):
                    st.session_state.f = None
                    st.rerun()

            # --- VISOR DEL FILTRO ---
            f = st.session_state.get('f')
            if f:
                st.markdown("<br>", unsafe_allow_html=True)
                if f in ["inst", "venc", "px25", "rest"]:
                    if f == "inst": titulo, dff, color = "MERCADERIA INSTRUIDA", df_inst, "#00ff88"
                    elif f == "venc": titulo, dff, color = "MERCADERIA VENCIDA A INSTRUIR (URGENTE)", df_urgente, "#ff4b4b"
                    elif f == "px25": titulo, dff, color = "PROXIMA A INSTRUIR (PANEADO ACCIÓN)", df_accionar, "#ffaa00"
                    elif f == "rest": titulo, dff, color = "MERCADERIA PROGRAMADA (FUTURA)", df_futura, "#94a3b8"

                    cant_so_f = len(dff)
                    m3_f = int(round(dff['M3 Total'].sum()))

                    st.markdown(f"""
                        <div class="custom-card" style="border-left: 5px solid {color};">
                            <p class="custom-card-title" style="color:{color};">{titulo} ({int(round(m3_f/m3_totales_global*100)) if m3_totales_global > 0 else 0}%)</p>
                            <div class="grid-2">
                                <div><p class="minicard-title">CANTIDAD SO</p><p class="minicard-value">{cant_so_f}</p></div>
                                <div><p class="minicard-title">VOLUMEN TOTAL</p><p class="minicard-value">{m3_f:,} M3</p></div>
                            </div>
                        </div>
                    """, unsafe_allow_html=True)
                    cols_to_show = ['SO', col_rank, 'Proveedor', 'M3 Total', 'Fecha de Instruccion' if f=='inst' else df.columns[99]]
                    if 'Repuestos' in df.columns:
                        cols_to_show.insert(3, 'Repuestos')
                    st.dataframe(dff[cols_to_show], use_container_width=True)

                elif f == "rank":
                    col_rank = df.columns[1]
                    col_prior = df.columns[99]
                    df_rank = df[df['Rank_Num'] <= 100].sort_values(by='Rank_Num').copy()
                    df_rank['Status'] = df_rank['Fecha_Inst_DT'].apply(lambda x: "✅ OK" if pd.notna(x) else "❌ PEND")

                    st.markdown(f"""
                        <div class="custom-card" style="border-left: 5px solid #00a8ff;">
                            <p class="custom-card-title" style="color:#00a8ff;">TOP 100 RANKING - RESUMEN</p>
                            <div class="grid-2">
                                <div><p class="minicard-title">EMBARQUES EN RANGO</p><p class="minicard-value">{df_rank['SO'].nunique()}</p></div>
                                <div><p class="minicard-title">M3 TOTAL PRIORITARIO</p><p class="minicard-value">{int(df_rank['M3 Total'].sum()):,} M3</p></div>
                            </div>
                        </div>
                    """, unsafe_allow_html=True)
                    cols_rank = ['SO', col_rank, 'Proveedor', col_prior, 'M3 Total', 'Status']
                    if 'Repuestos' in df.columns: cols_rank.insert(3, 'Repuestos')
                    st.dataframe(df_rank[cols_rank], use_container_width=True)

                elif f == "estr":
                    col_cp = df.columns[93]
                    df['Tipo_Carga'] = df[col_cp].apply(lambda x: 'MONOPROVEEDOR' if str(x).upper() == 'SI' else 'CONSOLIDADO')
                    
                    st.markdown("<p style='color:#00a8ff; font-weight:700; letter-spacing:4px; margin-bottom:20px; font-size:18px;'>ANALISIS ESTRUCTURA DE CARGA</p>", unsafe_allow_html=True)
                    e1, e2 = st.columns(2)
                    tipos = ["CONSOLIDADO", "MONOPROVEEDOR"]
                    colores_e = ["#94a3b8", "#00a8ff"]

                    for i, t_carga in enumerate(tipos):
                        df_c = df[df['Tipo_Carga'] == t_carga]
                        with [e1, e2][i]:
                            st.markdown(f"""
                                <div class="custom-card" style="border-left: 5px solid {colores_e[i]};">
                                    <p class="custom-card-title" style="color:{colores_e[i]};">{t_carga}</p>
                                    <div class="grid-2">
                                        <div><p class="minicard-title">CANT. SO</p><p class="minicard-value">{df_c['SO'].nunique()}</p></div>
                                        <div><p class="minicard-title">TOTAL M3</p><p class="minicard-value">{int(df_c['M3 Total'].sum()):,}</p></div>
                                    </div>
                                </div>
                            """, unsafe_allow_html=True)

            st.markdown("<hr class='glow-divider'>", unsafe_allow_html=True)

            # --- BLOQUE 4: PARTICIPACIÓN POR PAÍS ---
            st.markdown("<p style='color:#00a8ff; font-weight:700; letter-spacing:4px; font-size:18px; margin-bottom:25px;'>DISTRIBUCIÓN GEOGRÁFICA</p>", unsafe_allow_html=True)

            df['Pais Destino'] = df['Pais Destino'].fillna('SIN DEFINIR').replace('', 'SIN DEFINIR')
            res_p = df.groupby('Pais Destino').agg({'SO': 'nunique', 'M3 Total': 'sum'}).rename(columns={'SO': 'CANT_SO', 'M3 Total': 'M3'}).sort_values(by='M3', ascending=False)
            total_so_p = res_p['CANT_SO'].sum()
            total_m3_p = res_p['M3'].sum()

            h1, h2, h3, h4 = st.columns([1.5, 1, 1, 0.8])
            h1.markdown("<p style='color:#94a3b8; font-size:12px; letter-spacing:1px; font-weight:700;'>PAÍS DE DESTINO</p>", unsafe_allow_html=True)
            h2.markdown("<p style='color:#94a3b8; font-size:12px; letter-spacing:1px; font-weight:700; text-align:center;'>VOLUMEN (M3)</p>", unsafe_allow_html=True)
            h3.markdown("<p style='color:#94a3b8; font-size:12px; letter-spacing:1px; font-weight:700; text-align:center;'>CANTIDAD SO</p>", unsafe_allow_html=True)
            h4.markdown("<p style='color:#94a3b8; font-size:12px; letter-spacing:1px; font-weight:700; text-align:right;'>SHARE %</p>", unsafe_allow_html=True)
            st.markdown("<hr style='margin:0; border: none; border-top: 2px solid rgba(255,255,255,0.4);'>", unsafe_allow_html=True)

            for pais, row in res_p.iterrows():
                m3_v = int(round(row['M3']))
                so_v = int(row['CANT_SO'])
                pct_v = int(round((m3_v / total_m3_p * 100))) if total_m3_p > 0 else 0
                color_texto = "#ffffff" if pais != "SIN DEFINIR" else "#64748b"

                c1, c2, c3, c4 = st.columns([1.5, 1, 1, 0.8])
                c1.markdown(f"<p style='color:{color_texto}; font-weight:600; letter-spacing:2px; font-size:18px; margin:15px 0;'>{pais.upper()}</p>", unsafe_allow_html=True)
                c2.markdown(f"<p style='color:#00a8ff; font-weight:300; font-size:24px; text-align:center; margin:10px 0;'>{m3_v:,}</p>", unsafe_allow_html=True)
                c3.markdown(f"<p style='color:{color_texto}; font-weight:300; font-size:24px; text-align:center; margin:10px 0;'>{so_v}</p>", unsafe_allow_html=True)
                c4.markdown(f"<p style='color:#00ff88; font-weight:700; font-size:20px; text-align:right; margin:12px 0;'>{pct_v}%</p>", unsafe_allow_html=True)
                st.markdown("<hr class='white-divider'>", unsafe_allow_html=True)

            t1, t2, t3, t4 = st.columns([1.5, 1, 1, 0.8])
            t1.markdown("<p style='color:#f8fafc; font-weight:900; letter-spacing:2px; font-size:20px; margin:15px 0;'>TOTAL GENERAL</p>", unsafe_allow_html=True)
            t2.markdown(f"<p style='color:#00a8ff; font-weight:800; font-size:28px; text-align:center; margin:10px 0; text-shadow:0 0 10px rgba(0,168,255,0.5);'>{int(round(total_m3_p)):,}</p>", unsafe_allow_html=True)
            t3.markdown(f"<p style='color:#f8fafc; font-weight:800; font-size:28px; text-align:center; margin:10px 0;'>{int(total_so_p)}</p>", unsafe_allow_html=True)
            t4.markdown("<p style='color:#00ff88; font-weight:900; font-size:24px; text-align:right; margin:12px 0;'>100%</p>", unsafe_allow_html=True)

            st.markdown("<hr class='glow-divider'>", unsafe_allow_html=True)

            # --- BLOQUE 5: GRÁFICOS ---
            col_puerto = df.columns[41]
            p_df = df.groupby(col_puerto).agg({'M3 Total': 'sum'}).reset_index().sort_values(by='M3 Total')
            st.markdown(f"<p style='color:#00a8ff; font-weight:700; font-size:18px; text-align:center; letter-spacing:4px; margin-bottom:20px;'>VOLUMEN POR PUERTO DE SALIDA <span style='font-size:14px; font-weight:400; color:#f8fafc; text-shadow:none;'>| TOTAL: {int(round(p_df['M3 Total'].sum())):,} M3</span></p>", unsafe_allow_html=True)

            fig_p = px.bar(p_df, y=col_puerto, x='M3 Total', orientation='h', text_auto=',.0f', color_discrete_sequence=['#00a8ff'])
            fig_p.update_traces(textposition='outside', cliponaxis=False, textfont_size=16, textfont_color="#f8fafc", marker=dict(cornerradius=5))
            fig_p.update_layout(
                xaxis_visible=True, xaxis_title="Total M3", yaxis_title="Puerto", height=500, margin=dict(l=150, r=100, t=20, b=20),
                font=dict(size=14, family='Outfit, sans-serif'),
                paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)'
            )
            fig_p.update_xaxes(showgrid=True, gridwidth=1, gridcolor='rgba(255,255,255,0.1)')
            st.plotly_chart(fig_p, use_container_width=True)

            ga, gb = st.columns(2)
            with ga:
                etd_p = df.groupby('Mes_ETD_Full').agg({'M3 Total': 'sum'}).reset_index()
                st.markdown(f"<p style='color:#00ff88; font-weight:700; font-size:16px; text-align:center; letter-spacing:2px; margin-bottom:20px;'>PROYECCIÓN MENSUAL ETD<br><span style='font-size:14px; font-weight:400; color:#f8fafc; text-shadow:none;'>TOTAL: {int(round(etd_p['M3 Total'].sum())):,} M3</span></p>", unsafe_allow_html=True)
                fig_e = px.bar(etd_p, x='Mes_ETD_Full', y='M3 Total', text_auto=',.0f', color_discrete_sequence=['#00ff88'])
                fig_e.update_traces(textfont_size=16, textposition='outside', textfont_color="#f8fafc", marker=dict(cornerradius=5))
                fig_e.update_layout(
                    yaxis_visible=True, yaxis_title="Total M3", xaxis_title="Mes ETD", height=450, margin=dict(l=20, r=20, t=20, b=20),
                    font=dict(size=14, family='Outfit, sans-serif'), paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)'
                )
                fig_e.update_yaxes(showgrid=True, gridwidth=1, gridcolor='rgba(255,255,255,0.1)')
                st.plotly_chart(fig_e, use_container_width=True)

            with gb:
                eta_p = df.groupby('Mes_ETA_Full', observed=True).agg({'M3 Total': 'sum'}).reset_index()
                st.markdown(f"<p style='color:#ff4b4b; font-weight:700; font-size:16px; text-align:center; letter-spacing:2px; margin-bottom:20px;'>PROYECCIÓN MENSUAL ETA<br><span style='font-size:14px; font-weight:400; color:#f8fafc; text-shadow:none;'>TOTAL: {int(round(eta_p['M3 Total'].sum())):,} M3</span></p>", unsafe_allow_html=True)
                fig_a = px.bar(eta_p, x='Mes_ETA_Full', y='M3 Total', text_auto=',.0f', color_discrete_sequence=['#ff4b4b'])
                fig_a.update_traces(textfont_size=16, textposition='outside', textfont_color="#f8fafc", marker=dict(cornerradius=5))
                fig_a.update_layout(
                    yaxis_visible=True, yaxis_title="Total M3", xaxis_title="Mes ETA", height=450, margin=dict(l=20, r=20, t=20, b=20),
                    font=dict(size=14, family='Outfit, sans-serif'), paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)'
                )
                fig_a.update_yaxes(showgrid=True, gridwidth=1, gridcolor='rgba(255,255,255,0.1)')
                st.plotly_chart(fig_a, use_container_width=True)

            st.markdown("<hr class='white-divider'>", unsafe_allow_html=True)

            gc, gd = st.columns(2)
            with gc:
                col_mod_opciones = [c for c in df.columns if 'MODALIDAD' in str(c).upper() and 'COSTEO' in str(c).upper()]
                col_mod = col_mod_opciones[0] if col_mod_opciones else 'Modalidad de Costeo Reposicion'
                
                if col_mod in df.columns:
                    mask_barco = df[col_mod].astype(str).str.upper().str.startswith("BARCO")
                    df_c_etd = df[mask_barco].groupby('Mes_ETD_Full').agg({'M3 Total': 'sum'}).reset_index()
                    df_c_etd['Contenedores'] = (df_c_etd['M3 Total'] / 60).round().astype(int)
                    tot_cont_etd = df_c_etd['Contenedores'].sum()
                    st.markdown(f"<p style='color:#ffaa00; font-weight:700; font-size:16px; text-align:center; letter-spacing:2px; margin-bottom:20px;'>PROYECCIÓN CONTENEDORES (ETD)<br><span style='font-size:14px; font-weight:400; color:#f8fafc; text-shadow:none;'>TOTAL: {int(tot_cont_etd):,} CNTR</span></p>", unsafe_allow_html=True)
                    
                    fig_cetd = px.bar(df_c_etd, x='Mes_ETD_Full', y='Contenedores', text_auto=',.0f', color_discrete_sequence=['#ffaa00'])
                    fig_cetd.update_traces(textfont_size=16, textposition='outside', textfont_color="#f8fafc", marker=dict(cornerradius=5))
                    fig_cetd.update_layout(yaxis_visible=True, yaxis_title="Cant. Cont", xaxis_title="Mes ETD", height=450, margin=dict(l=20, r=20, t=20, b=20), font=dict(size=14, family='Outfit, sans-serif'), paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)')
                    fig_cetd.update_yaxes(showgrid=True, gridwidth=1, gridcolor='rgba(255,255,255,0.1)')
                    st.plotly_chart(fig_cetd, use_container_width=True)
                else:
                    st.warning(f"La columna requerida '{col_mod}' no se encuentra para calcular la proyección.")

            with gd:
                if col_mod in df.columns:
                    mask_barco = df[col_mod].astype(str).str.upper().str.startswith("BARCO")
                    df_c_eta = df[mask_barco].groupby('Mes_ETA_Full', observed=True).agg({'M3 Total': 'sum'}).reset_index()
                    df_c_eta['Contenedores'] = (df_c_eta['M3 Total'] / 60).round().astype(int)
                    tot_cont_eta = df_c_eta['Contenedores'].sum()
                    st.markdown(f"<p style='color:#ffaa00; font-weight:700; font-size:16px; text-align:center; letter-spacing:2px; margin-bottom:20px;'>PROYECCIÓN CONTENEDORES (ETA)<br><span style='font-size:14px; font-weight:400; color:#f8fafc; text-shadow:none;'>TOTAL: {int(tot_cont_eta):,} CNTR</span></p>", unsafe_allow_html=True)
                    
                    fig_ceta = px.bar(df_c_eta, x='Mes_ETA_Full', y='Contenedores', text_auto=',.0f', color_discrete_sequence=['#ffaa00'])
                    fig_ceta.update_traces(textfont_size=16, textposition='outside', textfont_color="#f8fafc", marker=dict(cornerradius=5))
                    fig_ceta.update_layout(yaxis_visible=True, yaxis_title="Cant. Cont", xaxis_title="Mes ETA", height=450, margin=dict(l=20, r=20, t=20, b=20), font=dict(size=14, family='Outfit, sans-serif'), paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)')
                    fig_ceta.update_yaxes(showgrid=True, gridwidth=1, gridcolor='rgba(255,255,255,0.1)')
                    st.plotly_chart(fig_ceta, use_container_width=True)

        except Exception as e:
            st.error(f"Error en Solapa Origen: {e}")

    # --- SOLAPA 2: CONTROL GESTIÓN RESERVAS ---
    with tabs[1]:
        try:
            url_reserva = f"{base_url}/export?format=csv&gid=276804813&nocache={time.time()}"

            @st.cache_data(ttl=60) 
            def load_reserva_data(url): return pd.read_csv(url, engine='python', on_bad_lines='skip')

            try: df_res = load_reserva_data(url_reserva)
            except Exception: df_res = pd.read_csv(url_reserva)
            df_res.columns = df_res.columns.str.strip()

            df_res['Fecha_Inst_H'] = df_res.iloc[:, 7].astype(str).str.strip()
            df_g = df_res[df_res['Fecha_Inst_H'].apply(lambda x: len(str(x)) > 4)].copy()

            # KPIs MASIVOS
            st.markdown("<br>", unsafe_allow_html=True)
            k1, k2, k3 = st.columns(3)
            with k1: st.markdown(f"<div class='metric-container'><p>SO INSTRUIDAS</p><p>{int(df_inst['SO'].nunique())}</p></div>", unsafe_allow_html=True)
            with k2: st.markdown(f"<div class='metric-container'><p>VOLUMEN (M3)</p><p>{int(round(df_inst['M3 Total'].sum())):,}</p></div>", unsafe_allow_html=True)
            with k3: st.markdown(f"<div class='metric-container'><p>PROVEEDORES</p><p>{int(df_inst['Proveedor'].nunique())}</p></div>", unsafe_allow_html=True)
            st.markdown("<hr class='glow-divider'>", unsafe_allow_html=True)

            # OVERALL PERFORMANCE FROM PLANIF CARGAS
            if '¿ETD OK FFWW?' in df_inst.columns:
                col_etd = '¿ETD OK FFWW?'
            else:
                col_etd = df_inst.columns[97]
                
            df_inst_t = df_inst.copy()
            df_inst_t['ETD_Status_P'] = df_inst_t[col_etd].astype(str).str.upper().str.strip()
            df_p_ok = df_inst_t[df_inst_t['ETD_Status_P'] == "OK"]
            df_p_pend = df_inst_t[df_inst_t['ETD_Status_P'] != "OK"]
            
            c_so_ok = df_p_ok['SO'].nunique()
            c_emb_ok = df_p_ok.iloc[:, 16].nunique()
            prov_ok_p = df_p_ok['Proveedor'].nunique()
            m3_ok_p = df_p_ok['M3 Total'].sum()
            
            c_so_pend = df_p_pend['SO'].nunique()
            c_emb_pend = df_p_pend.iloc[:, 16].nunique()
            prov_pend_p = df_p_pend['Proveedor'].nunique()
            m3_pend_p = df_p_pend['M3 Total'].sum()
            
            total_so_p = df_inst_t['SO'].nunique()
            pct_ok_p = round((c_so_ok / total_so_p * 100)) if total_so_p > 0 else 0
            pct_pend_p = 100 - pct_ok_p if total_so_p > 0 else 0

            st.markdown(f"""
                <div class="grid-2">
                    <div class="custom-card" style="border: 2px solid rgba(0,255,136,0.5); box-shadow: 0 0 30px rgba(0,255,136,0.15);">
                        <p style="font-size: 22px; font-weight: 800; color: #00ff88; margin-bottom: 20px; letter-spacing: 2px; text-transform: uppercase;">EMBARQUES CON ETD OK ({pct_ok_p}%)</p>
                        <div class="grid-2" style="text-align: center;">
                            <div><p class="minicard-title">CANTIDAD SOs</p><p style="font-size:45px; font-weight:900; color:#f8fafc; margin:0; text-shadow:0 0 15px rgba(0,255,136,0.4);">{c_so_ok}</p></div>
                            <div><p class="minicard-title">EMBARQUES</p><p style="font-size:45px; font-weight:600; color:#f8fafc; margin:0;">{c_emb_ok}</p></div>
                            <div><p class="minicard-title">PROVEEDORES</p><p style="font-size:45px; font-weight:600; color:#00ff88; margin:0;">{prov_ok_p}</p></div>
                            <div><p class="minicard-title">VOLUMEN TOTAL</p><p style="font-size:35px; font-weight:800; color:#f8fafc; margin:0;">{int(round(m3_ok_p)):,} <span style="font-size:16px;">M3</span></p></div>
                        </div>
                    </div>
                    <div class="custom-card" style="border: 2px solid rgba(255,75,75,0.5); box-shadow: 0 0 30px rgba(255,75,75,0.15);">
                        <p style="font-size: 22px; font-weight: 800; color: #ff4b4b; margin-bottom: 20px; letter-spacing: 2px; text-transform: uppercase;">EMBARQUES PENDIENTES ({pct_pend_p}%)</p>
                        <div class="grid-2" style="text-align: center;">
                            <div><p class="minicard-title">CANTIDAD SOs</p><p style="font-size:45px; font-weight:900; color:#f8fafc; margin:0; text-shadow:0 0 15px rgba(255,75,75,0.4);">{c_so_pend}</p></div>
                            <div><p class="minicard-title">EMBARQUES</p><p style="font-size:45px; font-weight:600; color:#f8fafc; margin:0;">{c_emb_pend}</p></div>
                            <div><p class="minicard-title">PROVEEDORES</p><p style="font-size:45px; font-weight:600; color:#ff4b4b; margin:0;">{prov_pend_p}</p></div>
                            <div><p class="minicard-title">VOLUMEN TOTAL</p><p style="font-size:35px; font-weight:800; color:#f8fafc; margin:0;">{int(round(m3_pend_p)):,} <span style="font-size:16px;">M3</span></p></div>
                        </div>
                    </div>
                </div>
            """, unsafe_allow_html=True)

            st.markdown("<br>", unsafe_allow_html=True)
            st.markdown("<div class='custom-card' style='text-align:center; border-color:#00a8ff; box-shadow: 0 0 30px rgba(0,168,255,0.1);'><h2 style='color:#00a8ff; font-weight:800; letter-spacing:4px; margin:0; font-size:22px;'>MONITOR DE GESTIÓN POR FORWARDER</h2></div>", unsafe_allow_html=True)
            
            df_g['DT_Inst'] = pd.to_datetime(df_g.iloc[:, 7], dayfirst=True, errors='coerce')
            df_g['ETD_Status_K'] = df_g.iloc[:, 10].astype(str).str.upper().str.strip()
            df_fw = df_g[df_g['DT_Inst'].notna()].copy()
            
            def safe_float_f(val):
                try:
                    if pd.isna(val) or val == '': return 0.0
                    s = str(val).replace('.', '').replace(',', '.')
                    num = ''.join(c for c in s if c.isdigit() or c == '.')
                    return float(num) if num else 0.0
                except: return 0.0
                
            if not df_fw.empty:
                df_fw['Tipo_T'] = df_fw.iloc[:, 5].apply(lambda x: "MARITIMO" if any(m in str(x).upper() for m in ["40", "20", "MARITIMO", "NOR"]) else "AVION / COURIER")
                t_sel_fw = st.radio("SELECCIONE VÍA PARA FORWARDERS:", ["MARITIMO", "AVION / COURIER"], horizontal=True, key="ag_radio_res")
                df_fwd = df_fw[df_fw['Tipo_T'] == t_sel_fw].copy()

                df_fwd['DT_ETD'] = pd.to_datetime(df_fwd.iloc[:, 11], dayfirst=True, errors='coerce')
                df_fwd['M3_Num'] = df_fwd.iloc[:, 24].apply(safe_float_f)
                df_fwd['CNTR_Num'] = df_fwd.iloc[:, 1].apply(safe_float_f)
                
                df_fwd['Gestion'] = (df_fwd['DT_ETD'] - df_fwd['DT_Inst']).dt.days
                df_fwd['Espera'] = (pd.to_datetime('today') - df_fwd['DT_Inst']).dt.days

                res_fw = df_fwd.groupby(df_fwd.columns[6]).agg(
                    Cant_Emb=(df_fwd.columns[0], 'count'),
                    Cant_CNTR=('CNTR_Num', 'sum'),
                    M3=('M3_Num', 'sum'),
                    Confirmados=('ETD_Status_K', lambda x: (x == "OK").sum()),
                    Prom_Gest=('Gestion', lambda x: x[df_fwd.loc[x.index, 'ETD_Status_K'] == "OK"].mean()),
                    Prom_Esp=('Espera', lambda x: x[df_fwd.loc[x.index, 'ETD_Status_K'] != "OK"].mean())
                ).reset_index()

                res_fw['%_OK'] = (res_fw['Confirmados'] / res_fw['Cant_Emb'] * 100).fillna(0)
                res_fw = res_fw.sort_values('Cant_Emb', ascending=False)

                st.dataframe(
                    res_fw,
                    column_config={
                        df_fwd.columns[6]: "Agente Forwarder",
                        "Cant_Emb": "Cant. Embarques",
                        "Cant_CNTR": "Cant. CTNRS",
                        "M3": st.column_config.NumberColumn("M3 Total", format="%.1f"),
                        "Prom_Gest": st.column_config.NumberColumn("Gestión OK (Días)", format="%d"),
                        "Prom_Esp": st.column_config.NumberColumn("Espera PEND. (Días)", format="%d"),
                        "%_OK": st.column_config.ProgressColumn("Efectividad %", min_value=0, max_value=100, format="%d%%")
                    },
                    use_container_width=True, hide_index=True
                )
            
            st.markdown("<hr class='glow-divider'>", unsafe_allow_html=True)
            st.markdown("<br><p style='text-align:center; color:#00a8ff; font-weight:700; letter-spacing:4px; font-size:16px;'>DESGLOSE POR TIPO DE TRANSPORTE</p>", unsafe_allow_html=True)

            # MARITIMO / AEREO
            def clasificar_transporte(x):
                x = str(x).upper()
                if any(m in x for m in ["40 HQ", "40 ST", "20 ST", "40NOR"]): return "MARITIMO"
                if any(a in x for a in ["AVION", "COURIER", "COURRIER"]): return "AVION / COURIER"
                return "OTROS"

            df_g['Transporte'] = df_g.iloc[:, 5].apply(clasificar_transporte) 
            t1, t2 = st.columns(2)
            for i, tipo in enumerate(["MARITIMO", "AVION / COURIER"]):
                df_tipo = df_g[df_g['Transporte'] == tipo]
                total_t = len(df_tipo)
                ok_t = len(df_tipo[df_tipo['ETD_Status_K'] == "OK"])
                pend_t = total_t - ok_t
                pct_ok = round((ok_t / total_t * 100)) if total_t > 0 else 0
                pct_pend = 100 - pct_ok if total_t > 0 else 0
                color_status = "#00ff88" if ok_t >= pend_t and total_t > 0 else "#ff4b4b"
                flecha = "▲" if ok_t >= pend_t else "▼"
                
                with [t1, t2][i]:
                    st.markdown(f"""
                    <div class="custom-card">
                        <div style="display: flex; justify-content: space-between; align-items: flex-start;">
                            <p class="custom-card-title" style="color: #00a8ff;">{tipo}</p>
                            <div style="text-align: right;">
                                <p style="color: {color_status}; font-weight: 700; margin: 0; font-size: 22px;">{flecha} {int(pct_ok)}% <span style="font-size:12px; color:#94a3b8;">OK</span></p>
                                <p style="color: #ff4b4b; font-weight: 600; margin: 0; font-size: 16px; opacity: 0.8;">{int(pct_pend)}% <span style="font-size:11px; color:#94a3b8;">PEND</span></p>
                            </div>
                        </div>
                        <p style="font-size: 35px; font-weight: 300; color: #f8fafc; margin-top: 15px; margin-bottom: 5px;">Total: <span style="font-weight:700;">{total_t}</span></p>
                        <p style="font-size: 14px; color: #94a3b8; font-weight: 600; margin: 0;"><span style="color: #00ff88;">Confirmados: {ok_t}</span> | <span style="color: #ff4b4b;">Pendientes: {pend_t}</span></p>
                    </div>""", unsafe_allow_html=True)

            st.markdown("<br>", unsafe_allow_html=True)

            # ANALISIS DE BOOKINGS
            df_mar = df_g[df_g['Transporte'] == "MARITIMO"].copy()
            def clean_val(value):
                if pd.isna(value): return 0
                s = str(value).replace('.', '').replace(',', '.')
                num = ''.join(c for c in s if c.isdigit() or c == '.')
                return pd.to_numeric(num, errors='coerce') if num else 0

            df_mar.iloc[:, 1] = pd.to_numeric(df_mar.iloc[:, 1], errors='coerce').fillna(0)
            df_mar.iloc[:, 29] = pd.to_numeric(df_mar.iloc[:, 29], errors='coerce').fillna(0)
            df_mar.iloc[:, 21] = df_mar.iloc[:, 21].apply(clean_val).fillna(0)

            st.markdown("<div style='margin-bottom:10px;'>", unsafe_allow_html=True)
            if st.button("ANALISIS BOOKING IN ADVANCE", key="btn_adv", use_container_width=True): st.session_state.mode = 'adv' if st.session_state.get('mode') != 'adv' else None
            st.markdown("</div>", unsafe_allow_html=True)
            
            def renderizar_detalle(mask, etiquetas, is_adv):
                col_a, col_b = st.columns(2)
                tot_local = len(df_mar) if len(df_mar) > 0 else 1
                for i_b, (titulo, dff_loc) in enumerate(etiquetas):
                    c_emb = len(dff_loc)
                    c_rel = round((c_emb / tot_local) * 100)
                    c_adv = len(dff_loc[dff_loc.iloc[:, 8].astype(str).str.strip() == "Booked in Advance"])
                    p_adv = round((c_adv / c_emb * 100)) if c_emb > 0 else 0
                    c_box = "#00a8ff" if i_b == 0 else "#94a3b8"
                    
                    with [col_a, col_b][i_b]:
                        st.markdown(f"""
                            <div class="custom-card" style="border-left: 5px solid {c_box}; margin-bottom: 20px;">
                                <div style="display: flex; justify-content: space-between; align-items: flex-start; margin-bottom: 25px;">
                                    <p class="custom-card-title" style="color:{c_box};">{titulo} ({int(c_rel)}%)</p>
                                    <div style="text-align: right;">
                                        <p style="font-size:11px; color:#00ff88; font-weight:700; margin:0; letter-spacing:1px;">ADVANCE: {int(p_adv)}%</p>
                                        <p style="font-size:11px; color:#ff4b4b; font-weight:700; margin:0; letter-spacing:1px;">SPOT: {int(100 - p_adv)}%</p>
                                    </div>
                                </div>
                                <div class="grid-4">
                                    <div><p class="minicard-title">CANT. SOs</p><p class="minicard-value" style="font-weight:600;">{int(c_emb)}</p></div>
                                    <div><p class="minicard-title">CONTS.</p><p class="minicard-value" style="font-weight:600;">{int(round(dff_loc.iloc[:, 1].sum()))}</p></div>
                                    <div><p class="minicard-title">PROM. CONS.</p><p class="minicard-value" style="font-weight:600; color:#00ff88;">{int(round(dff_loc.iloc[:, 29].mean() if c_emb > 0 else 0))}d</p></div>
                                    <div><p class="minicard-title">FOB USD</p><p class="minicard-value" style="font-size:22px;">{int(round(dff_loc.iloc[:, 21].sum())):,}</p></div>
                                </div>
                            </div>
                        """, unsafe_allow_html=True)

            mode = st.session_state.get('mode')
            if mode == 'adv':
                msk_adv = df_mar.iloc[:, 8].astype(str).str.strip() == "Booked in Advance"
                lbl_adv = [("Booked in Advance", df_mar[msk_adv]), ("No Booked in Advance", df_mar[~msk_adv])]
                renderizar_detalle(msk_adv, lbl_adv, True)

            st.markdown("<div style='margin-bottom:10px;'>", unsafe_allow_html=True)
            if st.button("ANALISIS MONOPROVEEDOR / CONSOLIDADO", key="btn_mono", use_container_width=True): st.session_state.mode = 'mono' if st.session_state.get('mode') != 'mono' else None
            st.markdown("</div>", unsafe_allow_html=True)
            
            if mode == 'mono':
                msk_mon = df_mar.iloc[:, 34].astype(str).str.strip() == "Monoproveedor"
                lbl_mon = [("Monoproveedor", df_mar[msk_mon]), ("Consolidado", df_mar[~msk_mon])]
                renderizar_detalle(msk_mon, lbl_mon, False)

        except Exception as e:
            st.error(f"Error en Gestión de Reservas: {e}")

    # --- SOLAPA 3: INDICADORES (SLA & CONSOLIDACIÓN) ---
    with tabs[2]:
        st.markdown("""
            <style>
            .stTabs [data-testid="stVerticalBlock"] div[data-testid="stColumn"] button {
                height: 30px !important;
                min-height: 30px !important;
                width: 100% !important;
                padding: 0px !important;
                font-size: 11px !important;
                margin-top: 15px !important;
                border-radius: 6px !important;
                background: rgba(0, 168, 255, 0.1) !important;
                border: 1px solid rgba(0, 168, 255, 0.3) !important;
            }
            .kpi-highlight {
                font-size: 24px !important;
                font-weight: 900 !important;
                margin: 0;
            }
            .sla-status {
                text-align: center;
                border-radius: 8px;
                margin-top: 5px;
                font-size: 12px;
                font-weight: 800;
                padding: 6px 0;
                text-transform: uppercase;
                letter-spacing: 2px;
                box-shadow: 0 0 10px rgba(0,0,0,0.5);
            }
            .table-row-hover:hover {
                background: rgba(255,255,255,0.03);
            }
            </style>
        """, unsafe_allow_html=True)

        try:
            url_hist = f"{base_url}/export?format=csv&gid=32771816&nocache={time.time()}"
            @st.cache_data(ttl=60)
            def load_hist(u): return pd.read_csv(u, engine='python')
            df_h = load_hist(url_hist)
            df_h.columns = df_h.columns.str.strip()

            nombres_meses = {1: "Enero", 2: "Febrero", 3: "Marzo", 4: "Abril", 5: "Mayo", 6: "Junio",
                            7: "Julio", 8: "Agosto", 9: "Septiembre", 10: "Octubre", 11: "Noviembre", 12: "Diciembre"}

            df_h['ETD_DT'] = pd.to_datetime(df_h.iloc[:, 11], dayfirst=True, errors='coerce')
            for i in [30, 31, 32]: df_h.iloc[:, i] = pd.to_numeric(df_h.iloc[:, i].astype(str).str.replace(',', '.'), errors='coerce').fillna(0)

            def es_maritimo(x): return any(m in str(x).upper() for m in ["40 HQ", "40 ST", "20 ST", "40NOR", "MARITIMO"])
            df_ind = df_h[(df_h['ETD_DT'].dt.year == 2026) & (df_h.iloc[:, 5].apply(es_maritimo))].copy()
            df_ind['Mes_Num'] = df_ind['ETD_DT'].dt.month

            @st.dialog("ANÁLISIS DE SLA POR PUERTO", width="large")
            def mostrar_detalle(df_f, nombre_mes, meta_val):
                st.subheader(f"Performance: {nombre_mes} 2026")
                st.info(f"Meta SLA: <= {meta_val} días")
                puerto_col = df_ind.columns[4]; tiempo_col = df_ind.columns[32]
                df_p = df_f.groupby(puerto_col).agg( Total_Emb=(df_ind.columns[0], 'count'), Prom_Consol=(tiempo_col, 'mean'), Dentro_SLA=(tiempo_col, lambda x: (x <= meta_val).sum()), Fuera_SLA=(tiempo_col, lambda x: (x > meta_val).sum())).reset_index()
                df_p['Dentro SLA %'] = (df_p['Dentro_SLA'] / df_p['Total_Emb'] * 100)
                df_p['Fuera SLA %'] = (df_p['Fuera_SLA'] / df_p['Total_Emb'] * 100)
                t_e = df_p["Total_Emb"].sum()
                t_row = pd.DataFrame({
                    puerto_col: ["TOTAL MENSUAL"], "Total_Emb": [t_e], "Prom_Consol": [df_f[tiempo_col].mean()],
                    "Dentro SLA %": [(df_p['Dentro_SLA'].sum()/t_e*100) if t_e>0 else 0], "Fuera SLA %": [(df_p['Fuera_SLA'].sum()/t_e*100) if t_e>0 else 0]
                })
                st.dataframe(pd.concat([df_p[[puerto_col, "Total_Emb", "Prom_Consol", "Dentro SLA %", "Fuera SLA %"]], t_row], ignore_index=True).style.format(precision=1).set_properties(subset=pd.IndexSlice[len(df_p), :], **{'background-color': '#0f172a', 'color': '#00a8ff'}), use_container_width=True, hide_index=True)

            # CONSOL GENERAL
            st.markdown("<br><p style='color:#00a8ff; font-weight:900; letter-spacing:6px; font-size:24px; text-align:center;'>INDICADORES DE CONSOLIDACIÓN</p>", unsafe_allow_html=True)
            cols = st.columns([1, 0.8, 1, 1, 1.3, 0.8, 0.8, 0.5])
            for i, c in enumerate(["MES", "EMBARQUES", "T. COMEX", "T. AGENTE", "TIEMPO TOTAL", "% MONO", "% CONSOL", "INFO"]):
                cols[i].markdown(f"<p style='color:#94a3b8; font-size:11px; font-weight:800; text-align:center;'>{c}</p>", unsafe_allow_html=True)
            st.markdown("<hr style='margin:0; border-top: 2px solid rgba(0,168,255,0.8); box-shadow: 0 0 15px rgba(0,168,255,0.5);'>", unsafe_allow_html=True)

            res_gen = df_ind.groupby('Mes_Num').agg({df_ind.columns[0]:'count', df_ind.columns[30]:'mean', df_ind.columns[31]:'mean', df_ind.columns[32]:'mean'}).reset_index()
            for _, row in res_gen.iterrows():
                m_idx = int(row['Mes_Num']); df_m = df_ind[df_ind['Mes_Num'] == m_idx]
                p_mono = int(round((len(df_m[df_m.iloc[:, 24].astype(str).str.upper().str.contains("SI|MONO", na=False)])/len(df_m))*100)) if len(df_m)>0 else 0
                st.markdown("<div class='table-row-hover' style='padding: 5px 0; border-radius: 8px; transition: background 0.3s;'>", unsafe_allow_html=True)
                rc = st.columns([1, 0.8, 1, 1, 1.3, 0.8, 0.8, 0.5])
                rc[0].markdown(f"<p style='text-align:center; font-weight:700; margin-top:12px; font-size:16px;'>{nombres_meses.get(m_idx)}</p>", unsafe_allow_html=True)
                rc[1].markdown(f"<p style='text-align:center; margin-top:12px; font-size:18px;'>{int(row.iloc[1])}</p>", unsafe_allow_html=True)
                rc[2].markdown(f"<p style='text-align:center; margin-top:12px; color:#94a3b8;'>{int(round(row.iloc[2]))}d</p>", unsafe_allow_html=True)
                rc[3].markdown(f"<p style='text-align:center; margin-top:12px; color:#94a3b8;'>{int(round(row.iloc[3]))}d</p>", unsafe_allow_html=True)
                rc[4].markdown(f"<p class='kpi-highlight' style='text-align:center; color:#00a8ff; margin-top:8px; text-shadow:0 0 15px rgba(0,168,255,0.4);'>{int(round(row.iloc[4]))}d</p>", unsafe_allow_html=True)
                rc[5].markdown(f"<p style='text-align:center; margin-top:12px; font-weight:600;'>{p_mono}%</p>", unsafe_allow_html=True)
                rc[6].markdown(f"<p style='text-align:center; margin-top:12px; font-weight:600;'>{100-p_mono}%</p>", unsafe_allow_html=True)
                with rc[7]:
                    if st.button("🔍", key=f"g_ind_{m_idx}"): mostrar_detalle(df_m, nombres_meses[m_idx], 25)
                st.markdown("</div><hr class='white-divider' style='margin: 5px 0;'>", unsafe_allow_html=True)

            # MONOPROVEEDOR (VERDE)
            st.markdown("<br><p style='color:#00ff88; font-weight:900; letter-spacing:6px; font-size:24px; text-align:center;'>PERFORMANCE MONOPROVEEDOR</p>", unsafe_allow_html=True)
            df_mono = df_ind[df_ind.iloc[:, 24].astype(str).str.upper().str.contains("SI|MONOPROVEEDOR", na=False)].copy()
            cols_m = st.columns([1, 1, 1, 1, 1.5, 0.5])
            for i, c in enumerate(['MES', 'EMBARQUES', 'META SLA', 'PROM. MES', 'ESTADO SLA', 'INFO']): cols_m[i].markdown(f"<p style='color:#94a3b8; font-size:11px; font-weight:800; text-align:center;'>{c}</p>", unsafe_allow_html=True)
            st.markdown("<hr style='margin:0; border-top: 2px solid rgba(0,255,136,0.8); box-shadow: 0 0 15px rgba(0,255,136,0.5);'>", unsafe_allow_html=True)

            res_mono = df_mono.groupby('Mes_Num').agg({df_mono.columns[0]:'count', df_mono.columns[32]:'mean'}).reset_index()
            for _, row in res_mono.iterrows():
                m_idx = int(row['Mes_Num']); df_m_mono = df_mono[df_mono['Mes_Num'] == m_idx]
                meta_act = 15 if m_idx <= 2 else 7; cumple = row.iloc[2] <= meta_act; c_st = "#00ff88" if cumple else "#ff4b4b"
                st.markdown("<div class='table-row-hover' style='padding: 5px 0; border-radius: 8px; transition: background 0.3s;'>", unsafe_allow_html=True)
                rc = st.columns([1, 1, 1, 1, 1.5, 0.5])
                rc[0].markdown(f"<p style='text-align:center; font-weight:700; margin-top:12px; font-size:16px;'>{nombres_meses.get(m_idx)}</p>", unsafe_allow_html=True)
                rc[1].markdown(f"<p style='text-align:center; margin-top:12px; font-size:18px;'>{int(row.iloc[1])}</p>", unsafe_allow_html=True)
                rc[2].markdown(f"<p style='text-align:center; margin-top:12px; color:#94a3b8;'>< {meta_act}d</p>", unsafe_allow_html=True)
                rc[3].markdown(f"<p class='kpi-highlight' style='text-align:center; color:{c_st}; margin-top:8px; text-shadow:0 0 15px {c_st}66;'>{int(round(row.iloc[2]))}d</p>", unsafe_allow_html=True)
                rc[4].markdown(f"<div class='sla-status' style='background: {c_st}15; color: {c_st}; border: 1px solid {c_st}55;'>{'ALCANZADO' if cumple else 'EXCEDIDO'}</div>", unsafe_allow_html=True)
                with rc[5]:
                    if st.button("🔍", key=f"mon_{m_idx}"): mostrar_detalle(df_m_mono, nombres_meses[m_idx], meta_act)
                st.markdown("</div><hr class='white-divider' style='margin: 5px 0;'>", unsafe_allow_html=True)

            # CONSOLIDADOS (NARANJA)
            st.markdown("<br><p style='color:#ffaa00; font-weight:900; letter-spacing:6px; font-size:24px; text-align:center;'>PERFORMANCE CONSOLIDADOS</p>", unsafe_allow_html=True)
            df_cons = df_ind[~df_ind.iloc[:, 24].astype(str).str.upper().str.contains("SI|MONOPROVEEDOR", na=False)].copy()
            cols_c = st.columns([1, 1, 1, 1, 1.5, 0.5])
            for i, c in enumerate(['MES', 'EMBARQUES', 'META SLA', 'PROM. MES', 'ESTADO SLA', 'INFO']): cols_c[i].markdown(f"<p style='color:#94a3b8; font-size:11px; font-weight:800; text-align:center;'>{c}</p>", unsafe_allow_html=True)
            st.markdown("<hr style='margin:0; border-top: 2px solid rgba(255,170,0,0.8); box-shadow: 0 0 15px rgba(255,170,0,0.5);'>", unsafe_allow_html=True)

            res_cons = df_cons.groupby('Mes_Num').agg({df_cons.columns[0]:'count', df_cons.columns[32]:'mean'}).reset_index()
            for _, row in res_cons.iterrows():
                m_idx = int(row['Mes_Num']); df_m_cons = df_cons[df_cons['Mes_Num'] == m_idx]; meta_c = 25
                cumple_c = row.iloc[2] <= meta_c; c_st_c = "#00ff88" if cumple_c else "#ff4b4b"
                st.markdown("<div class='table-row-hover' style='padding: 5px 0; border-radius: 8px; transition: background 0.3s;'>", unsafe_allow_html=True)
                rc = st.columns([1, 1, 1, 1, 1.5, 0.5])
                rc[0].markdown(f"<p style='text-align:center; font-weight:700; margin-top:12px; font-size:16px;'>{nombres_meses.get(m_idx)}</p>", unsafe_allow_html=True)
                rc[1].markdown(f"<p style='text-align:center; margin-top:12px; font-size:18px;'>{int(row.iloc[1])}</p>", unsafe_allow_html=True)
                rc[2].markdown(f"<p style='text-align:center; margin-top:12px; color:#94a3b8;'>< {meta_c}d</p>", unsafe_allow_html=True)
                rc[3].markdown(f"<p class='kpi-highlight' style='text-align:center; color:#ffaa00; margin-top:8px; text-shadow:0 0 15px rgba(255,170,0,0.6);'>{int(round(row.iloc[2]))}d</p>", unsafe_allow_html=True)
                rc[4].markdown(f"<div class='sla-status' style='background: {c_st_c}15; color: {c_st_c}; border: 1px solid {c_st_c}55;'>{'ALCANZADO' if cumple_c else 'EXCEDIDO'}</div>", unsafe_allow_html=True)
                with rc[5]:
                    if st.button("🔍", key=f"con_{m_idx}"): mostrar_detalle(df_m_cons, nombres_meses[m_idx], meta_c)
                st.markdown("</div><hr class='white-divider' style='margin: 5px 0;'>", unsafe_allow_html=True)

        except Exception as e:
            st.error(f"Error en Indicadores: {e}")

    # --- SOLAPA 4: AGENTES ---
    with tabs[3]:
        st.markdown("<div class='custom-card' style='text-align:center; border-color:#00a8ff; box-shadow: 0 0 50px rgba(0,168,255,0.1);'><h2 style='color:#00a8ff; font-weight:800; letter-spacing:6px; text-shadow: 0 0 20px rgba(0,168,255,0.4); margin:0;'>MONITOR DE GESTIÓN POR FORWARDER</h2></div>", unsafe_allow_html=True)
        try:
            u_ag = f"{base_url}/export?format=csv&gid=276804813"
            @st.cache_data(ttl=60)
            def load_ag(u): return pd.read_csv(u, engine='python')
            df_ag_raw = load_ag(u_ag)
            df_ag_raw.columns = [str(c).strip() for c in df_ag_raw.columns]

            df_ag_raw['DT_Inst'] = pd.to_datetime(df_ag_raw.iloc[:, 7], dayfirst=True, errors='coerce')
            df_a = df_ag_raw[df_ag_raw['DT_Inst'].notna()].copy()

            if df_a.empty: st.warning("No hay fechas de instrucción.")
            else:
                df_a['Tipo_T'] = df_a.iloc[:, 5].apply(lambda x: "MARITIMO" if any(m in str(x).upper() for m in ["40", "20", "MARITIMO"]) else "AVION / COURIER")
                t_sel = st.radio("SELECCIONE VÍA:", ["MARITIMO", "AVION / COURIER"], horizontal=True, key="ag_radio_fixed")
                df_f = df_a[df_a['Tipo_T'] == t_sel].copy()

                hoy_f = pd.Timestamp("2026-04-02")
                df_f['DT_ETD'] = pd.to_datetime(df_f.iloc[:, 11], dayfirst=True, errors='coerce')
                df_f['Status_K'] = df_f.iloc[:, 10].astype(str).str.upper().str.strip()
                df_f['Gestion'] = (df_f['DT_ETD'] - df_f['DT_Inst']).dt.days
                df_f['Espera'] = (hoy_f - df_f['DT_Inst']).dt.days

                res_ag = df_f.groupby(df_f.columns[6]).agg(
                    SO=(df_f.columns[0], 'count'),
                    M3=(df_f.columns[24], lambda x: pd.to_numeric(x.astype(str).str.replace(',', '.'), errors='coerce').sum()),
                    Confirmados=('Status_K', lambda x: (x == "OK").sum()),
                    Prom_Gest=('Gestion', 'mean'),
                    Prom_Esp=('Espera', lambda x: x[df_f.loc[x.index, 'Status_K'] != "OK"].mean())
                ).reset_index()

                res_ag['%_OK'] = (res_ag['Confirmados'] / res_ag['SO'] * 100).fillna(0)
                res_ag = res_ag.sort_values('SO', ascending=False)

                st.markdown("<br>", unsafe_allow_html=True)
                st.dataframe(
                    res_ag,
                    column_config={
                        df_f.columns[6]: "Agente Forwarder",
                        "SO": "Cant. SO",
                        "M3": st.column_config.NumberColumn("M3 Total", format="%.1f"),
                        "Prom_Gest": st.column_config.NumberColumn("Gestión (Días)", format="%d"),
                        "Prom_Esp": st.column_config.NumberColumn("Espera (Días)", format="%d"),
                        "%_OK": st.column_config.ProgressColumn("Efectividad %", min_value=0, max_value=100, format="%d%%")
                    },
                    use_container_width=True, hide_index=True
                )
        except Exception as e: st.error(f"Error en Solapa Agentes: {e}")

    with tabs[4]: st.info("Módulo Analistas en desarrollo.")
    with tabs[5]: st.info("Módulo Fletes en desarrollo.")

    # --- SOLAPA 7: COTIZACIÓN FFWW ---
    with tabs[6]:
        try:
            st.markdown("<p style='color:#00a8ff; font-weight:700; font-size:20px; letter-spacing:4px; text-transform:uppercase;'>Cotización Forwarders (Proyección Marítima)</p>", unsafe_allow_html=True)
            st.markdown("<p style='color:#94a3b8; font-size:14px; margin-bottom:30px;'>Módulo exclusivo para consultar volumen semanal (M3) y cantidad de contenedores requeridos por puerto.</p>", unsafe_allow_html=True)
            
            col_mod_opciones = [c for c in df.columns if 'MODALIDAD' in str(c).upper() and 'COSTEO' in str(c).upper()]
            col_mod = col_mod_opciones[0] if col_mod_opciones else 'Modalidad de Costeo Reposicion'
            
            if col_mod in df.columns:
                mask_barco = df[col_mod].astype(str).str.upper().str.startswith("BARCO")
                df_ffww = df[mask_barco].copy()
                
                if not df_ffww.empty:
                    meses_disp = [m for m in df_ffww['Mes_ETD_Full'].unique() if m not in ["PASADO/REALIZADO", "SIN FECHA"]]
                    meses_disp = sorted(meses_disp, key=lambda x: datetime.strptime(x, '%m/%Y'))
                    
                    if meses_disp:
                        sel_mes = st.selectbox("📅 SELECCIONE EL MES A COTIZAR:", meses_disp, index=0)
                        df_mes = df_ffww[df_ffww['Mes_ETD_Full'] == sel_mes].copy()
                        
                        if not df_mes.empty:
                            df_mes['Semana_Num'] = df_mes['ETD_DT'].dt.isocalendar().week
                            col_puerto = df.columns[41] # Puerto de Salida
                            
                            # Agrupación por semana y puerto
                            res_ffww = df_mes.groupby(['Semana_Num', col_puerto]).agg({'M3 Total': 'sum'}).reset_index()
                            res_ffww['Contenedores'] = (res_ffww['M3 Total'] / 60).round().astype(int)
                            res_ffww['M3 Total'] = res_ffww['M3 Total'].round().astype(int)
                            res_ffww['Semana'] = "Semana " + res_ffww['Semana_Num'].astype(str)
                            
                            # Guardamos los totales limpios para los indicadores de abajo
                            tot_mes_cont = res_ffww['Contenedores'].sum()
                            tot_mes_m3 = res_ffww['M3 Total'].sum()
                            
                            # Subtotales por semana
                            subtot_ffww = res_ffww.groupby(['Semana_Num', 'Semana']).agg({'Contenedores': 'sum', 'M3 Total': 'sum'}).reset_index()
                            subtot_ffww[col_puerto] = "📌 SUBTOTAL SEMANA"
                            
                            # Marcador para ordenar el subtotal siempre abajo por semana
                            res_ffww['IsTotal'] = False
                            subtot_ffww['IsTotal'] = True
                            
                            final_ffww = pd.concat([res_ffww, subtot_ffww], ignore_index=True)
                            final_ffww = final_ffww.sort_values(by=['Semana_Num', 'IsTotal', 'Contenedores'], ascending=[True, True, False])
                            
                            # Formateamos DataFrame final
                            final_ffww = final_ffww[['Semana', col_puerto, 'Contenedores', 'M3 Total']]
                            final_ffww.columns = ['Semana (ISO)', 'Puerto de Salida', 'Cant. Contenedores', 'Total M3']
                            
                            st.markdown("<hr class='white-divider'>", unsafe_allow_html=True)
                            
                            st.dataframe(
                                final_ffww,
                                use_container_width=True,
                                hide_index=True,
                                column_config={
                                    'Semana (ISO)': st.column_config.TextColumn("Semana del Año"),
                                    'Puerto de Salida': st.column_config.TextColumn("Pol"),
                                    'Total M3': st.column_config.NumberColumn(format="%d M3"),
                                    'Cant. Contenedores': st.column_config.NumberColumn(format="%d CNTR")
                                }
                            )
                            
                            st.markdown("<br>", unsafe_allow_html=True)
                            c1, c2, _ = st.columns([1,1,2])
                            with c1:
                                st.markdown(f"<div class='custom-card' style='border-left: 4px solid #ffaa00;'><p class='minicard-title'>TOTAL CONTENEDORES (MES)</p><p class='minicard-value' style='font-size:26px;'>{tot_mes_cont}</p></div>", unsafe_allow_html=True)
                            with c2:
                                st.markdown(f"<div class='custom-card' style='border-left: 4px solid #00a8ff;'><p class='minicard-title'>VOLUMEN TOTAL (MES)</p><p class='minicard-value' style='font-size:26px;'>{tot_mes_m3:,} M3</p></div>", unsafe_allow_html=True)
                        else:
                            st.info("No hay operaciones marítimas para el mes seleccionado.")
                    else:
                        st.info("No hay proyecciones de meses futuros disponibles para cotizar.")
                else:
                    st.info("No se registran operaciones marítimas ('Barco') en la base actual.")
            else:
                st.warning("Falta la columna 'Modalidad de Costeo' para identificar la carga marítima.")
                
        except Exception as e:
            st.error(f"Error cargando solapa de Cotización FFWW: {e}")

except Exception as e:
    st.error(f"Error crítico en el Tablero: {e}")
