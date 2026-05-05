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
.main { background-color: #020617;    color: #00ff88;
}

/* BOTONES COMPACTOS INDICADORES */
div[data-testid="stColumn"] div[data-testid="stButton"] button {
    height: 28px !important;
    min-height: 28px !important;
    padding: 0px 8px !important;
    font-size: 12px !important;
    border-radius: 6px !important;
}

/* DIVIDORES Y ESPACIOS */
hr { margin: 1rem 0 !important; opacity: 0.1; }

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
    df['ETD_DT'] = pd.to_datetime(df.iloc[:, 23], dayfirst=True, errors='coerce')
    df['ETA_DT'] = pd.to_datetime(df.iloc[:, 24], dayfirst=True, errors='coerce')
    df['Fecha_Prior_DT'] = pd.to_datetime(df.iloc[:, 99], dayfirst=True, errors='coerce') 

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
    tabs = st.tabs(["ORIGEN", "MERCADERÍA EN PROCESO", "PERFORMANCE DE AGENTES Y ANALISTAS", "FLETES, GASTOS Y CERTIFICACIONES", "COTIZACIÓN FFWW", "INDICADORES", "ALERTAS ESTRATÉGICAS", "ASK COMEX"])

     # --- SOLAPA 1: ORIGEN ---
    with tabs[0]:
        try:
            df['Fecha_Inst_DT'] = pd.to_datetime(df['Fecha de Instruccion'], dayfirst=True, errors='coerce')
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

            # --- NORMALIZACIÓN Y CONDICIONES BASE ---
            df['Pais Destino'] = df['Pais Destino'].fillna('SIN DEFINIR').astype(str).str.strip()
            df['Repuestos'] = df['Repuestos'].fillna('').astype(str).str.strip()
            
            # Condición de Prioridad Principal (Argentina y Producto Terminado/Gadnic)
            cond_prioridad = (df['Pais Destino'].str.upper() == 'ARGENTINA') & (df['Tipo_Repuesto'] == 'Gadnic')
            
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

            # Dataframes de Status (SOLO PRIORIDAD PRINCIPAL)
            df_inst = df[cond_instruido & cond_prioridad].sort_values(by='Rank_Num').copy()
            df_urgente = df[cond_urgente & cond_prioridad].sort_values(by='Rank_Num').copy()
            df_accionar = df[cond_accionar & cond_prioridad].sort_values(by='Rank_Num').copy()
            df_futura = df[cond_futura & cond_prioridad].sort_values(by='Rank_Num').copy()

            # Dataframes de Seguimiento Complementario (Otros Países / Repuestos)
            cond_complementario = cond_pendiente & (~cond_prioridad)
            df_complem = df[cond_complementario].sort_values(by=['Fecha_Prior_DT', 'Rank_Num']).copy()
            
            df_otros_p = df_complem[df_complem['Pais Destino'].str.upper() != 'ARGENTINA'].copy()
            df_repuestos = df_complem[df_complem['Tipo_Repuesto'] != 'Gadnic'].copy()
            
            # SOs Demoradas en seguimiento complementario
            cant_demorados_comp = df_complem[df_complem['Fecha_Prior_DT'] < hoy]['SO'].nunique()

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
                                <p style="font-size:12px; margin:5px 0;">MONOPROVEEDOR: <b>{df_inst[df_inst['Tipo_Carga']=='MONOPROVEEDOR']['SO'].nunique()} SO</b> ({int(round(df_inst[df_inst['Tipo_Carga']=='MONOPROVEEDOR']['M3 Total'].sum()))} m3)</p>
                                <p style="font-size:12px; margin:5px 0;">CONSOLIDADOS: <b>{df_inst[df_inst['Tipo_Carga']=='CONSOLIDADO']['SO'].nunique()} SO</b> ({int(round(df_inst[df_inst['Tipo_Carga']=='CONSOLIDADO']['M3 Total'].sum()))} m3)</p>
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
                if st.button(f"🔴 NIVEL 1: VENCIDA (URGENTE) - {int(round(df_urgente['M3 Total'].sum()))} M3", key="btn_urg_new", use_container_width=True):
                    st.session_state.f = 'venc' if filtro_actual != 'venc' else None
                    st.rerun()

                # NIVEL 2: ACCIONAR
                if st.button(f"🟠 NIVEL 2: ACCIONAR (PRÓXIMA) - {int(round(df_accionar['M3 Total'].sum()))} M3", key="btn_acc_new", use_container_width=True):
                    st.session_state.f = 'px25' if filtro_actual != 'px25' else None
                    st.rerun()

                # NIVEL 3: PROGRAMADA
                if st.button(f"🔵 NIVEL 3: PROGRAMADA (FUTURA) - {int(round(df_futura['M3 Total'].sum()))} M3", key="btn_rest_new", use_container_width=True):
                    st.session_state.f = 'rest' if filtro_actual != 'rest' else None
                    st.rerun()

            st.markdown("<br>", unsafe_allow_html=True)
            c_sec1, c_sec2, c_sec3 = st.columns(3)
            with c_sec1:
                st.markdown("<div style='height: 20px;'></div>", unsafe_allow_html=True)
                if st.button("🏆 TOP 100 RANKING", key="btn_rank_new", use_container_width=True):
                    st.session_state.f = 'rank' if filtro_actual != 'rank' else None
                    st.rerun()
            with c_sec2:
                st.markdown("<div style='height: 20px;'></div>", unsafe_allow_html=True)
                if st.button(f"🔎 SEGUIMIENTO COMPLEMENTARIO ({df_complem['SO'].nunique()})", key="btn_comp_new", use_container_width=True):
                    st.session_state.f = 'comp' if filtro_actual != 'comp' else None
                    st.rerun()
            with c_sec3:
                st.markdown("<div style='height: 20px;'></div>", unsafe_allow_html=True)
                if st.button("🏗️ ESTRUCTURA DE CARGA", key="btn_estr_new", use_container_width=True):
                    st.session_state.f = 'estr' if filtro_actual != 'estr' else None
                    st.rerun()

            # --- VISOR DEL FILTRO ---
            f = st.session_state.get('f')
            if f:
                st.markdown("<br>", unsafe_allow_html=True)
                if f in ["inst", "venc", "px25", "rest", "comp"]:
                    if f == "inst": titulo, dff, color = "MERCADERIA INSTRUIDA (PRIORIDAD)", df_inst, "#00ff88"
                    elif f == "venc": titulo, dff, color = "MERCADERIA VENCIDA (URGENTE)", df_urgente, "#ff4b4b"
                    elif f == "px25": titulo, dff, color = "PROXIMA A INSTRUIR (ACCIÓN)", df_accionar, "#ffaa00"
                    elif f == "rest": titulo, dff, color = "MERCADERIA PROGRAMADA (FUTURA)", df_futura, "#94a3b8"
                    elif f == "comp": titulo, dff, color = "SEGUIMIENTO ESPECIAL (OTROS PAÍSES / REPUESTOS)", df_complem, "#00a8ff"

                    cant_so_f = dff['SO'].nunique()
                    m3_f = int(round(dff['M3 Total'].sum()))
                    
                    if f == "comp":
                        msg_extra = f"<p style='color:#ff4b4b; font-size:14px; font-weight:700;'>🚨 {cant_demorados_comp} SO DEMORADAS EN SEGUIMIENTO</p>"
                        st.markdown(f"""
                            <div class="custom-card" style="border-left: 5px solid {color};">
                                <p class="custom-card-title" style="color:{color};">{titulo}</p>
                                {msg_extra}
                                <div class="grid-2">
                                    <div style="background:rgba(255,255,255,0.03); padding:10px; border-radius:10px;">
                                        <p class="minicard-title">DESTINOS EXTERNOS</p>
                                        <p style="font-size:20px; font-weight:700; color:#fff; margin:0;">{df_otros_p['SO'].nunique()} SO | {int(round(df_otros_p['M3 Total'].sum()))} M3</p>
                                    </div>
                                    <div style="background:rgba(255,255,255,0.03); padding:10px; border-radius:10px;">
                                        <p class="minicard-title">REPUESTOS / MUESTRAS</p>
                                        <p style="font-size:20px; font-weight:700; color:#fff; margin:0;">{df_repuestos['SO'].nunique()} SO | {int(round(df_repuestos['M3 Total'].sum()))} M3</p>
                                    </div>
                                </div>
                            </div>
                        """, unsafe_allow_html=True)
                    else:
                        st.markdown(f"""
                            <div class="custom-card" style="border-left: 5px solid {color};">
                                <p class="custom-card-title" style="color:{color};">{titulo} ({int(round(m3_f/m3_totales_global*100)) if m3_totales_global > 0 else 0}%)</p>
                                <div class="grid-2">
                                    <div><p class="minicard-title">CANTIDAD SO</p><p class="minicard-value">{cant_so_f}</p></div>
                                    <div><p class="minicard-title">VOLUMEN TOTAL</p><p class="minicard-value">{m3_f:,} M3</p></div>
                                </div>
                            </div>
                        """, unsafe_allow_html=True)
                    
                    col_puerto = df.columns[41]
                    # Aquí está la modificación requerida:
                    cols_to_show = ['SO', col_rank, 'Proveedor', col_puerto, 'Pais Destino', 'M3 Total', df.columns[99], 'Fecha de Instruccion']
                    
                    if 'Repuestos' in df.columns:
                        cols_to_show.insert(4, 'Repuestos')
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
                    col_puerto = df.columns[41]
                    cols_rank = ['SO', col_rank, 'Proveedor', col_puerto, 'Pais Destino', col_prior, 'M3 Total', 'Status']
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
            st.markdown("<p style='color:#00a8ff; font-weight:700; letter-spacing:4px; font-size:18px; margin-bottom:25px; text-align:center;'>DISTRIBUCIÓN GEOGRÁFICA</p>", unsafe_allow_html=True)

            # Participación por País
            res_p = df.groupby('Pais Destino').agg({'SO': 'nunique', 'M3 Total': 'sum'}).rename(columns={'SO': 'CANT_SO', 'M3 Total': 'M3'}).sort_values(by='M3', ascending=False)
            total_so_p = res_p['CANT_SO'].sum()
            total_m3_p = res_p['M3'].sum()

            hp1, hp2, hp3, hp4 = st.columns([1.5, 1, 1, 0.8])
            hp1.markdown("<p style='color:#94a3b8; font-size:12px; letter-spacing:1px; font-weight:700;'>DESTINO</p>", unsafe_allow_html=True)
            hp2.markdown("<p style='color:#94a3b8; font-size:12px; letter-spacing:1px; font-weight:700; text-align:center;'>VOLUMEN (M3)</p>", unsafe_allow_html=True)
            hp3.markdown("<p style='color:#94a3b8; font-size:12px; letter-spacing:1px; font-weight:700; text-align:center;'>CANTIDAD SO</p>", unsafe_allow_html=True)
            hp4.markdown("<p style='color:#94a3b8; font-size:12px; letter-spacing:1px; font-weight:700; text-align:right;'>SHARE %</p>", unsafe_allow_html=True)
            st.markdown("<hr style='margin:0 0 10px 0; border: none; border-top: 1px solid rgba(255,255,255,0.2);'>", unsafe_allow_html=True)

            for pais, row in res_p.iterrows():
                m3_v = int(round(row['M3']))
                so_v = int(row['CANT_SO'])
                pct_v = int(round((m3_v / total_m3_p * 100))) if total_m3_p > 0 else 0
                color_texto = "#ffffff" if pais != "SIN DEFINIR" else "#64748b"

                cp1, cp2, cp3, cp4 = st.columns([1.5, 1, 1, 0.8])
                cp1.markdown(f"<p style='color:{color_texto}; font-weight:600; font-size:16px; margin:8px 0;'>{pais.upper()}</p>", unsafe_allow_html=True)
                cp2.markdown(f"<p style='color:#00a8ff; font-weight:400; font-size:20px; text-align:center; margin:8px 0;'>{m3_v:,}</p>", unsafe_allow_html=True)
                cp3.markdown(f"<p style='color:{color_texto}; font-weight:400; font-size:20px; text-align:center; margin:8px 0;'>{so_v}</p>", unsafe_allow_html=True)
                cp4.markdown(f"<p style='color:#00ff88; font-weight:700; font-size:18px; text-align:right; margin:8px 0;'>{pct_v}%</p>", unsafe_allow_html=True)

            st.markdown("<hr style='margin:15px 0; border: none; border-top: 1px solid rgba(255,255,255,0.4);'>", unsafe_allow_html=True)
            tp1, tp2, tp3, tp4 = st.columns([1.5, 1, 1, 0.8])
            tp1.markdown("<p style='color:#f8fafc; font-weight:800; font-size:18px;'>TOTAL GENERAL</p>", unsafe_allow_html=True)
            tp2.markdown(f"<p style='color:#00a8ff; font-weight:800; font-size:22px; text-align:center;'>{int(round(total_m3_p)):,}</p>", unsafe_allow_html=True)
            tp3.markdown(f"<p style='color:#f8fafc; font-weight:800; font-size:22px; text-align:center;'>{int(total_so_p)}</p>", unsafe_allow_html=True)
            tp4.markdown("<p style='color:#00ff88; font-weight:900; font-size:20px; text-align:right;'>100%</p>", unsafe_allow_html=True)

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

            # --- INICIALIZACIÓN Y SCOPE (GESTIÓN RESERVAS) ---
            df_res['Fecha_Inst_H'] = df_res.iloc[:, 7].astype(str).str.strip()
            df_g = df_res[df_res['Fecha_Inst_H'].apply(lambda x: len(str(x)) > 4)].copy()
            df_g['DT_Inst'] = pd.to_datetime(df_g.iloc[:, 7], dayfirst=True, errors='coerce')
            df_g['ETD_Status_K'] = df_g.iloc[:, 10].astype(str).str.upper().str.strip()
            df_g['Espera'] = (pd.to_datetime('today') - df_g['DT_Inst']).dt.days
            df_g['Critico'] = (df_g['ETD_Status_K'] != "OK") & (df_g['Espera'] > 5)

            # Columnas Automáticas para Reservas (para evitar NameError)
            col_so_res = [c for c in df_g.columns if 'SO' in str(c).upper()][0] if any('SO' in str(c).upper() for c in df_g.columns) else df_g.columns[2]
            
            # --- PLANIF CARGAS (Resumen Superior) ---
            # Col U (index 20) es Fecha Instrucción
            df_plan_res = df_inst[df_inst.iloc[:, 20].notna() & (df_inst.iloc[:, 20].astype(str).str.strip() != "")].copy()
            col_etd_plan = '¿ETD OK FFWW?' if '¿ETD OK FFWW?' in df_plan_res.columns else df_plan_res.columns[97]
            df_plan_res['Status_P'] = df_plan_res[col_etd_plan].astype(str).str.lower().str.strip()
            
            def safe_float_f(val):
                if isinstance(val, (int, float)): return float(val)
                if pd.isna(val) or str(val).strip() in ['', 'nan']: return 0.0
                try:
                    s = str(val).strip()
                    if ',' in s and '.' in s:
                        if s.find('.') < s.find(','): s = s.replace('.', '').replace(',', '.')
                        else: s = s.replace(',', '')
                    elif ',' in s: s = s.replace(',', '.')
                    return float(s)
                except: return 0.0

            # KPIs MASIVOS
            st.markdown("<br>", unsafe_allow_html=True)
            k1, k2, k3, k4 = st.columns(4)
            # Asegurar limpieza para el KPI masivo también por si acaso
            m3_total_clean = df_inst['M3 Total'].apply(safe_float_f).sum()
            fob_total_clean = df_inst['Fob total Origen'].apply(safe_float_f).sum()
            
            with k1: st.markdown(f"<div class='metric-container'><p>SO INSTRUIDAS</p><p>{int(df_inst['SO'].nunique())}</p></div>", unsafe_allow_html=True)
            with k2: st.markdown(f"<div class='metric-container'><p>VOLUMEN (M3)</p><p>{int(round(m3_total_clean)):,}</p></div>", unsafe_allow_html=True)
            with k3: st.markdown(f"<div class='metric-container'><p>PROVEEDORES</p><p>{int(df_inst['Proveedor'].nunique())}</p></div>", unsafe_allow_html=True)
            with k4: st.markdown(f"<div class='metric-container'><p>FOB TOTAL (USD)</p><p>${int(round(fob_total_clean)):,}</p></div>", unsafe_allow_html=True)
            
            # Título Estilizado para la solapa
            st.markdown("<div style='text-align:center; padding: 20px; background: rgba(0, 168, 255, 0.05); border-radius: 20px; margin: 30px 0;'><h2 style='color:#00a8ff; font-weight:800; letter-spacing:5px; margin:0;'>CONTROL GESTIÓN RESERVAS</h2></div>", unsafe_allow_html=True)
            
            st.markdown("<hr class='glow-divider'>", unsafe_allow_html=True)

            # OVERALL PERFORMANCE FROM PLANIF CARGAS
            # SO: Col A (0), Prov: Col AE (30), M3: Col AY (50) - Confirmado: 'M3 Total'
            df_p_ok = df_plan_res[df_plan_res['Status_P'] == "ok"]
            df_p_pend = df_plan_res[df_plan_res['Status_P'] != "ok"]
            
            c_so_ok = df_p_ok.iloc[:, 0].nunique()
            c_emb_ok = df_p_ok.iloc[:, 16].nunique()
            prov_ok_p = df_p_ok.iloc[:, 30].nunique()
            m3_ok_p = df_p_ok['M3 Total'].apply(safe_float_f).sum()
            
            c_so_pend = df_p_pend.iloc[:, 0].nunique()
            c_emb_pend = df_p_pend.iloc[:, 16].nunique()
            prov_pend_p = df_p_pend.iloc[:, 30].nunique()
            m3_pend_p = df_p_pend['M3 Total'].apply(safe_float_f).sum()
            
            total_emb_p = df_plan_res.iloc[:, 16].nunique()
            pct_ok_p = round((c_emb_ok / total_emb_p * 100)) if total_emb_p > 0 else 0
            pct_pend_p = 100 - pct_ok_p if total_emb_p > 0 else 0

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
            st.markdown("<br>", unsafe_allow_html=True)
            st.markdown("<p style='text-align:center; color:#00a8ff; font-weight:700; letter-spacing:4px; font-size:16px;'>DESGLOSE POR TIPO DE TRANSPORTE</p>", unsafe_allow_html=True)

            # MARITIMO / AEREO (SACA DE RESERVAS SEGÚN PEDIDO)
            def clasificar_transp_res(x):
                x = str(x).upper().strip()
                if any(m in x for m in ["40 HQ", "40 ST", "40 NOR", "20 ST", "40NOR"]): return "MARITIMO"
                if any(a in x for a in ["AVION", "COURIER", "COURRIER"]): return "AVION / COURIER"
                return "OTROS"

            # Aplicar a df_g (Reservas) usando Columna F (index 5)
            df_g['Transporte'] = df_g.iloc[:, 5].apply(clasificar_transp_res) 
            t1, t2 = st.columns(2)
            for i, tipo in enumerate(["MARITIMO", "AVION / COURIER"]):
                df_tipo = df_g[df_g['Transporte'] == tipo]
                total_t = df_tipo.iloc[:, 0].nunique()
                ok_t = df_tipo[df_tipo['ETD_Status_K'] == "OK"].iloc[:, 0].nunique()
                pend_t = total_t - ok_t
                crit_t = df_tipo[df_tipo['Critico']].iloc[:, 0].nunique()
                
                # Métricas adicionales (Contenedores y M3)
                m3_t = df_tipo.iloc[:, 24].apply(safe_float_f).sum()
                cntr_t = df_tipo.iloc[:, 1].apply(safe_float_f).sum()
                
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
                        <p style="font-size: 35px; font-weight: 300; color: #f8fafc; margin-top: 15px; margin-bottom: 5px;">Emb: <span style="font-weight:700;">{total_t}</span></p>
                        <div style="display: flex; gap: 15px; margin-top: 5px;">
                            <p style="color: #94a3b8; font-size: 13px;">CTNRS: <span style="color: #f8fafc; font-weight: 600;">{int(cntr_t)}</span></p>
                            <p style="color: #94a3b8; font-size: 13px;">VOL: <span style="color: #f8fafc; font-weight: 600;">{int(round(m3_t)):,} M3</span></p>
                        </div>
                        <p style="font-size: 14px; color: #94a3b8; font-weight: 600; margin: 0;">
                            <span style="color: #00ff88;">Confirmados: {ok_t}</span> | <span style="color: #ff4b4b;">Pendientes: {pend_t}</span>
                        </p>
                        {f'<p style="font-size:13px; color:#ff4b4b; font-weight:700; margin-top:10px;">🚨 CRÍTICOS (>5d): {crit_t}</p>' if crit_t > 0 else ""}
                    </div>""", unsafe_allow_html=True)
            
            st.markdown("<hr class='glow-divider'>", unsafe_allow_html=True)
            

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

            # --- MONITOR DE GESTIÓN POR FORWARDER (AL PIE) ---
            st.markdown("<hr class='glow-divider'>", unsafe_allow_html=True)
            st.markdown("<h2 style='color:#00a8ff; font-weight:800; letter-spacing:4px; margin:20px 0; font-size:22px; text-align:center;'>MONITOR DE GESTIÓN POR FORWARDER</h2>", unsafe_allow_html=True)
            
            df_fw = df_g.copy()
            if not df_fw.empty:
                df_fw['Tipo_T'] = df_fw.iloc[:, 5].apply(lambda x: "MARITIMO" if any(m in str(x).upper() for m in ["40", "20", "MARITIMO", "NOR"]) else "AVION / COURIER")
                t_sel_fw = st.radio("SELECCIONE VÍA PARA FORWARDERS:", ["MARITIMO", "AVION / COURIER"], horizontal=True, key="ag_radio_res")
                df_fwd = df_fw[df_fw['Tipo_T'] == t_sel_fw].copy()

                # Datos de Reservas: Embarque (0), Contenedores (1), Agente (6), Instr (7), ETD (9), Status (10), Confirma (11), M3 (24)
                df_fwd['DT_Conf'] = pd.to_datetime(df_fwd.iloc[:, 11], dayfirst=True, errors='coerce')
                df_fwd['DT_ETD'] = pd.to_datetime(df_fwd.iloc[:, 9], dayfirst=True, errors='coerce')
                df_fwd['M3_Num'] = df_fwd.iloc[:, 24].apply(safe_float_f)
                df_fwd['CNTR_Num'] = df_fwd.iloc[:, 1].apply(safe_float_f)
                
                # Métricas de Tiempo
                df_fwd['Gestion_Resp'] = (df_fwd['DT_Conf'] - df_fwd['DT_Inst']).dt.days # Respuesta Agente
                df_fwd['Gestion_ETD'] = (df_fwd['DT_ETD'] - df_fwd['DT_Inst']).dt.days # Instruccion -> ETD
                
                tot_m3_via = df_fwd['M3_Num'].sum()
                tot_emb_via = df_fwd.iloc[:, 0].nunique()
                
                st.markdown(f"""
                    <div style="background: rgba(0,168,255,0.05); padding: 15px; border-radius: 10px; margin-bottom: 20px; border-left: 4px solid #00a8ff;">
                        <p style="margin:0; font-size:14px; color:#94a3b8;">DETALLE {t_sel_fw}: <b>{int(tot_emb_via)} EMBS</b> | <b>{int(round(tot_m3_via)):,} M3 ACTUALES EN ESTA VÍA</b></p>
                    </div>
                """, unsafe_allow_html=True)

                # --- 1. PERFORMANCE Y SHARE DE CARGA ---
                st.markdown("<p style='color:#f8fafc; font-weight:700; margin-bottom:10px;'>1. PERFORMANCE Y SHARE DE CARGA (SOLAPA RESERVAS)</p>", unsafe_allow_html=True)
                
                # Expandimos a ancho completo para mejor lectura
                st.markdown("<p style='color:#00ff88; font-size:14px; font-weight:700;'>A. CASOS CONFIRMADOS (ETD OK)</p>", unsafe_allow_html=True)
                df_ok = df_fwd[df_fwd['ETD_Status_K'] == "OK"]
                if not df_ok.empty:
                    res_ok = df_ok.groupby(df_ok.columns[6]).agg(
                        Cant_Emb=(df_ok.columns[0], 'nunique'),
                        Share_Pct=('M3_Num', lambda x: (x.sum() / tot_m3_via * 100)),
                        Prom_Resp=('Gestion_Resp', 'mean'),
                        Prom_ETD=('Gestion_ETD', 'mean')
                    ).reset_index()
                    st.dataframe(res_ok.sort_values('Cant_Emb', ascending=False), 
                                 column_config={
                                     df_ok.columns[6]: "Agente",
                                     "Cant_Emb": "Embs",
                                     "Share_Pct": st.column_config.NumberColumn("Share %", format="%.1f%%"),
                                     "Prom_Resp": st.column_config.NumberColumn("Respuesta (d)", format="%d"),
                                     "Prom_ETD": st.column_config.NumberColumn("Instr->ETD (d)", format="%d")
                                 }, hide_index=True, use_container_width=True)
                else: st.info("Sin casos confirmados.")

                st.markdown("<br><p style='color:#ff4b4b; font-size:14px; font-weight:700;'>B. CASOS PENDIENTES (SIN OK)</p>", unsafe_allow_html=True)
                df_pen = df_fwd[df_fwd['ETD_Status_K'] != "OK"]
                if not df_pen.empty:
                    res_pen = df_pen.groupby(df_pen.columns[6]).agg(
                        Cant_Emb=(df_pen.columns[0], 'nunique'),
                        Share_Pct=('M3_Num', lambda x: (x.sum() / tot_m3_via * 100)),
                        Prom_Esp=('Espera', 'mean')
                    ).reset_index()
                    st.dataframe(res_pen.sort_values('Prom_Esp', ascending=False), 
                                 column_config={
                                     df_pen.columns[6]: "Agente",
                                     "Cant_Emb": "Embs",
                                     "Share_Pct": st.column_config.NumberColumn("Share %", format="%.1f%%"),
                                     "Prom_Esp": st.column_config.NumberColumn("Espera Avg (d)", format="%d")
                                 }, hide_index=True, use_container_width=True)
                else: st.info("Sin casos pendientes.")

        except Exception as e:
            st.error(f"Error en Gestión de Reservas: {e}")

        # --- SOLAPA 3: PERFORMANCE DE AGENTES Y ANALISTAS ---
    with tabs[2]:
        st.markdown("<div style='text-align:center; padding: 20px; background: rgba(0, 168, 255, 0.05); border-radius: 20px; margin: 30px 0;'><h2 style='color:#00a8ff; font-weight:800; letter-spacing:5px; margin:0;'>PERFORMANCE DE AGENTES Y ANALISTAS</h2></div>", unsafe_allow_html=True)
        try:
            u_ag = f"{base_url}/export?format=csv&gid=276804813"
            @st.cache_data(ttl=60)
            def load_ag_v_vfinal(u): return pd.read_csv(u, engine='python')
            df_ag_raw = load_ag_v_vfinal(u_ag)
            df_ag_raw.columns = [str(c).strip() for c in df_ag_raw.columns]
            df_ag_raw['DT_Inst'] = pd.to_datetime(df_ag_raw.iloc[:, 7], dayfirst=True, errors='coerce')
            df_a = df_ag_raw[df_ag_raw['DT_Inst'].notna()].copy()

            if df_a.empty: st.warning("Esperando datos de instrucción para el análisis.")
            else:
                df_a['Tipo_T'] = df_a.iloc[:, 5].apply(lambda x: "MARITIMO" if any(m in str(x).upper() for m in ["40", "20", "MARITIMO"]) else "AVION / COURIER")
                t_sel = st.radio("Carga vía:", ["MARITIMO", "AVION / COURIER"], horizontal=True, key="ag_analistas_radio_vfinal_v2")
                df_f = df_a[df_a['Tipo_T'] == t_sel].copy()
                
                # Resumen Agentes
                res_ag = df_f.groupby(df_f.columns[6]).agg(
                    SO=(df_f.columns[0], 'count'),
                    M3=(df_f.columns[24], lambda x: pd.to_numeric(x.astype(str).str.replace(',', '.'), errors='coerce').sum())
                ).reset_index()
                st.dataframe(res_ag.sort_values('SO', ascending=False), use_container_width=True, hide_index=True)
                
                st.markdown("<hr class='white-divider'>", unsafe_allow_html=True)
                st.info("💡 Módulo : Próximamente integración de métricas de performance por usuario (Comex/Agentes).")
        except Exception as e: st.error(f"Error en Performance Agentes: {e}")

    # --- SOLAPA 4: CONTROL DE FLETES, GASTOS Y CERTIFICACIONES ---
    with tabs[3]:
        st.markdown("<div style='text-align:center; padding: 20px; background: rgba(255, 170, 0, 0.05); border-radius: 20px; margin-bottom: 30px;'><h2 style='color:#ffaa00; font-weight:800; letter-spacing:5px; margin:0;'>CONTROL DE FLETES, GASTOS Y CERTIFICACIONES</h2></div>", unsafe_allow_html=True)
        st.info("Módulo en desarrollo: Integración de costos logísticos, certificación de fletes gastos en origen y destino.")

    # --- SOLAPA 5: COTIZACIÓN FFWW ---
    with tabs[4]:
        try:
            st.markdown("<div style='background: rgba(0, 168, 255, 0.05); padding: 15px 25px; border-radius: 20px; border: 1px solid rgba(0, 168, 255, 0.2); margin: 15px 0;'><h3 style='color:#00a8ff; margin:0; text-align:center; letter-spacing:5px; text-transform:uppercase; font-weight:900;'>COTIZACIÓN FFWW — PROYECCIÓN MARÍTIMA</h3></div>", unsafe_allow_html=True)
            st.markdown("<p style='color:#94a3b8; font-size:13px; text-align:center; margin-bottom:20px;'>Fuente: <b>Planif Cargas</b> · Filtro: Modalidad de Costeo = <b>BARCO</b> · ETD = Columna X</p>", unsafe_allow_html=True)

            # Cargar datos SIN filtro de SO para capturar TODAS las filas de planificación
            @st.cache_data(ttl=60)
            def load_planif_raw(u):
                d = pd.read_csv(u)
                d.columns = d.columns.str.strip()
                if 'M3 Total' in d.columns:
                    d['M3 Total'] = d['M3 Total'].astype(str).str.replace('.', '', regex=False).str.replace(',', '.', regex=False)
                    d['M3 Total'] = pd.to_numeric(d['M3 Total'], errors='coerce').fillna(0)
                return d

            df_raw = load_planif_raw(f"{base_url}/export?format=csv&gid=0&nocache={time.time()}")

            # Detectar columna Modalidad de Costeo
            col_mod_opciones = [c for c in df_raw.columns if 'MODALIDAD' in str(c).upper() and 'COSTEO' in str(c).upper()]
            col_mod = col_mod_opciones[0] if col_mod_opciones else 'Modalidad de Costeo Reposicion'

            if col_mod in df_raw.columns:
                mask_barco = df_raw[col_mod].astype(str).str.upper().str.startswith("BARCO")
                df_ffww = df_raw[mask_barco].copy()

                if not df_ffww.empty:
                    # ETD = Columna X = índice 23
                    df_ffww['ETD_DT'] = pd.to_datetime(df_ffww.iloc[:, 23], dayfirst=True, errors='coerce')
                    df_ffww['Mes_ETD_Full'] = df_ffww['ETD_DT'].apply(lambda x: label_proyeccion(x, inicio_mes))

                    meses_disp = [m for m in df_ffww['Mes_ETD_Full'].unique() if m not in ["PASADO/REALIZADO", "SIN FECHA"]]
                    meses_disp = sorted(meses_disp, key=lambda x: datetime.strptime(x, '%m/%Y'))


                    if meses_disp:
                        # Detectar columna Puerto
                        col_puerto_opts = [c for c in df.columns if 'PUERTO' in str(c).upper() and 'SAL' in str(c).upper()]
                        col_puerto = col_puerto_opts[0] if col_puerto_opts else df.columns[41]

                        c_sel, _ = st.columns([1, 2])
                        with c_sel:
                            sel_mes = st.selectbox("📅 SELECCIONE EL MES A COTIZAR:", meses_disp, index=0)

                        df_mes = df_ffww[df_ffww['Mes_ETD_Full'] == sel_mes].copy()

                        if not df_mes.empty:
                            # Semana dentro del mes (1-5) basada en el día del ETD
                            def semana_del_mes(dt):
                                if pd.isnull(dt): return 0
                                day = dt.day
                                month = dt.month
                                year = dt.year
                                # Determinar el rango de la semana para el label
                                if day <= 7: return 1, "01-07"
                                elif day <= 14: return 2, "08-14"
                                elif day <= 21: return 3, "15-21"
                                else: return 4, f"22-{pd.Period(dt, freq='M').days_in_month}"

                            df_mes[['Sem_Mes', 'Sem_Rango']] = df_mes['ETD_DT'].apply(
                                lambda x: pd.Series(semana_del_mes(x)) if pd.notnull(x) else pd.Series([0, ""])
                            )
                            
                            df_mes['Semana_Label'] = df_mes.apply(
                                lambda r: f"Semana {int(r['Sem_Mes'])} ({r['Sem_Rango']}) — {sel_mes}" if r['Sem_Mes'] > 0 else "📋 SIN ETD ASIGNADO",
                                axis=1
                            )

                            # Agrupación por semana del mes y puerto
                            res_ffww = df_mes.groupby(['Sem_Mes', 'Semana_Label', col_puerto]).agg({'M3 Total': 'sum'}).reset_index()
                            res_ffww['Contenedores'] = (res_ffww['M3 Total'] / 60).round().astype(int)
                            res_ffww['M3 Total'] = res_ffww['M3 Total'].round().astype(int)

                            # Subtotales por semana del mes
                            subtot_ffww = res_ffww.groupby(['Sem_Mes', 'Semana_Label']).agg({'Contenedores': 'sum', 'M3 Total': 'sum'}).reset_index()
                            subtot_ffww[col_puerto] = "📌 SUBTOTAL SEMANA"

                            res_ffww['IsTotal'] = False
                            subtot_ffww['IsTotal'] = True

                            final_ffww = pd.concat([res_ffww, subtot_ffww], ignore_index=True)
                            
                            # Forzar mostrar todas las semanas aunque no tengan datos (Opcional, pero aquí simplemente ordenamos)
                            final_ffww = final_ffww.sort_values(
                                by=['Sem_Mes', 'IsTotal', 'Contenedores'],
                                ascending=[True, True, False]
                            )

                            final_ffww = final_ffww[['Semana_Label', col_puerto, 'Contenedores', 'M3 Total']]
                            final_ffww.columns = ['Semana del Mes', 'Puerto de Salida', 'Cant. Contenedores', 'Total M3']

                            st.dataframe(final_ffww, use_container_width=True, hide_index=True,
                                column_config={
                                    'Total M3': st.column_config.NumberColumn(format="%d M3"),
                                    'Cant. Contenedores': st.column_config.NumberColumn(format="%d CNTR")
                                })

                            # Alerta si hay embarques sin ETD
                            sin_etd = (df_mes['Sem_Mes'] == 0).sum()
                            if sin_etd > 0:
                                st.warning(f"⚠️ **{sin_etd} embarque(s)** no tienen ETD asignado y aparecen en '📋 SIN ETD ASIGNADO'.")

                            st.markdown("<div style='height:15px;'></div>", unsafe_allow_html=True)
                            cc1, cc2, cc3, _ = st.columns([1, 1, 1, 1])
                            # Filtro Sem_Mes > 0 para excluir sin ETD de la suma de contenedores si se prefiere, pero aquí sumamos todo lo visible
                            cc1.metric("CONTENEDORES (MES)", int(res_ffww['Contenedores'].sum()))
                            cc2.metric("VOLUMEN TOTAL (MES)", f"{int(res_ffww['M3 Total'].sum()):,} M3")
                            cc3.metric("EMBARQUES (MES)", len(df_mes))
                        else:
                            st.info("No hay proyecciones para este mes.")


                    else:
                        st.info("No hay meses futuros disponibles.")
                else:
                    st.info("No hay operaciones marítimas activas (modalidad BARCO).")
            else:
                st.warning(f"No se encontró la columna de Modalidad de Costeo. Columnas disponibles: {list(df.columns[:10])}")
        except Exception as e:
            st.error(f"Error en Cotización FFWW: {e}")


    # --- SOLAPA 6: INDICADORES (SLA & CONSOLIDACIÓN) ---
    with tabs[5]:
        st.markdown("<div style='text-align:center; padding: 20px; background: rgba(0, 255, 136, 0.05); border-radius: 20px; margin: 30px 0;'><h2 style='color:#00ff88; font-weight:800; letter-spacing:5px; margin:0;'>INDICADORES DE CONSOLIDACIÓN Y SLA</h2></div>", unsafe_allow_html=True)
        try:
            # Carga de datos históricos (Gid 32771816)
            url_hi = f"{base_url}/export?format=csv&gid=32771816&nocache={time.time()}"
            @st.cache_data(ttl=60)
            def load_hi_vfinal(u): return pd.read_csv(u, engine='python')
            
            df_hi = load_hi_vfinal(url_hi)
            df_hi.columns = [str(c).strip() for c in df_hi.columns]
            
            # Filtro para año 2026 y Marítimos
            df_hi['ETD_DT'] = pd.to_datetime(df_hi.iloc[:, 11], dayfirst=True, errors='coerce') 
            df_2026 = df_hi[df_hi.iloc[:, 25].astype(str).str.contains("2026")].copy()
            
            if not df_2026.empty:
                df_2026['Mes'] = df_2026['ETD_DT'].dt.month
                col_tipo_carga_hi = df_hi.columns[5] 
                df_mar = df_2026[~df_2026[col_tipo_carga_hi].astype(str).str.upper().str.contains('AVION|COURRIER', na=False)].copy()
                
                meses_dict = {1:"Enero", 2:"Febrero", 3:"Marzo", 4:"Abril", 5:"Mayo", 6:"Junio", 7:"Julio", 8:"Agosto", 9:"Septiembre", 10:"Octubre", 11:"Noviembre", 12:"Diciembre"}
                df_mar['Mes_Nombre'] = df_mar['Mes'].map(meses_dict)
                
                # Identificación de columnas críticas
                col_mono_hi = df_hi.columns[24]    # ¿Es Monoproveedor?
                col_puerto_hi = df_hi.columns[4]   # Puerto
                col_cons_hi = df_hi.columns[32]    # Días Consolidación
                
                def clean_n_hi(val):
                    if pd.isna(val) or str(val).strip() in ['', 'nan']: return 0.0
                    try:
                        s = str(val).replace(',', '.').replace(' ', '').strip()
                        return pd.to_numeric(s, errors='coerce')
                    except: return 0.0

                df_mar[col_cons_hi] = df_mar[col_cons_hi].apply(clean_n_hi).fillna(0.0).round(0)
                
                st.markdown("<div style='background: rgba(0, 168, 255, 0.05); padding: 15px 25px; border-radius: 20px; border: 1px solid rgba(0, 168, 255, 0.2); margin: 15px 0;'><h3 style='color:#00a8ff; margin:0; text-align:center; letter-spacing:5px; text-transform:uppercase; font-weight:900;'>RESUMEN MES CERRADO (MARÍTIMOS 2026)</h3></div>", unsafe_allow_html=True)
                
                # --- DIALOG DE DETALLE (CORREGIDO) ---
                @st.dialog("🚢 DETALLE POR PUERTO Y SLA", width="large")
                def show_detalle_mes(df_sub, mes_lbl, mode="mixed"):
                    st.markdown(f"### Análisis de Cumplimiento: {mes_lbl.upper()}")
                    res_p = df_sub.groupby(col_puerto_hi).agg({df_hi.columns[0]: 'count', col_cons_hi: 'mean'}).reset_index()
                    
                    p_rows = []
                    for _, r in res_p.iterrows():
                        df_p_t = df_sub[df_sub[col_puerto_hi] == r[col_puerto_hi]].copy()
                        tp_p = r[df_hi.columns[0]]
                        
                        def check_sla(row):
                            days = row[col_cons_hi]
                            is_mono = "SÍ" in str(row[col_mono_hi]).upper() or "SI" in str(row[col_mono_hi]).upper()
                            limit = (15 if row['Mes'] <= 2 else 7) if is_mono else 25
                            return days <= limit
                        
                        df_p_t['SLA_OK'] = df_p_t.apply(check_sla, axis=1)
                        pct_sla = int((len(df_p_t[df_p_t['SLA_OK']]) / tp_p) * 100) if tp_p > 0 else 0
                        
                        row_data = {
                            "Puerto": r[col_puerto_hi], 
                            "Embs": tp_p, 
                            "Días Avg": int(round(r[col_cons_hi])),
                            "% Cumple SLA": f"{pct_sla}%",
                            "% Fuera SLA": f"{100 - pct_sla}%",
                            "TOTAL": "100%"
                        }
                        
                        if mode == "mixed":
                            cm_p = len(df_p_t[df_p_t[col_mono_hi].astype(str).str.contains('SÍ|SI|MONO', case=False, na=False)])
                            row_data["% Mono"] = f"{int((cm_p/tp_p)*100)}%"
                            row_data["% Cons"] = f"{int((1-(cm_p/tp_p))*100)}%"
                        
                        p_rows.append(row_data)
                    
                    st.dataframe(pd.DataFrame(p_rows).sort_values("Embs", ascending=False), use_container_width=True, hide_index=True)

                # --- RENDER DE TABLA MENSUAL ---
                thc = st.columns([1.5, 1, 1.2, 1, 1, 0.8])
                headers = ["MES ETD", "EMBS", "DIAS AVG", "% MONO", "% CONS", "DETALLE"]
                for i, h in enumerate(headers):
                    thc[i].markdown(f"<p style='color:#94a3b8; font-size:11px; font-weight:800; text-align:center;'>{h}</p>", unsafe_allow_html=True)
                
                res_mensual = df_mar.groupby(['Mes', 'Mes_Nombre']).agg({df_hi.columns[0]: 'count', col_cons_hi: 'mean'}).reset_index()
                
                for _, row in res_mensual.iterrows():
                    df_m_temp = df_mar[df_mar['Mes'] == row['Mes']].copy()
                    df_m_mono = df_m_temp[df_m_temp[col_mono_hi].astype(str).str.contains('SÍ|SI|MONO', case=False, na=False)]
                    tot_m = len(df_m_temp)
                    p_mono = (len(df_m_mono) / tot_m) if tot_m > 0 else 0
                    
                    tr1, tr2, tr3, tr4, tr5, tr6 = st.columns([1.5, 1, 1.2, 1, 1, 0.8])
                    tr1.markdown(f"<p style='font-weight:700; color:#fff; text-align:center; margin-top:5px;'>{row['Mes_Nombre'].upper()}</p>", unsafe_allow_html=True)
                    tr2.markdown(f"<p style='text-align:center; margin-top:5px;'>{tot_m}</p>", unsafe_allow_html=True)
                    tr3.markdown(f"<p style='color:#00ff88; font-weight:700; text-align:center; margin-top:5px;'>{int(round(row[col_cons_hi]))}d</p>", unsafe_allow_html=True)
                    tr4.markdown(f"<p style='color:#00a8ff; text-align:center; margin-top:5px;'>{int(p_mono*100)}%</p>", unsafe_allow_html=True)
                    tr5.markdown(f"<p style='color:#94a3b8; text-align:center; margin-top:5px;'>{int((1-p_mono)*100)}%</p>", unsafe_allow_html=True)
                    with tr6:
                        if st.button("🔍 VER", key=f"btn_det_v4_{row['Mes']}", use_container_width=True):
                            show_detalle_mes(df_m_temp, row['Mes_Nombre'], mode="mixed")

                # --- SECCIONES DE APERTURA (MONO / CONSOLIDADO) ---
                st.markdown("<br>", unsafe_allow_html=True)
                
                # 1. MONOPROVEEDOR
                st.markdown("<div style='background: rgba(0, 168, 255, 0.05); padding: 8px 15px; border-radius: 8px; border-left: 5px solid #00a8ff; text-align:center;'><h4 style='color:#00a8ff; margin:0; font-size:14px;'>1. SOLAMENTE MONOPROVEEDOR (MARÍTIMOS 2026)</h4></div>", unsafe_allow_html=True)
                df_mono_v4 = df_mar[df_mar[col_mono_hi].astype(str).str.contains('SÍ|SI|MONO', case=False, na=False)].copy()
                if not df_mono_v4.empty:
                    res_m = df_mono_v4.groupby(['Mes', 'Mes_Nombre']).agg({df_hi.columns[0]: 'count', col_cons_hi: 'mean'}).reset_index()
                    for _, rm in res_m.iterrows():
                        st.markdown("<div style='padding:4px 0; border-bottom:1px solid rgba(255,255,255,0.02);'>", unsafe_allow_html=True)
                        m1, m2, m3, m4 = st.columns([2, 1, 1, 1])
                        m1.write(f"**{rm['Mes_Nombre']}**")
                        m2.write(f"{int(rm.iloc[2])} embs")
                        m3.write(f"Avg: **{int(round(rm.iloc[3]))}d**")
                        with m4:
                            if st.button("DETALLE", key=f"btn_m_{rm['Mes']}", use_container_width=True):
                                show_detalle_mes(df_mono_v4[df_mono_v4['Mes']==rm['Mes']], f"MONO - {rm['Mes_Nombre']}", mode="specific")
                        st.markdown("</div>", unsafe_allow_html=True)

                st.markdown("<br>", unsafe_allow_html=True)
                
                # 2. CONSOLIDADO
                st.markdown("<div style='background: rgba(0, 255, 136, 0.05); padding: 8px 15px; border-radius: 8px; border-left: 5px solid #00ff88; text-align:center;'><h4 style='color:#00ff88; margin:0; font-size:14px;'>2. SOLAMENTE CONSOLIDADO (MARÍTIMOS 2026)</h4></div>", unsafe_allow_html=True)
                df_cons_v4 = df_mar[~df_mar[col_mono_hi].astype(str).str.contains('SÍ|SI|MONO', case=False, na=False)].copy()
                if not df_cons_v4.empty:
                    res_c = df_cons_v4.groupby(['Mes', 'Mes_Nombre']).agg({df_hi.columns[0]: 'count', col_cons_hi: 'mean'}).reset_index()
                    for _, rc in res_c.iterrows():
                        st.markdown("<div style='padding:4px 0; border-bottom:1px solid rgba(255,255,255,0.02);'>", unsafe_allow_html=True)
                        c1, c2, c3, c4 = st.columns([2, 1, 1, 1])
                        c1.write(f"**{rc['Mes_Nombre']}**")
                        c2.write(f"{int(rc.iloc[2])} embs")
                        c3.write(f"Avg: **{int(round(rc.iloc[3]))}d**")
                        with c4:
                            if st.button("DETALLE", key=f"btn_c_{rc['Mes']}", use_container_width=True):
                                show_detalle_mes(df_cons_v4[df_cons_v4['Mes']==rc['Mes']], f"CONS - {rc['Mes_Nombre']}", mode="specific")
                        st.markdown("</div>", unsafe_allow_html=True)
            else:
                st.warning("No se encontraron registros marítimos para el año 2026.")
        except Exception as e:
            st.error(f"Error en Indicadores: {e}")


    # --- SOLAPA 7: ALERTAS ESTRATÉGICAS ---
    with tabs[6]:
        try:
            st.markdown("<div style='text-align:center; padding: 20px; background: rgba(255, 75, 75, 0.05); border-radius: 20px; margin-bottom: 30px;'><h2 style='color:#ff4b4b; font-weight:800; letter-spacing:5px; margin:0;'>ALERTAS ESTRATÉGICAS</h2></div>", unsafe_allow_html=True)
            
            # Recargamos Reservas para asegurar datos frescos para las alertas
            url_r_alt = f"{base_url}/export?format=csv&gid=276804813&nocache={time.time()}"
            @st.cache_data(ttl=60)
            def load_res_alt_v4(u): return pd.read_csv(u, engine='python')
            df_re = load_res_alt_v4(url_r_alt)
            df_re.columns = [str(c).strip() for c in df_re.columns]

            # 1. MERCADERÍA SIN INSTRUIR (CONSOLIDACIONES PENDIENTES) ---
            st.markdown("<p style='color:#ffaa00; font-weight:700; font-size:18px; letter-spacing:2px;'>1. MERCADERÍA SIN INSTRUIR (CONSOLIDACIONES PENDIENTES)</p>", unsafe_allow_html=True)
            
            col_inst_idx = 20
            col_inst_name = [c for c in df.columns if 'INSTRUCCION' in c.upper()]
            col_mono_plan = [c for c in df.columns if 'MONOPROVEEDOR' in c.upper()]
            
            c_inst = col_inst_name[0] if col_inst_name else df.columns[col_inst_idx]
            c_mono_p = col_mono_plan[0] if col_mono_plan else df.columns[31]
            
            df_ni = df[df[c_inst].isna() | (df[c_inst].astype(str).str.strip().isin(['', 'nan', 'SIN INSTRUCCION', 'sin instruccion']))].copy()
            
            # Filtro 1: Exclusión de Muestras y Repuestos (Col AN / índice 39)
            keywords_excl = ["MUESTRA COURRIER", "MUESTRAS", "MUESTRA", "REPUESTOS"]
            df_ni = df_ni[~df_ni.iloc[:, 39].astype(str).str.upper().str.contains('|'.join(keywords_excl), na=False)].copy()
            
            # Filtro 2: Por Fecha Prioritaria y Monoproveedor
            # Mono "No" -> hoy + 10 días
            # Mono "Si" -> hoy + 25 días
            hoy_ni = pd.Timestamp(datetime.now().date())
            df_ni['Fecha_Prior_DT'] = pd.to_datetime(df.iloc[:, 99], dayfirst=True, errors='coerce')
            
            def filter_ni(row):
                is_mono = "SÍ" in str(row[c_mono_p]).upper() or "SI" in str(row[c_mono_p]).upper()
                limite = hoy_ni + timedelta(days=25 if is_mono else 10)
                return row['Fecha_Prior_DT'] <= limite

            df_no_inst = df_ni[df_ni.apply(filter_ni, axis=1)].copy()
            
            if not df_no_inst.empty:
                col_puerto = df.columns[41]
                puertos_disp = sorted(df_no_inst[col_puerto].astype(str).unique().tolist())
                # Placeholder para ocultar por defecto
                sel_ptr = st.selectbox("🚢 FILTRAR POR PUERTO DE SALIDA (PENDIENTES):", ["-- SELECCIONAR PUERTO --", "TODOS"] + puertos_disp, key="sel_ptr_noinst_vfinal")
                
                if sel_ptr != "-- SELECCIONAR PUERTO --":
                    df_no_inst_f = df_no_inst if sel_ptr == "TODOS" else df_no_inst[df_no_inst[col_puerto] == sel_ptr]
                    
                    # Columna AD (índice 29) es N Invoice
                    col_n_inv = df.columns[29]
                    
                    # Preparación de tabla ordenada y formateada
                    df_no_inst_f = df_no_inst_f.sort_values('Fecha_Prior_DT', ascending=True)
                    df_no_inst_f['F. Prioritaria'] = df_no_inst_f['Fecha_Prior_DT'].dt.strftime('%d/%m/%Y')
                    
                    st.dataframe(df_no_inst_f[[col_n_inv, 'SO', 'F. Prioritaria', 'M3 Total', c_mono_p]], 
                                 column_config={'M3 Total': st.column_config.NumberColumn("M3", format="%.1f")},
                                 use_container_width=True, hide_index=True)
                    st.info(f"💡 Mostrando SOs sin instruir con prioridad <= {hoy_ni.strftime('%d/%m')} (+10d No Mono / +25d Mono).")
            else: st.info("Sin SOs pendientes de instrucción para el rango de fechas actual.")

            st.markdown("<br><hr class='white-divider'><br>", unsafe_allow_html=True)

            # --- MONITOR 2: ALERTA DE TIEMPOS DE CONSOLIDACIÓN (SLA) ---
            st.markdown("<p style='color:#00ff88; font-weight:700; font-size:18px; letter-spacing:2px;'>2. ALERTA DE TIEMPOS DE CONSOLIDACIÓN (FUERA DE SLA)</p>", unsafe_allow_html=True)
            
            col_mono = [c for c in df_re.columns if 'MONOPROVEEDOR' in c.upper()][0] if any('MONOPROVEEDOR' in c.upper() for c in df_re.columns) else df_re.columns[31]
            
            def clean_num_alert(val):
                if pd.isna(val) or str(val).strip() in ['', 'nan']: return 0.0
                try:
                    s = str(val).replace(',', '.').replace(' ', '').strip()
                    return pd.to_numeric(s, errors='coerce')
                except: return 0.0

            df_re['T_Consol'] = df_re.iloc[:, 29].apply(clean_num_alert).fillna(0.0)
            df_re['DT_ETD_M'] = pd.to_datetime(df_re.iloc[:, 12], dayfirst=True, errors='coerce')
            
            def get_sla(row):
                if "SÍ" in str(row[col_mono]).upper() or "SI" in str(row[col_mono]).upper() or "MONO" in str(row[col_mono]).upper():
                    return 7
                return 25
            
            df_re['SLA_Limit'] = df_re.apply(get_sla, axis=1)
            df_sla_alert = df_re[df_re['T_Consol'] > df_re['SLA_Limit']].copy()
            
            if not df_sla_alert.empty:
                col_resp_sla = [c for c in df_re.columns if 'ANALISTA' in c.upper() or 'RESPONSABLE' in c.upper()]
                col_r_sla = col_resp_sla[0] if col_resp_sla else df_re.columns[6]
                
                analistas_sla = sorted(df_sla_alert[col_r_sla].astype(str).unique().tolist())
                sel_an_sla = st.selectbox("🎯 FILTRAR POR RESPONSABLE (SLA):", ["-- SELECCIONAR RESPONSABLE --", "TODOS"] + analistas_sla, key="sel_sla_an_vfinal_v2")
                
                if sel_an_sla != "-- SELECCIONAR RESPONSABLE --":
                    df_sla_f = df_sla_alert if sel_an_sla == "TODOS" else df_sla_alert[df_sla_alert[col_r_sla] == sel_an_sla]
                    
                    df_sla_table = df_sla_f[[df_sla_f.columns[0], df_sla_f.columns[4], 'DT_ETD_M', 'T_Consol', col_r_sla, col_mono]].copy()
                    df_sla_table['DT_ETD_M'] = df_sla_table['DT_ETD_M'].dt.strftime('%d/%m/%Y')
                    df_sla_table.columns = ["Embarque", "Puerto/Aero", "ETD", "Días Consol.", "Responsable", "¿Mono?"]
                    
                    st.dataframe(df_sla_table.sort_values("ETD", ascending=True), use_container_width=True, hide_index=True)
                    st.info("💡 Los casos anteriores superan los 7 días (Monoproveedor) o 25 días (Consolidado).")
            else: st.success("Todos los tiempos de consolidación están dentro de los límites de SLA.")

            st.markdown("<br><hr class='white-divider'><br>", unsafe_allow_html=True)

            # --- MONITOR 3: MONITOR DE AGRUPAMIENTO (>7 DÍAS VENTANA) ---
            st.markdown("<p style='color:#00a8ff; font-weight:700; font-size:18px; letter-spacing:2px;'>3. MONITOR DE AGRUPAMIENTO (>7 DÍAS VENTANA)</p>", unsafe_allow_html=True)
            df_re['P_Min'] = pd.to_datetime(df_re.iloc[:, 18], dayfirst=True, errors='coerce')
            df_re['P_Max'] = pd.to_datetime(df_re.iloc[:, 19], dayfirst=True, errors='coerce')
            df_re['Rango_Dias'] = (df_re['P_Max'] - df_re['P_Min']).dt.days
            
            df_alert_g = df_re[df_re['Rango_Dias'] > 7].copy()
            if not df_alert_g.empty:
                col_analista = [c for c in df_re.columns if 'ANALISTA' in c.upper() or 'RESPONSABLE' in c.upper()]
                col_an = col_analista[0] if col_analista else df_re.columns[6]
                
                analistas_disp = sorted(df_alert_g[col_an].astype(str).unique().tolist())
                sel_an = st.selectbox("🎯 FILTRAR POR ANALISTA (AGRUPAMIENTO):", ["-- SELECCIONAR ANALISTA --", "TODOS"] + analistas_disp, key="sel_an_agrup_v4")
                
                if sel_an != "-- SELECCIONAR ANALISTA --":
                    df_g_show = df_alert_g if sel_an == "TODOS" else df_alert_g[df_alert_g[col_an] == sel_an]
                    
                    df_g_table = df_g_show.groupby(df_re.columns[0]).agg({
                        col_an: 'first',
                        'P_Min': 'min',
                        'P_Max': 'max',
                        'Rango_Dias': 'max',
                        df_re.columns[10]: 'first', # ETD OK FFWW
                        df_re.columns[12]: 'first'  # ETD
                    }).reset_index()
                    
                    df_g_table['P_Min'] = pd.to_datetime(df_g_table['P_Min']).dt.strftime('%d/%m/%Y')
                    df_g_table['P_Max'] = pd.to_datetime(df_g_table['P_Max']).dt.strftime('%d/%m/%Y')
                    df_g_table.columns = ["Embarque", "Analista", "F. Min Packeo", "F. Max Packeo", "Días Rango", "ETD Status", "ETD"]
                    
                    st.dataframe(df_g_table.sort_values('Días Rango', ascending=False), use_container_width=True, hide_index=True)
            else: st.success("Agrupamientos eficientes (<= 7 días).")

            st.markdown("<br><hr class='white-divider'><br>", unsafe_allow_html=True)

            # --- MONITOR 4: ALERTA CARGA NO MOVILIZADA (PENDIENTE TRÁNSITO) ---
            st.markdown("<p style='color:#ff4b4b; font-weight:700; font-size:18px; letter-spacing:2px;'>4. ALERTA CARGA NO MOVILIZADA (TRÁNSITO PENDIENTE)</p>", unsafe_allow_html=True)
            
            df_re['DT_ETD_M'] = pd.to_datetime(df_re.iloc[:, 12], dayfirst=True, errors='coerce')
            df_re['Status_OK_K'] = df_re.iloc[:, 10].astype(str).str.lower().str.strip() == "ok"
            
            col_impo2_v4 = df_re.columns[30]
            df_re['Impo2_Status'] = df_re[col_impo2_v4].astype(str).str.strip()
            
            hoy_v4 = pd.Timestamp(datetime.now().date())
            df_no_mov = df_re[df_re['Status_OK_K'] & (df_re['DT_ETD_M'] <= hoy_v4) & (df_re['Impo2_Status'] == "Falta cargar")].copy()
            
            if not df_no_mov.empty:
                col_resp_v4 = [c for c in df_re.columns if 'ANALISTA' in c.upper() or 'RESPONSABLE' in c.upper()]
                col_r_v4 = col_resp_v4[0] if col_resp_v4 else df_re.columns[6]
                
                analistas_m3 = sorted(df_no_mov[col_r_v4].astype(str).unique().tolist())
                sel_an3 = st.selectbox("👨‍💻 FILTRAR POR RESPONSABLE (MOVILIZACIÓN):", ["-- SELECCIONAR RESPONSABLE --", "TODOS"] + analistas_m3, key="sel_an_mov_v4")
                
                if sel_an3 != "-- SELECCIONAR RESPONSABLE --":
                    df_no_mov_f = df_no_mov if sel_an3 == "TODOS" else df_no_mov[df_no_mov[col_r_v4] == sel_an3]
                    
                    df_view = df_no_mov_f[[df_no_mov_f.columns[0], df_no_mov_f.columns[12], col_resp_v4[0] if col_resp_v4 else df_no_mov_f.columns[6], col_impo2_v4]].copy()
                    df_view.columns = ["Embarque", "ETD (Col M)", "Responsable", "Status Impo2"]
                    st.dataframe(df_view.sort_values("ETD (Col M)", ascending=True), use_container_width=True, hide_index=True)
            else: st.success("Todo movilizado correctamente según Reservas.")

        except Exception as e: st.error(f"Error en Alertas: {e}")

      # --- SOLAPA 8: ASK COMEX ---
    with tabs[7]:
        st.markdown("<div style='text-align:center; padding: 40px; background: rgba(0, 168, 255, 0.05); border-radius: 20px; border: 2px dashed rgba(0, 168, 255, 0.2);'><h2 style='color:#00a8ff; font-weight:800; letter-spacing:10px;'>ASK COMEX</h2><p style='color:#94a3b8; font-size:18px; margin-top:20px;'>Inteligencia Operativa en Tiempo Real.</p></div>", unsafe_allow_html=True)
        
        # --- CHAT FLOTANTE IA (CAPITÁN COMEX) ---
        st.markdown("<br>", unsafe_allow_html=True)
        try:
            # El botón emergente (Popover)
            with st.popover("💬 Hablar con Capitán Comex (IA)", use_container_width=False):
                st.markdown("<h4 style='color:#00ff88; margin-bottom:0;'>🚢 Capitán Comex</h4>", unsafe_allow_html=True)
                st.caption("Asistente Logístico con IA (Google Gemini)")
                
                # Inicializar historial de chat si no existe
                if "chat_history" not in st.session_state:
                    st.session_state.chat_history = [{"role": "assistant", "content": "¡Hola! Soy Capitán Comex. ¿Qué embarque buscamos o qué duda operativa tienes?"}]
                
                # Contenedor con altura máxima para el chat
                chat_container = st.container(height=400)
                
                # Mostrar mensajes previos
                with chat_container:
                    for msg in st.session_state.chat_history:
                        avatar = "🚢" if msg["role"] == "assistant" else "👤"
                        with st.chat_message(msg["role"], avatar=avatar):
                            st.markdown(msg["content"])
                
                # Caja de texto para que el usuario pregunte
                if prompt := st.chat_input("Hazle una pregunta a la IA..."):
                    st.session_state.chat_history.append({"role": "user", "content": prompt})
                    with chat_container:
                        with st.chat_message("user", avatar="👤"):
                            st.markdown(prompt)
                        
                        with st.chat_message("assistant", avatar="🚢"):
                            resp_placeholder = st.empty()
                            resp_placeholder.markdown("Pensando... ⏳")
                            
                            # --- CONEXIÓN A GEMINI ---
                            try:
                                import google.generativeai as genai
                                # Llave ingresada directamente para pruebas rápidas
                                api_key = "AIzaSyD-U3LuAqHWDJzsYJrjUcX9l6YXh6tmdNI"
                                
                                if not api_key:
                                    respuesta_ia = "⚠️ Falla: No encontré la GEMINI_API_KEY en los secretos de Streamlit."
                                else:
                                    genai.configure(api_key=api_key)
                                    
                                    # Usamos gemini-pro que es el más universal y estable
                                    model = genai.GenerativeModel('gemini-pro')
                                    
                                    # Personalidad de la IA
                                    system_prompt = """Eres 'Capitán Comex', un asistente ejecutivo experto en comercio exterior y logística internacional de la empresa Bidcom. 
