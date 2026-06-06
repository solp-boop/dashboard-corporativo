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
    border: 1px solid rgba(255,255,255,0.08);
    box-shadow: 0 10px 35px rgba(0,0,0,0.35);
    transition: all 0.4s ease;
    margin-bottom: 25px;
    animation: fadeInUp 1s backwards;
}
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
    # ─────────────────────────────────────────────────────────────────────────────
    # --- POP-UP ALERTA DE MERCADO (aparece una vez por sesión al ingresar) ---
    # ─────────────────────────────────────────────────────────────────────────────
    if 'alerta_mercado_mostrada' not in st.session_state:
        st.session_state.alerta_mercado_mostrada = False
    @st.dialog("⚠️ ALERTA DE MERCADO — JUNIO 2026", width="large")
    def mostrar_alerta_mercado():
        st.markdown("""
        <div style='background: linear-gradient(135deg, rgba(255,170,0,0.1), rgba(255,75,75,0.05));
        border-radius: 16px; padding: 25px; border: 1px solid rgba(255,170,0,0.3);'>
        <p style='color:#ffaa00; font-weight:800; font-size:16px; letter-spacing:2px; margin-bottom:20px;'>
        📌 ACTUALIZACIÓN MERCADO MARÍTIMO — JUNIO 2026</p>
        <ul style='color:#cbd5e1; font-size:13px; line-height:2.2; padding-left:20px; margin:0 0 20px 0;'>
            <li><b style='color:#ff4b4b;'>Espacio en buques limitado</b> y mayor riesgo de rollovers</li>
            <li><b style='color:#ffaa00;'>Disponibilidad ajustada</b> de contenedores</li>
            <li><b style='color:#ffaa00;'>Warehouses y consolidadores</b> operando con alto volumen de carga</li>
            <li><b style='color:#ffaa00;'>Posibles demoras</b> en transbordos y puertos de origen</li>
            <li><b style='color:#ffaa00;'>Navieras aplicando incrementos tarifarios</b> (GRI/PSS)</li>
        </ul>
        <div style='background:rgba(255,75,75,0.08); border-radius:10px; padding:14px; border-left:4px solid #ff4b4b; margin-bottom:14px;'>
            <p style='color:#94a3b8; font-size:11px; letter-spacing:1px; margin:0 0 6px 0;'>IMPACTO ESPERADO</p>
            <p style='color:#ff4b4b; font-size:13px; font-weight:600; margin:0; line-height:1.7;'>
            Mayor presión operativa en origen · Posibles reprogramaciones de ETD · Costos de flete al alza durante junio
            </p>
        </div>
        <div style='background:rgba(255,170,0,0.08); border-radius:10px; padding:14px; border-left:4px solid #ffaa00;'>
            <p style='color:#94a3b8; font-size:11px; letter-spacing:1px; margin:0 0 5px 0;'>PRONÓSTICO DE FLETES — JUNIO 2026</p>
            <p style='color:#ffaa00; font-size:26px; font-weight:900; margin:0;'>USD 8.900</p>
            <p style='color:#94a3b8; font-size:11px; margin:4px 0 0 0;'>estimado por contenedor 40' HC · sujeto a naviera y disponibilidad</p>
        </div>
        </div>
        """, unsafe_allow_html=True)
        st.markdown("<br>", unsafe_allow_html=True)
        if st.button("✅ ENTENDIDO — INGRESAR AL DASHBOARD", use_container_width=True):
            st.session_state.alerta_mercado_mostrada = True
            st.rerun()
    if not st.session_state.alerta_mercado_mostrada:
        mostrar_alerta_mercado()
    # ─────────────────────────────────────────────────────────────────────────────
    # --- HEADER BIDCOM ---
    # ─────────────────────────────────────────────────────────────────────────────
    st.markdown("<div class='bidcom-header'><h1>BIDCOM</h1><div class='bidcom-subtitle'>Tablero Logística Internacional</div></div>", unsafe_allow_html=True)
    # ─────────────────────────────────────────────────────────────────────────────
    # --- BANNER ALERTA MERCADO (colapsable, siempre visible debajo del header) ---
    # ─────────────────────────────────────────────────────────────────────────────
    with st.expander("⚠️  ALERTA DE MERCADO ACTIVA — JUNIO 2026  |  Mercado marítimo bajo presión · USD 8.900/cntr estimado · Clic para ver detalle", expanded=False):
        st.markdown("""
        <div style='padding: 20px; background: rgba(255,170,0,0.05); border-radius: 12px;'>
        <div style='display:grid; grid-template-columns: repeat(3,1fr); gap:12px; margin-bottom:16px;'>
            <div style='text-align:center; padding:12px; background:rgba(255,75,75,0.08); border-radius:10px; border-top:3px solid #ff4b4b;'>
                <p style='color:#94a3b8; font-size:10px; letter-spacing:1px; margin:0 0 4px 0;'>PRONÓSTICO FLETE (40'HC)</p>
                <p style='color:#ff4b4b; font-size:20px; font-weight:900; margin:0;'>USD 8.900</p>
            </div>
            <div style='text-align:center; padding:12px; background:rgba(255,170,0,0.08); border-radius:10px; border-top:3px solid #ffaa00;'>
                <p style='color:#94a3b8; font-size:10px; letter-spacing:1px; margin:0 0 4px 0;'>DISPONIBILIDAD</p>
                <p style='color:#ffaa00; font-size:20px; font-weight:900; margin:0;'>AJUSTADA</p>
            </div>
            <div style='text-align:center; padding:12px; background:rgba(255,75,75,0.08); border-radius:10px; border-top:3px solid #ff4b4b;'>
                <p style='color:#94a3b8; font-size:10px; letter-spacing:1px; margin:0 0 4px 0;'>RIESGO ROLLOVER</p>
                <p style='color:#ff4b4b; font-size:20px; font-weight:900; margin:0;'>ALTO</p>
            </div>
        </div>
        <p style='color:#cbd5e1; font-size:13px; line-height:1.8; margin:0;'>
        🔴 <b style='color:#ff4b4b;'>Espacio en buques limitado</b> — mayor riesgo de rollovers &nbsp;|&nbsp;
        🟠 <b style='color:#ffaa00;'>Disponibilidad ajustada de contenedores</b> &nbsp;|&nbsp;
        🟠 <b style='color:#ffaa00;'>Warehouses y consolidadores</b> con alto volumen de carga &nbsp;|&nbsp;
        🟠 <b style='color:#ffaa00;'>Posibles demoras</b> en transbordos y puertos de origen &nbsp;|&nbsp;
        🟠 <b style='color:#ffaa00;'>Navieras aplicando GRI/PSS</b> — costos al alza &nbsp;|&nbsp;
        ⚡ <b style='color:#ff4b4b;'>Pronóstico flete: USD 8.900/cntr 40'HC</b>
        </p>
        </div>
        """, unsafe_allow_html=True)
    st.markdown("<br>", unsafe_allow_html=True)
    col_ref, _ = st.columns([1, 5])
    with col_ref:
        if st.button("🔄 Actualizar datos", key="btn_refresh", use_container_width=True):
            st.cache_data.clear()
            st.rerun()
    tabs = st.tabs(["ORIGEN", "MERCADERÍA EN PROCESO", "PERFORMANCE DE AGENTES Y ANALISTAS", "FLETES, GASTOS Y CERTIFICACIONES", "PROYECCIÓN SEMANAL ETD", "INDICADORES", "ALERTAS ESTRATÉGICAS", "ASK COMEX"])
 # --- SOLAPA 1: ORIGEN ---
    with tabs[0]:
        try:
            df['Fecha_Inst_DT'] = pd.to_datetime(df['Fecha de Instruccion'], dayfirst=True, errors='coerce')
            col_rank = df.columns[1]
            df['Rank_Num'] = df[col_rank].astype(str).str.replace('.', '', regex=False).str.replace(',', '.', regex=False)
            df['Rank_Num'] = pd.to_numeric(df['Rank_Num'], errors='coerce').fillna(999999)
            col_cp = df.columns[93]
            df['Tipo_Carga'] = df[col_cp].apply(lambda x: 'MONOPROVEEDOR' if str(x).upper() == 'SI' else 'CONSOLIDADO')

            # ── CLASIFICACIÓN TIPO DE NEGOCIO ──────────────────────────────
            def get_tipo_negocio(row):
                col_prov = df.columns[30]  # AE = Proveedor
                val_rep  = str(row['Repuestos']).strip().lower() if 'Repuestos' in df.columns else ''
                val_prov = str(row[col_prov]).strip().upper()    if len(df.columns) > 30 else ''
                if val_rep in ['', 'nan', 'none']:
                    if 'DJI' in val_prov:                       return 'DJI'
                    if 'IFLIGHT TECHNOLOGY CO LTD' in val_prov: return 'AGRAS'
                    return 'GADNIC'
                if 'repuesto' in val_rep:         return 'REPUESTOS'
                if 'muestra'  in val_rep:         return 'MUESTRAS'
                if 'sin planeamiento' in val_rep: return 'MARCAS'
                return 'GADNIC'
            df['Tipo_Repuesto'] = df.apply(get_tipo_negocio, axis=1) if 'Repuestos' in df.columns else 'GADNIC'

            df['Pais Destino'] = df['Pais Destino'].fillna('SIN DEFINIR').astype(str).str.strip()
            df['Repuestos'] = df['Repuestos'].fillna('').astype(str).str.strip()
            cond_prioridad = (df['Pais Destino'].str.upper() == 'ARGENTINA') & (df['Tipo_Repuesto'] == 'GADNIC')
            cond_instruido = df['Fecha_Inst_DT'].notna() & ~(df['Fecha de Instruccion'].astype(str).str.upper().str.contains("SIN INSTRUCCION", na=False))
            cond_pendiente = ~cond_instruido
            cond_urgente = cond_pendiente & (df['Fecha_Prior_DT'] < hoy)
            cond_pd_futura = cond_pendiente & (df['Fecha_Prior_DT'] >= hoy)
            cond_acc_mono = cond_pd_futura & (df['Tipo_Carga'] == 'MONOPROVEEDOR') & (df['Fecha_Prior_DT'] <= hoy + timedelta(days=25))
            cond_acc_consol = cond_pd_futura & (df['Tipo_Carga'] == 'CONSOLIDADO') & (df['Fecha_Prior_DT'] <= hoy + timedelta(days=10))
            cond_accionar = cond_acc_mono | cond_acc_consol
            cond_futura = cond_pendiente & (~cond_urgente) & (~cond_accionar)
            df_inst = df[cond_instruido & cond_prioridad].sort_values(by='Rank_Num').copy()
            cond_prov_no_prior = (
                df['Proveedor'].astype(str).str.upper().str.contains('DJI', na=False) |
                (df['Proveedor'].astype(str).str.strip().str.upper() == 'IFLIGHT TECHNOLOGY CO LTD')
            )
            cond_venc_prior = (
                cond_urgente &
                (df['Pais Destino'].str.upper() == 'ARGENTINA') &
                (df['Tipo_Repuesto'] == 'GADNIC') &
                ~cond_prov_no_prior
            )
            cond_venc_sinprior = cond_urgente & ~cond_venc_prior
            df_urgente_prior = df[cond_venc_prior].sort_values(by='Rank_Num').copy()
            df_urgente_sinprior = df[cond_venc_sinprior].sort_values(by=['Fecha_Prior_DT', 'Rank_Num']).copy()
            df_urgente = df_urgente_prior
            df_accionar = df[cond_accionar & cond_prioridad].sort_values(by='Rank_Num').copy()
            df_futura = df[cond_futura & cond_prioridad].sort_values(by='Rank_Num').copy()
            m3_inst = df_inst['M3 Total'].sum()
            m3_urgente = df_urgente_prior['M3 Total'].sum() + df_urgente_sinprior['M3 Total'].sum()
            m3_accionar = df_accionar['M3 Total'].sum()
            m3_futura = df_futura['M3 Total'].sum()
            m3_pend_total = m3_urgente + m3_accionar + m3_futura
            p_inst_val = int(round(m3_inst / m3_totales_global * 100)) if m3_totales_global > 0 else 0
            p_pend_val = 100 - p_inst_val
            fob_total_global = df['Fob total Origen'].sum()
            st.markdown("<br>", unsafe_allow_html=True)
            o1, o2, o3, o4 = st.columns(4)
            with o1: st.markdown(f"<div class='metric-container'><p>CANTIDAD DE SO</p><p>{int(cant_so_global)}</p></div>", unsafe_allow_html=True)
            with o2: st.markdown(f"<div class='metric-container'><p>VOLUMEN TOTAL (M3)</p><p>{int(round(m3_totales_global)):,}</p></div>", unsafe_allow_html=True)
            with o3: st.markdown(f"<div class='metric-container'><p>PROVEEDORES</p><p>{int(cant_proveedores_global)}</p></div>", unsafe_allow_html=True)
            with o4: st.markdown(f"<div class='metric-container'><p>FOB TOTAL (USD)</p><p>${int(round(fob_total_global)):,}</p></div>", unsafe_allow_html=True)
            st.markdown("<hr class='glow-divider'>", unsafe_allow_html=True)
            st.markdown("<div style='text-align:center; padding: 20px; background: rgba(0, 168, 255, 0.05); border-radius: 20px; margin-bottom: 30px;'><h2 style='color:#00a8ff; font-weight:800; letter-spacing:5px; margin:0;'>CONTROL DE STATUS DE MERCADERÍA</h2></div>", unsafe_allow_html=True)
            s1, s2 = st.columns([1.2, 1])
            filtro_actual = st.session_state.get('f')
            with s1:
                # ── CALCULAR % POR TIPO DE NEGOCIO ─────────────────────────
                _tipos_orden  = ['GADNIC', 'REPUESTOS', 'MUESTRAS', 'MARCAS', 'DJI', 'AGRAS']
                _colores_tipo = {
                    'GADNIC'   : '#00ff88',
                    'REPUESTOS': '#00a8ff',
                    'MUESTRAS' : '#ffaa00',
                    'MARCAS'   : '#a855f7',
                    'DJI'      : '#06b6d4',
                    'AGRAS'    : '#f97316',
                }
                _total_so_inst = df_inst['SO'].nunique()
                _filas_tipo = ''
                for _t in _tipos_orden:
                    _n   = df_inst[df_inst['Tipo_Repuesto'] == _t]['SO'].nunique()
                    if _n == 0: continue
                    _pct = round(_n / _total_so_inst * 100) if _total_so_inst > 0 else 0
                    _c   = _colores_tipo.get(_t, '#94a3b8')
                    _filas_tipo += (
                        f"<div style='margin-bottom:8px;'>"
                        f"<div style='display:flex;justify-content:space-between;align-items:center;margin-bottom:3px;'>"
                        f"<p style='color:{_c};font-size:12px;font-weight:700;margin:0;'>{_t}</p>"
                        f"<p style='color:{_c};font-size:15px;font-weight:900;margin:0;'>{_pct}%"
                        f"<span style='color:#475569;font-size:11px;font-weight:400;margin-left:6px;'>({_n} SO)</span></p>"
                        f"</div>"
                        f"<div style='height:4px;background:rgba(255,255,255,0.06);border-radius:2px;'>"
                        f"<div style='height:4px;width:{_pct}%;background:{_c};border-radius:2px;'></div>"
                        f"</div></div>"
                    )
                st.markdown(
                    f"<div class='custom-card' style='border-top:5px solid #00ff88;background:rgba(0,255,136,0.02);'>"
                    f"<div style='display:flex;justify-content:space-between;align-items:center;margin-bottom:25px;'>"
                    f"<p class='custom-card-title' style='color:#00ff88;font-size:18px;'>MERCANDAR\u00cdA INSTRUIDA</p>"
                    f"<p style='color:#00ff88;font-weight:900;font-size:32px;margin:0;'>{p_inst_val}%"
                    f"<span style='font-size:14px;color:#94a3b8;font-weight:400;'> M3</span></p>"
                    f"</div>"
                    f"<div class='grid-2'>"
                    f"<div><p class='minicard-title'>CANTIDAD SO</p><p class='minicard-value' style='color:#00ff88;'>{df_inst['SO'].nunique()}</p></div>"
                    f"<div><p class='minicard-title'>VOLUMEN TOTAL</p><p class='minicard-value'>{int(round(m3_inst)):,} M3</p></div>"
                    f"</div>"
                    f"<hr style='border:none;border-top:1px solid rgba(255,255,255,0.08);margin:20px 0;'>"
                    f"<div class='grid-2'>"
                    f"<div>"
                    f"<p class='minicard-title' style='color:#00a8ff;'>ESTRUCTURA DE CARGA</p>"
                    f"<p style='font-size:12px;margin:5px 0;'>MONOPROVEEDOR: <b>{df_inst[df_inst['Tipo_Carga']=='MONOPROVEEDOR']['SO'].nunique()} SO</b>"
                    f" ({int(round(df_inst[df_inst['Tipo_Carga']=='MONOPROVEEDOR']['M3 Total'].sum()))} m3)</p>"
                    f"<p style='font-size:12px;margin:5px 0;'>CONSOLIDADOS: <b>{df_inst[df_inst['Tipo_Carga']=='CONSOLIDADO']['SO'].nunique()} SO</b>"
                    f" ({int(round(df_inst[df_inst['Tipo_Carga']=='CONSOLIDADO']['M3 Total'].sum()))} m3)</p>"
                    f"</div>"
                    f"<div>"
                    f"<p class='minicard-title' style='color:#ffaa00;'>TIPO DE NEGOCIO</p>"
                    f"{_filas_tipo}"
                    f"</div>"
                    f"</div>"
                    f"</div>",
                    unsafe_allow_html=True
                )
                if st.button("VER DETALLE INSTRUIDO", key="btn_inst_new", use_container_width=True):
                    st.session_state.f = 'inst' if filtro_actual != 'inst' else None
                    st.rerun()
            with s2:
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
                if st.button(f"🔴 NIVEL 1A: VENCIDA PRIORITARIA (ARG·GADNIC) - {int(round(df_urgente_prior['M3 Total'].sum()))} M3", key="btn_urg_new", use_container_width=True):
                    st.session_state.f = 'venc' if filtro_actual != 'venc' else None
                    st.rerun()
                if st.button(f"🟥 NIVEL 1B: VENCIDA SIN PRIORIDAD - {int(round(df_urgente_sinprior['M3 Total'].sum()))} M3", key="btn_urg_sp_new", use_container_width=True):
                    st.session_state.f = 'venc_sp' if filtro_actual != 'venc_sp' else None
                    st.rerun()
                if st.button(f"🟠 NIVEL 2: ACCIONAR (PRÓXIMA) - {int(round(df_accionar['M3 Total'].sum()))} M3", key="btn_acc_new", use_container_width=True):
                    st.session_state.f = 'px25' if filtro_actual != 'px25' else None
                    st.rerun()
                if st.button(f"🔵 NIVEL 3: PROGRAMADA (FUTURA) - {int(round(df_futura['M3 Total'].sum()))} M3", key="btn_rest_new", use_container_width=True):
                    st.session_state.f = 'rest' if filtro_actual != 'rest' else None
                    st.rerun()

            f = st.session_state.get('f')
            if f:
                st.markdown("<br>", unsafe_allow_html=True)
                if f in ["inst", "venc", "venc_sp", "px25", "rest"]:
                    if f == "inst": titulo, dff, color = "MERCADERIA INSTRUIDA (PRIORIDAD)", df_inst, "#00ff88"
                    elif f == "venc": titulo, dff, color = "VENCIDA CON PRIORIDAD (ARG · SIN REPUESTO)", df_urgente_prior, "#ff4b4b"
                    elif f == "venc_sp": titulo, dff, color = "VENCIDA SIN PRIORIDAD", df_urgente_sinprior, "#ff8c42"
                    elif f == "px25": titulo, dff, color = "PROXIMA A INSTRUIR (ACCIÓN)", df_accionar, "#ffaa00"
                    elif f == "rest": titulo, dff, color = "MERCADERIA PROGRAMADA (FUTURA)", df_futura, "#94a3b8"
                    cant_so_f = dff['SO'].nunique()
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
                    col_puerto = df.columns[41]
                    cols_to_show = ['SO', col_rank, 'Proveedor', col_puerto, 'Pais Destino', 'M3 Total', df.columns[99], 'Fecha de Instruccion']
                    if 'Repuestos' in df.columns:
                        cols_to_show.insert(4, 'Repuestos')
                    st.dataframe(dff[cols_to_show], use_container_width=True)

            st.markdown("<hr class='glow-divider'>", unsafe_allow_html=True)
            st.markdown("<p style='color:#00a8ff; font-weight:700; letter-spacing:4px; font-size:18px; margin-bottom:25px; text-align:center;'>DISTRIBUCIÓN GEOGRÁFICA</p>", unsafe_allow_html=True)
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
            col_puerto = df.columns[41]
            p_df = df.groupby(col_puerto).agg({'M3 Total': 'sum'}).reset_index().sort_values(by='M3 Total')
            total_m3_puertos = p_df['M3 Total'].sum()
            p_df['Pct'] = (p_df['M3 Total'] / total_m3_puertos * 100).round(1) if total_m3_puertos > 0 else 0
            p_df['label'] = p_df.apply(lambda r: f"{int(round(r['M3 Total'])):,} M3  ({r['Pct']}%)", axis=1)
            st.markdown(f"<p style='color:#00a8ff; font-weight:700; font-size:18px; text-align:center; letter-spacing:4px; margin-bottom:20px;'>VOLUMEN POR PUERTO DE SALIDA <span style='font-size:14px; font-weight:400; color:#f8fafc; text-shadow:none;'>| TOTAL: {int(round(total_m3_puertos)):,} M3</span></p>", unsafe_allow_html=True)
            fig_p = px.bar(p_df, y=col_puerto, x='M3 Total', orientation='h', text='label', color_discrete_sequence=['#00a8ff'])
            fig_p.update_traces(textposition='outside', cliponaxis=False, textfont_size=14, textfont_color="#f8fafc", marker=dict(cornerradius=5))
            fig_p.update_layout(xaxis_visible=True, xaxis_title="Total M3", yaxis_title="Puerto", height=500, margin=dict(l=150, r=160, t=20, b=20), font=dict(size=14, family='Outfit, sans-serif'), paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)')
            fig_p.update_xaxes(showgrid=True, gridwidth=1, gridcolor='rgba(255,255,255,0.1)')
            st.plotly_chart(fig_p, use_container_width=True)
            ga, gb = st.columns(2)
            with ga:
                etd_all = df.groupby('Mes_ETD_Full').agg({'M3 Total': 'sum'}).reset_index()
                etd_vencido = etd_all[etd_all['Mes_ETD_Full'] == 'PASADO/REALIZADO']
                etd_p = etd_all[~etd_all['Mes_ETD_Full'].isin(['PASADO/REALIZADO', 'SIN FECHA'])]
                if not etd_vencido.empty and etd_vencido['M3 Total'].sum() > 0:
                    m3_venc_etd = int(round(etd_vencido['M3 Total'].sum()))
                    st.markdown(f"<div style='background:rgba(255,75,75,0.08); border-radius:8px; padding:8px 14px; border-left:3px solid #ff4b4b; margin-bottom:10px;'><p style='color:#ff4b4b; font-size:12px; font-weight:700; margin:0;'>VENCIDO/REALIZADO: {m3_venc_etd:,} M3 en meses anteriores (no se muestran en el gráfico)</p></div>", unsafe_allow_html=True)
                st.markdown(f"<p style='color:#00ff88; font-weight:700; font-size:16px; text-align:center; letter-spacing:2px; margin-bottom:20px;'>PROYECCIÓN MENSUAL ETD<br><span style='font-size:14px; font-weight:400; color:#f8fafc; text-shadow:none;'>TOTAL FUTURO: {int(round(etd_p['M3 Total'].sum())):,} M3</span></p>", unsafe_allow_html=True)
                fig_e = px.bar(etd_p, x='Mes_ETD_Full', y='M3 Total', text_auto=',.0f', color_discrete_sequence=['#00ff88'])
                fig_e.update_traces(textfont_size=16, textposition='outside', textfont_color="#f8fafc", marker=dict(cornerradius=5))
                fig_e.update_layout(yaxis_visible=True, yaxis_title="Total M3", xaxis_title="Mes ETD", height=450, margin=dict(l=20, r=20, t=20, b=20), font=dict(size=14, family='Outfit, sans-serif'), paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)')
                fig_e.update_yaxes(showgrid=True, gridwidth=1, gridcolor='rgba(255,255,255,0.1)')
                st.plotly_chart(fig_e, use_container_width=True)
            with gb:
                eta_all = df.groupby('Mes_ETA_Full', observed=True).agg({'M3 Total': 'sum'}).reset_index()
                eta_vencido = eta_all[eta_all['Mes_ETA_Full'] == 'PASADO/REALIZADO']
                eta_p = eta_all[~eta_all['Mes_ETA_Full'].isin(['PASADO/REALIZADO', 'SIN FECHA'])]
                if not eta_vencido.empty and eta_vencido['M3 Total'].sum() > 0:
                    m3_venc_eta = int(round(eta_vencido['M3 Total'].sum()))
                    st.markdown(f"<div style='background:rgba(255,75,75,0.08); border-radius:8px; padding:8px 14px; border-left:3px solid #ff4b4b; margin-bottom:10px;'><p style='color:#ff4b4b; font-size:12px; font-weight:700; margin:0;'>VENCIDO/REALIZADO: {m3_venc_eta:,} M3 en meses anteriores (no se muestran en el gráfico)</p></div>", unsafe_allow_html=True)
                st.markdown(f"<p style='color:#ff4b4b; font-weight:700; font-size:16px; text-align:center; letter-spacing:2px; margin-bottom:20px;'>PROYECCIÓN MENSUAL ETA<br><span style='font-size:14px; font-weight:400; color:#f8fafc; text-shadow:none;'>TOTAL FUTURO: {int(round(eta_p['M3 Total'].sum())):,} M3</span></p>", unsafe_allow_html=True)
                fig_a = px.bar(eta_p, x='Mes_ETA_Full', y='M3 Total', text_auto=',.0f', color_discrete_sequence=['#ff4b4b'])
                fig_a.update_traces(textfont_size=16, textposition='outside', textfont_color="#f8fafc", marker=dict(cornerradius=5))
                fig_a.update_layout(yaxis_visible=True, yaxis_title="Total M3", xaxis_title="Mes ETA", height=450, margin=dict(l=20, r=20, t=20, b=20), font=dict(size=14, family='Outfit, sans-serif'), paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)')
                fig_a.update_yaxes(showgrid=True, gridwidth=1, gridcolor='rgba(255,255,255,0.1)')
                st.plotly_chart(fig_a, use_container_width=True)
            st.markdown("<hr class='white-divider'>", unsafe_allow_html=True)
            gc, gd = st.columns(2)
            with gc:
                col_mod_opciones = [c for c in df.columns if 'MODALIDAD' in str(c).upper() and 'COSTEO' in str(c).upper()]
                col_mod = col_mod_opciones[0] if col_mod_opciones else 'Modalidad de Costeo Reposicion'
                if col_mod in df.columns:
                    mask_arg   = df['Pais Destino'].astype(str).str.strip().str.upper() == 'ARGENTINA'
                    mask_barco = (
                        df[col_mod].astype(str).str.upper().str.startswith("BARCO") |
                        df[col_mod].astype(str).str.upper().str.contains("COSTO HIBRIDO PUERTO ZFLP", na=False)
                    )
                    mask_cntr = mask_arg & mask_barco
                    df_c_etd_all = df[mask_cntr].groupby('Mes_ETD_Full').agg({'M3 Total': 'sum'}).reset_index()
                    df_c_etd_venc = df_c_etd_all[df_c_etd_all['Mes_ETD_Full'] == 'PASADO/REALIZADO']
                    df_c_etd = df_c_etd_all[~df_c_etd_all['Mes_ETD_Full'].isin(['PASADO/REALIZADO', 'SIN FECHA'])]
                    df_c_etd['Contenedores'] = (df_c_etd['M3 Total'] / 60).round().astype(int)
                    tot_cont_etd = df_c_etd['Contenedores'].sum()
                    if not df_c_etd_venc.empty and df_c_etd_venc['M3 Total'].sum() > 0:
                        cont_venc_etd = int(round(df_c_etd_venc['M3 Total'].sum() / 60))
                        st.markdown(f"<div style='background:rgba(255,75,75,0.08); border-radius:8px; padding:8px 14px; border-left:3px solid #ff4b4b; margin-bottom:10px;'><p style='color:#ff4b4b; font-size:12px; font-weight:700; margin:0;'>VENCIDO: ~{cont_venc_etd} CNTR en meses anteriores (no se muestran)</p></div>", unsafe_allow_html=True)
                    st.markdown(f"<p style='color:#ffaa00; font-weight:700; font-size:16px; text-align:center; letter-spacing:2px; margin-bottom:20px;'>PROYECCIÓN CONTENEDORES (ETD)<br><span style='font-size:14px; font-weight:400; color:#f8fafc; text-shadow:none;'>TOTAL FUTURO: {int(tot_cont_etd):,} CNTR</span></p>", unsafe_allow_html=True)
                    fig_cetd = px.bar(df_c_etd, x='Mes_ETD_Full', y='Contenedores', text_auto=',.0f', color_discrete_sequence=['#ffaa00'])
                    fig_cetd.update_traces(textfont_size=16, textposition='outside', textfont_color="#f8fafc", marker=dict(cornerradius=5))
                    fig_cetd.update_layout(yaxis_visible=True, yaxis_title="Cant. Cont", xaxis_title="Mes ETD", height=450, margin=dict(l=20, r=20, t=20, b=20), font=dict(size=14, family='Outfit, sans-serif'), paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)')
                    fig_cetd.update_yaxes(showgrid=True, gridwidth=1, gridcolor='rgba(255,255,255,0.1)')
                    st.plotly_chart(fig_cetd, use_container_width=True)
                else:
                    st.warning(f"La columna requerida '{col_mod}' no se encuentra para calcular la proyección.")
            with gd:
                if col_mod in df.columns:
                    mask_arg   = df['Pais Destino'].astype(str).str.strip().str.upper() == 'ARGENTINA'
                    mask_barco = (
                        df[col_mod].astype(str).str.upper().str.startswith("BARCO") |
                        df[col_mod].astype(str).str.upper().str.contains("COSTO HIBRIDO PUERTO ZFLP", na=False)
                    )
                    mask_cntr = mask_arg & mask_barco
                    df_c_eta_all = df[mask_cntr].groupby('Mes_ETA_Full', observed=True).agg({'M3 Total': 'sum'}).reset_index()
                    df_c_eta_venc = df_c_eta_all[df_c_eta_all['Mes_ETA_Full'] == 'PASADO/REALIZADO']
                    df_c_eta = df_c_eta_all[~df_c_eta_all['Mes_ETA_Full'].isin(['PASADO/REALIZADO', 'SIN FECHA'])]
                    df_c_eta['Contenedores'] = (df_c_eta['M3 Total'] / 60).round().astype(int)
                    tot_cont_eta = df_c_eta['Contenedores'].sum()
                    if not df_c_eta_venc.empty and df_c_eta_venc['M3 Total'].sum() > 0:
                        cont_venc_eta = int(round(df_c_eta_venc['M3 Total'].sum() / 60))
                        st.markdown(f"<div style='background:rgba(255,75,75,0.08); border-radius:8px; padding:8px 14px; border-left:3px solid #ff4b4b; margin-bottom:10px;'><p style='color:#ff4b4b; font-size:12px; font-weight:700; margin:0;'>VENCIDO: ~{cont_venc_eta} CNTR en meses anteriores (no se muestran)</p></div>", unsafe_allow_html=True)
                    st.markdown(f"<p style='color:#ffaa00; font-weight:700; font-size:16px; text-align:center; letter-spacing:2px; margin-bottom:20px;'>PROYECCIÓN CONTENEDORES (ETA)<br><span style='font-size:14px; font-weight:400; color:#f8fafc; text-shadow:none;'>TOTAL FUTURO: {int(tot_cont_eta):,} CNTR</span></p>", unsafe_allow_html=True)
                    fig_ceta = px.bar(df_c_eta, x='Mes_ETA_Full', y='Contenedores', text_auto=',.0f', color_discrete_sequence=['#ffaa00'])
                    fig_ceta.update_traces(textfont_size=16, textposition='outside', textfont_color="#f8fafc", marker=dict(cornerradius=5))
                    fig_ceta.update_layout(yaxis_visible=True, yaxis_title="Cant. Cont", xaxis_title="Mes ETA", height=450, margin=dict(l=20, r=20, t=20, b=20), font=dict(size=14, family='Outfit, sans-serif'), paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)')
                    fig_ceta.update_yaxes(showgrid=True, gridwidth=1, gridcolor='rgba(255,255,255,0.1)')
                    st.plotly_chart(fig_ceta, use_container_width=True)
        except Exception as e:
            st.error(f"Error en Solapa Origen: {e}")
