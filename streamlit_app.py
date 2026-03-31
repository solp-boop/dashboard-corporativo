
st.markdown("<br><hr style='opacity:0.1;'><br>", unsafe_allow_html=True)

        # --- BLOQUE 2: BOTONES DE FILTRADO CON RESALTADO DINÁMICO (RESERVAS) ---
            r1, r2, r3, r4, r5 = st.columns(5)
 # --- SOLAPA 2: CONTROL GESTIÓN RESERVAS ---
    with tabs[1]:
        try:
            # 1. Carga de Reservas (Ya optimizada con caché para evitar IncompleteRead)
            url_reserva = f"{base_url}/export?format=csv&gid=276804813&nocache={time.time()}"
            df_res = pd.read_csv(url_reserva, engine='python')
            df_res.columns = df_res.columns.str.strip()

            # Filtrar solo lo instruido (Columna H = índice 7)
            df_res['Fecha_Inst_H'] = df_res.iloc[:, 7].astype(str).str.strip()
            df_g = df_res[df_res['Fecha_Inst_H'].apply(lambda x: len(str(x)) > 4)].copy()

            # --- CÁLCULO DE PORCENTAJES PARA BOTONES (CORRECCIÓN DE ERROR) ---
            total_gestion = len(df_g) if len(df_g) > 0 else 1
            
            # Booking in Advance (Columna I = índice 8)
            cant_adv = len(df_g[df_g.iloc[:, 8].astype(str).str.strip() == "Booked in Advance"])
            cant_spot = len(df_g[df_g.iloc[:, 8].astype(str).str.strip() == "No Booked in Advance"])

            # Recuperamos el filtro activo específico de reservas (usamos una clave distinta a origen para que no se pisen)
            # Avion / Courier (Columna F = índice 5)
            cant_avion = len(df_g[df_g.iloc[:, 5].astype(str).str.upper().str.contains("AVION|COURIER|COURRIER", na=False)])
            
            p_adv = int(round((cant_adv / total_gestion) * 100))
            p_spot = int(round((cant_spot / total_gestion) * 100))
            p_avion = int(round((cant_avion / total_gestion) * 100))

            # --- BLOQUE 1: KPIs GRANDES (Mismo formato que Origen) ---
            st.markdown("<br>", unsafe_allow_html=True)
            k1, k2, k3 = st.columns(3)
            with k1: st.markdown(f"<div class='metric-container'><p style='font-size: 22px; color: #00a8ff; letter-spacing: 4px; font-weight: 700; margin-bottom: 0;'>SO INSTRUIDAS</p><p style='font-size: 90px; font-weight: 900; color: #00a8ff; line-height: 1; margin: 0; text-shadow: 0 0 25px rgba(0,168,255,0.4);'>{int(len(df_g))}</p></div>", unsafe_allow_html=True)
            with k2: 
                # Volumen total de esta solapa (Columna AV = índice 47 o similar, ajustamos según tu M3 Total)
                m3_res = pd.to_numeric(df_g.iloc[:, 47].astype(str).str.replace(r'[^0-9.]', '', regex=True), errors='coerce').sum()
                st.markdown(f"<div class='metric-container'><p style='font-size: 22px; color: #00a8ff; letter-spacing: 4px; font-weight: 700; margin-bottom: 0;'>VOLUMEN (M3)</p><p style='font-size: 90px; font-weight: 900; color: #00a8ff; line-height: 1; margin: 0; text-shadow: 0 0 25px rgba(0,168,255,0.4);'>{int(round(m3_res)):,}</p></div>", unsafe_allow_html=True)
            with k3: 
                prov_res = df_g.iloc[:, 3].nunique() # Columna Proveedor (índice 3)
                st.markdown(f"<div class='metric-container'><p style='font-size: 22px; color: #00a8ff; letter-spacing: 4px; font-weight: 700; margin-bottom: 0;'>PROVEEDORES</p><p style='font-size: 90px; font-weight: 900; color: #00a8ff; line-height: 1; margin: 0; text-shadow: 0 0 25px rgba(0,168,255,0.4);'>{int(prov_res)}</p></div>", unsafe_allow_html=True)

            st.markdown("<br><hr style='opacity:0.1;'><br>", unsafe_allow_html=True)

            # --- BLOQUE 2: BOTONES DE FILTRADO CON RESALTADO ---
            r1, r2, r3, r4, r5 = st.columns(5)
filtro_reserva = st.session_state.get('f_res')

            # Función para aplicar estilo de "Resaltado"
def get_res_btn_style(target):
if filtro_reserva == target:
return "border: 2px solid #00a8ff; background: rgba(0, 168, 255, 0.1);"
@@ -430,9 +467,8 @@ def get_res_btn_style(target):
st.rerun()
st.markdown("</div>", unsafe_allow_html=True)

            # --- LÓGICA DE DESPLIEGUE ---
            # Asegúrate de que los cuadros de abajo (if f_res == 'adv', etc.) 
            # usen 'f_res' en lugar de 'f' para mantener las solapas independientes.
        except Exception as e:
            st.error(f"Error en Gestión de Reservas: {e}")

# --- BLOQUE 3: MARITIMO VS AEREO ---
def clasificar_transporte(x):