Tu trabajo es analizar los datos de los embarques en pantalla y responder a las consultas del usuario de manera clara, proactiva y muy profesional. 
Usa emojis sutiles. Si te preguntan por riesgos operativos, evalúa las fechas (Fin de Producción, Instrucción, ETD, ETA) y las cantidades para detectar alertas (ej: demoras excesivas, consolidaciones lentas).
No inventes datos. Si te preguntan algo que no está en el contexto, indícalo amablemente."""
                                    
                                    # Armar contexto basado en la última búsqueda del usuario
                                    contexto = "Datos actuales de la búsqueda en pantalla:\n"
                                    if "ultimos_resultados" in st.session_state and st.session_state.ultimos_resultados:
                                        for r in st.session_state.ultimos_resultados:
                                            contexto += f"- Invoice: {r['inv']}, SO: {r['so']}, Embarque: {r['emb']}, Proveedor: {r['prov']}, Estadio: {r['estadio']} ({r['desc_estadio']}), Cantidad Total: {r['cant']}, Fecha Instrucción: {r['fecha_inst']}. {r['info_extra']}\n"
                                    else:
                                        contexto += "El usuario no tiene ningún embarque filtrado en pantalla en este momento."
                                    
                                    # Prompt unificado
                                    prompt_final = f"{system_prompt}\n\nCONTEXTO INVISIBLE DE LA PANTALLA ACTUAL:\n{contexto}\n\nPREGUNTA DEL USUARIO:\n{prompt}"
                                    
                                    # Generar respuesta
                                    response = model.generate_content(prompt_final)
                                    respuesta_ia = response.text
                            except Exception as e:
                                respuesta_ia = f"Hubo un error de conexión con la IA: {str(e)}"
                            
                            resp_placeholder.markdown(respuesta_ia)
                            st.session_state.chat_history.append({"role": "assistant", "content": respuesta_ia})
                            
        except AttributeError:
            st.error("⚠️ Para usar este chat flotante, necesitamos actualizar Streamlit. (Requiere versión 1.33 o superior).")
            
        st.markdown("<hr class='white-divider'>", unsafe_allow_html=True)
        
        # Carga de datos secundaria para búsquedas
        @st.cache_data(ttl=60)
        def load_ask_comex_data():
            url_reserva = f"{base_url}/export?format=csv&gid=276804813"
            url_hist = f"{base_url}/export?format=csv&gid=32771816"
            url_emb_hist = "https://docs.google.com/spreadsheets/d/1uDV3-CK5aeb-PI81uNc54t4L50HhscHe5xkp-pL9SyI/export?format=csv&gid=50628730"
            try:
                res = pd.read_csv(url_reserva, engine='python', on_bad_lines='skip')
            except:
                res = pd.DataFrame()
            try:
                hi = pd.read_csv(url_hist, engine='python', on_bad_lines='skip')
            except:
                hi = pd.DataFrame()
            try:
                emb_hi = pd.read_csv(url_emb_hist, engine='python', on_bad_lines='skip')
            except:
                emb_hi = pd.DataFrame()
            return res, hi, emb_hi

        df_res_ask, df_hi_ask, df_emb_hi_ask = load_ask_comex_data()
        
        st.markdown("<br>", unsafe_allow_html=True)
        query = st.text_input("🔍 INGRESE SO, INVOICE O SKU (CÓDIGO):", placeholder="Ej: SO-12345, INV-999, SKU-XYZ...")
        
        if query:
            query = str(query).strip().upper()
            
            # Aseguramos columnas GSO
            col_so = [c for c in df.columns if 'SO' in c.upper()][0] if any('SO' in c.upper() for c in df.columns) else df.columns[0]
            col_inv = [c for c in df.columns if 'N INVOICE' in c.upper() or 'N° INVOICE' in c.upper()][0] if any('N INVOICE' in c.upper() or 'N° INVOICE' in c.upper() for c in df.columns) else df.columns[29]
            col_sku = [c for c in df.columns if c.strip().upper() == 'CODIGO' or c.strip().upper() == 'CÓDIGO'][0] if any(c.strip().upper() in ['CODIGO', 'CÓDIGO'] for c in df.columns) else df.columns[32]
            
            mask_so = df[col_so].astype(str).str.upper().str.contains(query, na=False)
            mask_inv = df[col_inv].astype(str).str.upper().str.contains(query, na=False)
            mask_sku = df[col_sku].astype(str).str.upper().str.contains(query, na=False)
            
            df_found = df[mask_so | mask_inv | mask_sku]
            is_historical = False
            
            # Busqueda en cascada: si no hay en activo, buscamos en historico
            if df_found.empty and not df_emb_hi_ask.empty:
                col_embhi_so = df_emb_hi_ask.columns[0] if len(df_emb_hi_ask.columns) > 0 else None
                col_embhi_inv = df_emb_hi_ask.columns[19] if len(df_emb_hi_ask.columns) > 19 else None
                col_embhi_sku = df_emb_hi_ask.columns[5] if len(df_emb_hi_ask.columns) > 5 else None
                
                if col_embhi_so and col_embhi_inv and col_embhi_sku:
                    m_so = df_emb_hi_ask[col_embhi_so].astype(str).str.upper().str.contains(query, na=False)
                    m_inv = df_emb_hi_ask[col_embhi_inv].astype(str).str.upper().str.contains(query, na=False)
                    m_sku = df_emb_hi_ask[col_embhi_sku].astype(str).str.upper().str.contains(query, na=False)
                    df_found = df_emb_hi_ask[m_so | m_inv | m_sku]
                    if not df_found.empty:
                        is_historical = True
            
            if df_found.empty:
                st.warning(f"No se encontraron registros para '{query}' en GSO v4 ni en Embarques Históricos.")
            else:
                origen = "Embarques Históricos" if is_historical else "GSO v4 (Planif Cargas)"
                st.success(f"✅ ¡Registro encontrado! ({len(df_found)} coincidencias en {origen})")
                
                if len(df_found) > 50:
                    st.warning(f"⚠️ Se encontraron {len(df_found)} resultados. Procesando los primeros 50 para agrupar.")
                    df_found = df_found.head(50)
                
                resultados_procesados = []
                
                for i, row in df_found.iterrows():
                    if is_historical:
                        # Extraer datos con indices historicos
                        val_so = str(row.iloc[0])
                        val_inv = str(row.iloc[19])
                        val_sku = str(row.iloc[5])
                        val_emb = str(row.iloc[4]).strip()
                        if val_emb.lower() == 'nan': val_emb = "Sin Asignar"
                        val_prov = str(row.iloc[18])
                        
                        val_etd_gso = str(row.iloc[6]).strip()
                        val_eta_gso = str(row.iloc[7]).strip()
                        val_fin_prod = str(row.iloc[2]).strip()
                        if val_fin_prod.lower() == 'nan' or val_fin_prod == '': val_fin_prod = "Sin Info"
                        
                        try: val_cant_emb = float(str(row.iloc[9]).replace(',', '.').strip())
                        except: val_cant_emb = 0.0
                        cantidad_mostrar = int(val_cant_emb)
                        label_cant = "CANTIDAD EMB"
                        
                        # Buscar Fecha Instruccion en Reservas Historicas (col H = index 7) por Embarque (col A = index 0)
                        val_fecha_inst = "Pendiente"
                        if not df_hi_ask.empty and len(df_hi_ask.columns) > 7:
                            col_hi_emb = df_hi_ask.columns[0]
                            hi_match = df_hi_ask[df_hi_ask[col_hi_emb].astype(str).str.strip().str.upper() == val_emb.upper()]
                            if not hi_match.empty:
                                val_f = str(hi_match.iloc[0].iloc[7]).strip()
                                if val_f.lower() != 'nan' and val_f != '':
                                    val_fecha_inst = val_f
                        
                        hoy = datetime.now().date()
                        try: dt_eta = pd.to_datetime(val_eta_gso, dayfirst=True).date()
                        except: dt_eta = None
                        
                        if dt_eta and dt_eta < hoy:
                            estadio = 5
                            desc_estadio = "ARRIBADO (HISTÓRICO)"
                            color_estadio = "#00ff88"
                            info_extra = f"La carga finalizó su ciclo y se encuentra en archivo histórico. (ETA: {val_eta_gso})"
                        else:
                            estadio = 4
                            desc_estadio = "EN TRÁNSITO (HISTÓRICO)"
                            color_estadio = "#00a8ff"
                            info_extra = f"La carga figura despachada en registros históricos pero su ETA es futura. (ETA: {val_eta_gso})"
                            
                    else:
                        # Extraer datos de GSO v4
                        val_so = str(row[col_so])
                        val_inv = str(row[col_inv])
                        val_sku = str(row[col_sku])
                        
                        col_prov = [c for c in df.columns if 'PROVEEDOR' in c.upper()][0] if any('PROVEEDOR' in c.upper() for c in df.columns) else df.columns[30]
                        val_prov = str(row[col_prov])
                        
                        col_emb = [c for c in df.columns if 'EMBARQUE' in c.upper()][0] if any('EMBARQUE' in c.upper() for c in df.columns) else df.columns[16]
                        val_emb = str(row[col_emb]).strip()
                        if val_emb.lower() == 'nan': val_emb = "Sin Asignar"
                        
                        col_inst = [c for c in df.columns if 'INSTRUCCION' in c.upper() or 'INSTRUCCIÓN' in c.upper()][0] if any('INSTRUCCION' in c.upper() or 'INSTRUCCIÓN' in c.upper() for c in df.columns) else df.columns[20]
                        val_inst = str(row[col_inst]).strip()
                        
                        col_fin_prod = [c for c in df.columns if 'FIN PRODUCCIÓN REAL' in c.upper() or 'FIN PRODUCCION REAL' in c.upper()][0] if any('FIN PRODUCCI' in c.upper() and 'REAL' in c.upper() for c in df.columns) else df.columns[4]
                        val_fin_prod = str(row[col_fin_prod]).strip()
                        if val_fin_prod.lower() == 'nan' or val_fin_prod == '': val_fin_prod = "Sin Info"
                        
                        val_fecha_inst = val_inst if (val_inst != "" and val_inst.lower() != "nan" and "sin instruccion" not in val_inst.lower()) else "Pendiente"
                        
                        col_eta = [c for c in df.columns if 'ETA' in c.upper()][0] if any('ETA' in c.upper() for c in df.columns) else df.columns[24]
                        val_eta_gso = str(row[col_eta]).strip()
                        
                        col_etd = [c for c in df.columns if 'ETD' in c.upper()][0] if any('ETD' in c.upper() for c in df.columns) else df.columns[23]
                        val_etd_gso = str(row[col_etd]).strip()
                        
                        col_cant_pend = [c for c in df.columns if 'CANTIDAD PENDIENTE DE EMBARCAR' in c.upper()][0] if any('CANTIDAD PENDIENTE DE EMBARCAR' in c.upper() for c in df.columns) else df.columns[21]
                        col_cant_emb = [c for c in df.columns if 'CANTIDAD EMB' in c.upper() and 'PREVENTA' not in c.upper()][0] if any('CANTIDAD EMB' in c.upper() and 'PREVENTA' not in c.upper() for c in df.columns) else df.columns[60]
                        
                        try: val_cant_pend = float(str(row[col_cant_pend]).replace(',', '.').strip())
                        except: val_cant_pend = 0.0
                        try: val_cant_emb = float(str(row[col_cant_emb]).replace(',', '.').strip())
                        except: val_cant_emb = 0.0
                        
                        if val_cant_pend == 0:
                            cantidad_mostrar = int(val_cant_emb)
                            label_cant = "CANTIDAD EMB"
                        else:
                            cantidad_mostrar = int(val_cant_pend)
                            label_cant = "CANT. PENDIENTE"
                        
                        estadio = 1
                        desc_estadio = "PENDIENTE DE INSTRUCCIÓN"
                        color_estadio = "#94a3b8"
                        info_extra = "La carga no ha sido instruida. Se encuentra en origen sin gestión iniciada."
                        
                        tiene_inst = val_fecha_inst != "Pendiente"
                        
                        if tiene_inst:
                            estadio = 2
                            desc_estadio = "INSTRUIDA / EN GESTIÓN"
                            color_estadio = "#ffaa00"
                            info_extra = f"Instruida el {val_inst}. Esperando confirmación de Booking en Reservas."
                            
                            df_res_ask.columns = df_res_ask.columns.str.strip()
                            col_res_emb = df_res_ask.columns[0] if not df_res_ask.empty else None
                            
                            status_res = ""
                            if col_res_emb:
                                res_match = df_res_ask[df_res_ask[col_res_emb].astype(str).str.strip().str.upper() == val_emb.upper()]
                                if not res_match.empty:
                                    r_row = res_match.iloc[0]
                                    status_res = str(r_row.iloc[10]).upper().strip() if len(r_row) > 10 else ""
                            
                            hoy = datetime.now().date()
                            try: dt_eta_gso = pd.to_datetime(val_eta_gso, dayfirst=True).date()
                            except: dt_eta_gso = None
                            try: dt_etd_gso = pd.to_datetime(val_etd_gso, dayfirst=True).date()
                            except: dt_etd_gso = None
                            
                            in_historical = False
                            if not df_hi_ask.empty:
                                df_hi_ask.columns = df_hi_ask.columns.str.strip()
                                col_hi_emb = df_hi_ask.columns[0]
                                hi_match = df_hi_ask[df_hi_ask[col_hi_emb].astype(str).str.strip().str.upper() == val_emb.upper()]
                                if not hi_match.empty:
                                    in_historical = True
                            
                            if in_historical or (dt_eta_gso and dt_eta_gso <= hoy):
                                estadio = 5
                                desc_estadio = "ARRIBADO"
                                color_estadio = "#00ff88"
                                info_extra = f"La carga ha llegado a destino. (ETA GSO: {val_eta_gso})"
                            elif dt_etd_gso and dt_etd_gso <= hoy:
                                estadio = 4
                                desc_estadio = "EN TRÁNSITO"
                                color_estadio = "#00a8ff"
                                info_extra = f"La carga está navegando/volando hacia destino. (ETD: {dt_etd_gso.strftime('%d/%m/%Y')} | ETA: {val_eta_gso})"
                            elif status_res == "OK" or (dt_etd_gso and dt_etd_gso > hoy):
                                estadio = 3
                                desc_estadio = "BOOKING CONFIRMADO"
                                color_estadio = "#a855f7"
                                info_extra = f"Espacio confirmado. Esperando zarpada. (ETD aprox: {dt_etd_gso.strftime('%d/%m/%Y') if dt_etd_gso else 'No def'})"

                    resultados_procesados.append({
                        "estadio": estadio,
                        "desc_estadio": desc_estadio,
                        "color_estadio": color_estadio,
                        "info_extra": info_extra,
                        "so": val_so,
                        "inv": val_inv,
                        "sku": val_sku,
                        "emb": val_emb,
                        "prov": val_prov,
                        "cant": cantidad_mostrar,
                        "label_cant": label_cant,
                        "fecha_inst": val_fecha_inst,
                        "fin_prod": val_fin_prod
                    })

                # Guardar en memoria para que la IA los pueda leer
                st.session_state.ultimos_resultados = resultados_procesados

                # AGRUPACIÓN DE RESULTADOS
                agrupados = {}
                for r in resultados_procesados:
                    key = (r['estadio'], r['inv'], r['emb'])
                    if key not in agrupados:
                        agrupados[key] = {
                            "estadio": r['estadio'],
                            "desc_estadio": r['desc_estadio'],
                            "color_estadio": r['color_estadio'],
                            "info_extra": r['info_extra'],
                            "inv": r['inv'],
                            "emb": r['emb'],
                            "prov": r['prov'],
                            "sos": [],
                            "skus": [],
                            "total_cant": 0,
                            "label_cant": r['label_cant'],
                            "fechas_inst": set(),
                            "fines_prod": set()
                        }
                    
                    if r['so'] not in agrupados[key]['sos']:
                        agrupados[key]['sos'].append(r['so'])
                    if r['sku'] not in agrupados[key]['skus']:
                        agrupados[key]['skus'].append(r['sku'])
                    
                    agrupados[key]['total_cant'] += r['cant']
                    agrupados[key]['fechas_inst'].add(r['fecha_inst'])
                    agrupados[key]['fines_prod'].add(r['fin_prod'])

                # MOSTRAR TARJETAS AGRUPADAS
                st.success(f"📌 Mostrando {len(agrupados)} agrupaciones de cargas consolidadas.")
                
                for key, grp in agrupados.items():
                    sos_str = "<br>".join(grp['sos'])
                    skus_str = "<br>".join(grp['skus'])
                    f_inst_str = "<br>".join(sorted(list(grp['fechas_inst'])))
                    f_prod_str = "<br>".join(sorted(list(grp['fines_prod'])))
                    
                    # Scroll interno si hay muchos elementos en la lista
                    div_sos = f"<div style='max-height:80px; overflow-y:auto; padding-right:5px;'>{sos_str}</div>" if len(grp['sos']) > 2 else sos_str
                    div_skus = f"<div style='max-height:80px; overflow-y:auto; padding-right:5px;'>{skus_str}</div>" if len(grp['skus']) > 2 else skus_str
                    
                    html_card = f"""