# =========================================================================
    # --- SOLAPA 2: COORDINACIÓN ACTIVA ---
    # =========================================================================
    with tabs[1]:
        try:
            url_reserva = f"{base_url}/export?format=csv&gid=276804813&nocache={time.time()}"

            @st.cache_data(ttl=60)
            def load_reserva_data(url):
                return pd.read_csv(url, engine='python', on_bad_lines='skip')

            try:
                df_res = load_reserva_data(url_reserva)
            except Exception:
                df_res = pd.read_csv(url_reserva)
            df_res.columns = df_res.columns.str.strip()

            df_g = df_res[df_res.iloc[:, 7].astype(str).apply(lambda x: len(str(x)) > 4)].copy()
            df_g['DT_Inst']      = pd.to_datetime(df_g.iloc[:, 7], dayfirst=True, errors='coerce')
            df_g['ETD_Status_K'] = df_g.iloc[:, 10].astype(str).str.upper().str.strip()
            df_g['Espera']       = (pd.to_datetime('today') - df_g['DT_Inst']).dt.days
            df_g['DT_ETD']       = pd.to_datetime(df_g.iloc[:, 12], dayfirst=True, errors='coerce')

            df_inst_s2 = df[cond_instruido].copy()

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

            m3_total_clean  = df_inst_s2['M3 Total'].apply(safe_float_f).sum()
            fob_total_clean = df_inst_s2['Fob total Origen'].apply(safe_float_f).sum()

            def clasificar_transp_res(x):
                x = str(x).upper().strip()
                if any(m in x for m in ["40 HQ", "40 ST", "40 NOR", "20 ST", "40NOR"]): return "MARITIMO"
                if any(a in x for a in ["AVION", "COURIER", "COURRIER"]): return "AEREO"
                return "OTROS"

            df_g['Transporte'] = df_g.iloc[:, 5].apply(clasificar_transp_res)
            df_mar = df_g[df_g['Transporte'] == "MARITIMO"].copy()
            df_mar.iloc[:, 1] = pd.to_numeric(df_mar.iloc[:, 1], errors='coerce').fillna(0)

            def clean_val_mar(value):
                if pd.isna(value): return 0
                s = str(value).replace('.', '').replace(',', '.')
                num = ''.join(c for c in s if c.isdigit() or c == '.')
                return pd.to_numeric(num, errors='coerce') if num else 0

            df_mar.iloc[:, 21] = df_mar.iloc[:, 21].apply(clean_val_mar).fillna(0)

            # --- Métricas marítimas ---
            total_mar  = df_mar.iloc[:, 0].nunique()
            ok_mar     = df_mar[df_mar['ETD_Status_K'] == "OK"].iloc[:, 0].nunique()
            pend_mar   = total_mar - ok_mar
            m3_mar     = df_mar.iloc[:, 23].apply(safe_float_f).sum()
            cntr_mar   = df_mar.iloc[:, 1].apply(safe_float_f).sum()
            pct_ok_mar = round(ok_mar / total_mar * 100) if total_mar > 0 else 0

            # Destinos Argentina vs otros — embarques de df_mar (Reservas), col 3 = destino
            mask_arg_mar  = df_mar.iloc[:, 3].astype(str).str.strip().str.upper() == 'ARGENTINA'
            emb_arg       = df_mar[mask_arg_mar].iloc[:, 0].nunique()
            emb_otros     = df_mar[~mask_arg_mar].iloc[:, 0].nunique()
            total_emb_dest = emb_arg + emb_otros
            pct_arg       = round(emb_arg / total_emb_dest * 100) if total_emb_dest > 0 else 0
            pct_otros     = 100 - pct_arg

            # Estructura de carga
            msk_mono  = df_mar.iloc[:, 32].astype(str).str.strip().str.upper().isin(['SI', 'SÍ', 'S', 'MONOPROVEEDOR'])
            df_mono_m = df_mar[msk_mono]; df_cons_m = df_mar[~msk_mono]
            tot_mc    = len(df_mono_m) + len(df_cons_m)
            pct_mono_m = round(len(df_mono_m) / tot_mc * 100) if tot_mc > 0 else 0
            pct_cons_m = 100 - pct_mono_m

            # Booking
            msk_adv  = df_mar.iloc[:, 8].astype(str).str.strip() == "Booked in Advance"
            pct_adv  = round(msk_adv.sum() / total_mar * 100) if total_mar > 0 else 0
            pct_spot = 100 - pct_adv

            # Medianas de consolidación
            # Buscamos la columna por nombre para evitar desplazamiento de índices
            # La columna es "Tiempo total consolidacion" → AC en Reservas = col 28 del df_res original
            # Usamos df_res original (antes de agregar columnas calculadas) con col nombre
            _col_cons_name = df_res.columns[28]  # AC = Tiempo total consolidacion
            # Agregamos la columna al df_mar alineando por índice con df_g
            df_mar['_dias_cons'] = df_res.loc[df_mar.index, _col_cons_name].apply(safe_float_f) if _col_cons_name in df_res.columns else pd.Series(0.0, index=df_mar.index)

            def safe_median(series):
                s = series[series > 0]
                return s.median() if not s.empty else 0

            # Máscaras ya definidas sobre df_mar — reutilizamos sus índices directamente
            dias_consol_raw = df_mar['_dias_cons']
            dias_mono_raw   = df_mar.loc[msk_mono, '_dias_cons']
            dias_cons_raw   = df_mar.loc[~msk_mono, '_dias_cons']
            dias_adv_raw    = df_mar.loc[msk_adv, '_dias_cons']
            dias_spot_raw   = df_mar.loc[~msk_adv, '_dias_cons']
            mediana_mono    = safe_median(dias_mono_raw)
            mediana_cons    = safe_median(dias_cons_raw)
            mediana_adv     = safe_median(dias_adv_raw)
            mediana_spot    = safe_median(dias_spot_raw)

            # ETD esta semana (lunes a domingo)
            lunes_semana   = hoy - timedelta(days=hoy.weekday())
            domingo_semana = lunes_semana + timedelta(days=6)
            df_mar_ok      = df_mar[df_mar['ETD_Status_K'] == "OK"].copy()
            mask_semana    = (
                df_mar_ok['DT_ETD'].notna() &
                (df_mar_ok['DT_ETD'] >= pd.Timestamp(lunes_semana)) &
                (df_mar_ok['DT_ETD'] <= pd.Timestamp(domingo_semana))
            )
            df_etd_semana  = df_mar_ok[mask_semana].copy()
            cant_etd_sem   = df_etd_semana.iloc[:, 0].nunique()
            cntr_etd_sem   = df_etd_semana.iloc[:, 1].sum()
            m3_etd_sem     = df_etd_semana.iloc[:, 23].apply(safe_float_f).sum()

            msk_adv_sem  = df_etd_semana.iloc[:, 8].astype(str).str.strip() == "Booked in Advance"
            df_adv_sem   = df_etd_semana[msk_adv_sem]
            df_spot_sem  = df_etd_semana[~msk_adv_sem]

            med_adv_sem  = safe_median(df_adv_sem['_dias_cons']) if not df_adv_sem.empty else 0
            med_spot_sem = safe_median(df_spot_sem['_dias_cons']) if not df_spot_sem.empty else 0

            # Semaforo ETD
            if pct_ok_mar >= 70:
                semaforo_color = "#00ff88"; semaforo_label = "SITUACION CONTROLADA"
            elif pct_ok_mar >= 40:
                semaforo_color = "#ffaa00"; semaforo_label = "ATENCION REQUERIDA"
            else:
                semaforo_color = "#ff4b4b"; semaforo_label = "ALERTA OPERATIVA"

            def color_dias(d, sla):
                if d <= sla: return "#00ff88"
                elif d <= sla * 1.4: return "#ffaa00"
                else: return "#ff4b4b"

            # Alturas fijas para armonizar
            H_ROW1  = "300px"   # fila 1: embarques + ETD
            H_ROW2  = "210px"   # fila 2: estructura + booking + consolidacion
            H_ROW3  = "200px"   # fila ETD semana
            H_AE    = "300px"   # aereos fila 1

            # ═══════════════════════════════════════════════════════
            # HEADER GENERAL
            # ═══════════════════════════════════════════════════════
            st.markdown("<br>", unsafe_allow_html=True)
            st.markdown("""
<div style='text-align:center; padding:24px 20px 16px 20px; margin-bottom:4px;'>
<p style='color:#475569; font-size:11px; letter-spacing:6px; margin:0 0 6px 0; text-transform:uppercase;'>Panel Ejecutivo · Tiempo Real</p>
<h2 style='color:#f8fafc; font-weight:900; letter-spacing:8px; margin:0; font-size:28px;'>COORDINACION ACTIVA</h2>
</div>""", unsafe_allow_html=True)

            k1, k2, k3, k4 = st.columns(4)
            with k1: st.markdown(f"<div class='metric-container'><p>SO EN PROCESO</p><p>{int(df_inst_s2['SO'].nunique())}</p></div>", unsafe_allow_html=True)
            with k2: st.markdown(f"<div class='metric-container'><p>VOLUMEN TOTAL</p><p>{int(round(m3_total_clean)):,} <span style='font-size:30px;'>M3</span></p></div>", unsafe_allow_html=True)
            with k3: st.markdown(f"<div class='metric-container'><p>PROVEEDORES</p><p>{int(df_inst_s2['Proveedor'].nunique())}</p></div>", unsafe_allow_html=True)
            with k4: st.markdown(f"<div class='metric-container'><p>FOB EN PROCESO</p><p><span style='font-size:38px;'>USD {round(fob_total_clean/1_000_000, 1)}M</span></p></div>", unsafe_allow_html=True)

            # ═══════════════════════════════════════════════════════
            # BLOQUE MARITIMO
            # ═══════════════════════════════════════════════════════
            st.markdown("<br>", unsafe_allow_html=True)
            st.markdown("""
<div style='border-bottom:2px solid rgba(0,168,255,0.3); padding-bottom:10px; margin-bottom:28px;'>
<span style='color:#00a8ff; font-size:13px; font-weight:800; letter-spacing:5px; text-transform:uppercase;'>MARITIMO</span>
<span style='color:#475569; font-size:11px; letter-spacing:2px; margin-left:16px;'>RESERVAS ACTIVAS</span>
</div>""", unsafe_allow_html=True)

            # --- FILA 1: embarques + ETD (misma altura fija) ---
            col_big, col_sem = st.columns([1.2, 1])

            with col_big:
                st.markdown(f"""
<div style='background:linear-gradient(145deg, rgba(0,168,255,0.07), rgba(0,168,255,0.02));
border-radius:20px; border:1px solid rgba(0,168,255,0.15); padding:28px;
height:{H_ROW1}; box-sizing:border-box; display:flex; flex-direction:column; justify-content:space-between;'>
<div>
    <p style='color:#64748b; font-size:11px; letter-spacing:3px; margin:0 0 6px 0; text-transform:uppercase;'>Embarques bajo gestion</p>
    <p style='color:#f8fafc; font-size:88px; font-weight:900; margin:0; line-height:1; letter-spacing:-4px;'>{total_mar}</p>
</div>
<div style='display:flex; gap:28px; margin-top:12px;'>
    <div>
        <p style='color:#64748b; font-size:10px; letter-spacing:1px; margin:0 0 3px 0;'>CONTENEDORES</p>
        <p style='color:#00a8ff; font-size:22px; font-weight:800; margin:0;'>{int(cntr_mar)}</p>
    </div>
    <div>
        <p style='color:#64748b; font-size:10px; letter-spacing:1px; margin:0 0 3px 0;'>VOLUMEN</p>
        <p style='color:#00a8ff; font-size:22px; font-weight:800; margin:0;'>{int(round(m3_mar)):,} M3</p>
    </div>
</div>
<div style='border-top:1px solid rgba(255,255,255,0.07); padding-top:14px; display:flex; gap:24px;'>
    <div>
        <p style='color:#64748b; font-size:10px; letter-spacing:1px; margin:0 0 3px 0;'>ARGENTINA</p>
        <p style='color:#f8fafc; font-size:17px; font-weight:800; margin:0;'>{pct_arg}% <span style='font-size:12px; color:#475569; font-weight:400;'>({emb_arg} emb)</span></p>
    </div>
    <div>
        <p style='color:#64748b; font-size:10px; letter-spacing:1px; margin:0 0 3px 0;'>OTROS DESTINOS</p>
        <p style='color:#f8fafc; font-size:17px; font-weight:800; margin:0;'>{pct_otros}% <span style='font-size:12px; color:#475569; font-weight:400;'>({emb_otros} emb)</span></p>
    </div>
</div>
</div>""", unsafe_allow_html=True)

            with col_sem:
                st.markdown(f"""
<div style='background:rgba(255,255,255,0.02); border-radius:20px;
border:1px solid rgba(255,255,255,0.07); padding:28px;
height:{H_ROW1}; box-sizing:border-box; display:flex; flex-direction:column; justify-content:space-between;'>
<div>
    <p style='color:#64748b; font-size:11px; letter-spacing:3px; margin:0 0 14px 0; text-transform:uppercase;'>Estado ETD</p>
    <p style='color:{semaforo_color}; font-size:72px; font-weight:900; margin:0; line-height:1;'>{pct_ok_mar}%</p>
    <p style='color:{semaforo_color}; font-size:13px; font-weight:800; letter-spacing:3px; margin:10px 0 4px 0;'>{semaforo_label}</p>
    <p style='color:#475569; font-size:11px; margin:0;'>{ok_mar} confirmados · {pend_mar} pendientes de booking</p>
</div>
<div>
    <div style='height:6px; background:rgba(255,255,255,0.07); border-radius:3px; margin-bottom:8px;'>
        <div style='height:6px; width:{pct_ok_mar}%; background:{semaforo_color}; border-radius:3px;'></div>
    </div>
    <p style='color:#334155; font-size:10px; margin:0;'>{pct_ok_mar}% del total con ETD confirmado</p>
</div>
</div>""", unsafe_allow_html=True)

            st.markdown("<br>", unsafe_allow_html=True)

            # --- FILA 2: estructura + booking + consolidacion (misma altura fija) ---
            col_est, col_book, col_cons = st.columns(3)

            with col_est:
                st.markdown(f"""
<div style='background:rgba(255,255,255,0.03); border-radius:16px;
border:1px solid rgba(255,255,255,0.07); padding:24px;
height:{H_ROW2}; box-sizing:border-box; display:flex; flex-direction:column; justify-content:space-between;'>
<p style='color:#64748b; font-size:10px; letter-spacing:3px; margin:0; text-transform:uppercase;'>Estructura de carga</p>
<div>
    <div style='display:flex; justify-content:space-between; margin-bottom:5px;'>
        <p style='color:#00a8ff; font-size:12px; font-weight:700; margin:0;'>MONOPROVEEDOR</p>
        <p style='color:#00a8ff; font-size:20px; font-weight:900; margin:0;'>{pct_mono_m}%</p>
    </div>
    <div style='height:5px; background:rgba(255,255,255,0.06); border-radius:3px;'>
        <div style='height:5px; width:{pct_mono_m}%; background:#00a8ff; border-radius:3px;'></div>
    </div>
    <p style='color:#334155; font-size:11px; margin:4px 0 0 0;'>{len(df_mono_m)} embarques</p>
</div>
<div>
    <div style='display:flex; justify-content:space-between; margin-bottom:5px;'>
        <p style='color:#ffaa00; font-size:12px; font-weight:700; margin:0;'>CONSOLIDADO</p>
        <p style='color:#ffaa00; font-size:20px; font-weight:900; margin:0;'>{pct_cons_m}%</p>
    </div>
    <div style='height:5px; background:rgba(255,255,255,0.06); border-radius:3px;'>
        <div style='height:5px; width:{pct_cons_m}%; background:#ffaa00; border-radius:3px;'></div>
    </div>
    <p style='color:#334155; font-size:11px; margin:4px 0 0 0;'>{len(df_cons_m)} embarques</p>
</div>
</div>""", unsafe_allow_html=True)

            with col_book:
                st.markdown(f"""
<div style='background:rgba(255,255,255,0.03); border-radius:16px;
border:1px solid rgba(255,255,255,0.07); padding:24px;
height:{H_ROW2}; box-sizing:border-box; display:flex; flex-direction:column; justify-content:space-between;'>
<p style='color:#64748b; font-size:10px; letter-spacing:3px; margin:0; text-transform:uppercase;'>Modalidad de booking</p>
<div>
    <div style='display:flex; justify-content:space-between; margin-bottom:5px;'>
        <p style='color:#00ff88; font-size:12px; font-weight:700; margin:0;'>IN ADVANCE</p>
        <p style='color:#00ff88; font-size:20px; font-weight:900; margin:0;'>{pct_adv}%</p>
    </div>
    <div style='height:5px; background:rgba(255,255,255,0.06); border-radius:3px;'>
        <div style='height:5px; width:{pct_adv}%; background:#00ff88; border-radius:3px;'></div>
    </div>
    <p style='color:#334155; font-size:11px; margin:4px 0 0 0;'>Espacio negociado anticipado</p>
</div>
<div>
    <div style='display:flex; justify-content:space-between; margin-bottom:5px;'>
        <p style='color:#94a3b8; font-size:12px; font-weight:700; margin:0;'>SPOT</p>
        <p style='color:#94a3b8; font-size:20px; font-weight:900; margin:0;'>{pct_spot}%</p>
    </div>
    <div style='height:5px; background:rgba(255,255,255,0.06); border-radius:3px;'>
        <div style='height:5px; width:{pct_spot}%; background:#94a3b8; border-radius:3px;'></div>
    </div>
    <p style='color:#334155; font-size:11px; margin:4px 0 0 0;'>Mercado abierto</p>
</div>
</div>""", unsafe_allow_html=True)

            with col_cons:
                cm = color_dias(mediana_mono, 7)
                cc = color_dias(mediana_cons, 25)
                ca = color_dias(mediana_adv, 20)
                cs = color_dias(mediana_spot, 20)
                st.markdown(f"""
<div style='background:rgba(255,255,255,0.03); border-radius:16px;
border:1px solid rgba(255,255,255,0.07); padding:24px;
height:{H_ROW2}; box-sizing:border-box; display:flex; flex-direction:column; justify-content:space-between;'>
<p style='color:#64748b; font-size:10px; letter-spacing:3px; margin:0; text-transform:uppercase;'>Tiempo de consolidacion <span style='color:#334155; font-weight:400; letter-spacing:0; text-transform:none;'>(mediana)</span></p>
<div style='display:grid; grid-template-columns:1fr 1fr; gap:8px; flex:1; align-content:center;'>
    <div style='background:rgba(0,168,255,0.07); border-radius:10px; padding:10px; text-align:center; border:1px solid rgba(0,168,255,0.1);'>
        <p style='color:#64748b; font-size:9px; letter-spacing:1px; margin:0 0 3px 0;'>MONO</p>
        <p style='color:{cm}; font-size:26px; font-weight:900; margin:0; line-height:1;'>{int(round(mediana_mono))}d</p>
        <p style='color:#334155; font-size:9px; margin:3px 0 0 0;'>SLA: 7d</p>
    </div>
    <div style='background:rgba(255,170,0,0.07); border-radius:10px; padding:10px; text-align:center; border:1px solid rgba(255,170,0,0.1);'>
        <p style='color:#64748b; font-size:9px; letter-spacing:1px; margin:0 0 3px 0;'>CONSOLIDADO</p>
        <p style='color:{cc}; font-size:26px; font-weight:900; margin:0; line-height:1;'>{int(round(mediana_cons))}d</p>
        <p style='color:#334155; font-size:9px; margin:3px 0 0 0;'>SLA: 25d</p>
    </div>
    <div style='background:rgba(0,255,136,0.06); border-radius:10px; padding:10px; text-align:center; border:1px solid rgba(0,255,136,0.08);'>
        <p style='color:#64748b; font-size:9px; letter-spacing:1px; margin:0 0 3px 0;'>IN ADVANCE</p>
        <p style='color:{ca}; font-size:26px; font-weight:900; margin:0; line-height:1;'>{int(round(mediana_adv))}d</p>
        <p style='color:#334155; font-size:9px; margin:3px 0 0 0;'>ref: 20d</p>
    </div>
    <div style='background:rgba(148,163,184,0.06); border-radius:10px; padding:10px; text-align:center; border:1px solid rgba(148,163,184,0.08);'>
        <p style='color:#64748b; font-size:9px; letter-spacing:1px; margin:0 0 3px 0;'>SPOT</p>
        <p style='color:{cs}; font-size:26px; font-weight:900; margin:0; line-height:1;'>{int(round(mediana_spot))}d</p>
        <p style='color:#334155; font-size:9px; margin:3px 0 0 0;'>ref: 20d</p>
    </div>
</div>
</div>""", unsafe_allow_html=True)

            # --- FILA 3: ETD ESTA SEMANA ---
            st.markdown("<br>", unsafe_allow_html=True)
            st.markdown(f"""
<div style='border-bottom:1px solid rgba(0,168,255,0.15); padding-bottom:8px; margin-bottom:20px;'>
<span style='color:#64748b; font-size:11px; font-weight:700; letter-spacing:4px; text-transform:uppercase;'>ETD ESTA SEMANA</span>
<span style='color:#334155; font-size:11px; letter-spacing:2px; margin-left:14px;'>{lunes_semana.strftime("%d/%m")} al {domingo_semana.strftime("%d/%m/%Y")}</span>
</div>""", unsafe_allow_html=True)

            cma = color_dias(med_adv_sem, 20)
            cms = color_dias(med_spot_sem, 20)

            col_s1, col_s2, col_s3, col_s4 = st.columns(4)

            with col_s1:
                st.markdown(f"""
<div style='background:linear-gradient(145deg, rgba(0,168,255,0.07), rgba(0,168,255,0.02));
border-radius:16px; border:1px solid rgba(0,168,255,0.15); padding:22px;
height:{H_ROW3}; box-sizing:border-box; display:flex; flex-direction:column; justify-content:space-between;'>
<p style='color:#64748b; font-size:10px; letter-spacing:2px; margin:0; text-transform:uppercase;'>Embarques con ETD OK</p>
<p style='color:#f8fafc; font-size:58px; font-weight:900; margin:0; line-height:1; letter-spacing:-2px;'>{cant_etd_sem}</p>
<div>
    <p style='color:#64748b; font-size:10px; margin:0 0 2px 0;'>CONTENEDORES</p>
    <p style='color:#00a8ff; font-size:18px; font-weight:800; margin:0;'>{int(cntr_etd_sem)}</p>
</div>
</div>""", unsafe_allow_html=True)

            with col_s2:
                st.markdown(f"""
<div style='background:rgba(255,255,255,0.03); border-radius:16px;
border:1px solid rgba(255,255,255,0.07); padding:22px;
height:{H_ROW3}; box-sizing:border-box; display:flex; flex-direction:column; justify-content:space-between;'>
<p style='color:#64748b; font-size:10px; letter-spacing:2px; margin:0; text-transform:uppercase;'>Volumen a zarpar</p>
<p style='color:#f8fafc; font-size:48px; font-weight:900; margin:0; line-height:1;'>{int(round(m3_etd_sem)):,}</p>
<p style='color:#475569; font-size:13px; font-weight:600; margin:0;'>M3 esta semana</p>
</div>""", unsafe_allow_html=True)

            with col_s3:
                st.markdown(f"""
<div style='background:rgba(0,255,136,0.04); border-radius:16px;
border:1px solid rgba(0,255,136,0.1); padding:22px;
height:{H_ROW3}; box-sizing:border-box; display:flex; flex-direction:column; justify-content:space-between;'>
<p style='color:#64748b; font-size:10px; letter-spacing:2px; margin:0; text-transform:uppercase;'>Consolidacion In Advance <span style='color:#334155; font-weight:400;'>(mediana)</span></p>
<div>
    <p style='color:{cma}; font-size:52px; font-weight:900; margin:0; line-height:1;'>{int(round(med_adv_sem))}d</p>
    <p style='color:#334155; font-size:10px; margin:6px 0 0 0;'>{len(df_adv_sem)} embarques · ref: 20d</p>
</div>
<div style='height:5px; background:rgba(255,255,255,0.06); border-radius:3px;'>
    <div style='height:5px; width:{min(int(round(med_adv_sem/20*100)), 100)}%; background:{cma}; border-radius:3px;'></div>
</div>
</div>""", unsafe_allow_html=True)

            with col_s4:
                st.markdown(f"""
<div style='background:rgba(148,163,184,0.04); border-radius:16px;
border:1px solid rgba(148,163,184,0.1); padding:22px;
height:{H_ROW3}; box-sizing:border-box; display:flex; flex-direction:column; justify-content:space-between;'>
<p style='color:#64748b; font-size:10px; letter-spacing:2px; margin:0; text-transform:uppercase;'>Consolidacion Spot <span style='color:#334155; font-weight:400;'>(mediana)</span></p>
<div>
    <p style='color:{cms}; font-size:52px; font-weight:900; margin:0; line-height:1;'>{int(round(med_spot_sem))}d</p>
    <p style='color:#334155; font-size:10px; margin:6px 0 0 0;'>{len(df_spot_sem)} embarques · ref: 20d</p>
</div>
<div style='height:5px; background:rgba(255,255,255,0.06); border-radius:3px;'>
    <div style='height:5px; width:{min(int(round(med_spot_sem/20*100)), 100)}%; background:{cms}; border-radius:3px;'></div>
</div>
</div>""", unsafe_allow_html=True)

            # ═══════════════════════════════════════════════════════
            # BLOQUE AEREO
            # ═══════════════════════════════════════════════════════
            st.markdown("<br><br>", unsafe_allow_html=True)
            st.markdown("""
<div style='border-bottom:2px solid rgba(168,85,247,0.3); padding-bottom:10px; margin-bottom:28px;'>
<span style='color:#a855f7; font-size:13px; font-weight:800; letter-spacing:5px; text-transform:uppercase;'>AEREO</span>
<span style='color:#475569; font-size:11px; letter-spacing:2px; margin-left:16px;'>SEGUIMIENTO ACTIVO</span>
</div>""", unsafe_allow_html=True)

            try:
                @st.cache_data(ttl=60)
                def load_aereos(base):
                    url_ae = f"{base}/export?format=csv&gid=88538385"
                    df_ae  = pd.read_csv(url_ae, engine='python', on_bad_lines='skip', header=0)
                    df_ae.columns = [str(c).strip() for c in df_ae.columns]
                    return df_ae

                df_ae = load_aereos(base_url)

                col_ae_estadio = df_ae.columns[0]
                col_ae_emb     = df_ae.columns[1]
                col_ae_empresa = df_ae.columns[2]
                col_ae_fwd     = df_ae.columns[7]
                col_ae_partic  = df_ae.columns[8]
                col_ae_etd     = df_ae.columns[14]
                col_ae_eta     = df_ae.columns[15]
                col_ae_m3      = df_ae.columns[21]
                col_ae_cant    = df_ae.columns[23]

                ORDEN_ESTADIOS = ['WAREHOUSE', 'EN ORIGEN', 'COORDINANDO', 'EN TRANSITO', 'EN TRÁNSITO', 'ARRIBADO', 'NACIONALIZADO', 'NACIONAZALIDO']
                COLORES_ESTADIOS = {
                    'WAREHOUSE'    : '#06b6d4',
                    'EN ORIGEN'    : '#ffaa00',
                    'COORDINANDO'  : '#f97316',
                    'EN TRANSITO'  : '#00a8ff',
                    'EN TRÁNSITO'  : '#00a8ff',
                    'ARRIBADO'     : '#a855f7',
                    'NACIONALIZADO': '#00ff88',
                    'NACIONAZALIDO': '#00ff88',
                }

                df_ae_clean = df_ae.copy()
                df_ae_clean[col_ae_estadio] = df_ae_clean[col_ae_estadio].astype(str).str.strip().str.upper()
                df_ae_activos = df_ae_clean[
                    df_ae_clean[col_ae_estadio].notna() &
                    (df_ae_clean[col_ae_estadio] != '') &
                    (df_ae_clean[col_ae_estadio] != 'NAN') &
                    (~df_ae_clean[col_ae_estadio].isin(['ENTREGADO']))
                ].copy()

                def safe_num_ae(v):
                    try: return float(str(v).replace(',', '.').strip())
                    except: return 0.0

                df_ae_activos[col_ae_m3]   = df_ae_activos[col_ae_m3].apply(safe_num_ae)
                df_ae_activos[col_ae_cant]  = df_ae_activos[col_ae_cant].apply(safe_num_ae)

                total_ae    = df_ae_activos[col_ae_emb].nunique()
                m3_ae       = df_ae_activos[col_ae_m3].sum()
                cant_ae     = df_ae_activos[col_ae_cant].sum()
                empresas_ae = df_ae_activos[col_ae_empresa].nunique()

                col_ae_big, col_ae_info = st.columns([1.2, 1])

                with col_ae_big:
                    st.markdown(f"""
<div style='background:linear-gradient(145deg, rgba(168,85,247,0.07), rgba(168,85,247,0.02));
border-radius:20px; border:1px solid rgba(168,85,247,0.15); padding:28px;
height:{H_AE}; box-sizing:border-box; display:flex; flex-direction:column; justify-content:space-between;'>
<div>
    <p style='color:#64748b; font-size:11px; letter-spacing:3px; margin:0 0 6px 0; text-transform:uppercase;'>Embarques aereos activos</p>
    <p style='color:#f8fafc; font-size:88px; font-weight:900; margin:0; line-height:1; letter-spacing:-4px;'>{total_ae}</p>
</div>
<div style='display:flex; gap:28px;'>
    <div>
        <p style='color:#64748b; font-size:10px; letter-spacing:1px; margin:0 0 3px 0;'>VOLUMEN</p>
        <p style='color:#a855f7; font-size:22px; font-weight:800; margin:0;'>{int(round(m3_ae)):,} M3</p>
    </div>
    <div>
        <p style='color:#64748b; font-size:10px; letter-spacing:1px; margin:0 0 3px 0;'>UNIDADES</p>
        <p style='color:#a855f7; font-size:22px; font-weight:800; margin:0;'>{int(cant_ae):,}</p>
    </div>
    <div>
        <p style='color:#64748b; font-size:10px; letter-spacing:1px; margin:0 0 3px 0;'>EMPRESAS</p>
        <p style='color:#a855f7; font-size:22px; font-weight:800; margin:0;'>{empresas_ae}</p>
    </div>
</div>
</div>""", unsafe_allow_html=True)

                with col_ae_info:
                    df_ae_activos['_partic'] = df_ae_activos[col_ae_partic].astype(str).str.strip()
                    df_ae_activos['_partic'] = df_ae_activos['_partic'].replace({'': 'SIN CLASIFICAR', 'nan': 'SIN CLASIFICAR', 'NaN': 'SIN CLASIFICAR'})
                    conteo_p = df_ae_activos.groupby('_partic')[col_ae_emb].nunique().reset_index()
                    conteo_p.columns = ['Tipo', 'Embarques']
                    conteo_p['Pct'] = (conteo_p['Embarques'] / conteo_p['Embarques'].sum() * 100).round(0)
                    conteo_p = conteo_p.sort_values('Embarques', ascending=False).head(4)
                    COLS_P = ['#a855f7', '#00a8ff', '#00ff88', '#ffaa00']

                    filas_tipo = ""
                    for i, (_, rp) in enumerate(conteo_p.iterrows()):
                        cp = COLS_P[i % len(COLS_P)]
                        filas_tipo += f"""
<div style='margin-bottom:14px;'>
    <div style='display:flex; justify-content:space-between; align-items:center; margin-bottom:5px;'>
        <p style='color:#94a3b8; font-size:12px; font-weight:600; margin:0;'>{rp['Tipo']}</p>
        <p style='color:{cp}; font-size:16px; font-weight:900; margin:0;'>{int(rp['Embarques'])} <span style='font-size:11px; color:#475569;'>({int(rp['Pct'])}%)</span></p>
    </div>
    <div style='height:5px; background:rgba(255,255,255,0.05); border-radius:3px;'>
        <div style='height:5px; width:{int(rp["Pct"])}%; background:{cp}; border-radius:3px;'></div>
    </div>
</div>"""

                    st.markdown(f"""
<div style='background:rgba(255,255,255,0.03); border-radius:20px;
border:1px solid rgba(255,255,255,0.07); padding:28px;
height:{H_AE}; box-sizing:border-box; display:flex; flex-direction:column; justify-content:space-between;'>
<p style='color:#64748b; font-size:10px; letter-spacing:3px; margin:0 0 16px 0; text-transform:uppercase;'>Tipo de negocio</p>
<div style='flex:1;'>{filas_tipo}</div>
</div>""", unsafe_allow_html=True)

                # Grafico estadios aereos
                st.markdown("<br>", unsafe_allow_html=True)
                st.markdown("""
<p style='color:#64748b; font-size:10px; letter-spacing:4px; font-weight:700;
text-transform:uppercase; margin:0 0 14px 0;'>ESTADIOS DE LAS CARGAS</p>""", unsafe_allow_html=True)

                orden_idx = {e: i for i, e in enumerate(ORDEN_ESTADIOS)}
                conteo_e = df_ae_activos.groupby(col_ae_estadio).agg(
                    Embarques=(col_ae_emb, 'nunique'),
                    M3=(col_ae_m3, 'sum')
                ).reset_index()
                conteo_e.columns = ['Estadio', 'Embarques', 'M3']
                conteo_e['_ord'] = conteo_e['Estadio'].map(lambda x: orden_idx.get(x, 99))
                conteo_e = conteo_e.sort_values('_ord').reset_index(drop=True)
                conteo_e['Color'] = conteo_e['Estadio'].map(lambda x: COLORES_ESTADIOS.get(x, '#94a3b8'))
                conteo_e['Label'] = conteo_e.apply(
                    lambda r: f"  {int(r['Embarques'])} emb · {int(round(r['M3']))} M3", axis=1
                )

                fig_ae = px.bar(
                    conteo_e,
                    y='Estadio',
                    x='Embarques',
                    orientation='h',
                    text='Label',
                    color='Estadio',
                    color_discrete_map={row['Estadio']: row['Color'] for _, row in conteo_e.iterrows()},
                )
                fig_ae.update_traces(
                    textposition='outside',
                    cliponaxis=False,
                    textfont=dict(size=13, color='#94a3b8', family='Outfit, sans-serif'),
                    marker=dict(cornerradius=6),
                    hovertemplate='<b>%{y}</b><br>Embarques: %{x}<extra></extra>'
                )
                fig_ae.update_layout(
                    height=max(220, len(conteo_e) * 54),
                    showlegend=False,
                    paper_bgcolor='rgba(0,0,0,0)',
                    plot_bgcolor='rgba(0,0,0,0)',
                    font=dict(family='Outfit, sans-serif', color='#94a3b8', size=12),
                    margin=dict(l=10, r=180, t=10, b=10),
                    xaxis=dict(
                        showgrid=True, gridwidth=1,
                        gridcolor='rgba(255,255,255,0.05)',
                        zeroline=False, showticklabels=False, title=''
                    ),
                    yaxis=dict(
                        showgrid=False, title='',
                        tickfont=dict(size=12, color='#94a3b8'),
                        categoryorder='array',
                        categoryarray=conteo_e['Estadio'].tolist()[::-1]
                    ),
                )
                st.plotly_chart(fig_ae, use_container_width=True)

            except Exception as e_ae:
                st.error(f"Error en seccion Aereos: {e_ae}")
                import traceback; st.code(traceback.format_exc())

        except Exception as e:
            st.error(f"Error en Coordinacion Activa: {e}")
            import traceback; st.code(traceback.format_exc())
    # --- SOLAPA 3: PERFORMANCE DE ANALISTAS ---
    with tabs[2]:
        st.markdown("<div style='text-align:center; padding: 20px; background: rgba(0, 168, 255, 0.05); border-radius: 20px; margin: 30px 0;'><h2 style='color:#00a8ff; font-weight:800; letter-spacing:5px; margin:0;'>PERFORMANCE DE ANALISTAS</h2><p style='color:#94a3b8; margin:8px 0 0 0; font-size:13px; letter-spacing:2px;'>BASADO EN RESERVAS HISTÓRICAS · 2026</p></div>", unsafe_allow_html=True)
        try:
            @st.cache_data(ttl=120)
            def load_perf_data(base):
                url_res_hi = f"{base}/export?format=csv&gid=32771816"
                url_emb_hi = f"{base}/export?format=csv&gid=50628730"
                rh = pd.read_csv(url_res_hi, engine='python', on_bad_lines='skip', header=0)
                eh = pd.read_csv(url_emb_hi, engine='python', on_bad_lines='skip', header=0)
                rh.columns = [str(c).strip() for c in rh.columns]
                eh.columns = [str(c).strip() for c in eh.columns]
                return rh, eh
            df_rh, df_eh = load_perf_data(base_url)
            col_rh_emb   = df_rh.columns[0]
            col_rh_resp  = df_rh.columns[14]
            col_rh_mono  = df_rh.columns[24]
            col_rh_tcons = df_rh.columns[32]
            col_eh_so   = df_eh.columns[0]
            col_eh_emb  = df_eh.columns[4]
            col_eh_etd  = df_eh.columns[6]
            col_eh_prov = df_eh.columns[18]
            df_eh['ETD_DT'] = pd.to_datetime(df_eh[col_eh_etd], dayfirst=True, errors='coerce')
            df_eh_2026 = df_eh[df_eh['ETD_DT'].dt.year == 2026].copy()
            df_eh_2026['Mes_Num']   = df_eh_2026['ETD_DT'].dt.month
            df_eh_2026['Mes_Label'] = df_eh_2026['ETD_DT'].dt.strftime('%B %Y').str.upper()
            if df_eh_2026.empty:
                st.warning("No se encontraron embarques históricos para 2026.")
            else:
                meses_disp = df_eh_2026.drop_duplicates('Mes_Num').sort_values('Mes_Num')[['Mes_Num','Mes_Label']].values.tolist()
                opciones_mes = {lbl: num for num, lbl in meses_disp}
                col_sel, _ = st.columns([2, 3])
                with col_sel:
                    mes_sel_lbl = st.selectbox("SELECCIONAR MES ETD:", list(opciones_mes.keys()), key="perf_mes_sel")
                mes_sel_num = opciones_mes[mes_sel_lbl]
                df_eh_mes = df_eh_2026[df_eh_2026['Mes_Num'] == mes_sel_num].copy()
                embs_mes  = df_eh_mes[col_eh_emb].astype(str).str.strip().str.upper().unique()
                df_rh['_emb_key'] = df_rh[col_rh_emb].astype(str).str.strip().str.upper()
                df_rh_mes = df_rh[df_rh['_emb_key'].isin(embs_mes)].copy()
                def clean_tcons(val):
                    try: return float(str(val).replace(',','.').strip())
                    except: return None
                df_rh_mes['T_Cons_Num'] = df_rh_mes[col_rh_tcons].apply(clean_tcons)
                df_rh_mes['Tipo_Carga'] = df_rh_mes[col_rh_mono].astype(str).str.strip().str.upper().apply(
                    lambda x: 'MONOPROVEEDOR' if 'MONO' in x else 'CONSOLIDADO'
                )
                df_rh_mes['Responsable'] = df_rh_mes[col_rh_resp].astype(str).str.strip()
                df_rh_mes = df_rh_mes[~df_rh_mes['Responsable'].isin(['', 'nan', 'NaN', 'None', '-', 'nan'])]
                if df_rh_mes.empty:
                    st.warning(f"No se encontraron datos para {mes_sel_lbl}.")
                else:
                    total_embs_mes  = len(embs_mes)
                    total_sos_mes   = df_eh_mes[col_eh_so].nunique()
                    total_provs_mes = df_eh_mes[col_eh_prov].nunique()
                    total_mono_mes  = (df_rh_mes['Tipo_Carga'] == 'MONOPROVEEDOR').sum()
                    total_cons_mes  = (df_rh_mes['Tipo_Carga'] == 'CONSOLIDADO').sum()
                    avg_tcons_mes   = df_rh_mes['T_Cons_Num'].mean()
                    st.markdown("<br>", unsafe_allow_html=True)
                    k1, k2, k3, k4, k5 = st.columns(5)
                    with k1: st.markdown(f"<div class='metric-container'><p>EMBARQUES</p><p>{total_embs_mes}</p></div>", unsafe_allow_html=True)
                    with k2: st.markdown(f"<div class='metric-container'><p>SOs TOTALES</p><p>{total_sos_mes}</p></div>", unsafe_allow_html=True)
                    with k3: st.markdown(f"<div class='metric-container'><p>PROVEEDORES</p><p>{total_provs_mes}</p></div>", unsafe_allow_html=True)
                    with k4: st.markdown(f"<div class='metric-container'><p>MONO / CONS</p><p style='font-size:40px !important;'>{total_mono_mes} / {total_cons_mes}</p></div>", unsafe_allow_html=True)
                    with k5: st.markdown(f"<div class='metric-container'><p>DIAS PROM. CONS.</p><p>{int(round(avg_tcons_mes)) if pd.notna(avg_tcons_mes) else 0}</p></div>", unsafe_allow_html=True)
                    st.markdown("<hr class='glow-divider'>", unsafe_allow_html=True)
                    st.markdown("<p style='color:#00a8ff; font-weight:800; letter-spacing:4px; font-size:16px; margin-bottom:20px; text-align:center;'>DESEMPENO POR ANALISTA</p>", unsafe_allow_html=True)
                    rows_analistas = []
                    for analista, grp_a in df_rh_mes.groupby('Responsable'):
                        embs_a   = grp_a['_emb_key'].unique()
                        df_eh_a  = df_eh_mes[df_eh_mes[col_eh_emb].astype(str).str.strip().str.upper().isin(embs_a)]
                        cant_embs    = len(embs_a)
                        cant_sos     = df_eh_a[col_eh_so].nunique()
                        cant_provs   = df_eh_a[col_eh_prov].nunique()
                        cant_mono    = (grp_a['Tipo_Carga'] == 'MONOPROVEEDOR').sum()
                        cant_cons    = (grp_a['Tipo_Carga'] == 'CONSOLIDADO').sum()
                        avg_tcons    = grp_a['T_Cons_Num'].mean()
                        avg_so_emb   = round(cant_sos / cant_embs, 1) if cant_embs > 0 else 0
                        prov_por_emb = df_eh_a.groupby(
                            df_eh_a[col_eh_emb].astype(str).str.strip().str.upper()
                        )[col_eh_prov].nunique()
                        avg_prov_emb = round(prov_por_emb.mean(), 1) if not prov_por_emb.empty else 0
                        es_azul = analista.strip().upper() == 'AZUL'
                        dias_cons_val = "✈️ En preparación" if es_azul else (f"{round(avg_tcons, 1)} d" if pd.notna(avg_tcons) else "—")
                        rows_analistas.append({
                            'Analista'         : analista,
                            'Embarques'        : cant_embs,
                            'SOs'              : cant_sos,
                            'Proveedores'      : cant_provs,
                            'Monoproveedor'    : int(cant_mono),
                            'Consolidado'      : int(cant_cons),
                            'Dias Prom. Cons.' : dias_cons_val,
                            'SO por Embarque'  : avg_so_emb,
                            'Prov por Embarque': avg_prov_emb,
                        })
                    df_analistas = pd.DataFrame(rows_analistas).sort_values('Embarques', ascending=False)
                    st.dataframe(
                        df_analistas, use_container_width=True, hide_index=True,
                        column_config={
                            'Analista'         : st.column_config.TextColumn("Analista"),
                            'Embarques'        : st.column_config.NumberColumn("Embarques", format="%d"),
                            'SOs'              : st.column_config.NumberColumn("SOs", format="%d"),
                            'Proveedores'      : st.column_config.NumberColumn("Proveedores", format="%d"),
                            'Monoproveedor'    : st.column_config.NumberColumn("Mono", format="%d"),
                            'Consolidado'      : st.column_config.NumberColumn("Consolidado", format="%d"),
                            'Dias Prom. Cons.' : st.column_config.TextColumn("Dias Prom. Cons."),
                            'SO por Embarque'  : st.column_config.NumberColumn("SO/Emb", format="%.1f"),
                            'Prov por Embarque': st.column_config.NumberColumn("Prov/Emb", format="%.1f"),
                        }
                    )
                    st.markdown("<hr class='glow-divider'>", unsafe_allow_html=True)
                    st.markdown("<p style='color:#00ff88; font-weight:800; letter-spacing:4px; font-size:16px; margin-bottom:20px; text-align:center;'>EVOLUCION MES A MES POR ANALISTA</p>", unsafe_allow_html=True)
                    rows_evol = []
                    for mes_num, mes_lbl in meses_disp:
                        df_eh_m = df_eh_2026[df_eh_2026['Mes_Num'] == mes_num]
                        embs_m  = df_eh_m[col_eh_emb].astype(str).str.strip().str.upper().unique()
                        df_rh_m = df_rh[df_rh['_emb_key'].isin(embs_m)].copy()
                        df_rh_m['T_Cons_Num'] = df_rh_m[col_rh_tcons].apply(clean_tcons)
                        df_rh_m['Tipo_Carga'] = df_rh_m[col_rh_mono].astype(str).str.strip().str.upper().apply(
                            lambda x: 'MONOPROVEEDOR' if 'MONO' in x else 'CONSOLIDADO'
                        )
                        df_rh_m['Responsable'] = df_rh_m[col_rh_resp].astype(str).str.strip()
                        df_rh_m = df_rh_m[~df_rh_m['Responsable'].isin(['', 'nan', 'NaN', 'None', '-', 'nan'])]
                        for analista, grp_a in df_rh_m.groupby('Responsable'):
                            embs_a  = grp_a['_emb_key'].unique()
                            df_eh_a = df_eh_m[df_eh_m[col_eh_emb].astype(str).str.strip().str.upper().isin(embs_a)]
                            avg_tc  = grp_a['T_Cons_Num'].mean()
                            rows_evol.append({
                                'Mes_Num'   : mes_num,
                                'Mes'       : mes_lbl,
                                'Analista'  : analista,
                                'Embarques' : len(embs_a),
                                'SOs'       : df_eh_a[col_eh_so].nunique(),
                                'Dias Cons.': round(avg_tc, 1) if pd.notna(avg_tc) else None,
                            })
                    df_evol = pd.DataFrame(rows_evol)
                    if not df_evol.empty:
                        analistas_disp = sorted(df_evol['Analista'].unique())
                        col_pick, _ = st.columns([2, 3])
                        with col_pick:
                            analista_sel = st.selectbox("VER EVOLUCION DE:", analistas_disp, key="perf_analista_sel")
                        df_evol_a = df_evol[df_evol['Analista'] == analista_sel].sort_values('Mes_Num')
                        es_azul_sel = analista_sel.strip().upper() == 'AZUL'
                        if es_azul_sel:
                            st.plotly_chart(
                                px.bar(df_evol_a, x='Mes', y='Embarques', text_auto=',.0f',
                                       color_discrete_sequence=['#00a8ff'],
                                       title=f"Embarques - {analista_sel}"
                                ).update_traces(textposition='outside', textfont_color='#f8fafc', marker=dict(cornerradius=5)
                                ).update_layout(height=350, paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)',
                                                font=dict(family='Outfit, sans-serif', color='#94a3b8'),
                                                title_font_color='#00a8ff',
                                                xaxis=dict(showgrid=False, tickangle=-30),
                                                yaxis=dict(showgrid=True, gridcolor='rgba(255,255,255,0.07)'),
                                                margin=dict(l=10,r=10,t=50,b=40)),
                                use_container_width=True
                            )
                            st.info("✈️ Azul gestiona cargas aéreas — los tiempos de consolidación marítima no aplican a su metodología.")
                            st.markdown("<br>", unsafe_allow_html=True)
                            st.dataframe(
                                df_evol_a[['Mes','Embarques','SOs']].reset_index(drop=True),
                                use_container_width=True, hide_index=True,
                                column_config={
                                    'Mes'      : st.column_config.TextColumn("Mes ETD"),
                                    'Embarques': st.column_config.NumberColumn("Embarques", format="%d"),
                                    'SOs'      : st.column_config.NumberColumn("SOs", format="%d"),
                                }
                            )
                        else:
                            ev1, ev2 = st.columns(2)
                            with ev1:
                                fig_ev_emb = px.bar(df_evol_a, x='Mes', y='Embarques', text_auto=',.0f', color_discrete_sequence=['#00a8ff'], title=f"Embarques - {analista_sel}")
                                fig_ev_emb.update_traces(textposition='outside', textfont_color='#f8fafc', marker=dict(cornerradius=5))
                                fig_ev_emb.update_layout(height=350, paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)', font=dict(family='Outfit, sans-serif', color='#94a3b8'), title_font_color='#00a8ff', xaxis=dict(showgrid=False, tickangle=-30), yaxis=dict(showgrid=True, gridcolor='rgba(255,255,255,0.07)'), margin=dict(l=10,r=10,t=50,b=40))
                                st.plotly_chart(fig_ev_emb, use_container_width=True)
                            with ev2:
                                fig_ev_tc = px.bar(df_evol_a, x='Mes', y='Dias Cons.', text_auto=',.1f', color_discrete_sequence=['#00ff88'], title=f"Dias Prom. Consolidacion - {analista_sel}")
                                fig_ev_tc.update_traces(textposition='outside', textfont_color='#f8fafc', marker=dict(cornerradius=5))
                                fig_ev_tc.update_layout(height=350, paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)', font=dict(family='Outfit, sans-serif', color='#94a3b8'), title_font_color='#00ff88', xaxis=dict(showgrid=False, tickangle=-30), yaxis=dict(showgrid=True, gridcolor='rgba(255,255,255,0.07)'), margin=dict(l=10,r=10,t=50,b=40))
                                st.plotly_chart(fig_ev_tc, use_container_width=True)
                            st.markdown("<br>", unsafe_allow_html=True)
                            st.dataframe(
                                df_evol_a[['Mes','Embarques','SOs','Dias Cons.']].reset_index(drop=True),
                                use_container_width=True, hide_index=True,
                                column_config={
                                    'Mes'       : st.column_config.TextColumn("Mes ETD"),
                                    'Embarques' : st.column_config.NumberColumn("Embarques", format="%d"),
                                    'SOs'       : st.column_config.NumberColumn("SOs", format="%d"),
                                    'Dias Cons.': st.column_config.NumberColumn("Dias Prom. Cons.", format="%.1f d"),
                                }
                            )
        except Exception as e:
            st.error(f"Error en Performance Analistas: {e}")
            import traceback
            st.code(traceback.format_exc())
        # PERFORMANCE DE AGENTES (FORWARDERS)
        st.markdown("<hr class='glow-divider'>", unsafe_allow_html=True)
        st.markdown("<div style='text-align:center; padding: 20px; background: rgba(255,170,0,0.05); border-radius: 20px; margin: 30px 0;'><h2 style='color:#ffaa00; font-weight:800; letter-spacing:5px; margin:0;'>PERFORMANCE DE AGENTES (FORWARDERS)</h2><p style='color:#94a3b8; margin:8px 0 0 0; font-size:13px; letter-spacing:2px;'>BASADO EN RESERVAS HISTORICAS 2026</p></div>", unsafe_allow_html=True)
        try:
            try:
                _ = df_rh
            except NameError:
                df_rh, df_eh = load_perf_data(base_url)
            col_ag_fwd        = df_rh.columns[6]
            col_ag_inst       = df_rh.columns[7]
            col_ag_etd        = df_rh.columns[11]
            col_ag_bl         = df_rh.columns[15]
            col_ag_conf       = df_rh.columns[18]
            col_ag_cntr       = df_rh.columns[1]
            col_ag_linea      = df_rh.columns[59]  if len(df_rh.columns) > 59 else None
            col_ag_gto_origen = df_rh.columns[38]  if len(df_rh.columns) > 38 else None
            col_ag_flete_pag  = df_rh.columns[51]  if len(df_rh.columns) > 51 else None
            col_ag_flete_cert = df_rh.columns[52]  if len(df_rh.columns) > 52 else None
            col_ag_gto_local  = df_rh.columns[54]  if len(df_rh.columns) > 54 else None
            df_rh['_ag_inst_dt'] = pd.to_datetime(df_rh[col_ag_inst], dayfirst=True, errors='coerce')
            df_rh['_ag_etd_dt']  = pd.to_datetime(df_rh[col_ag_etd],  dayfirst=True, errors='coerce')
            df_rh['_ag_bl_dt']   = pd.to_datetime(df_rh[col_ag_bl],   dayfirst=True, errors='coerce')
            df_rh['_ag_conf_dt'] = pd.to_datetime(df_rh[col_ag_conf], dayfirst=True, errors='coerce')
            df_rh_ag_2026 = df_rh[df_rh['_ag_etd_dt'].dt.year == 2026].copy()
            TIPOS_MAR_AG = ['40 HQ', '20 ST', '40 ST', '40 NOR']
            df_rh_ag_2026 = df_rh_ag_2026[
                df_rh_ag_2026[df_rh.columns[5]].astype(str).str.strip().str.upper().isin(
                    [t.upper() for t in TIPOS_MAR_AG]
                )
            ].copy()
            df_rh_ag_2026['Mes_Num_Ag']   = df_rh_ag_2026['_ag_etd_dt'].dt.month
            df_rh_ag_2026['Mes_Label_Ag'] = df_rh_ag_2026['_ag_etd_dt'].dt.strftime('%B %Y').str.upper()
            def safe_num_ag(val):
                try: return float(str(val).replace(',','.').replace(' ','').strip())
                except: return None
            for col in [col_ag_gto_origen, col_ag_flete_pag, col_ag_flete_cert, col_ag_gto_local, col_ag_cntr]:
                if col: df_rh_ag_2026[col] = df_rh_ag_2026[col].apply(safe_num_ag)
            if df_rh_ag_2026.empty:
                st.warning("No se encontraron datos maritimos de agentes para 2026.")
            else:
                meses_ag = df_rh_ag_2026.drop_duplicates('Mes_Num_Ag').sort_values('Mes_Num_Ag')[['Mes_Num_Ag','Mes_Label_Ag']].values.tolist()
                opciones_ag = {lbl: num for num, lbl in meses_ag}
                col_sel_ag, _ = st.columns([2, 3])
                with col_sel_ag:
                    mes_ag_lbl = st.selectbox("SELECCIONAR MES ETD (AGENTES):", list(opciones_ag.keys()), key="perf_ag_mes_sel")
                mes_ag_num = opciones_ag[mes_ag_lbl]
                df_ag_mes = df_rh_ag_2026[df_rh_ag_2026['Mes_Num_Ag'] == mes_ag_num].copy()
                df_ag_mes['_dias_instr_conf'] = (df_ag_mes['_ag_conf_dt'] - df_ag_mes['_ag_inst_dt']).dt.days
                df_ag_mes['_dias_etd_bl']     = (df_ag_mes['_ag_bl_dt']   - df_ag_mes['_ag_etd_dt']).dt.days
                df_ag_mes['_fwd_clean']        = df_ag_mes[col_ag_fwd].astype(str).str.strip()
                df_ag_mes = df_ag_mes[~df_ag_mes['_fwd_clean'].isin(['', 'nan', 'NaN', 'None', '-'])]
                total_embs_ag   = df_ag_mes[df_rh.columns[0]].nunique()
                total_cntrs_ag  = df_ag_mes[col_ag_cntr].sum()
                avg_dias_ic     = df_ag_mes['_dias_instr_conf'].mean()
                avg_dias_bl     = df_ag_mes['_dias_etd_bl'].mean()
                sum_fp_global   = df_ag_mes[col_ag_flete_pag].sum()  if col_ag_flete_pag  else 0
                sum_fc_global   = df_ag_mes[col_ag_flete_cert].sum() if col_ag_flete_cert else 0
                pct_cert_global = round(sum_fc_global / sum_fp_global * 100, 1) if sum_fp_global and sum_fp_global > 0 else None
                color_cert = "#00ff88" if pct_cert_global and pct_cert_global >= 75 else "#ff4b4b"
                st.markdown("<br>", unsafe_allow_html=True)
                kg1, kg2, kg3, kg4, kg5 = st.columns(5)
                with kg1: st.markdown(f"<div class='metric-container'><p>EMBARQUES</p><p>{total_embs_ag}</p></div>", unsafe_allow_html=True)
                with kg2: st.markdown(f"<div class='metric-container'><p>CONTENEDORES</p><p>{int(total_cntrs_ag)}</p></div>", unsafe_allow_html=True)
                with kg3: st.markdown(f"<div class='metric-container'><p>DIAS INSTR-CONF</p><p>{int(round(avg_dias_ic)) if pd.notna(avg_dias_ic) else 0}</p></div>", unsafe_allow_html=True)
                with kg4: st.markdown(f"<div class='metric-container'><p>DIAS ETD-BL</p><p>{int(round(avg_dias_bl)) if pd.notna(avg_dias_bl) else 0}</p></div>", unsafe_allow_html=True)
                with kg5:
                    val_cert = f"{pct_cert_global}%" if pct_cert_global else "SD"
                    st.markdown(f"<div class='metric-container' style='border:1px solid {color_cert}44;'><p>PCT CERTIFICACION</p><p style='color:{color_cert} !important;'>{val_cert}</p></div>", unsafe_allow_html=True)
                st.markdown("<hr class='white-divider'>", unsafe_allow_html=True)
                st.markdown("<p style='color:#ffaa00; font-weight:800; letter-spacing:4px; font-size:15px; margin-bottom:20px; text-align:center;'>DESEMPENO POR AGENTE</p>", unsafe_allow_html=True)
                rows_ag = []
                for fwd, grp_f in df_ag_mes.groupby('_fwd_clean'):
                    cant_embs_f  = grp_f[df_rh.columns[0]].nunique()
                    cant_cntrs_f = grp_f[col_ag_cntr].sum()
                    avg_ic = grp_f['_dias_instr_conf'].mean()
                    avg_bl = grp_f['_dias_etd_bl'].mean()
                    if col_ag_linea:
                        lineas = grp_f[col_ag_linea].dropna().astype(str).str.strip()
                        lineas = lineas[~lineas.isin(['', 'nan', 'None', '-'])]
                        lineas_str = ", ".join(sorted(lineas.unique())) if not lineas.empty else "Sin datos"
                    else:
                        lineas_str = "Sin datos"
                    avg_fp = grp_f[col_ag_flete_pag].mean()  if col_ag_flete_pag  else 0
                    avg_fc = grp_f[col_ag_flete_cert].mean() if col_ag_flete_cert else 0
                    avg_gl = grp_f[col_ag_gto_local].mean()  if col_ag_gto_local  else 0
                    avg_go = grp_f[col_ag_gto_origen].mean() if col_ag_gto_origen else 0
                    sum_fp_f = grp_f[col_ag_flete_pag].sum()  if col_ag_flete_pag  else 0
                    sum_fc_f = grp_f[col_ag_flete_cert].sum() if col_ag_flete_cert else 0
                    pct_f    = round(sum_fc_f / sum_fp_f * 100, 1) if sum_fp_f and sum_fp_f > 0 else None
                    kpi_str  = ("OK >=75%" if pct_f >= 75 else "BAJO <75%") if pct_f else "Sin datos"
                    rows_ag.append({
                        'Agente'              : fwd,
                        'Embarques'           : cant_embs_f,
                        'Contenedores'        : int(cant_cntrs_f) if pd.notna(cant_cntrs_f) else 0,
                        'Dias Instr-Conf'     : round(avg_ic, 1) if pd.notna(avg_ic) else None,
                        'Dias ETD-BL'         : round(avg_bl, 1) if pd.notna(avg_bl) else None,
                        'Lineas Maritimas'    : lineas_str,
                        'Prom Flete Pag USD'  : round(avg_fp, 0) if avg_fp else None,
                        'Prom Flete Cert USD' : round(avg_fc, 0) if avg_fc else None,
                        'Prom Gtos Local USD' : round(avg_gl, 0) if avg_gl else None,
                        'Prom Gtos Orig USD'  : round(avg_go, 0) if avg_go else None,
                        'Pct Certif'          : f"{pct_f}%" if pct_f else "Sin datos",
                        'KPI Certif'          : kpi_str,
                    })
                df_ag_tabla = pd.DataFrame(rows_ag).sort_values('Embarques', ascending=False)
                st.dataframe(
                    df_ag_tabla, use_container_width=True, hide_index=True,
                    column_config={
                        'Agente'              : st.column_config.TextColumn("Agente"),
                        'Embarques'           : st.column_config.NumberColumn("Embarques", format="%d"),
                        'Contenedores'        : st.column_config.NumberColumn("CTNRS", format="%d"),
                        'Dias Instr-Conf'     : st.column_config.NumberColumn("Dias Instr-Conf", format="%.1f d"),
                        'Dias ETD-BL'         : st.column_config.NumberColumn("Dias ETD-BL", format="%.1f d"),
                        'Lineas Maritimas'    : st.column_config.TextColumn("Lineas Maritimas"),
                        'Prom Flete Pag USD'  : st.column_config.NumberColumn("Prom Flete Pag", format="$ %,.0f"),
                        'Prom Flete Cert USD' : st.column_config.NumberColumn("Prom Flete Cert", format="$ %,.0f"),
                        'Prom Gtos Local USD' : st.column_config.NumberColumn("Prom Gtos Locales", format="$ %,.0f"),
                        'Prom Gtos Orig USD'  : st.column_config.NumberColumn("Prom Gtos Origen", format="$ %,.0f"),
                        'Pct Certif'          : st.column_config.TextColumn("% Certif."),
                        'KPI Certif'          : st.column_config.TextColumn("KPI >=75%"),
                    }
                )
                estado_nota = "OBJETIVO CUMPLIDO" if pct_cert_global and pct_cert_global >= 75 else "POR DEBAJO DEL OBJETIVO - revisar certificacion"
                val_nota = f"{pct_cert_global}% - {estado_nota}" if pct_cert_global else "Sin datos suficientes"
                st.markdown(
                    "<div style='margin-top:15px; padding:12px 18px; background:rgba(255,255,255,0.02);"
                    f"border-radius:10px; border-left:4px solid {color_cert};'>"
                    f"<p style='color:#94a3b8; font-size:12px; margin:0;'>"
                    f"KPI CERTIFICACION: objetivo >= 75%. "
                    f"Total Flete Certificado / Total Flete Pagado x 100. "
                    f"Resultado del mes: "
                    f"<b style='color:{color_cert};'>{val_nota}</b> "
                    f"| Meta: lograr que la totalidad de las cargas tengan flete certificado al menos en un 75% del valor pagado."
                    f"</p></div>",
                    unsafe_allow_html=True
                )
        except Exception as e:
            st.error(f"Error en Performance Agentes: {e}")
            import traceback
            st.code(traceback.format_exc())
    # --- SOLAPA 4: CONTROL DE FLETES, GASTOS Y CERTIFICACIONES ---
    with tabs[3]:
        try:
            st.markdown("""
<div style='text-align:center; padding:25px; background:linear-gradient(135deg,rgba(255,170,0,0.08),rgba(0,168,255,0.05));
border-radius:20px; border:1px solid rgba(255,170,0,0.2); margin-bottom:30px;'>
<h2 style='color:#ffaa00; font-weight:900; letter-spacing:6px; margin:0; font-size:26px;'>FLETES & GASTOS LOCALES</h2>
<p style='color:#94a3b8; margin:8px 0 0 0; font-size:13px; letter-spacing:2px;'>MARITIMO 2026 - COTIZACIONES EN TIEMPO REAL</p>
</div>""", unsafe_allow_html=True)
            SHEET_URL = "https://docs.google.com/spreadsheets/d/1UJ1bDyDQdIQSSVQ6dyChVKbMX1d69G68ji_dpsOzfHg"
            @st.cache_data(ttl=300)
            def load_fletes_data(url):
                csv_url = f"{url}/export?format=csv&gid=0"
                df_f = pd.read_csv(csv_url, header=0, dtype=str, on_bad_lines='skip')
                df_f.columns = [str(c).strip() for c in df_f.columns]
                return df_f
            df_fl = load_fletes_data(SHEET_URL)
            def parse_usd_fl(val):
                try:
                    s = str(val).replace('USD','').replace('$','').replace(' ','').strip()
                    s = s.replace('.','').replace(',','.')
                    return float(s)
                except:
                    return None
            col_fl_tipo   = df_fl.columns[0]
            col_fl_agente = df_fl.columns[1]
            col_fl_flete  = df_fl.columns[3]
            col_fl_desde  = df_fl.columns[10]
            col_fl_hasta  = df_fl.columns[11]
            col_fl_local  = df_fl.columns[14]
            col_fl_cnt    = df_fl.columns[15]
            df_fl['_desde_dt'] = pd.to_datetime(df_fl[col_fl_desde], dayfirst=True, errors='coerce')
            df_fl['_hasta_dt'] = pd.to_datetime(df_fl[col_fl_hasta], dayfirst=True, errors='coerce')
            df_fl['_flete']    = df_fl[col_fl_flete].apply(parse_usd_fl)
            df_fl['_local']    = df_fl[col_fl_local].apply(parse_usd_fl)
            df_fl['_cnt']      = df_fl[col_fl_cnt].astype(str).str.strip().str.upper()
            df_fl['_agente']   = df_fl[col_fl_agente].astype(str).str.strip()
            df_fl['_mes_num']  = df_fl['_desde_dt'].dt.month
            df_fl['_mes_label']= df_fl['_desde_dt'].dt.strftime('%B %Y').str.upper()
            df_fl['_anio']     = df_fl['_desde_dt'].dt.year
            df_fl_2026 = df_fl[
                (df_fl['_anio'] == 2026) &
                df_fl['_flete'].notna() &
                (df_fl['_cnt'] != 'NAN') &
                (df_fl['_cnt'] != '') &
                ~df_fl[df_fl.columns[8]].astype(str).str.strip().str.upper().str.contains('LAZARO|CARDENAS|CÁRDENAS', na=False)
            ].copy()
            TIPOS_CNT  = ['40ST/40HQ', '20ST', '40NOR']
            TARGET_PCT = 0.85
            COLORES_CNT = {'40ST/40HQ': '#00a8ff', '20ST': '#00ff88', '40NOR': '#ffaa00'}
            if df_fl_2026.empty:
                st.warning("No se encontraron cotizaciones validas para 2026.")
            else:
                df_vig = df_fl_2026[
                    (df_fl_2026['_desde_dt'] <= hoy) &
                    (df_fl_2026['_hasta_dt'] >= hoy)
                ].copy()
                st.markdown(f"""
<div style='padding:14px 20px; background:rgba(255,255,255,0.02); border-radius:12px;
border-left:4px solid #00ff88; margin-bottom:20px;'>
<p style='color:#00ff88; font-weight:800; font-size:15px; letter-spacing:3px; margin:0;'>
COTIZACIONES VIGENTES HOY {hoy.strftime('%d/%m/%Y')}</p>
<p style='color:#94a3b8; font-size:11px; margin:4px 0 0 0;'>
Validez Quincena Desde menor o igual a hoy y Validez Quincena Hasta mayor o igual a hoy</p>
</div>""", unsafe_allow_html=True)
                if df_vig.empty:
                    st.info("No hay cotizaciones vigentes para hoy. Mostrando el periodo mas reciente disponible.")
                    ultimo_desde = df_fl_2026['_desde_dt'].max()
                    if pd.notna(ultimo_desde):
                        df_vig = df_fl_2026[df_fl_2026['_desde_dt'] == ultimo_desde].copy()
                if not df_vig.empty:
                    cant_agentes_vig = df_vig['_agente'].nunique()
                    v1, v2 = st.columns([1, 3])
                    with v1:
                        st.markdown(f"""
<div class='custom-card' style='border-top:3px solid #00ff88; text-align:center;'>
<p class='minicard-title'>AGENTES COTIZADOS</p>
<p style='font-size:52px; font-weight:900; color:#00ff88; margin:0;'>{cant_agentes_vig}</p>
</div>""", unsafe_allow_html=True)
                    with v2:
                        rows_vig = []
                        for cnt in TIPOS_CNT:
                            df_cnt = df_vig[df_vig['_cnt'] == cnt]
                            if df_cnt.empty: continue
                            prom   = df_cnt['_flete'].mean()
                            minimo = df_cnt['_flete'].min()
                            ag_min = df_cnt.loc[df_cnt['_flete'].idxmin(), '_agente']
                            target = prom * TARGET_PCT
                            vs_tgt = round((minimo - target) / target * 100, 1) if target > 0 else None
                            ok     = minimo <= target
                            rows_vig.append({
                                'Tipo CNT'       : cnt,
                                'Agentes'        : df_cnt['_agente'].nunique(),
                                'Prom. Mercado'  : round(prom, 0),
                                'Target -15%'    : round(target, 0),
                                'Mejor Oferta'   : round(minimo, 0),
                                'Agente Ganador' : ag_min,
                                'Vs Target'      : f"{'OK' if ok else 'ALTO'} {vs_tgt:+.1f}%" if vs_tgt else "SD",
                            })
                        if rows_vig:
                            df_vig_tabla = pd.DataFrame(rows_vig)
                            st.dataframe(
                                df_vig_tabla, use_container_width=True, hide_index=True,
                                column_config={
                                    'Tipo CNT'      : st.column_config.TextColumn("Tipo CNT"),
                                    'Agentes'       : st.column_config.NumberColumn("Agentes", format="%d"),
                                    'Prom. Mercado' : st.column_config.NumberColumn("Prom. Mercado", format="$ %,.0f"),
                                    'Target -15%'   : st.column_config.NumberColumn("Target -15%", format="$ %,.0f"),
                                    'Mejor Oferta'  : st.column_config.NumberColumn("Mejor Oferta", format="$ %,.0f"),
                                    'Agente Ganador': st.column_config.TextColumn("Agente Ganador"),
                                    'Vs Target'     : st.column_config.TextColumn("Vs Target"),
                                }
                            )
                st.markdown("<br>", unsafe_allow_html=True)
                st.markdown("""
<div style='padding:14px 20px; background:rgba(255,255,255,0.02); border-radius:12px;
border-left:4px solid #00a8ff; margin-bottom:15px;'>
<p style='color:#00a8ff; font-weight:800; font-size:15px; letter-spacing:3px; margin:0;'>
TARIFAS POR FORWARDER (FFWW)</p>
<p style='color:#94a3b8; font-size:11px; margin:4px 0 0 0;'>
Seleccioná un agente para ver sus tarifas vigentes por tipo de CNT</p>
</div>""", unsafe_allow_html=True)
                ffww_opciones = sorted(df_vig['_agente'].dropna().astype(str).str.strip().unique().tolist()) if not df_vig.empty else []
                ffww_opciones = [f for f in ffww_opciones if f.lower() not in ['', 'nan', 'none']]
                if ffww_opciones:
                    col_ffww, _ = st.columns([2, 3])
                    with col_ffww:
                        ffww_sel = st.selectbox("SELECCIONAR FFWW:", ["COMPARATIVA GENERAL"] + ffww_opciones, key="ffww_sel")
                    if ffww_sel == "COMPARATIVA GENERAL":
                        rows_ffww = []
                        for agente in ffww_opciones:
                            df_ag = df_vig[df_vig['_agente'].astype(str).str.strip() == agente]
                            for cnt in TIPOS_CNT:
                                df_c = df_ag[df_ag['_cnt'] == cnt]
                                if df_c.empty: continue
                                tarifa   = df_c['_flete'].mean()
                                prom_mkt = df_vig[df_vig['_cnt'] == cnt]['_flete'].mean()
                                target   = prom_mkt * TARGET_PCT
                                vs_tgt   = round((tarifa - target) / target * 100, 1) if target > 0 else None
                                ok       = tarifa <= target
                                rows_ffww.append({
                                    'FFWW'         : agente,
                                    'Tipo CNT'     : cnt,
                                    'Su Tarifa'    : round(tarifa, 0),
                                    'Prom. Mercado': round(prom_mkt, 0),
                                    'Target -15%'  : round(target, 0),
                                    'Vs Target'    : ("✅ OK " if ok else "🔴 ALTO ") + f"{vs_tgt:+.1f}%" if vs_tgt is not None else "SD",
                                })
                        if rows_ffww:
                            st.dataframe(
                                pd.DataFrame(rows_ffww),
                                use_container_width=True, hide_index=True,
                                column_config={
                                    'FFWW'         : st.column_config.TextColumn("FFWW"),
                                    'Tipo CNT'     : st.column_config.TextColumn("Tipo CNT"),
                                    'Su Tarifa'    : st.column_config.NumberColumn("Su Tarifa", format="$ %,.0f"),
                                    'Prom. Mercado': st.column_config.NumberColumn("Prom. Mercado", format="$ %,.0f"),
                                    'Target -15%'  : st.column_config.NumberColumn("Target -15%", format="$ %,.0f"),
                                    'Vs Target'    : st.column_config.TextColumn("Vs Target"),
                                }
                            )
                    else:
                        df_ffww = df_vig[df_vig['_agente'].astype(str).str.strip() == ffww_sel]
                        rows_ffww = []
                        for cnt in TIPOS_CNT:
                            df_c = df_ffww[df_ffww['_cnt'] == cnt]
                            if df_c.empty: continue
                            tarifa   = df_c['_flete'].mean()
                            prom_mkt = df_vig[df_vig['_cnt'] == cnt]['_flete'].mean()
                            target   = prom_mkt * TARGET_PCT
                            vs_tgt   = round((tarifa - target) / target * 100, 1) if target > 0 else None
                            ok       = tarifa <= target
                            rows_ffww.append({
                                'Tipo CNT'     : cnt,
                                'Tarifa FFWW'  : round(tarifa, 0),
                                'Prom. Mercado': round(prom_mkt, 0),
                                'Target -15%'  : round(target, 0),
                                'Vs Target'    : ("✅ OK " if ok else "🔴 ALTO ") + f"{vs_tgt:+.1f}%" if vs_tgt is not None else "SD",
                            })
                        if rows_ffww:
                            st.dataframe(
                                pd.DataFrame(rows_ffww),
                                use_container_width=True, hide_index=True,
                                column_config={
                                    'Tipo CNT'     : st.column_config.TextColumn("Tipo CNT"),
                                    'Tarifa FFWW'  : st.column_config.NumberColumn("Tarifa FFWW", format="$ %,.0f"),
                                    'Prom. Mercado': st.column_config.NumberColumn("Prom. Mercado", format="$ %,.0f"),
                                    'Target -15%'  : st.column_config.NumberColumn("Target -15%", format="$ %,.0f"),
                                    'Vs Target'    : st.column_config.TextColumn("Vs Target"),
                                }
                            )
                        else:
                            st.info(f"No hay tarifas vigentes para {ffww_sel}.")
                else:
                    st.info("No hay forwarders disponibles en el período vigente.")
                st.markdown("<br>", unsafe_allow_html=True)
                st.markdown("""
<div style='padding:14px 20px; background:rgba(255,255,255,0.02); border-radius:12px;
border-left:4px solid #a855f7; margin-bottom:20px;'>
<p style='color:#a855f7; font-weight:800; font-size:15px; letter-spacing:3px; margin:0;'>
GASTOS LOCALES ARG - VIGENTES HOY</p>
</div>""", unsafe_allow_html=True)
                df_loc_vig = df_fl_2026[
                    (df_fl_2026['_desde_dt'] <= hoy) &
                    (df_fl_2026['_hasta_dt'] >= hoy) &
                    df_fl_2026['_local'].notna()
                ].copy()
                if df_loc_vig.empty:
                    ultimo_l = df_fl_2026[df_fl_2026['_local'].notna()]['_desde_dt'].max()
                    if pd.notna(ultimo_l):
                        df_loc_vig = df_fl_2026[
                            (df_fl_2026['_desde_dt'] == ultimo_l) &
                            df_fl_2026['_local'].notna()
                        ].copy()
                if not df_loc_vig.empty:
                    prom_loc = df_loc_vig['_local'].mean()
                    min_loc  = df_loc_vig['_local'].min()
                    max_loc  = df_loc_vig['_local'].max()
                    ag_loc   = df_loc_vig.loc[df_loc_vig['_local'].idxmin(), '_agente']
                    la, lb, lc, ld = st.columns(4)
                    for col_card, valor, label, color in [
                        (la, f"USD {prom_loc:,.0f}", "PROM. LOCALES",     "#a855f7"),
                        (lb, f"USD {min_loc:,.0f}",  "MENOR LOCAL",       "#00ff88"),
                        (lc, ag_loc,                  "AGENTE MAS BARATO", "#f8fafc"),
                        (ld, f"USD {max_loc:,.0f}",  "MAYOR LOCAL",       "#ff4b4b"),
                    ]:
                        col_card.markdown(f"""
<div style='text-align:center; padding:16px 8px; background:rgba(255,255,255,0.02);
border-radius:14px; border-top:3px solid {color};'>
<p style='color:#94a3b8; font-size:10px; letter-spacing:1px; margin:0 0 6px 0;'>{label}</p>
<p style='color:{color}; font-size:22px; font-weight:900; margin:0;'>{valor}</p>
</div>""", unsafe_allow_html=True)
                else:
                    st.info("No hay gastos locales disponibles para el periodo vigente.")
                st.markdown("<br>", unsafe_allow_html=True)
                st.markdown("<hr style='border:none; border-top:2px solid rgba(255,170,0,0.15); margin:10px 0 25px 0;'>", unsafe_allow_html=True)
                st.markdown("""
<div style='padding:14px 20px; background:rgba(255,255,255,0.02); border-radius:12px;
border-left:4px solid #ffaa00; margin-bottom:20px;'>
<p style='color:#ffaa00; font-weight:800; font-size:15px; letter-spacing:3px; margin:0;'>
HISTORICO 2026 - EVOLUCION MENSUAL POR TIPO DE CNT</p>
<p style='color:#94a3b8; font-size:11px; margin:4px 0 0 0;'>
Promedio de mercado, mejor oferta y target -15% por mes y tipo de contenedor</p>
</div>""", unsafe_allow_html=True)
                rows_hist = []
                meses_ord = df_fl_2026.drop_duplicates('_mes_num').sort_values('_mes_num')[['_mes_num','_mes_label']].values.tolist()
                for mes_num, mes_lbl in meses_ord:
                    df_mes = df_fl_2026[df_fl_2026['_mes_num'] == mes_num]
                    for cnt in TIPOS_CNT:
                        df_c = df_mes[df_mes['_cnt'] == cnt]
                        if df_c.empty: continue
                        prom   = df_c['_flete'].mean()
                        minimo = df_c['_flete'].min()
                        target = prom * TARGET_PCT
                        dif    = round(prom - minimo, 0)
                        desv   = round((minimo - prom) / prom * 100, 1) if prom > 0 else None
                        vs_tgt = round((minimo - target) / target * 100, 1) if target > 0 else None
                        rows_hist.append({
                            'Mes'           : mes_lbl,
                            '_mes_num'      : mes_num,
                            'Tipo CNT'      : cnt,
                            'Prom. Mercado' : round(prom, 0),
                            'Target -15%'   : round(target, 0),
                            'Mejor Oferta'  : round(minimo, 0),
                            'Dif. USD'      : round(dif, 0),
                            '% Desvio'      : f"{desv:+.1f}%" if desv is not None else "SD",
                            'Vs Target'     : f"{vs_tgt:+.1f}%" if vs_tgt is not None else "SD",
                        })
                df_hist = pd.DataFrame(rows_hist)
                if not df_hist.empty:
                    meses_disponibles = ["TODOS"] + [m for _, m in meses_ord]
                    cnts_disponibles  = ["TODOS"] + TIPOS_CNT
                    fh1, fh2 = st.columns(2)
                    with fh1:
                        mes_sel_hist = st.selectbox("MES:", meses_disponibles, key="hist_mes_sel")
                    with fh2:
                        cnt_sel_hist = st.selectbox("TIPO CNT:", cnts_disponibles, key="hist_cnt_sel")
                    df_hist_fil = df_hist.copy()
                    if mes_sel_hist != "TODOS":
                        df_hist_fil = df_hist_fil[df_hist_fil['Mes'] == mes_sel_hist]
                    if cnt_sel_hist != "TODOS":
                        df_hist_fil = df_hist_fil[df_hist_fil['Tipo CNT'] == cnt_sel_hist]
                    if not df_hist_fil.empty:
                        avg_prom  = df_hist_fil['Prom. Mercado'].mean()
                        avg_mejor = df_hist_fil['Mejor Oferta'].mean()
                        avg_tgt   = df_hist_fil['Target -15%'].mean()
                        avg_dif   = df_hist_fil['Dif. USD'].mean()
                        kh1, kh2, kh3, kh4 = st.columns(4)
                        color_dif = "#00ff88" if avg_dif > 0 else "#ff4b4b"
                        for col_k, valor, label, color in [
                            (kh1, f"USD {int(avg_prom):,}",  "PROM. MERCADO", "#f8fafc"),
                            (kh2, f"USD {int(avg_mejor):,}", "MEJOR OFERTA",  "#00ff88"),
                            (kh3, f"USD {int(avg_tgt):,}",   "TARGET -15%",   "#ffaa00"),
                            (kh4, f"USD {int(avg_dif):,}",   "AHORRO PROM.",  color_dif),
                        ]:
                            col_k.markdown(f"""
<div style='text-align:center; padding:12px 8px; background:rgba(255,255,255,0.02);
border-radius:12px; border-top:2px solid {color};'>
<p style='color:#94a3b8; font-size:10px; letter-spacing:1px; margin:0 0 4px 0;'>{label}</p>
<p style='color:{color}; font-size:18px; font-weight:800; margin:0;'>{valor}</p>
</div>""", unsafe_allow_html=True)
                        st.markdown("<br>", unsafe_allow_html=True)
                    st.dataframe(
                        df_hist_fil.drop(columns=['_mes_num']),
                        use_container_width=True, hide_index=True,
                        column_config={
                            'Mes'          : st.column_config.TextColumn("Mes"),
                            'Tipo CNT'     : st.column_config.TextColumn("Tipo CNT"),
                            'Prom. Mercado': st.column_config.NumberColumn("Prom. Mercado", format="$ %,.0f"),
                            'Target -15%'  : st.column_config.NumberColumn("Target -15%", format="$ %,.0f"),
                            'Mejor Oferta' : st.column_config.NumberColumn("Mejor Oferta", format="$ %,.0f"),
                            'Dif. USD'     : st.column_config.NumberColumn("Dif. USD", format="$ %,.0f"),
                            '% Desvio'     : st.column_config.TextColumn("% Desvio"),
                            'Vs Target'    : st.column_config.TextColumn("Vs Target"),
                        }
                    )
                    st.markdown("<br>", unsafe_allow_html=True)
                    df_hist_graf = df_hist.copy()
                    if cnt_sel_hist != "TODOS":
                        df_hist_graf = df_hist_graf[df_hist_graf['Tipo CNT'] == cnt_sel_hist]
                    titulo_graf = f"Evolucion de Costos - {'Todos los tipos CNT' if cnt_sel_hist == 'TODOS' else cnt_sel_hist}"
                    fig_evol = px.line(
                        df_hist_graf.sort_values(['_mes_num','Tipo CNT']),
                        x='Mes', y='Prom. Mercado', color='Tipo CNT',
                        markers=True, color_discrete_map=COLORES_CNT,
                        labels={'Prom. Mercado': 'USD Promedio de Mercado', 'Mes': ''},
                        title=titulo_graf
                    )
                    fig_evol.update_traces(line_width=3, marker_size=10)
                    fig_evol.update_layout(
                        height=480, paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)',
                        font=dict(size=12, family='Outfit, sans-serif', color='#94a3b8'),
                        title_font_color='#ffaa00', title_font_size=14,
                        legend=dict(orientation='h', yanchor='bottom', y=1.02, xanchor='right', x=1, title_text=''),
                        xaxis=dict(showgrid=False, tickangle=-30),
                        yaxis=dict(showgrid=True, gridcolor='rgba(255,255,255,0.07)', title='USD'),
                        margin=dict(l=20, r=20, t=80, b=40)
                    )
                    if mes_sel_hist != "TODOS":
                        fig_evol.add_vrect(
                            x0=mes_sel_hist, x1=mes_sel_hist,
                            fillcolor="rgba(255,255,255,0.08)",
                            layer="below", line_width=0,
                        )
                    st.plotly_chart(fig_evol, use_container_width=True)
        except Exception as e:
            st.error(f"Error en Fletes y Gastos: {e}")
            import traceback
            st.code(traceback.format_exc())