<div class="custom-card" style="border-top: 5px solid {grp['color_estadio']};">
    <h3 style="color:{grp['color_estadio']}; text-transform:uppercase; letter-spacing:2px; margin-bottom: 10px;">ESTADIO {grp['estadio']}: {grp['desc_estadio']}</h3>
    <p style="color:#f8fafc; font-size:16px;">{grp['info_extra']}</p>
    <hr style="border:none; border-top:1px solid rgba(255,255,255,0.1); margin:20px 0;">
    <div class="grid-4" style="align-items: start;">
        <div><p class="minicard-title">SO ({len(grp['sos'])})</p><p class="minicard-value" style="font-size:16px;">{div_sos}</p></div>
        <div><p class="minicard-title">INVOICE</p><p class="minicard-value" style="font-size:20px;">{grp['inv']}</p></div>
        <div><p class="minicard-title">SKU / CÓDIGO ({len(grp['skus'])})</p><p class="minicard-value" style="font-size:16px;">{div_skus}</p></div>
        <div><p class="minicard-title">EMBARQUE</p><p class="minicard-value" style="font-size:20px; color:#00a8ff;">{grp['emb']}</p></div>
    </div>
    <div class="grid-4" style="margin-top:20px; align-items: center; border-top: 1px dashed rgba(255,255,255,0.1); padding-top: 15px;">
        <div style="grid-column: span 1;">
            <p class="minicard-title">F. INSTRUCCIÓN</p>
            <p style="font-size:16px; color:#f8fafc;">{f_inst_str}</p>
        </div>
        <div style="grid-column: span 1;">
            <p class="minicard-title">FIN PRODUCCIÓN</p>
            <p style="font-size:16px; color:#f8fafc;">{f_prod_str}</p>
        </div>
        <div style="grid-column: span 1;">
            <p class="minicard-title">PROVEEDOR</p>
            <p style="font-size:16px; color:#f8fafc; font-weight:600; text-overflow: ellipsis; overflow: hidden; white-space: nowrap;" title="{grp['prov']}">{grp['prov']}</p>
        </div>
        <div style="text-align: right;">
            <p class="minicard-title">TOTAL {grp['label_cant']}</p>
            <p style="font-size:28px; color:#00ff88; font-weight:900; margin:0;">{grp['total_cant']}</p>
        </div>
    </div>
</div>
"""
                    st.markdown(html_card, unsafe_allow_html=True)
                    
                    pct_progreso = grp['estadio'] * 20
                    html_progress = f"""
<div style="width: 100%; background-color: rgba(255,255,255,0.1); border-radius: 10px; margin-top:20px; height: 10px;">
    <div style="width: {pct_progreso}%; background-color: {grp['color_estadio']}; height: 10px; border-radius: 10px; transition: width 0.5s;"></div>
</div>
<div style="display: flex; justify-content: space-between; margin-top: 10px; padding: 0 5px;">
    <span style="font-size: 11px; font-weight:700; color: {'#fff' if grp['estadio'] >= 1 else '#64748b'};">1. PENDIENTE</span>
    <span style="font-size: 11px; font-weight:700; color: {'#fff' if grp['estadio'] >= 2 else '#64748b'};">2. INSTRUIDO</span>
    <span style="font-size: 11px; font-weight:700; color: {'#fff' if grp['estadio'] >= 3 else '#64748b'};">3. BOOKING</span>
    <span style="font-size: 11px; font-weight:700; color: {'#fff' if grp['estadio'] >= 4 else '#64748b'};">4. TRÁNSITO</span>
    <span style="font-size: 11px; font-weight:700; color: {'#fff' if grp['estadio'] >= 5 else '#64748b'};">5. ARRIBADO</span>