# --- SOLAPA 5: PROYECCIÓN SEMANAL ETD ---
    with tabs[4]:
        st.markdown("""
<div style='text-align:center; padding:25px; background:linear-gradient(135deg,rgba(0,168,255,0.08),rgba(0,255,136,0.04));
border-radius:20px; border:1px solid rgba(0,168,255,0.2); margin-bottom:30px;'>
<h2 style='color:#00a8ff; font-weight:900; letter-spacing:6px; margin:0; font-size:26px;'>PROYECCIÓN SEMANAL ETD</h2>
<p style='color:#94a3b8; margin:8px 0 0 0; font-size:13px; letter-spacing:2px;'>CARGA MARÍTIMA ARGENTINA · PRÓXIMAS SEMANAS DE ZARPE</p>
</div>""", unsafe_allow_html=True)
        try:
            def find_col_proy(df, keywords):
                for kw in keywords:
                    matches = [c for c in df.columns if kw.upper() in str(c).upper()]
                    if matches: return matches[0]
                return None
            col_etd_proy    = find_col_proy(df, ['ETD']) or df.columns[23]
            col_mod_proy    = find_col_proy(df, ['MODALIDAD DE COSTEO', 'MODALIDAD COSTEO']) or df.columns[68]
            col_puerto_proy = find_col_proy(df, ['PUERTO DE SALIDA', 'PUERTO SALIDA', 'PUERTO']) or df.columns[41]
            col_pais_proy   = df.columns[18]

            df_proy = df.copy()
            df_proy['_m3'] = pd.to_numeric(df_proy['M3 Total'], errors='coerce').fillna(0)
            mask_pais = df_proy[col_pais_proy].astype(str).str.strip().str.upper() == 'ARGENTINA'
            mask_mod  = (
                df_proy[col_mod_proy].astype(str).str.strip().str.upper().str.startswith('BARCO') |
                df_proy[col_mod_proy].astype(str).str.strip().str.upper().str.contains('COSTO HIBRIDO PUERTO ZFLP', na=False)
            )
            df_proy = df_proy[mask_pais & mask_mod].copy()
            df_proy['_etd_dt'] = pd.to_datetime(df_proy[col_etd_proy], dayfirst=True, errors='coerce')
            df_proy = df_proy[df_proy['_etd_dt'].notna() & (df_proy['_etd_dt'] >= hoy)].copy()
            df_proy['_semana_inicio'] = df_proy['_etd_dt'].dt.to_period('W').apply(lambda p: p.start_time)
            df_proy['_mes_num']       = df_proy['_etd_dt'].dt.month
            df_proy['_mes_label']     = df_proy['_etd_dt'].dt.strftime('%B %Y').str.upper()
            df_proy['_puerto']        = df_proy[col_puerto_proy].astype(str).str.strip().str.upper().fillna('SIN DEFINIR')

            if df_proy.empty:
                st.warning("No hay carga futura proyectada.")
            else:
                meses_proy    = df_proy.drop_duplicates('_mes_num').sort_values('_mes_num')[['_mes_num','_mes_label']].values.tolist()
                opciones_proy = {lbl: num for num, lbl in meses_proy}
                mes_actual  = hoy.month
                default_lbl = next((lbl for lbl, num in opciones_proy.items() if num == mes_actual),
                                   list(opciones_proy.keys())[0])
                default_idx = list(opciones_proy.keys()).index(default_lbl)

                col_sp, _ = st.columns([2, 3])
                with col_sp:
                    mes_proy_lbl = st.selectbox("📅 SELECCIONAR MES:", list(opciones_proy.keys()),
                                                index=default_idx, key="proy_mes_sel")
                mes_proy_num = opciones_proy[mes_proy_lbl]
                df_mes = df_proy[df_proy['_mes_num'] == mes_proy_num].copy()

                total_m3   = df_mes['_m3'].sum()
                total_cntr = round(total_m3 / 60)
                total_so   = df_mes['SO'].nunique() if 'SO' in df_mes.columns else 0
                total_sem  = df_mes['_semana_inicio'].nunique()

                # ── KPI CARDS ──────────────────────────────────────────
                st.markdown("<br>", unsafe_allow_html=True)
                k1, k2, k3, k4 = st.columns(4)
                with k1:
                    st.markdown(f"""
<div style='text-align:center; padding:28px 16px;
background:linear-gradient(145deg,rgba(0,168,255,0.1),rgba(0,168,255,0.03));
border-radius:20px; border:1px solid rgba(0,168,255,0.2);'>
<p style='color:#64748b; font-size:11px; letter-spacing:3px; margin:0 0 10px 0; text-transform:uppercase;'>Contenedores estimados</p>
<p style='color:#00a8ff; font-size:72px; font-weight:900; margin:0; line-height:1; letter-spacing:-3px;'>{int(total_cntr)}</p>
<p style='color:#475569; font-size:12px; margin:8px 0 0 0;'>CNTRS 40\'HC · {mes_proy_lbl}</p>
</div>""", unsafe_allow_html=True)
                with k2:
                    st.markdown(f"""
<div style='text-align:center; padding:28px 16px;
background:linear-gradient(145deg,rgba(0,255,136,0.07),rgba(0,255,136,0.02));
border-radius:20px; border:1px solid rgba(0,255,136,0.15);'>
<p style='color:#64748b; font-size:11px; letter-spacing:3px; margin:0 0 10px 0; text-transform:uppercase;'>Volumen total</p>
<p style='color:#00ff88; font-size:72px; font-weight:900; margin:0; line-height:1; letter-spacing:-3px;'>{int(round(total_m3)):,}</p>
<p style='color:#475569; font-size:12px; margin:8px 0 0 0;'>M3 · {mes_proy_lbl}</p>
</div>""", unsafe_allow_html=True)
                with k3:
                    st.markdown(f"""
<div style='text-align:center; padding:28px 16px;
background:rgba(255,255,255,0.03); border-radius:20px; border:1px solid rgba(255,255,255,0.07);'>
<p style='color:#64748b; font-size:11px; letter-spacing:3px; margin:0 0 10px 0; text-transform:uppercase;'>Órdenes de compra</p>
<p style='color:#f8fafc; font-size:72px; font-weight:900; margin:0; line-height:1; letter-spacing:-3px;'>{total_so}</p>
<p style='color:#475569; font-size:12px; margin:8px 0 0 0;'>SOs con zarpe en {mes_proy_lbl}</p>
</div>""", unsafe_allow_html=True)
                with k4:
                    st.markdown(f"""
<div style='text-align:center; padding:28px 16px;
background:rgba(255,255,255,0.03); border-radius:20px; border:1px solid rgba(255,255,255,0.07);'>
<p style='color:#64748b; font-size:11px; letter-spacing:3px; margin:0 0 10px 0; text-transform:uppercase;'>Semanas activas</p>
<p style='color:#f8fafc; font-size:72px; font-weight:900; margin:0; line-height:1; letter-spacing:-3px;'>{total_sem}</p>
<p style='color:#475569; font-size:12px; margin:8px 0 0 0;'>Semanas con carga en {mes_proy_lbl}</p>
</div>""", unsafe_allow_html=True)

                # ── GRÁFICO: LÍNEA DE CONTENEDORES POR SEMANA ──────────
                st.markdown("<br>", unsafe_allow_html=True)
                st.markdown("""
<div style='border-bottom:1px solid rgba(0,168,255,0.15); padding-bottom:8px; margin-bottom:24px;'>
<span style='color:#00a8ff; font-size:12px; font-weight:800; letter-spacing:4px; text-transform:uppercase;'>EVOLUCIÓN DE CONTENEDORES POR SEMANA</span>
<span style='color:#475569; font-size:11px; margin-left:14px;'>estimado: 1 contenedor = 60 M3</span>
</div>""", unsafe_allow_html=True)

                df_linea = df_mes.groupby('_semana_inicio')['_m3'].sum().reset_index()
                df_linea['Semana'] = df_linea['_semana_inicio'].apply(
                    lambda d: d.strftime('%d/%m') + ' — ' + (d + pd.Timedelta(days=6)).strftime('%d/%m')
                )
                df_linea['CNTRS'] = (df_linea['_m3'] / 60).round(0).astype(int)

                fig = px.line(
                    df_linea, x='Semana', y='CNTRS',
                    markers=True,
                    text='CNTRS',
                    labels={'CNTRS': 'Contenedores estimados', 'Semana': ''},
                )
                fig.update_traces(
                    line=dict(color='#00a8ff', width=3),
                    marker=dict(size=12, color='#00a8ff', line=dict(color='#ffffff', width=2)),
                    texttemplate='<b>%{text}</b> CNTR',
                    textposition='top center',
                    textfont=dict(size=13, color='#f8fafc', family='Outfit, sans-serif'),
                    fill='tozeroy',
                    fillcolor='rgba(0,168,255,0.08)',
                )
                fig.update_layout(
                    height=420,
                    paper_bgcolor='rgba(0,0,0,0)',
                    plot_bgcolor='rgba(0,0,0,0)',
                    font=dict(family='Outfit, sans-serif', color='#94a3b8', size=13),
                    showlegend=False,
                    xaxis=dict(
                        showgrid=False,
                        tickfont=dict(size=13, color='#94a3b8'),
                        title='',
                    ),
                    yaxis=dict(
                        showgrid=True,
                        gridcolor='rgba(255,255,255,0.07)',
                        title='Contenedores estimados',
                        tickfont=dict(size=12),
                        rangemode='tozero',
                    ),
                    margin=dict(l=20, r=20, t=40, b=20),
                )
                st.plotly_chart(fig, use_container_width=True)

                # ── CARDS POR SEMANA (mismo tamaño fijo, números redondos) ──
                st.markdown("""
<div style='border-bottom:1px solid rgba(255,255,255,0.08); padding-bottom:8px; margin-bottom:24px;'>
<span style='color:#94a3b8; font-size:12px; font-weight:800; letter-spacing:4px; text-transform:uppercase;'>DESGLOSE POR SEMANA Y PUERTO</span>
</div>""", unsafe_allow_html=True)

                COLORES_PORTO = ['#00a8ff','#00ff88','#ffaa00','#ff4b4b','#a855f7','#06b6d4','#f97316']
                puertos_orden = df_mes.groupby('_puerto')['_m3'].sum().sort_values(ascending=False).index.tolist()
                semanas = sorted(df_mes['_semana_inicio'].unique())
                CARD_H = '320px'

                for fila_start in range(0, len(semanas), 4):
                    fila_sems = semanas[fila_start:fila_start+4]
                    # Siempre 4 columnas para coherencia
                    cols_fila = st.columns(4)
                    for idx in range(4):
                        with cols_fila[idx]:
                            if idx >= len(fila_sems):
                                # columna vacía para mantener alineación
                                st.markdown("<div></div>", unsafe_allow_html=True)
                                continue
                            sem = fila_sems[idx]
                            sem_fin   = sem + pd.Timedelta(days=6)
                            sem_label = sem.strftime('%d/%m') + ' AL ' + sem_fin.strftime('%d/%m')
                            df_sem    = df_mes[df_mes['_semana_inicio'] == sem]
                            m3_sem    = df_sem['_m3'].sum()
                            cntr_sem  = round(m3_sem / 60)   # entero
                            so_sem    = df_sem['SO'].nunique() if 'SO' in df_sem.columns else 0

                            puertos_html = ''
                            for pi, puerto in enumerate(puertos_orden):
                                m3_p = df_sem[df_sem['_puerto'] == puerto]['_m3'].sum()
                                if m3_p == 0: continue
                                pct_p  = round(m3_p / m3_sem * 100) if m3_sem > 0 else 0
                                cntr_p = round(m3_p / 60)   # entero
                                col_p  = COLORES_PORTO[pi % len(COLORES_PORTO)]
                                puertos_html += f"""
<div style='margin-bottom:9px;'>
<div style='display:flex; justify-content:space-between; align-items:center; margin-bottom:3px;'>
<p style='color:#94a3b8; font-size:10px; font-weight:600; margin:0;
white-space:nowrap; overflow:hidden; text-overflow:ellipsis; max-width:110px;'>{puerto}</p>
<p style='color:{col_p}; font-size:11px; font-weight:800; margin:0;'>{cntr_p} CNTR</p>
</div>
<div style='height:4px; background:rgba(255,255,255,0.06); border-radius:2px;'>
<div style='height:4px; width:{pct_p}%; background:{col_p}; border-radius:2px;'></div>
</div>
</div>"""

                            st.markdown(f"""
<div style='background:rgba(255,255,255,0.03); border-radius:16px;
border:1px solid rgba(255,255,255,0.08); padding:20px; margin-bottom:16px;
border-top:4px solid #00a8ff; height:{CARD_H}; box-sizing:border-box;
display:flex; flex-direction:column; justify-content:space-between;'>
<div>
    <p style='color:#00a8ff; font-size:11px; font-weight:800; letter-spacing:2px;
    margin:0 0 14px 0; text-transform:uppercase;'>📅 {sem_label}</p>
    <div style='display:flex; justify-content:space-between; align-items:flex-end; margin-bottom:14px;'>
        <div>
            <p style='color:#64748b; font-size:9px; letter-spacing:1px; margin:0 0 2px 0;'>CONTENEDORES</p>
            <p style='color:#00a8ff; font-size:42px; font-weight:900; margin:0; line-height:1;'>{int(cntr_sem)}</p>
        </div>
        <div style='text-align:right;'>
            <p style='color:#64748b; font-size:9px; letter-spacing:1px; margin:0 0 2px 0;'>M3</p>
            <p style='color:#f8fafc; font-size:20px; font-weight:700; margin:0; line-height:1;'>{int(round(m3_sem)):,}</p>
            <p style='color:#475569; font-size:10px; margin:4px 0 0 0;'>{so_sem} SOs</p>
        </div>
    </div>
</div>
<div style='border-top:1px solid rgba(255,255,255,0.06); padding-top:12px; flex:1; overflow:hidden;'>
{puertos_html}
</div>
</div>""", unsafe_allow_html=True)

        except Exception as e:
            st.error(f"Error en Proyeccion Semanal ETD: {e}")
            import traceback
            st.code(traceback.format_exc())
 # --- SOLAPA 6: INDICADORES (SLA & CONSOLIDACIÓN) ---
    with tabs[5]:
        st.markdown("<div style='text-align:center; padding: 20px; background: rgba(0, 255, 136, 0.05); border-radius: 20px; margin: 30px 0;'><h2 style='color:#00ff88; font-weight:800; letter-spacing:5px; margin:0;'>INDICADORES DE CONSOLIDACIÓN Y SLA</h2><p style='color:#64748b; font-size:11px; letter-spacing:2px; margin:10px 0 0 0;'>📊 DÍAS MOSTRADOS: MEDIANA · SLA MONO: 15d (ene-feb) / 10d (resto) · SLA CONSOLIDADO: 25d</p></div>", unsafe_allow_html=True)
        try:
            url_hi = f"{base_url}/export?format=csv&gid=32771816&nocache={time.time()}"
            @st.cache_data(ttl=60)
            def load_hi_vfinal(u): return pd.read_csv(u, engine='python')
            df_hi = load_hi_vfinal(url_hi)
            df_hi.columns = [str(c).strip() for c in df_hi.columns]
            df_hi['ETD_DT'] = pd.to_datetime(df_hi.iloc[:, 11], dayfirst=True, errors='coerce')
            mask_anio_etd = df_hi['ETD_DT'].dt.year == 2026
            mask_anio_col = df_hi.iloc[:, 25].astype(str).str.strip() == '2026'
            df_2026 = df_hi[mask_anio_etd | mask_anio_col].copy()
            df_2026.loc[df_2026['ETD_DT'].isna(), 'ETD_DT'] = pd.to_datetime(
                df_2026.loc[df_2026['ETD_DT'].isna(), df_hi.columns[11]], dayfirst=True, errors='coerce'
            )
            if not df_2026.empty:
                df_2026['Mes'] = df_2026['ETD_DT'].dt.month
                mask_sin_mes = df_2026['Mes'].isna()
                if mask_sin_mes.any():
                    df_2026.loc[mask_sin_mes, 'ETD_DT'] = pd.to_datetime(
                        df_2026.loc[mask_sin_mes, df_hi.columns[11]], dayfirst=True, errors='coerce'
                    )
                    df_2026.loc[mask_sin_mes, 'Mes'] = df_2026.loc[mask_sin_mes, 'ETD_DT'].dt.month
                df_2026 = df_2026[df_2026['Mes'].notna()].copy()
                df_2026['Mes'] = df_2026['Mes'].astype(int)
                col_tipo_carga_hi = df_hi.columns[5]
                df_mar = df_2026[~df_2026[col_tipo_carga_hi].astype(str).str.upper().str.contains('AVION|COURRIER', na=False)].copy()
                meses_dict = {1:"Enero", 2:"Febrero", 3:"Marzo", 4:"Abril", 5:"Mayo", 6:"Junio", 7:"Julio", 8:"Agosto", 9:"Septiembre", 10:"Octubre", 11:"Noviembre", 12:"Diciembre"}
                df_mar['Mes_Nombre'] = df_mar['Mes'].map(meses_dict)
                col_mono_hi  = df_hi.columns[24]
                col_puerto_hi = df_hi.columns[4]
                col_cons_hi  = df_hi.columns[32]
                def clean_n_hi(val):
                    if pd.isna(val) or str(val).strip() in ['', 'nan']: return 0.0
                    try:
                        s = str(val).replace(',', '.').replace(' ', '').strip()
                        return pd.to_numeric(s, errors='coerce')
                    except: return 0.0
                df_mar[col_cons_hi] = df_mar[col_cons_hi].apply(clean_n_hi).fillna(0.0).round(0)
                @st.dialog("🚢 DETALLE POR PUERTO Y SLA", width="large")
                def show_detalle_mes(df_sub, mes_lbl, mode="mixed"):
                    st.markdown(f"### Análisis {mes_lbl.upper()}")
                    res_p = df_sub.groupby(col_puerto_hi).agg({df_hi.columns[0]: 'count', col_cons_hi: 'median'}).reset_index()
                    p_rows = []
                    for _, r in res_p.iterrows():
                        df_p_t = df_sub[df_sub[col_puerto_hi] == r[col_puerto_hi]].copy()
                        tp_p = r[df_hi.columns[0]]
                        def check_sla(row):
                            days = row[col_cons_hi]
                            is_mono = "MONOPROVEEDOR" in str(row[col_mono_hi]).upper()
                            try:
                                mes_num = int(row['Mes'])
                            except:
                                mes_num = 3
                            limit = (15 if mes_num <= 2 else 10) if is_mono else 25
                            return days <= limit
                        df_p_t['SLA_OK'] = df_p_t.apply(check_sla, axis=1)
                        pct_sla = int((len(df_p_t[df_p_t['SLA_OK']]) / tp_p) * 100) if tp_p > 0 else 0
                        row_data = {"Puerto": r[col_puerto_hi], "Embs": tp_p, "Días Avg": int(round(r[col_cons_hi])), "% Cumple SLA": f"{pct_sla}%", "% Fuera SLA": f"{100 - pct_sla}%", "TOTAL": "100%"}
                        if mode == "mixed":
                            cm_p = len(df_p_t[df_p_t[col_mono_hi].astype(str).str.upper().str.contains('MONOPROVEEDOR', na=False)])
                            row_data["% Mono"] = f"{int((cm_p/tp_p)*100)}%"
                            row_data["% Cons"] = f"{int((1-(cm_p/tp_p))*100)}%"
                        p_rows.append(row_data)
                    st.dataframe(pd.DataFrame(p_rows).sort_values("Embs", ascending=False), use_container_width=True, hide_index=True)
                st.markdown("<div style='background: rgba(0, 168, 255, 0.05); padding: 15px 25px; border-radius: 20px; border: 1px solid rgba(0, 168, 255, 0.2); margin: 15px 0;'><h3 style='color:#00a8ff; margin:0; text-align:center; letter-spacing:5px; text-transform:uppercase; font-weight:900;'>RESUMEN MES CERRADO (MARÍTIMOS 2026)</h3></div>", unsafe_allow_html=True)
                thc = st.columns([1.5, 1, 1.2, 1, 1, 0.8])
                for i, h in enumerate(["MES ETD", "EMBS", "MEDIANA", "% MONO", "% CONS", "DETALLE"]):
                    thc[i].markdown(f"<p style='color:#94a3b8; font-size:11px; font-weight:800; text-align:center;'>{h}</p>", unsafe_allow_html=True)
                res_mensual = df_mar.groupby(['Mes', 'Mes_Nombre']).agg({df_hi.columns[0]: 'count', col_cons_hi: 'median'}).reset_index()
                for _, row in res_mensual.iterrows():
                    df_m_temp = df_mar[df_mar['Mes'] == row['Mes']].copy()
                    tot_m = len(df_m_temp)
                    df_m_mono = df_m_temp[df_m_temp[col_mono_hi].astype(str).str.upper().str.contains('MONOPROVEEDOR', na=False)]
                    p_mono = (len(df_m_mono) / tot_m) if tot_m > 0 else 0
                    tr1, tr2, tr3, tr4, tr5, tr6 = st.columns([1.5, 1, 1.2, 1, 1, 0.8])
                    tr1.markdown(f"<p style='font-weight:700; color:#fff; text-align:center; margin-top:5px;'>{row['Mes_Nombre'].upper()}</p>", unsafe_allow_html=True)
                    tr2.markdown(f"<p style='text-align:center; margin-top:5px;'>{tot_m}</p>", unsafe_allow_html=True)
                    tr3.markdown(f"<p style='color:#00ff88; font-weight:700; text-align:center; margin-top:5px;'>{int(round(row[col_cons_hi]))}d</p>", unsafe_allow_html=True)
                    tr4.markdown(f"<p style='color:#00a8ff; text-align:center; margin-top:5px;'>{int(p_mono*100)}%</p>", unsafe_allow_html=True)
                    tr5.markdown(f"<p style='color:#94a3b8; text-align:center; margin-top:5px;'>{int((1-p_mono)*100)}%</p>", unsafe_allow_html=True)
                    with tr6:
                        if st.button("🔍 VER", key=f"btn_res_{row['Mes']}", use_container_width=True):
                            show_detalle_mes(df_m_temp, row['Mes_Nombre'], mode="mixed")
                st.markdown("<br><div style='background: rgba(0, 168, 255, 0.05); padding: 15px; border-radius: 12px; border-left: 5px solid #00a8ff; margin-bottom:15px;'><h4 style='color:#00a8ff; margin:0; letter-spacing:2px; font-size:16px;'>1. SOLAMENTE MONOPROVEEDOR (MARÍTIMOS 2026)</h4></div>", unsafe_allow_html=True)
                df_mono_v4 = df_mar[df_mar[col_mono_hi].astype(str).str.upper().str.contains('MONOPROVEEDOR', na=False)].copy()
                if not df_mono_v4.empty:
                    mhc = st.columns([1.5, 1, 1.2, 2, 0.8])
                    for i, h in enumerate(["MES ETD", "EMBS", "MEDIANA", "CUMPLIMIENTO SLA", "DETALLE"]):
                        mhc[i].markdown(f"<p style='color:#94a3b8; font-size:11px; font-weight:800; text-align:center;'>{h}</p>", unsafe_allow_html=True)
                    res_m = df_mono_v4.groupby(['Mes', 'Mes_Nombre']).agg({df_hi.columns[0]: 'count', col_cons_hi: 'median'}).reset_index()
                    for _, rm in res_m.iterrows():
                        df_sub_m = df_mono_v4[df_mono_v4['Mes'] == rm['Mes']].copy()
                        lim_m = 15 if rm['Mes'] <= 2 else 10
                        pct_m = int((len(df_sub_m[df_sub_m[col_cons_hi] <= lim_m]) / len(df_sub_m)) * 100) if len(df_sub_m) > 0 else 0
                        mr1, mr2, mr3, mr4, mr5 = st.columns([1.5, 1, 1.2, 2, 0.8])
                        mr1.markdown(f"<p style='font-weight:700; color:#fff; text-align:center;'>{rm['Mes_Nombre'].upper()}</p>", unsafe_allow_html=True)
                        mr2.markdown(f"<p style='text-align:center;'>{int(rm.iloc[2])}</p>", unsafe_allow_html=True)
                        mr3.markdown(f"<p style='color:#00ff88; font-weight:700; text-align:center;'>{int(round(rm.iloc[3]))}d</p>", unsafe_allow_html=True)
                        mr4.markdown(f"<div style='background:rgba(0,168,255,0.1); border-radius:10px; text-align:center; padding:2px; border:1px solid rgba(0,168,255,0.2);'><span style='color:#00a8ff; font-weight:800; font-size:12px;'>SLA {pct_m}%</span></div>", unsafe_allow_html=True)
                        with mr5:
                            if st.button("🔍 VER", key=f"btn_m_v4_{rm['Mes']}", use_container_width=True):
                                show_detalle_mes(df_sub_m, f"MONO - {rm['Mes_Nombre']}", mode="specific")
                st.markdown("<br><div style='background: rgba(0, 255, 136, 0.05); padding: 15px; border-radius: 12px; border-left: 5px solid #00ff88; margin-bottom:15px;'><h4 style='color:#00ff88; margin:0; letter-spacing:2px; font-size:16px;'>2. SOLAMENTE CONSOLIDADO (MARÍTIMOS 2026)</h4></div>", unsafe_allow_html=True)
                df_cons_v4 = df_mar[~df_mar[col_mono_hi].astype(str).str.upper().str.contains('MONOPROVEEDOR', na=False)].copy()
                if not df_cons_v4.empty:
                    chc = st.columns([1.5, 1, 1.2, 2, 0.8])
                    for i, h in enumerate(["MES ETD", "EMBS", "MEDIANA", "CUMPLIMIENTO SLA", "DETALLE"]):
                        chc[i].markdown(f"<p style='color:#94a3b8; font-size:11px; font-weight:800; text-align:center;'>{h}</p>", unsafe_allow_html=True)
                    res_c = df_cons_v4.groupby(['Mes', 'Mes_Nombre']).agg({df_hi.columns[0]: 'count', col_cons_hi: 'median'}).reset_index()
                    for _, rc in res_c.iterrows():
                        df_sub_c = df_cons_v4[df_cons_v4['Mes'] == rc['Mes']].copy()
                        pct_c = int((len(df_sub_c[df_sub_c[col_cons_hi] <= 25]) / len(df_sub_c)) * 100) if len(df_sub_c) > 0 else 0
                        cr1, cr2, cr3, cr4, cr5 = st.columns([1.5, 1, 1.2, 2, 0.8])
                        cr1.markdown(f"<p style='font-weight:700; color:#fff; text-align:center;'>{rc['Mes_Nombre'].upper()}</p>", unsafe_allow_html=True)
                        cr2.markdown(f"<p style='text-align:center;'>{int(rc.iloc[2])}</p>", unsafe_allow_html=True)
                        cr3.markdown(f"<p style='color:#00ff88; font-weight:700; text-align:center;'>{int(round(rc.iloc[3]))}d</p>", unsafe_allow_html=True)
                        cr4.markdown(f"<div style='background:rgba(0,255,136,0.1); border-radius:10px; text-align:center; padding:2px; border:1px solid rgba(0,255,136,0.2);'><span style='color:#00ff88; font-weight:800; font-size:12px;'>SLA {pct_c}%</span></div>", unsafe_allow_html=True)
                        with cr5:
                            if st.button("🔍 VER", key=f"btn_c_v4_{rc['Mes']}", use_container_width=True):
                                show_detalle_mes(df_sub_c, f"CONS - {rc['Mes_Nombre']}", mode="specific")
            else:
                st.warning("No se encontraron registros marítimos para el año 2026.")
        except Exception as e:
            st.error(f"Error en Indicadores: {e}")
    # --- SOLAPA 7: ALERTAS ESTRATÉGICAS ---
    with tabs[6]:
        try:
            url_re = f"{base_url}/export?format=csv&gid=276804813"
            @st.cache_data(ttl=60)
            def load_alertas_data(u):
                return pd.read_csv(u, engine='python', on_bad_lines='skip')
            df_re = load_alertas_data(url_re)
            df_re.columns = [str(c).strip() for c in df_re.columns]
            def find_col(df, keywords, fallback_idx):
                for kw in keywords:
                    matches = [c for c in df.columns if kw.upper() in str(c).upper()]
                    if matches: return matches[0]
                return df.columns[fallback_idx]
            col_emb_re   = find_col(df_re, ['EMBARQUE'], 0)
            col_resp     = find_col(df_re, ['RESPONSABLE DE LA CARGA', 'RESPONSABLE'], 33)
            col_fwd      = find_col(df_re, ['FORWARDER', 'AGENTE'], 6)
            col_inst_re  = find_col(df_re, ['INSTRUCCION', 'INSTRUCCIÓN'], 7)
            col_etd_ok   = df_re.columns[10] if len(df_re.columns) > 10 else find_col(df_re, ['ETD OK FFWW'], 10)
            col_etd_re   = df_re.columns[12] if len(df_re.columns) > 12 else find_col(df_re, ['ETD'], 12)
            col_pack_min = find_col(df_re, ['PACKEO MIN', 'P MIN', 'MIN PACK'], 18)
            col_pack_max = find_col(df_re, ['PACKEO MAX', 'P MAX', 'MAX PACK'], 19)
            col_draft_bl = df_re.columns[35] if len(df_re.columns) > 35 else find_col(df_re, ['DRAFT BL'], 35)
            col_pack_lst = df_re.columns[36] if len(df_re.columns) > 36 else find_col(df_re, ['PACKING LIST'], 36)
            col_impo2    = df_re.columns[39] if len(df_re.columns) > 39 else find_col(df_re, ['PASAR A IMPO'], 39)
            col_t_consol = df_re.columns[29] if len(df_re.columns) > 29 else find_col(df_re, ['TIEMPO TOTAL', 'CONSOLIDACION'], 29)
            df_re['DT_Inst']       = pd.to_datetime(df_re[col_inst_re],  dayfirst=True, errors='coerce')
            df_re['DT_ETD']        = pd.to_datetime(df_re[col_etd_re],   dayfirst=True, errors='coerce')
            df_re['DT_PMin']       = pd.to_datetime(df_re[col_pack_min], dayfirst=True, errors='coerce')
            df_re['DT_PMax']       = pd.to_datetime(df_re[col_pack_max], dayfirst=True, errors='coerce')
            df_re['ETD_OK']        = df_re[col_etd_ok].astype(str).str.upper().str.strip() == "OK"
            df_re['Dias_Esp']      = (hoy - df_re['DT_Inst']).dt.days
            df_re['Rango_Pack']    = (df_re['DT_PMax'] - df_re['DT_PMin']).dt.days
            df_re['Dias_ETD_venc'] = (hoy - df_re['DT_ETD']).dt.days
            TIPOS_MARITIMO = ['20 ST', '40 ST', '40 HQ', '40 NOR']
            col_tipo_carga = find_col(df_re, ['TIPO CARGA', 'TIPO DE CARGA'], 5)
            col_emb_pc    = df.columns[16]
            col_rank_pc   = df.columns[1]
            col_puerto_pc = df.columns[41]
            col_n_inv_pc  = df.columns[29]
            col_inst_pc   = find_col(df, ['INSTRUCCION', 'INSTRUCCIÓN'], 20)
            col_mono_pc   = find_col(df, ['MONOPROVEEDOR'], 31)
            def find_sku_nuevo_col(df):
                for c in df.columns:
                    limpio = str(c).strip().replace('¿','').replace('?','').upper()
                    if 'SKU NUEVO' in limpio or 'SKU_NUEVO' in limpio:
                        return c
                if len(df.columns) > 111:
                    return df.columns[111]
                return None
            col_nuevo = find_sku_nuevo_col(df)
            col_mod_pc    = find_col(df, ['MODALIDAD DE COSTEO', 'MODALIDAD COSTEO'], 68)
            col_pais_pc   = find_col(df, ['PAIS DESTINO', 'PAÍS DESTINO'], 0)
            PUERTOS_DAVID = ['SHANGHAI', 'QINGDAO', 'TIANJIN', 'NINGBO']
            def asignar_analista(modalidad, es_mono, puerto):
                mod  = str(modalidad).strip().upper()
                mono = str(es_mono).strip().upper()
                prt  = str(puerto).strip().upper()
                es_barco  = mod.startswith('BARCO') or 'COSTO HIBRIDO PUERTO ZFLP' in mod
                es_avion  = mod.startswith('AVION') or mod.startswith('AVIÓN')
                if es_avion: return 'AZUL'
                if es_barco:
                    if mono in ['SI', 'SÍ', 'S']: return 'AGUSTIN'
                    else:
                        if any(p in prt for p in PUERTOS_DAVID): return 'DAVID'
                        else: return 'SOFIA'
                return 'SIN ASIGNAR'
            df_ni = df[
                df[col_inst_pc].isna() |
                df[col_inst_pc].astype(str).str.strip().isin(['', 'nan', 'SIN INSTRUCCION', 'sin instruccion'])
            ].copy()
            df_ni = df_ni[~df_ni.iloc[:, 39].astype(str).str.upper().str.contains('MUESTRA|MUESTRAS|REPUESTOS', na=False)]
            df_ni['Fecha_Prior_DT'] = pd.to_datetime(df.iloc[:, 99], dayfirst=True, errors='coerce')
            def filter_ni(row):
                is_mono = "SÍ" in str(row[col_mono_pc]).upper() or "SI" in str(row[col_mono_pc]).upper()
                return row['Fecha_Prior_DT'] <= hoy + timedelta(days=25 if is_mono else 10)
            df_a1 = df_ni[df_ni.apply(filter_ni, axis=1)].copy()
            def safe_rank(val):
                try: return float(str(val).replace('.', '').replace(',', '.').strip())
                except: return 999999
            df_a1['Rank_Num'] = df_a1[col_rank_pc].apply(safe_rank)
            df_a1['Analista'] = df_a1.apply(lambda r: asignar_analista(r[col_mod_pc], r[col_mono_pc], r[col_puerto_pc]), axis=1)
            df_a1['Top Ranking'] = df_a1['Rank_Num'].apply(lambda x: "🏆 SÍ" if x < 300 else "—")
            if col_nuevo:
                df_a1['SKU Nuevo'] = df_a1[col_nuevo].apply(lambda x: "✨ SÍ" if str(x).strip().upper() == 'SI' else "—")
            else:
                df_a1['SKU Nuevo'] = "—"
            def clean_num_consol(val):
                try: return float(str(val).replace(',', '.').replace(' ', '').strip())
                except: return 0.0
            df_re['T_Consol'] = df_re[col_t_consol].apply(clean_num_consol)
            col_mono_re = find_col(df_re, ['MONOPROVEEDOR'], 31)
            df_re['Es_Mono'] = df_re[col_mono_re].astype(str).str.strip().str.upper().isin(['SI', 'SÍ', 'S', 'MONOPROVEEDOR'])
            df_mar_re = df_re[
                df_re[col_tipo_carga].astype(str).str.strip().str.upper().isin([t.upper() for t in TIPOS_MARITIMO])
            ].copy()
            df_mar_re['DT_Inst']       = pd.to_datetime(df_mar_re[col_inst_re],  dayfirst=True, errors='coerce')
            df_mar_re['DT_ETD']        = pd.to_datetime(df_mar_re[col_etd_re],   dayfirst=True, errors='coerce')
            df_mar_re['DT_PMin']       = pd.to_datetime(df_mar_re[col_pack_min], dayfirst=True, errors='coerce')
            df_mar_re['DT_PMax']       = pd.to_datetime(df_mar_re[col_pack_max], dayfirst=True, errors='coerce')
            df_mar_re['ETD_OK']        = df_mar_re[col_etd_ok].astype(str).str.upper().str.strip() == "OK"
            df_mar_re['Dias_Esp']      = (hoy - df_mar_re['DT_Inst']).dt.days
            df_mar_re['Rango_Pack']    = (df_mar_re['DT_PMax'] - df_mar_re['DT_PMin']).dt.days
            df_mar_re['Dias_ETD_venc'] = (hoy - df_mar_re['DT_ETD']).dt.days
            df_mar_re['T_Consol']      = df_re.loc[df_mar_re.index, 'T_Consol'] if 'T_Consol' in df_re.columns else 0
            df_mar_re['Es_Mono']       = df_re.loc[df_mar_re.index, 'Es_Mono'] if 'Es_Mono' in df_re.columns else False
            etd_ok_vacio_re = df_mar_re[col_etd_ok].astype(str).str.strip().str.upper() != 'OK'
            fuera_sla = (
                (df_mar_re['Es_Mono'] & (df_mar_re['T_Consol'] > 7)) |
                (~df_mar_re['Es_Mono'] & (df_mar_re['T_Consol'] > 25))
            )
            col_destino_re = df_re.columns[3] if len(df_re.columns) > 3 else find_col(df_re, ['DESTINO', 'PAIS'], 3)
            solo_argentina = df_mar_re[col_destino_re].astype(str).str.strip().str.upper() == 'ARGENTINA'
            df_a1b = df_mar_re[
                etd_ok_vacio_re & fuera_sla & (df_mar_re['T_Consol'] > 0) & solo_argentina
            ].copy()
            df_a2 = df_mar_re[df_mar_re['Rango_Pack'].notna() & (df_mar_re['Rango_Pack'] > 7)].copy()
            col_etd_ok_pc = find_col(df, ['ETD OK FFWW', 'ETD OK'], 97)
            col_pais_dest = find_col(df, ['PAIS DESTINO', 'PAÍS DESTINO'], 0)
            def enrich_a2(row):
                emb    = str(row[col_emb_re]).strip().upper()
                df_emb = df[df[col_emb_pc].astype(str).str.strip().str.upper() == emb]
                if df_emb.empty: return pd.Series({'ETD OK FFWW': '—', 'País Destino': '—'})
                etd_ok = df_emb[col_etd_ok_pc].astype(str).str.upper().str.strip().iloc[0]
                pais   = df_emb[col_pais_dest].astype(str).str.strip().iloc[0] if col_pais_dest in df_emb.columns else '—'
                return pd.Series({'ETD OK FFWW': '✅ OK' if etd_ok == 'OK' else '❌ Sin OK', 'País Destino': pais})
            if not df_a2.empty:
                enrich_cols = df_a2.apply(enrich_a2, axis=1)
                df_a2['ETD OK FFWW']  = enrich_cols['ETD OK FFWW']
                df_a2['País Destino'] = enrich_cols['País Destino']
            else:
                df_a2['ETD OK FFWW']  = []
                df_a2['País Destino'] = []
            df['Rank_Num_PC'] = df[col_rank_pc].apply(safe_rank)
            col_etd_ok_pc  = find_col(df, ['ETD OK FFWW'], 97)
            col_fecha_inst = find_col(df, ['FECHA DE INSTRUCCION', 'FECHA INSTRUCCION', 'FECHA DE INSTRUCCIÓN'], 20)
            df['DT_Inst_PC']  = pd.to_datetime(df[col_fecha_inst], dayfirst=True, errors='coerce')
            df['ETD_OK_PC']   = df[col_etd_ok_pc].astype(str).str.upper().str.strip()
            df['Dias_sin_OK'] = (hoy - df['DT_Inst_PC']).dt.days
            etd_ok_vacio = df['ETD_OK_PC'].isin(['', 'NAN', 'NONE', 'NO', '—']) | df[col_etd_ok_pc].isna()
            df_a3_base = df[df['DT_Inst_PC'].notna() & etd_ok_vacio & (df['Dias_sin_OK'] > 7)].copy()
            alerta3_rows = []
            if not df_a3_base.empty:
                for emb, grp in df_a3_base.groupby(col_emb_pc):
                    emb_str = str(emb).strip().upper()
                    if emb_str in ['', 'NAN', 'NONE']: continue
                    cant_top   = grp[grp['Rank_Num_PC'] < 300]['SO'].nunique()
                    cant_nuevo = grp[grp[col_nuevo].astype(str).str.upper().str.strip() == 'SI']['SO'].nunique() if col_nuevo else 0
                    total_sos  = grp['SO'].nunique()
                    flag       = "🚨 SÍ" if (cant_top > 0 or cant_nuevo > 0) else "—"
                    dt_inst    = grp['DT_Inst_PC'].min()
                    dias_sin_ok = int((hoy - dt_inst).days) if pd.notna(dt_inst) else 0
                    forwarder_fmt = '—'
                    pack_max_fmt  = '—'
                    resp          = '—'
                    if not df_re.empty:
                        match_re = df_re[df_re[col_emb_re].astype(str).str.strip().str.upper() == emb_str]
                        if not match_re.empty:
                            resp          = str(match_re[col_resp].iloc[0]).strip()
                            forwarder_fmt = str(match_re[col_fwd].iloc[0]).strip() if col_fwd in match_re.columns else '—'
                            pm            = match_re['DT_PMax'].iloc[0]
                            pack_max_fmt  = pm.strftime('%d/%m/%Y') if pd.notna(pm) else '—'
                    alerta3_rows.append({
                        'Embarque': emb, 'Responsable': resp, 'F. Instrucción': dt_inst.strftime('%d/%m/%Y') if pd.notna(dt_inst) else '—',
                        'Forwarder': forwarder_fmt, 'F. Packeo Max': pack_max_fmt, 'Días sin OK': dias_sin_ok,
                        'Total SOs': total_sos, 'SOs Top Ranking': str(cant_top) if cant_top > 0 else '—',
                        'SKUs Nuevos': str(cant_nuevo) if cant_nuevo > 0 else '—', 'Prod. Críticos': flag,
                    })
            df_a3 = pd.DataFrame(alerta3_rows)
            impo2_sin_fecha = (
                df_mar_re[col_impo2].isna() |
                df_mar_re[col_impo2].astype(str).str.strip().isin(['', 'nan', 'NaN', 'NONE', '-', '—'])
            )
            df_a5 = df_mar_re[
                df_mar_re['ETD_OK'] & df_mar_re['DT_ETD'].notna() &
                (df_mar_re['Dias_ETD_venc'] > 7) & impo2_sin_fecha
            ].copy()
            def doc_falta(val):
                return str(val).strip().upper() not in ['SI', 'SÍ', 'S']
            draft_vacio = df_mar_re[col_draft_bl].apply(doc_falta)
            pack_vacio  = df_mar_re[col_pack_lst].apply(doc_falta)
            df_a6 = df_mar_re[
                df_mar_re['ETD_OK'] & (draft_vacio | pack_vacio) &
                df_mar_re['DT_ETD'].notna() & (df_mar_re['DT_ETD'] < hoy)
            ].copy()
            df_a6['Falta_Draft'] = draft_vacio[df_a6.index]
            df_a6['Falta_Pack']  = pack_vacio[df_a6.index]
            st.markdown("""
<div style='text-align:center; padding:25px; background:linear-gradient(135deg,rgba(255,75,75,0.08),rgba(255,170,0,0.05));
border-radius:20px; border:1px solid rgba(255,75,75,0.2); margin-bottom:30px;'>
<h2 style='color:#ff4b4b; font-weight:900; letter-spacing:6px; margin:0; font-size:26px;'>⚡ ALERTAS ESTRATÉGICAS</h2>
<p style='color:#94a3b8; margin:8px 0 0 0; font-size:13px; letter-spacing:2px;'>MARÍTIMO · TIEMPO REAL</p>
</div>""", unsafe_allow_html=True)
            def render_alerta(key, emoji, titulo, subtitulo, color, conteo, tabla_fn):
                estado_key = f"alerta_open_{key}"
                if estado_key not in st.session_state:
                    st.session_state[estado_key] = False
                c_info, c_num, c_btn = st.columns([6, 1, 1.5])
                with c_info:
                    st.markdown(f"""
<div style='padding:14px 18px; background:rgba(255,255,255,0.02);
border-radius:12px; border-left:4px solid {color};'>
<p style='color:{color}; font-weight:800; font-size:14px; letter-spacing:2px; margin:0 0 4px 0;'>{emoji} {titulo}</p>
<p style='color:#94a3b8; font-size:11px; margin:0;'>{subtitulo}</p>
</div>""", unsafe_allow_html=True)
                with c_num:
                    st.markdown(f"""
<div style='text-align:center; padding:14px 4px; background:rgba(255,255,255,0.03);
border-radius:12px; border:1px solid {color}44;'>
<p style='font-size:36px; font-weight:900; color:{color}; margin:0; line-height:1;'>{conteo}</p>
</div>""", unsafe_allow_html=True)
                with c_btn:
                    abierto   = st.session_state[estado_key]
                    label_btn = "🔼 OCULTAR" if abierto else "🔽 VER DETALLE"
                    if st.button(label_btn, key=f"btn_{key}", use_container_width=True):
                        st.session_state[estado_key] = not abierto
                        st.rerun()
                if st.session_state[estado_key]:
                    if conteo == 0: st.success("✅ Sin casos para esta alerta.")
                    else: tabla_fn()
                st.markdown("<div style='height:10px;'></div>", unsafe_allow_html=True)
            def tabla_a1():
                cols_show = [col_n_inv_pc, 'SO', 'Analista', col_puerto_pc, 'M3 Total', col_mono_pc, 'Top Ranking', 'SKU Nuevo', 'Fecha_Prior_DT']
                df_show = df_a1[cols_show].copy()
                df_show['Fecha_Prior_DT'] = df_show['Fecha_Prior_DT'].dt.strftime('%d/%m/%Y')
                df_show = df_show.rename(columns={col_n_inv_pc: 'Invoice', col_puerto_pc: 'Puerto', col_mono_pc: '¿Mono?', 'Fecha_Prior_DT': 'F. Prioritaria'}).sort_values('F. Prioritaria')
                st.dataframe(df_show, use_container_width=True, hide_index=True, column_config={'M3 Total': st.column_config.NumberColumn("M3", format="%.1f"), 'Top Ranking': st.column_config.TextColumn("🏆 Ranking"), 'SKU Nuevo': st.column_config.TextColumn("✨ Nuevo"), 'Analista': st.column_config.TextColumn("Analista")})
            render_alerta("a1", "🔴", "ALERTA 1 — SIN INSTRUIR",
                "Gadnic + Argentina · ordenado por fecha prioritaria (más vieja primero) · con analista asignado",
                "#ff4b4b", len(df_a1), tabla_a1)
            def tabla_a2():
                df_show = df_a2.copy()
                df_show['F_Min'] = df_a2['DT_PMin'].dt.strftime('%d/%m/%Y')
                df_show['F_Max'] = df_a2['DT_PMax'].dt.strftime('%d/%m/%Y')
                cols = [col_emb_re, col_resp, 'F_Min', 'F_Max', 'Rango_Pack', 'ETD OK FFWW', 'País Destino']
                df_show = df_show[cols].rename(columns={col_emb_re: 'Embarque', col_resp: 'Responsable', 'F_Min': 'F. Packeo Min', 'F_Max': 'F. Packeo Max', 'Rango_Pack': 'Días Rango'}).sort_values('Días Rango', ascending=False)
                st.dataframe(df_show, use_container_width=True, hide_index=True, column_config={'Días Rango': st.column_config.NumberColumn(format="%d días ⚡"), 'ETD OK FFWW': st.column_config.TextColumn("ETD OK"), 'País Destino': st.column_config.TextColumn("País")})
            def tabla_a1b():
                df_show = df_a1b.copy()
                df_show['F_ETD']   = df_a1b['DT_ETD'].dt.strftime('%d/%m/%Y')
                df_show['Tipo']    = df_a1b['Es_Mono'].apply(lambda x: 'MONO' if x else 'CONSOLIDADO')
                df_show['SLA']     = df_a1b['Es_Mono'].apply(lambda x: '7 días' if x else '25 días')
                df_show['T. Consol (días)'] = df_a1b['T_Consol'].astype(int)
                df_show = df_show[[col_emb_re, col_resp, 'Tipo', 'F_ETD', 'T. Consol (días)', 'SLA']]
                df_show = df_show.rename(columns={col_emb_re: 'Embarque', col_resp: 'Responsable', 'F_ETD': 'ETD'}).sort_values('T. Consol (días)', ascending=False)
                st.dataframe(df_show, use_container_width=True, hide_index=True, column_config={'T. Consol (días)': st.column_config.NumberColumn(format="%d días ⚠️"), 'SLA': st.column_config.TextColumn("SLA Límite"), 'Tipo': st.column_config.TextColumn("Tipo Carga")})
            render_alerta("a1b", "🔴", "ALERTA 1B — TIEMPOS DE CONSOLIDACIÓN FUERA DE SLA",
                "Sin ETD OK · Consolidado >25 días / Monoproveedor >7 días · Ordenado por mayor demora",
                "#ff4b4b", len(df_a1b), tabla_a1b)
            render_alerta("a2", "🟠", "ALERTA 2 — VENTANA DE PRODUCCIÓN EXTENDIDA (>7 DÍAS)",
                "Embarques con más de 7 días entre primer y último packeo · incluye estado ETD y país destino",
                "#ffaa00", len(df_a2), tabla_a2)
            def tabla_a3():
                if df_a3.empty:
                    st.success("✅ Sin casos.")
                    return
                cols_order = ['Embarque', 'Responsable', 'Forwarder', 'F. Instrucción', 'F. Packeo Max', 'Días sin OK', 'Total SOs', 'SOs Top Ranking', 'SKUs Nuevos', 'Prod. Críticos']
                df_show = df_a3[[c for c in cols_order if c in df_a3.columns]].copy()
                df_show['_sort_pack'] = pd.to_datetime(df_show['F. Packeo Max'], dayfirst=True, errors='coerce')
                df_show = df_show.sort_values('_sort_pack', ascending=True).drop(columns=['_sort_pack'])
                st.dataframe(df_show, use_container_width=True, hide_index=True, column_config={'Días sin OK': st.column_config.NumberColumn(format="%d días ⚠️"), 'SOs Top Ranking': st.column_config.TextColumn("SOs Top Ranking 🏆"), 'SKUs Nuevos': st.column_config.TextColumn("SKUs Nuevos ✨"), 'Total SOs': st.column_config.NumberColumn(format="%d"), 'Forwarder': st.column_config.TextColumn("Forwarder"), 'F. Packeo Max': st.column_config.TextColumn("F. Packeo Max"), 'Prod. Críticos': st.column_config.TextColumn("🚨 Prod. Críticos")})
                cant_criticos = (df_a3['Prod. Críticos'] == "🚨 SÍ").sum()
                if cant_criticos > 0:
                    st.warning(f"💡 {cant_criticos} embarque(s) contienen productos top ranking o SKUs nuevos. Evaluar reasignación de carga.")
            render_alerta("a3", "🚨", "ALERTA 3 — INSTRUIDAS SIN ETD OK (>7 DÍAS) + PRODUCTOS CRÍTICOS",
                "Sin confirmación ETD del forwarder · Días contados desde Fecha Instrucción · Incluye flag de productos importantes",
                "#ff4b4b", len(df_a3), tabla_a3)
            def tabla_a5():
                df_show = df_a5.copy()
                df_show['F_ETD'] = df_a5['DT_ETD'].dt.strftime('%d/%m/%Y')
                df_show = df_show[[col_emb_re, col_resp, 'F_ETD', 'Dias_ETD_venc']]
                df_show = df_show.rename(columns={col_emb_re: 'Embarque', col_resp: 'Responsable', 'F_ETD': 'ETD', 'Dias_ETD_venc': 'Días vencida'}).sort_values('Días vencida', ascending=False)
                st.dataframe(df_show, use_container_width=True, hide_index=True, column_config={'Días vencida': st.column_config.NumberColumn(format="%d días 🔴")})
            render_alerta("a5", "🔴", "ALERTA 5 — ETD VENCIDA SIN PASAR A IMPO2 (>7 DÍAS)",
                "ETD confirmada · Zarpe hace más de 7 días · Columna 'Pasar a Impo2' vacía",
                "#ff4b4b", len(df_a5), tabla_a5)
            def tabla_a6():
                df_show = df_a6.copy()
                df_show['ETD']                = df_a6['DT_ETD'].dt.strftime('%d/%m/%Y')
                df_show['Falta Draft BL']     = df_a6['Falta_Draft'].apply(lambda x: "❌ Falta" if x else "✅ OK")
                df_show['Falta Packing List'] = df_a6['Falta_Pack'].apply(lambda x: "❌ Falta" if x else "✅ OK")
                df_show = df_show[[col_emb_re, col_resp, 'ETD', 'Falta Draft BL', 'Falta Packing List']].copy()
                df_show = df_show.rename(columns={col_emb_re: 'Embarque', col_resp: 'Responsable'})
                df_show['_sort'] = pd.to_datetime(df_a6['DT_ETD'].values)
                df_show = df_show.sort_values('_sort', ascending=True).drop(columns=['_sort'])
                st.dataframe(df_show, use_container_width=True, hide_index=True, column_config={'ETD': st.column_config.TextColumn("ETD (col M)")})
            render_alerta("a6", "📋", "ALERTA 6 — RESERVA OK PERO FALTAN DOCUMENTOS",
                "ETD OK confirmada · Falta Draft BL y/o Packing List Final en Reservas",
                "#ffaa00", len(df_a6), tabla_a6)
            def tabla_aereos():
                st.info("✈️ Módulo de alertas para cargas aéreas en desarrollo. Próximamente disponible.")
            render_alerta("aereos", "✈️", "ALERTA 7 — AÉREOS",
                "Módulo en desarrollo · Próximamente disponible",
                "#94a3b8", 0, tabla_aereos)
        except Exception as e:
            st.error(f"Error en Alertas Estratégicas: {e}")
            import traceback
            st.code(traceback.format_exc())
    # --- SOLAPA 8: ASK COMEX ---
    with tabs[7]:
        st.markdown("<div style='text-align:center; padding: 40px; background: rgba(0, 168, 255, 0.05); border-radius: 20px; border: 2px dashed rgba(0, 168, 255, 0.2);'><h2 style='color:#00a8ff; font-weight:800; letter-spacing:10px;'>ASK COMEX</h2><p style='color:#94a3b8; font-size:18px; margin-top:20px;'>Inteligencia Operativa en Tiempo Real.</p></div>", unsafe_allow_html=True)
        st.markdown("<br>", unsafe_allow_html=True)
        try:
            with st.popover("💬 Hablar con Capitán Comex (IA)", use_container_width=False):
                st.markdown("<h4 style='color:#00ff88; margin-bottom:0;'>🚢 Capitán Comex</h4>", unsafe_allow_html=True)
                st.caption("Asistente Logístico con IA (Google Gemini)")
                if "chat_history" not in st.session_state:
                    st.session_state.chat_history = [{"role": "assistant", "content": "¡Hola! Soy Capitán Comex. ¿Qué embarque buscamos o qué duda operativa tienes?"}]
                chat_container = st.container(height=400)
                with chat_container:
                    for msg in st.session_state.chat_history:
                        avatar = "🚢" if msg["role"] == "assistant" else "👤"
                        with st.chat_message(msg["role"], avatar=avatar):
                            st.markdown(msg["content"])
                if prompt := st.chat_input("Hazle una pregunta a la IA..."):
                    st.session_state.chat_history.append({"role": "user", "content": prompt})
                    with chat_container:
                        with st.chat_message("user", avatar="👤"):
                            st.markdown(prompt)
                        with st.chat_message("assistant", avatar="🚢"):
                            resp_placeholder = st.empty()
                            resp_placeholder.markdown("Pensando... ⏳")
                            try:
                                respuesta_ia = "🚧 Estamos trabajando en esta funcionalidad. Volvé a intentarlo pronto."
                            except Exception as e:
                                respuesta_ia = "🚧 Estamos trabajando en esta funcionalidad. Volvé a intentarlo pronto."
                            resp_placeholder.markdown(respuesta_ia)
                            st.session_state.chat_history.append({"role": "assistant", "content": respuesta_ia})
        except AttributeError:
            st.error("⚠️ Para usar este chat flotante, necesitamos actualizar Streamlit. (Requiere versión 1.33 o superior).")
        st.markdown("<hr class='white-divider'>", unsafe_allow_html=True)
        @st.cache_data(ttl=60)
        def load_ask_comex_data():
            url_reserva = f"{base_url}/export?format=csv&gid=276804813"
            url_hist = f"{base_url}/export?format=csv&gid=32771816"
            url_emb_hist = "https://docs.google.com/spreadsheets/d/1uDV3-CK5aeb-PI81uNc54t4L50HhscHe5xkp-pL9SyI/export?format=csv&gid=50628730"
            url_ddp   = "https://docs.google.com/spreadsheets/d/1uDV3-CK5aeb-PI81uNc54t4L50HhscHe5xkp-pL9SyI/export?format=csv&gid=2050674215"
            url_impo2 = "https://docs.google.com/spreadsheets/d/1uDV3-CK5aeb-PI81uNc54t4L50HhscHe5xkp-pL9SyI/export?format=csv&gid=131563120"
            try: res = pd.read_csv(url_reserva, engine='python', on_bad_lines='skip')
            except: res = pd.DataFrame()
            try: hi = pd.read_csv(url_hist, engine='python', on_bad_lines='skip')
            except: hi = pd.DataFrame()
            try: emb_hi = pd.read_csv(url_emb_hist, engine='python', on_bad_lines='skip')
            except: emb_hi = pd.DataFrame()
            try: ddp = pd.read_csv(url_ddp, engine='python', on_bad_lines='skip')
            except: ddp = pd.DataFrame()
            try: impo2 = pd.read_csv(url_impo2, engine='python', on_bad_lines='skip')
            except: impo2 = pd.DataFrame()
            return res, hi, emb_hi, ddp, impo2
        df_res_ask, df_hi_ask, df_emb_hi_ask, df_ddp_ask, df_impo2_ask = load_ask_comex_data()
        if not df_ddp_ask.empty:
            df_ddp_ask.columns = [str(c).strip() for c in df_ddp_ask.columns]
            df_ddp_ask['_emb_key'] = df_ddp_ask.iloc[:, 5].astype(str).str.strip().str.upper()
        if not df_impo2_ask.empty:
            df_impo2_ask.columns = [str(c).strip() for c in df_impo2_ask.columns]
            df_impo2_ask['_emb_key'] = df_impo2_ask.iloc[:, 0].astype(str).str.strip().str.upper()
        st.markdown("<br>", unsafe_allow_html=True)
        def get_estadio_impo2(emb, eta_str, df_impo2, hoy_d, historico=False):
            suffix = " (HISTORICO)" if historico else ""
            def es_vacio(v): return str(v).strip().lower() in ['', 'nan', 'none', '-', 'n/a']
            if df_impo2.empty:
                return 5, "EN PROCESO DE NACIONALIZACION" + suffix, "#ffaa00", "Carga arribada. Sin informacion de despacho aun. (ETA: " + str(eta_str) + ")"
            emb_key = str(emb).strip().upper()
            match = df_impo2[df_impo2['_emb_key'] == emb_key]
            if match.empty:
                return 5, "EN PROCESO DE NACIONALIZACION" + suffix, "#ffaa00", "Carga arribada. Sin registro en Despachos Directo Puerto aun."
            row_i = match.iloc[0]
            val_orden    = str(row_i.iloc[0]).strip() if len(row_i) > 0 else ""
            val_retiro   = str(row_i.iloc[1]).strip() if len(row_i) > 1 else ""
            val_ofi      = str(row_i.iloc[3]).strip() if len(row_i) > 3 else ""
            val_despacho = str(row_i.iloc[4]).strip() if len(row_i) > 4 else ""
            try:
                dt_retiro = pd.to_datetime(val_retiro, dayfirst=True).date()
                retiro_cumplido = dt_retiro <= hoy_d
            except:
                dt_retiro = None
                retiro_cumplido = False
            orden_txt    = (" | Orden WMS: " + val_orden)     if not es_vacio(val_orden)    else ""
            despacho_txt = (" | N Despacho: " + val_despacho) if not es_vacio(val_despacho) else ""
            ofi_txt      = (" | Fecha OFI: " + val_ofi)       if not es_vacio(val_ofi)      else ""
            retiro_txt   = (" | Retiro: " + val_retiro)        if not es_vacio(val_retiro)   else ""
            if not es_vacio(val_retiro) and retiro_cumplido:
                return 7, "ENTREGADO EN DEPOSITO", "#00ff88", "Carga retirada y entregada al deposito." + orden_txt + despacho_txt + ofi_txt + retiro_txt
            elif not es_vacio(val_retiro) and not retiro_cumplido:
                return 6, "NACIONALIZADO / RETIRO COORDINADO", "#a855f7", "Despacho oficializado. Retiro coordinado para: " + val_retiro + "." + orden_txt + despacho_txt + ofi_txt
            elif not es_vacio(val_ofi):
                return 6, "NACIONALIZADO / COORDINANDO RETIRO", "#a855f7", "Despacho oficializado el " + val_ofi + ". Pendiente coordinar retiro." + orden_txt + despacho_txt
            else:
                return 5, "EN PROCESO DE NACIONALIZACION" + suffix, "#ffaa00", "Carga arribada. Pendiente de oficializacion del despacho." + orden_txt
        query = st.text_input("🔍 INGRESE SO O N° DE EMBARQUE:", placeholder="Ej: SO-12345 o EMB-999...")
        if query:
            query = str(query).strip().upper()
            col_so         = [c for c in df.columns if c.strip().upper() == 'SO'][0] if any(c.strip().upper() == 'SO' for c in df.columns) else df.columns[0]
            col_emb_pc     = df.columns[16]
            is_historical = False
            df_found = pd.DataFrame()
            mask_so  = df[col_so].astype(str).str.upper().str.contains(query, na=False)
            mask_emb_pc = df[col_emb_pc].astype(str).str.strip().str.upper() == query
            df_found = df[mask_so | mask_emb_pc]
            if df_found.empty and not df_emb_hi_ask.empty:
                col_eh_emb = df_emb_hi_ask.columns[4]
                col_eh_so  = df_emb_hi_ask.columns[0]
                m_emb = df_emb_hi_ask[col_eh_emb].astype(str).str.strip().str.upper() == query
                m_so  = df_emb_hi_ask[col_eh_so].astype(str).str.upper().str.contains(query, na=False)
                df_found = df_emb_hi_ask[m_emb | m_so]
                if not df_found.empty: is_historical = True
            if df_found.empty:
                st.warning(f"No se encontraron registros para '{query}'.")
                st.info("Verificá que el SO o número de embarque esté exactamente como aparece en el sistema (ej: FCL 2050, AIR 152).")
            else:
                origen = "Embarques Históricos" if is_historical else "Planif Cargas"
                st.success(f"✅ Registro encontrado — {len(df_found)} coincidencias en {origen}")
                if len(df_found) > 50:
                    st.warning(f"⚠️ Se encontraron {len(df_found)} resultados. Procesando los primeros 50.")
                    df_found = df_found.head(50)
                resultados_procesados = []
                for i, row in df_found.iterrows():
                    if is_historical:
                        val_so  = str(row.iloc[0]).strip()
                        val_sku = str(row.iloc[5]).strip() if len(row) > 5 else "—"
                        val_inv = str(row.iloc[17]).strip() if len(row) > 17 else "—"
                        if val_sku.lower() in ["nan","none",""]: val_sku = "—"
                        if val_inv.lower() in ["nan","none",""]: val_inv = "—"
                        val_emb = str(row.iloc[4]).strip()
                        if val_emb.lower() in ['nan', 'none', '']: val_emb = "Sin Asignar"
                        val_prov = str(row.iloc[18])
                        val_etd_gso = str(row.iloc[6]).strip(); val_eta_gso = str(row.iloc[7]).strip()
                        val_fin_prod = str(row.iloc[2]).strip()
                        if val_fin_prod.lower() == 'nan' or val_fin_prod == '': val_fin_prod = "Sin Info"
                        try: val_cant_emb = float(str(row.iloc[9]).replace(',', '.').strip())
                        except: val_cant_emb = 0.0
                        cantidad_mostrar = int(val_cant_emb); label_cant = "CANTIDAD EMB"
                        val_fecha_inst = "Pendiente"
                        if not df_hi_ask.empty and len(df_hi_ask.columns) > 7:
                            col_hi_emb = df_hi_ask.columns[0]
                            hi_match = df_hi_ask[df_hi_ask[col_hi_emb].astype(str).str.strip().str.upper() == val_emb.upper()]
                            if not hi_match.empty:
                                val_f = str(hi_match.iloc[0].iloc[7]).strip()
                                if val_f.lower() != 'nan' and val_f != '': val_fecha_inst = val_f
                        hoy_d = datetime.now().date()
                        try:
                            dt_eta_parsed = pd.to_datetime(val_eta_gso, dayfirst=True)
                            dt_eta = dt_eta_parsed.date() if pd.notna(dt_eta_parsed) else None
                        except: dt_eta = None
                        if dt_eta is not None and dt_eta < hoy_d:
                            estadio_ddp, desc_ddp, color_ddp, info_ddp = get_estadio_impo2(val_emb, val_eta_gso, df_ddp_ask, hoy_d, historico=True)
                            if estadio_ddp == 5:
                                estadio = 6; desc_estadio = "ARRIBADO (HISTORICO)"; color_estadio = "#00ff88"
                                info_extra = "La carga ha llegado a destino. Pendiente proceso de aduana. ETA: " + str(val_eta_gso)
                            else:
                                estadio = estadio_ddp + 1
                                desc_estadio = desc_ddp; color_estadio = color_ddp; info_extra = info_ddp
                        else:
                            estadio = 4; desc_estadio = "EN TRÁNSITO (HISTÓRICO)"; color_estadio = "#00a8ff"
                            info_extra = f"La carga figura despachada en registros históricos pero su ETA es futura. (ETA: {val_eta_gso})"
                        etd_display = val_etd_gso if val_etd_gso and str(val_etd_gso).lower() not in ["nan","none",""] else "Sin fecha"
                        eta_display = val_eta_gso if val_eta_gso and str(val_eta_gso).lower() not in ["nan","none",""] else "Sin fecha"
                    else:
                        val_so  = str(row[col_so]).strip()
                        val_sku = str(row[df.columns[32]]).strip() if len(df.columns) > 32 else ""
                        val_inv = str(row[df.columns[29]]).strip() if len(df.columns) > 29 else ""
                        if val_sku.lower() in ["nan","none",""]: val_sku = "—"
                        if val_inv.lower() in ["nan","none",""]: val_inv = "—"
                        col_prov = [c for c in df.columns if 'PROVEEDOR' in c.upper()][0] if any('PROVEEDOR' in c.upper() for c in df.columns) else df.columns[30]
                        val_prov = str(row[col_prov])
                        col_emb = [c for c in df.columns if 'EMBARQUE' in c.upper()][0] if any('EMBARQUE' in c.upper() for c in df.columns) else df.columns[16]
                        val_emb = str(row[col_emb]).strip()
                        if val_emb.lower() == 'nan': val_emb = "Sin Asignar"
                        col_inst = [c for c in df.columns if 'INSTRUCCION' in c.upper() or 'INSTRUCCIÓN' in c.upper()][0] if any('INSTRUCCION' in c.upper() or 'INSTRUCCIÓN' in c.upper() for c in df.columns) else df.columns[20]
                        val_inst = str(row[col_inst]).strip()
                        col_fin_prod = df.columns[99]
                        val_fin_prod = str(row[col_fin_prod]).strip()
                        if val_fin_prod.lower() == 'nan' or val_fin_prod == '': val_fin_prod = "Sin Info"
                        val_fecha_inst = val_inst if (val_inst != "" and val_inst.lower() != "nan" and "sin instruccion" not in val_inst.lower()) else "Pendiente"
                        val_etd_gso = str(row[df.columns[23]]).strip()
                        val_eta_gso = str(row[df.columns[24]]).strip()
                        col_cant_pend = [c for c in df.columns if 'CANTIDAD PENDIENTE DE EMBARCAR' in c.upper()][0] if any('CANTIDAD PENDIENTE DE EMBARCAR' in c.upper() for c in df.columns) else df.columns[21]
                        col_cant_emb = [c for c in df.columns if 'CANTIDAD EMB' in c.upper() and 'PREVENTA' not in c.upper()][0] if any('CANTIDAD EMB' in c.upper() and 'PREVENTA' not in c.upper() for c in df.columns) else df.columns[60]
                        try: val_cant_pend = float(str(row[col_cant_pend]).replace(',', '.').strip())
                        except: val_cant_pend = 0.0
                        try: val_cant_emb = float(str(row[col_cant_emb]).replace(',', '.').strip())
                        except: val_cant_emb = 0.0
                        if val_cant_pend == 0:
                            cantidad_mostrar = int(val_cant_emb); label_cant = "CANTIDAD EMB"
                        else:
                            cantidad_mostrar = int(val_cant_pend); label_cant = "CANT. PENDIENTE"
                        col_etd_ok_ask = next((c for c in df.columns if "ETD OK FFWW" in str(c).upper() or "ETD OK" in str(c).upper()), df.columns[97])
                        val_etd_ok = str(row[col_etd_ok_ask]).strip().upper() if col_etd_ok_ask in df.columns else ""
                        hoy_d = datetime.now().date()
                        try:
                            _p = pd.to_datetime(val_eta_gso, dayfirst=True)
                            dt_eta_gso = _p.date() if pd.notna(_p) else None
                        except: dt_eta_gso = None
                        try:
                            _p = pd.to_datetime(val_etd_gso, dayfirst=True)
                            dt_etd_gso = _p.date() if pd.notna(_p) else None
                        except: dt_etd_gso = None
                        in_historical = False
                        if not df_hi_ask.empty:
                            df_hi_ask.columns = df_hi_ask.columns.str.strip()
                            col_hi_emb = df_hi_ask.columns[0]
                            hi_match = df_hi_ask[df_hi_ask[col_hi_emb].astype(str).str.strip().str.upper() == val_emb.upper()]
                            if not hi_match.empty: in_historical = True
                        tiene_emb  = val_emb not in ["Sin Asignar", "", "nan", "NAN"]
                        tiene_inst = val_fecha_inst != "Pendiente"
                        etd_ok     = val_etd_ok == "OK"
                        etd_display = val_etd_gso if val_etd_gso and str(val_etd_gso).lower() not in ["nan","none",""] else "Sin fecha"
                        eta_display = val_eta_gso if val_eta_gso and str(val_eta_gso).lower() not in ["nan","none",""] else "Sin fecha"
                        f_salida_origen = ""; f_arribo_aduana = ""
                        if not df_impo2_ask.empty and val_emb not in ["Sin Asignar","","nan","NAN"]:
                            impo2_match = df_impo2_ask[df_impo2_ask["_emb_key"] == val_emb.upper()]
                            if not impo2_match.empty:
                                f_salida_origen = str(impo2_match.iloc[0].iloc[1]).strip()
                                f_arribo_aduana = str(impo2_match.iloc[0].iloc[2]).strip()
                                if f_salida_origen.lower() in ["nan","none",""]: f_salida_origen = ""
                                if f_arribo_aduana.lower() in ["nan","none",""]: f_arribo_aduana = ""
                        if in_historical or (dt_eta_gso and dt_eta_gso <= hoy_d):
                            estadio_ddp, desc_ddp, color_ddp, info_ddp = get_estadio_impo2(val_emb, val_eta_gso, df_ddp_ask, hoy_d, historico=False)
                            if estadio_ddp == 5:
                                estadio = 6; desc_estadio = "ARRIBADO"; color_estadio = "#00ff88"
                                arribo_txt = " | Arribo a aduana: " + f_arribo_aduana if f_arribo_aduana else ""
                                info_extra = "La carga ha llegado a destino. ETA: " + eta_display + arribo_txt
                            else:
                                estadio = estadio_ddp + 1
                                desc_estadio = desc_ddp; color_estadio = color_ddp; info_extra = info_ddp
                        elif dt_etd_gso and dt_etd_gso <= hoy_d and etd_ok:
                            estadio = 5; desc_estadio = "EN TRANSITO"; color_estadio = "#00a8ff"
                            salida_txt = " | Salida origen: " + f_salida_origen if f_salida_origen else ""
                            arribo_txt = " | Arribo estimado aduana: " + f_arribo_aduana if f_arribo_aduana else " | ETA: " + eta_display
                            info_extra = "La carga esta navegando. ETD: " + (dt_etd_gso.strftime("%d/%m/%Y") if dt_etd_gso else "SD") + salida_txt + arribo_txt
                        elif etd_ok and (not dt_etd_gso or dt_etd_gso > hoy_d):
                            estadio = 4; desc_estadio = "BOOKING CONFIRMADO"; color_estadio = "#a855f7"
                            info_extra = "Espacio confirmado. Esperando zarpada. ETD: " + etd_display + " | ETA estimada: " + eta_display
                        elif tiene_inst and not etd_ok:
                            estadio = 3; desc_estadio = "INSTRUCCION ENVIADA - ESPERA BOOKING"; color_estadio = "#ffaa00"
                            info_extra = "Instruccion enviada el " + val_inst + ". Esperando confirmacion de booking. ETA estimada: " + eta_display
                        elif tiene_emb and not tiene_inst:
                            estadio = 2; desc_estadio = "EN PROCESO DE CONSOLIDACION"; color_estadio = "#06b6d4"
                            info_extra = "SO asignado al embarque " + val_emb + ". Pendiente de instruccion al agente."
                        else:
                            estadio = 1; desc_estadio = "PENDIENTE DE INSTRUCCION"; color_estadio = "#94a3b8"
                            info_extra = "Sin embarque asignado. Carga en origen sin gestion iniciada."
                    resultados_procesados.append({
                        "estadio": estadio, "desc_estadio": desc_estadio, "color_estadio": color_estadio,
                        "info_extra": info_extra, "so": val_so, "inv": val_inv, "sku": val_sku,
                        "emb": val_emb, "prov": val_prov, "cant": cantidad_mostrar,
                        "label_cant": label_cant, "fecha_inst": val_fecha_inst, "fin_prod": val_fin_prod,
                        "etd": etd_display, "eta": eta_display
                    })
                st.session_state.ultimos_resultados = resultados_procesados
                st.success(f"📌 {len(resultados_procesados)} SO(s) encontrados.")
                for r in resultados_procesados:
                    etd_val = r.get('etd', 'Sin fecha')
                    eta_val = r.get('eta', 'Sin fecha')
                    c_est   = r['color_estadio']
                    st.markdown(
                        "<div class='custom-card' style='border-top:5px solid " + c_est + ";'>"
                        "<h3 style='color:" + c_est + "; text-transform:uppercase; letter-spacing:2px; margin-bottom:10px;'>"
                        "ESTADIO " + str(r['estadio']) + ": " + r['desc_estadio'] + "</h3>"
                        "<p style='color:#f8fafc; font-size:14px; margin-bottom:15px;'>" + r['info_extra'] + "</p>"
                        "<hr style='border:none; border-top:1px solid rgba(255,255,255,0.1); margin:15px 0;'>"
                        "<div class='grid-4' style='align-items:start;'>"
                        "<div><p class='minicard-title'>SO</p><p style='font-size:18px; font-weight:700; color:#f8fafc; margin:0;'>" + r['so'] + "</p></div>"
                        "<div><p class='minicard-title'>EMBARQUE</p><p style='font-size:18px; font-weight:700; color:#00a8ff; margin:0;'>" + r['emb'] + "</p></div>"
                        "<div><p class='minicard-title'>SKU / CÓDIGO</p><p style='font-size:16px; font-weight:600; color:#f8fafc; margin:0;'>" + r['sku'] + "</p></div>"
                        "<div><p class='minicard-title'>N° INVOICE</p><p style='font-size:16px; font-weight:600; color:#f8fafc; margin:0;'>" + r['inv'] + "</p></div>"
                        "</div>"
                        "<div class='grid-4' style='margin-top:15px; padding-top:15px; border-top:1px dashed rgba(255,255,255,0.1);'>"
                        "<div><p class='minicard-title'>ETD</p><p style='font-size:15px; color:#ffaa00; margin:0;'>" + etd_val + "</p></div>"
                        "<div><p class='minicard-title'>ETA</p><p style='font-size:15px; color:#00a8ff; margin:0;'>" + eta_val + "</p></div>"
                        "<div><p class='minicard-title'>F. INSTRUCCION</p><p style='font-size:15px; color:#f8fafc; margin:0;'>" + r['fecha_inst'] + "</p></div>"
                        "<div><p class='minicard-title'>FIN PRODUCCION</p><p style='font-size:15px; color:#f8fafc; margin:0;'>" + r['fin_prod'] + "</p></div>"
                        "</div>"
                        "<div class='grid-4' style='margin-top:15px; padding-top:15px; border-top:1px dashed rgba(255,255,255,0.1);'>"
                        "<div><p class='minicard-title'>PROVEEDOR</p><p style='font-size:14px; color:#f8fafc; margin:0; font-weight:600;'>" + r['prov'] + "</p></div>"
                        "<div><p class='minicard-title'>TOTAL " + r['label_cant'] + "</p><p style='font-size:24px; color:#00ff88; font-weight:900; margin:0;'>" + str(r['cant']) + "</p></div>"
                        "<div></div><div></div>"
                        "</div></div>",
                        unsafe_allow_html=True
                    )
                    pct_p = round(r['estadio'] / 8 * 100)
                    c1 = '#fff' if r['estadio'] >= 1 else '#64748b'
                    c2 = '#fff' if r['estadio'] >= 2 else '#64748b'
                    c3 = '#fff' if r['estadio'] >= 3 else '#64748b'
                    c4 = '#fff' if r['estadio'] >= 4 else '#64748b'
                    c5 = '#fff' if r['estadio'] >= 5 else '#64748b'
                    c6 = '#fff' if r['estadio'] >= 6 else '#64748b'
                    c7 = '#fff' if r['estadio'] >= 7 else '#64748b'
                    c8 = '#fff' if r['estadio'] >= 8 else '#64748b'
                    st.markdown(
                        "<div style='width:100%; background-color:rgba(255,255,255,0.1); border-radius:10px; margin-top:15px; height:10px;'>"
                        "<div style='width:" + str(pct_p) + "%; background-color:" + c_est + "; height:10px; border-radius:10px;'></div></div>"
                        "<div style='display:flex; justify-content:space-between; margin-top:8px; padding:0 5px;'>"
                        "<span style='font-size:9px; font-weight:700; color:" + c1 + ";'>1.PENDIENTE</span>"
                        "<span style='font-size:9px; font-weight:700; color:" + c2 + ";'>2.CONSOLID.</span>"
                        "<span style='font-size:9px; font-weight:700; color:" + c3 + ";'>3.INSTRUC.</span>"
                        "<span style='font-size:9px; font-weight:700; color:" + c4 + ";'>4.BOOKING</span>"
                        "<span style='font-size:9px; font-weight:700; color:" + c5 + ";'>5.TRANSITO</span>"
                        "<span style='font-size:9px; font-weight:700; color:" + c6 + ";'>6.ARRIBADO</span>"
                        "<span style='font-size:9px; font-weight:700; color:" + c7 + ";'>7.NACIONALIZ.</span>"
                        "<span style='font-size:9px; font-weight:700; color:" + c8 + ";'>8.ENTREGADO</span>"
                        "</div><br>",
                        unsafe_allow_html=True
                    )
except Exception as e:
    st.error(f"Error general al cargar el dashboard: {e}")
    import traceback
    st.code(traceback.format_exc())