</div>
<br><br>
"""
                    st.markdown(html_progress, unsafe_allow_html=True)


    # --- SOLAPA 6: ALERTAS ESTRATÉGICAS ---
    with tabs[5]:
        try:
            st.markdown("<h2 style='color:#00a8ff; font-weight:800; letter-spacing:4px; margin:20px 0; font-size:24px; text-align:center;'>ALERTAS ESTRATÉGICAS</h2>", unsafe_allow_html=True)
            
            # Recargamos Reservas para asegurar datos frescos
            url_reserva = f"{base_url}/export?format=csv&gid=276804813&nocache={time.time()}"
            try: df_res_alt = load_reserva_data(url_reserva)
            except: df_res_alt = pd.read_csv(url_reserva)
            df_res_alt.columns = df_res_alt.columns.str.strip()

            # 1. MONITOR DE GESTIÓN POR FORWARDER (CRÍTICOS MOVILIZADOS)
            st.markdown("<hr class='glow-divider'>", unsafe_allow_html=True)
            st.markdown("<p style='color:#ff4b4b; font-weight:700; letter-spacing:2px; font-size:18px;'>1. MONITOR DE GESTIÓN POR FORWARDER (CRÍTICOS)</p>", unsafe_allow_html=True)
            
            df_res_alt['DT_Inst'] = pd.to_datetime(df_res_alt.iloc[:, 7], dayfirst=True, errors='coerce')
            df_res_alt['ETD_Status_K'] = df_res_alt.iloc[:, 10].astype(str).str.upper().str.strip()
            df_res_alt['Espera'] = (pd.to_datetime('today') - df_res_alt['DT_Inst']).dt.days
            df_res_alt['Critico'] = (df_res_alt['ETD_Status_K'] != "OK") & (df_res_alt['Espera'] > 5)
            
            df_crit = df_res_alt[df_res_alt['Critico']].copy()
            if not df_crit.empty:
                agentes_crit = sorted(df_crit.iloc[:, 6].unique().tolist())
                sel_ag = st.selectbox("FILTRAR POR AGENTE (CASOS CRÍTICOS):", ["TODOS"] + agentes_crit, key="ag_crit_tab3")
                df_crit_show = df_crit if sel_ag == "TODOS" else df_crit[df_crit.iloc[:, 6] == sel_ag]
                
                # Columnas: Embarque (0), Fecha Instruccion (7), Packeo Min (18), Packeo Max (19), Espera
                cols_show = [df_crit.columns[0], df_crit.columns[7], df_crit.columns[18], df_crit.columns[19], 'Espera']
                df_crit_disp = df_crit_show[cols_show].copy()
                df_crit_disp.columns = ["Embarque", "Fecha Instrucción", "F. Packeo Min", "F. Packeo Max", "Días de Espera"]
                
                st.dataframe(df_crit_disp.sort_values('Días de Espera', ascending=False), 
                             column_config={"Días de Espera": st.column_config.NumberColumn("Wait", format="%d ⚠️")},
                             use_container_width=True, hide_index=True)
            else:
                st.success("No hay alertas de gestión pendientes. ✅")

            # 2. MONITOR DE AGRUPAMIENTO DE MERCADERÍA
            st.markdown("<br><hr class='glow-divider'>", unsafe_allow_html=True)
            st.markdown("<p style='color:#00a8ff; font-weight:700; letter-spacing:2px; font-size:18px;'>2. MONITOR DE AGRUPAMIENTO DE MERCADERÍA</p>", unsafe_allow_html=True)
            
            df_res_alt['P_Min'] = pd.to_datetime(df_res_alt.iloc[:, 18], dayfirst=True, errors='coerce')
            df_res_alt['P_Max'] = pd.to_datetime(df_res_alt.iloc[:, 19], dayfirst=True, errors='coerce')
            df_res_alt['Rango_Dias'] = (df_res_alt['P_Max'] - df_res_alt['P_Min']).dt.days
            
            # Alertamos si el rango es > 7 días
            df_alert_g = df_res_alt[df_res_alt['Rango_Dias'] > 7].copy()
            
            if not df_alert_g.empty:
                st.warning(f"Se han detectado {len(df_alert_g.iloc[:, 0].unique())} embarques con ventanas de producción extendidas (>7 días).")
                
                # Agrupamos por embarque para ver el rango real
                df_g_table = df_alert_g.groupby(df_alert_g.columns[0]).agg({
                    df_alert_g.columns[6]: 'first', # Agente
                    'P_Min': 'min',
                    'P_Max': 'max',
                    'Rango_Dias': 'max'
                }).reset_index()
                
                df_g_table.columns = ["Embarque", "Agente", "Fecha Min Packeo", "Fecha Max Packeo", "Días de Rango"]
                st.dataframe(df_g_table.sort_values('Días de Rango', ascending=False),
                             column_config={"Días de Rango": st.column_config.NumberColumn("Rango", format="%d ⚡")},
                             use_container_width=True, hide_index=True)
                
                st.info("💡 Un rango elevado indica que la mercadería está tardando mucho en consolidarse para este embarque.")
            else:
                st.success("El agrupamiento de mercadería es eficiente para todos los embarques (Rango <= 7 días).")

        except Exception as e:
            st.error(f"Error en Solapa Alertas: {e}")

except Exception as e:
    st.error(f"Error crítico en el Tablero: {e}")
