import streamlit as st
import sqlite3
import pandas as pd
import google.generativeai as genai

st.set_page_config(page_title="Plataforma Acción Legal BPO", layout="wide", page_icon="⚖️")

# Estilos corporativos inyectados
st.markdown("""
<style>
    /* Paleta Corporativa BPO */
    :root {
        --bpo-dark: #0f172a;
        --bpo-gold: #f59e0b;
        --bpo-blue: #0284c7;
    }
    
    /* Branding Header Centrado */
    .brand-box {
        text-align: center;
        padding-top: 5px;
        padding-bottom: 15px;
        border-bottom: 1px solid #334155;
        margin-bottom: 25px;
    }
    .brand-logo {
        font-size: 3.8rem;
        font-weight: 900;
        letter-spacing: -1.5px;
        color: white;
        margin-bottom: -15px;
        line-height: 1.2;
        font-family: 'Helvetica Neue', Arial, sans-serif;
    }
    .brand-logo span {
        color: var(--bpo-gold);
    }
    .brand-slogan {
        font-size: 1.05rem;
        font-weight: 600;
        letter-spacing: 5px;
        color: #94a3b8;
        text-transform: uppercase;
        margin-top: 5px;
    }
    
    /* Redireccionando Sidebar */
    [data-testid="stSidebar"] {
        border-right: 1px solid #1e293b;
    }
    
    /* Botones corporativos */
    .stButton>button {
        border-radius: 6px;
        font-weight: bold;
        transition: all 0.3s ease;
    }
    
    /* Section lines */
    .section-title { font-size: 1.4rem; font-weight: 700; margin-top: 2rem; border-bottom: 2px solid #334155; padding-bottom: 8px; margin-bottom: 20px;}
</style>

<div class="brand-box">
    <div class="brand-logo">ACCIÓN<span>LEGAL</span></div>
    <div class="brand-slogan">SOLUCIONES EFECTIVAS BPO</div>
</div>
""", unsafe_allow_html=True)

try:
    # Intenta leer la llave secreta desde la Bóveda de Streamlit Cloud
    api_key_gemini = st.secrets["GEMINI_API_KEY"]
except:
    # Llave dummy de protección para cuando suba a Github
    api_key_gemini = "TU_NUEVA_LLAVE_API_AQUI"

genai.configure(api_key=api_key_gemini)
# Seleccionamos explícitamente el modelo más moderno y rápido soportado
# (evitamos genai.list_models() porque a veces falla en la nube de Streamlit)
model = genai.GenerativeModel('gemini-2.5-flash')

def get_bd_data():
    import os
    db_path = os.path.join(os.path.dirname(__file__), 'demo_cartera_accion_legal.sqlite')
    conn = sqlite3.connect(db_path)
    df_deudores = pd.read_sql_query("SELECT d.*, c.nombre_empresa, c.sector, c.cartera_asignada_total FROM deudores d JOIN empresas_clientes c ON d.id_cliente = c.id_cliente", conn)
    df_gestiones = pd.read_sql_query("SELECT * FROM gestiones", conn)
    df_asesores = pd.read_sql_query("SELECT * FROM asesores", conn)
    return df_deudores, df_gestiones, df_asesores, conn

st.sidebar.image("https://cdn-icons-png.flaticon.com/512/6009/6009864.png", width=100)
st.sidebar.title("Plataforma Multinivel")
rol_usuario = st.sidebar.radio("Seleccione el Perfil de Acceso:", [
    "📈 Torre de Control (Gerencia y Supervisión)",
    "👤 Consola de Asesor (Copiloto IA)", 
    "🤝 Portal de Transparencia (Cliente B2B)"
])

try:
    df_deudores, df_gestiones, df_asesores, conn = get_bd_data()
except Exception as e:
    st.error("Error cargando BD Mocks.")
    st.stop()


# =========================================================================
# VISTA 1: GERENCIA
# =========================================================================
if rol_usuario == "📈 Torre de Control (Gerencia y Supervisión)":
    st.title("🏦 Dashboard Ejecutivo: Control Operativo")
    
    filtro_empresa = st.selectbox("Filtro Origen Cartera (Banco/Retail):", ["Toda la Operación"] + list(df_deudores['nombre_empresa'].unique()))
    df_d = df_deudores[df_deudores['nombre_empresa'] == filtro_empresa] if filtro_empresa != "Toda la Operación" else df_deudores
    df_g_base = df_gestiones[df_gestiones['id_deudor'].isin(df_d['id_deudor'])]

    # 1. EL FLUJO DE CAJA (KPIs MONETARIOS DUROS)
    st.markdown("<div class='section-title'>💰 Resumen Financiero Macro (Flujo de Caja)</div>", unsafe_allow_html=True)
    asignacion_total = df_d['asignacion_inicial'].sum()
    recaudado_total = asignacion_total - df_d['saldo_adeudado'].sum()
    
    f1, f2, f3 = st.columns(3)
    f1.metric("Bolsa de Cartera Asignada", f"${asignacion_total/1e6:,.1f} Millones", help="Valor total del crédito originado por los clientes al BPO.")
    f2.metric("Valor Neto Recuperado", f"${recaudado_total/1e6:,.1f} Millones", delta="Retorno Efectivo", help="El dinero duro que los asesores ya cobraron y entró a caja.")
    f3.metric("Saldo en Riesgo (Por Cobrar)", f"${df_d['saldo_adeudado'].sum()/1e6:,.1f} Millones", help="El saldo que aún está en la calle pendiente de PTP.")

    # 2. TABLA MAESTRA EN LA CIMA
    st.markdown("<div class='section-title'>👥 Panel de Rendimiento Maestro (Nómina)</div>", unsafe_allow_html=True)
    st.caption("Al dar CLIC en la fila de cualquier asesor, la analítica inferior se recalculará exclusivamente para él.")
    
    # ================= LOGICA DE CROSS-FILTERING (PRE-CÁLCULO) =================
    n_ase = df_asesores['nombre_asesor'].tolist()
    df_d_calc = df_d.copy()
    df_d_calc['asesor_asignado'] = [n_ase[i % len(n_ase)] for i in range(len(df_d_calc))]

    perf = []
    for num, row in df_asesores.iterrows():
        a_nom = row['nombre_asesor']
        lis_g = df_g_base[df_g_base['asesor_humano'] == a_nom]
        df_a_cart = df_d_calc[df_d_calc['asesor_asignado'] == a_nom]
        
        # Meta Monetaria de este Agente
        asig = df_a_cart['asignacion_inicial'].sum()
        rec = asig - df_a_cart['saldo_adeudado'].sum()
        perc_rec = (rec / asig) * 100 if asig > 0 else 0
        
        pr_hechas = lis_g[lis_g['hubo_compromiso']==1]
        pr_keeps = len(pr_hechas[pr_hechas['promesa_cumplida']==1]) / len(pr_hechas) * 100 if len(pr_hechas)>0 else 0
        rpc_ind = len(lis_g[lis_g['rpc']==1])/len(lis_g) * 100 if len(lis_g)>0 else 0
        
        perf.append({
            "Asesor": a_nom,
            "% Recaudo": round(perc_rec, 1),
            "Volumen Llamadas": len(lis_g),
            "Efectividad PTP": round(pr_keeps, 1),
            "Tasa RPC": round(rpc_ind, 1),
            "Infracciones": len(lis_g[lis_g['alerta_legal'] != 'Ninguna'])
        })
        
    df_p = pd.DataFrame(perf).sort_values("% Recaudo", ascending=False)
    
    # Tabla Nativa Elegante
    ev_ase = st.dataframe(df_p, hide_index=True, use_container_width=True, selection_mode="single-row", on_select="rerun")


    asesor_sel = None
    if len(ev_ase.selection.rows) > 0:
        selec_idx = ev_ase.selection.rows[0]
        asesor_sel = df_p.iloc[selec_idx]['Asesor']
        df_g_metricas = df_g_base[df_g_base['asesor_humano'] == asesor_sel]
        df_d_metricas = df_d_calc[df_d_calc['asesor_asignado'] == asesor_sel]
        st.markdown(f"<div class='section-title'>🔎 Indicadores Analíticos del GESTOR: {asesor_sel}</div>", unsafe_allow_html=True)
    else:
        df_g_metricas = df_g_base
        df_d_metricas = df_d_calc
        st.markdown("<div class='section-title'>🌍 MATRIZ INDICADORES (Monitor Global Máster)</div>", unsafe_allow_html=True)

    # 3. EL FLUJO DE CAJA DINÁMICO (RESPONDE A LA TABLA MAESTRA)
    st.markdown("**💰 Flujo de Caja en Riesgo (El Dinero Fuerte)**")
    asig_din = df_d_metricas['asignacion_inicial'].sum()
    rec_din = asig_din - df_d_metricas['saldo_adeudado'].sum()
    
    d1, d2, d3 = st.columns(3)
    d1.metric("Cartera de Responsabilidad Directa", f"${asig_din/1e6:,.1f} Millones")
    d1.caption("Saldo total del portafolio que el marcaje/filtros indicaron que se debe auditar/cobrar.")
    
    d2.metric("Valor Neto Recuperado a la Vena", f"${rec_din/1e6:,.1f} Millones", delta=f"{ (rec_din/asig_din)*100 if asig_din > 0 else 0 :.1f}% de Ejecución")
    d2.caption("Impacto en caja real descontado de los saldos iniciales vencidos.")
    
    d3.metric("Bolsa Invertida en Mora (Sin cobrar)", f"${df_d_metricas['saldo_adeudado'].sum()/1e6:,.1f} Millones", delta="Meta Pendiente", delta_color="inverse")
    d3.caption("El saldo que todavía quema en los balances, listo para aplicar NLP y automatización AI.")

    # 4. INDICADORES DE EFICIENCIA CALCULADOS SOBRE LA SELECCIÓN
    ptp_hechas = df_g_metricas[df_g_metricas['hubo_compromiso'] == 1]
    ptp_cump = ptp_hechas[ptp_hechas['promesa_cumplida'] == 1]
    ptp_keep = (len(ptp_cump) / len(ptp_hechas)) * 100 if len(ptp_hechas) > 0 else 0
    t_gest = len(df_g_metricas)
    rpc_rate = (len(df_g_metricas[df_g_metricas['rpc']==1]) / t_gest) * 100 if t_gest > 0 else 0
    aht_seg = df_g_metricas[df_g_metricas['rpc']==1]['duracion_segundos'].mean() if not df_g_metricas[df_g_metricas['rpc']==1].empty else 0
    multas = len(df_g_metricas[df_g_metricas['alerta_legal'] != 'Ninguna'])
    zero_violation = 100 - ((multas / t_gest) * 100) if t_gest > 0 else 100
    sentim_prom = df_g_metricas['sentiment_score'].mean() if not df_g_metricas.empty else 0

    st.markdown("**🏆 Métrica de Negociación y Eficiencia Financiera**")
    c1, c2, c3 = st.columns(3)
    c1.metric("Tasa Reales de Pago (PTP Keep Rate)", f"{ptp_keep:.1f}%")
    c1.caption("Porcentaje de deudores que cumplen su promesa de pago tras colgar. Delata a los asesores que hacen cierres falsos o forzados.")
    
    c2.metric("Contacto Útil y Directo (RPC)", f"{rpc_rate:.1f}%")
    c2.caption("Right Party Contact: Mide la calidad de la base de datos de Acción Legal. Porcentaje de veces que contestó el titular y no un buzón de voz.")
    
    c3.metric("Tiempo Medio Telefónico (AHT)", f"{aht_seg/60:.1f} Minutos")
    c3.caption("Average Handle Time: El tiempo estándar que requiere un asesor para lograr convencer y comprometer exitosamente al deudor.")

    st.markdown("**🛡️ Métrica de Riesgo Legal Penal (Leyes Colombianas)**")
    r1, r2, r3 = st.columns(3)
    r1.metric("Gestiones Legales (Zero-Violation)", f"{zero_violation:.1f}%")
    r1.caption("Índice de calidad absoluta. Proporción de todo el volumen operativo sin acoso detectado, libre de infracciones a la Ley 2300.")
    
    r2.metric("Infracciones SIC Identificadas", f"{multas} Gravedades", delta="Peligro Inminente", delta_color="inverse")
    r2.caption("Llamadas bloqueadas o auditadas por la lA Gemini que rebasan estatutos constitucionales.")
    
    r3.metric("Clima y Sentimiento Verbal", f"{sentim_prom*100:.0f} Puntos / 100")
    r3.caption("Evaluación algorítmica de la voz. Entre más bajo sea, mayor nivel de agresión u ofuscamiento por parte de nuestro gestor.")

    # TRIPLE DRILL DOWN (Nivel 3: EMPRESA -> GESTOR -> DEUDOR)
    if asesor_sel:
        st.divider()
        st.markdown(f"### 📋 Portafolio Asignado ({asesor_sel})")
        st.caption("👆 **Haz CLIC Físico** en cualquier deudor u objetivo comercial de esta tabla para entrar e investigar todo su expediente, historial de llamadas y riesgos penales.")
        
        df_port = df_d_metricas[['id_deudor', 'nombre_completo', 'nombre_empresa', 'saldo_adeudado', 'dias_mora', 'riesgo_ai_score']].copy()
        
        df_visual_p = df_port.copy()
        df_visual_p.rename(columns={'id_deudor':'ID','nombre_completo': 'Deudor', 'nombre_empresa': 'Cliente B2B', 'saldo_adeudado': 'Saldo Mora', 'dias_mora': 'Días Atraso', 'riesgo_ai_score':'Propensión a Pagar'}, inplace=True)
        df_visual_p['Saldo Mora'] = df_visual_p['Saldo Mora'].apply(lambda x: f"${x:,.0f}")
        df_visual_p['Propensión a Pagar'] = df_visual_p['Propensión a Pagar'].apply(lambda x: f"{x*100:.0f}% Nudge")
        
        # Tabla Maestra Nivel 2 (Pantalla Completa + Interactiva)
        ev_port = st.dataframe(df_visual_p.sort_values(by='Días Atraso', ascending=False), hide_index=True, use_container_width=True, selection_mode="single-row", on_select="rerun")

        # DRILL DOWN DE TERCER NIVEL
        if len(ev_port.selection.rows) > 0:
            idx_p = ev_port.selection.rows[0]
            # Extraemos la ID real basándonos en el orden ordenado de df_visual_p (Debemos asegurar orden)
            deudor_sel_id = df_visual_p.sort_values(by='Días Atraso', ascending=False).iloc[idx_p]['ID']
            deudor_name = df_visual_p.sort_values(by='Días Atraso', ascending=False).iloc[idx_p]['Deudor']
            
            st.divider()
            st.markdown(f"<div class='section-title'>🔍 Expediente Transversal del Sujeto: {deudor_name}</div>", unsafe_allow_html=True)
            
            gest_deudor = df_g_metricas[df_g_metricas['id_deudor'] == deudor_sel_id]
            
            if gest_deudor.empty:
                st.info(f"El asesor {asesor_sel} lamentablemente aún no ha realizado NINGUNA gestión telefónica ni táctica sobre este deudor.")
            else:
                colL, colR = st.columns([1.5, 1])
                
                with colL:
                    st.markdown("**1. Libro Mayor (Gestiones Previas Realizadas por el Gestor):**")
                    st.dataframe(gest_deudor[['fecha_contacto', 'tipo_contacto', 'rpc', 'hubo_compromiso', 'resumen_IA']], hide_index=True, use_container_width=True)
                    
                with colR:
                    st.markdown("**2. ☢️ Escáner Integral de Riesgo (Ley 2300):**")
                    malas = gest_deudor[gest_deudor['alerta_legal'] != 'Ninguna']
                    if not malas.empty:
                        st.warning("Se detectaron grabaciones que violaron la ley (Acoso/Horarios).")
                        for idx_m, mala in malas.iterrows():
                            st.write(f"⚠️ {mala['fecha_contacto']} - **{mala['alerta_legal']}**")
                            
                        if st.button("⚖️ Auditar Riesgo Máximo (Dictamen AI)", key="btn_audit_deudor"):
                            with st.spinner("Construyendo jurisprudencia y elaborando dictamen sancionatorio..."):
                                audio_txt = malas.iloc[0]['alerta_legal']
                                p_obj = f"Eres un Abogado BPO de Compliance. Analiza esta falta cometida por {asesor_sel} al deudor {deudor_name}: '{audio_txt}'. Inventa un diálogo crudo simulado que demuestre esa falta y luego lista los artículos colombianos violados. Sé punitivo y tajante."
                                try:
                                    st.error(model.generate_content(p_obj).text)
                                except:
                                    st.error("Error API")
                    else:
                        st.success("✅ La gerencia certifica que todo el historial de contacto con este cliente cumple con los estándares Constitucionales al 100%. Nivel de riesgo Cero.")


# =========================================================================
# VISTA 2: ASESOR OPERATIVO
# =========================================================================
elif rol_usuario == "👤 Consola de Asesor (Copiloto IA)":
    st.title("⚡ Copilot IA: Asistente Operacional de Planta")
    colA, colB = st.columns([1, 2.5])
    with colA:
        st.subheader("📋 Mi Cartera Asignada Hoy")
        n_asesores = df_asesores['nombre_asesor'].tolist()
        mi_nombre = st.selectbox("Asesor de Planta:", n_asesores)
        cliente_filtro = st.selectbox("Operación Cliente:", ["Todos"] + list(df_deudores['nombre_empresa'].unique()))
        
        df_deudores['asesor_asignado'] = [n_asesores[i % len(n_asesores)] for i in range(len(df_deudores))]
        df_f = df_deudores[df_deudores['asesor_asignado'] == mi_nombre]
        if cliente_filtro != "Todos": df_f = df_f[df_f['nombre_empresa'] == cliente_filtro]
            
        if df_f.empty:
            st.info("Meta lograda o sin clientes asignados bajo este cruce.")
            lista_d = []
            deudor_str = None
        else:
            lista_d = df_f.apply(lambda row: f"ID:{row['id_deudor']} | {row['nombre_completo']}", axis=1).tolist()
            deudor_str = st.selectbox("Seleccionar Caso a Evaluar:", lista_d)
        
        df_visual = df_f[['nombre_completo', 'saldo_adeudado']].copy()
        df_visual.rename(columns={'nombre_completo': 'Titular'}, inplace=True)
        df_visual['Saldo Mora'] = df_visual['saldo_adeudado'].apply(lambda x: f"${x:,.0f}")
        df_visual = df_visual.drop(columns=['saldo_adeudado'])
        # Tabla Nativa Limpia
        st.dataframe(df_visual, hide_index=True, use_container_width=True)

    with colB:
        if deudor_str:
            id_sel = int(deudor_str.split(" | ")[0].replace("ID:", ""))
            deudor = df_f[df_f['id_deudor'] == id_sel].iloc[0]
            score = deudor['riesgo_ai_score']
            
            st.header(f"👤 {deudor['nombre_completo']}")
            m1, m2, m3 = st.columns(3)
            m1.metric("Cartera Mora", f"${deudor['saldo_adeudado']:,.0f}")
            m2.metric("Retardo Días", f"{deudor['dias_mora']} días")
            m3.metric("🧠 Model IA Probabilidad", f"{score*100:.0f}%", delta="Propensión Nudge", delta_color="off")
            
            st.divider()
            tab1, tab2, tab3 = st.tabs(["🪄 Estrategia Omnicanal IA", "🎙️ NLP Auditor PBX", "📝 Historial y CRM Operativo"])
            
            # Traer el historial previo para darle "memoria" a la IA
            mis_llamadas = df_gestiones[df_gestiones['id_deudor'] == id_sel]
            historia_corta = "Cliente virgen, sin gestiones previas."
            if not mis_llamadas.empty:
                historia_corta = " | ".join(mis_llamadas['resumen_IA'].tail(3).fillna("").astype(str).tolist())
            
            with tab1:
                st.markdown("### 🎯 Orquestador Omnicanal (Predictivo)")
                st.caption("La IA estudiará toda la bitácora anterior del deudor, decidirá qué canal (Voz/WA/Mail) es el único matemáticamente funcional hoy, y te redactará el anclaje.")
                
                # Contactos Demo (Prueba Técnica en Vivo):
                cel_simulado = "573216361135"  # Con prefijo país Colombia para API WA
                correo_sim = "edissongranados@gmail.com"

                if st.button("🚀 Evaluar Caso y Generar Estrategia", type="primary"):
                    with st.spinner("La lA está escaneando historial y calculando el canal de menor resistencia..."):
                        p = f"""
                        Eres el Director de la Campaña de Cobranza.
                        Señor(a): {deudor['nombre_completo']}. Mora: ${deudor['saldo_adeudado']:,.0f} desde hace {deudor['dias_mora']} días. Probabilidad: {score*100:.0f}%.
                        Bitácora anterior: '{historia_corta}'.
                        
                        REGLAS:
                        1. NO repitas canales que fracasaron en la bitácora. (Ej. si dice que no contesta, usa WhatsApp, o si es negación rotunda, envía Correo formal).
                        2. Comienza tu respuesta OBLIGATORIAMENTE con uno de estos 3 encabezados:
                           [CANAL: WHATSAPP]
                           [CANAL: LLAMADA]
                           [CANAL: CORREO]
                        3. Debajo del encabezado, redacta el guión o texto final usando Psicología Económica Nudge, de impacto, sin saludos largos.
                        """
                        try:
                            resp = model.generate_content(p).text
                            st.session_state[f'ia_response_{id_sel}'] = resp
                            
                            # Parser sencillo
                            if "WHATSAPP" in resp.upper(): st.session_state[f'ia_canal_{id_sel}'] = "WHATSAPP"
                            elif "CORREO" in resp.upper(): st.session_state[f'ia_canal_{id_sel}'] = "CORREO"
                            else: st.session_state[f'ia_canal_{id_sel}'] = "LLAMADA"
                            
                        except Exception as e:
                            st.error(f"ERROR REAL IA: {str(e)[:300]} | Tipo: {type(e).__name__}")

                # Renderizar estado guardado para que no se pierda si da Clic por ahí
                if f'ia_response_{id_sel}' in st.session_state:
                    ai_texto = st.session_state[f'ia_response_{id_sel}']
                    canal = st.session_state[f'ia_canal_{id_sel}']
                    
                    st.info(ai_texto)
                    
                    # ENLACES NATIVOS PARA DISPARAR LA ACCIÓN AUTOMÁTICA
                    st.divider()
                    st.write("**🕹️ Acciones de 1-Clic a Centrales Operativas:**")
                    colACT1, colACT2 = st.columns(2)
                    
                    with colACT1:
                        import urllib.parse
                        texto_codificado = urllib.parse.quote(ai_texto.replace("[CANAL: WHATSAPP]", "").replace("[CANAL: CORREO]", "").replace("[CANAL: LLAMADA]", "").strip()) 
                        
                        if canal == "WHATSAPP":
                            st.markdown(f"🚥 <a href='https://wa.me/{cel_simulado}?text={texto_codificado}' target='_blank'><button style='background-color:#25D366; color:white; border-radius:5px; padding:8px;'>📱 Enviar WhatsApp con AI Text</button></a>", unsafe_allow_html=True)
                        elif canal == "CORREO":
                            st.markdown(f"🚥 <a href='mailto:{correo_sim}?subject=Notificación Crítica - {deudor['nombre_completo']}&body={texto_codificado}' target='_blank'><button style='background-color:#D44638; color:white; border-radius:5px; padding:8px;'>✉️ Lanzar Servidor de Correo</button></a>", unsafe_allow_html=True)
                        else:
                            st.markdown(f"🚥 <a href='tel:{cel_simulado}' target='_blank'><button style='background-color:#3498db; color:white; border-radius:5px; padding:8px;'>📞 Disparar PBX Telefónico</button></a>", unsafe_allow_html=True)
                            
                    with colACT2:
                        if st.button("✅ Confirmar Envío a Historial (Saliente)"):
                            try:
                                from datetime import datetime
                                c = conn.cursor()
                                fn = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                                
                                c.execute('''
                                    INSERT INTO gestiones 
                                    (id_deudor, asesor_humano, fecha_contacto, tipo_contacto, rpc, duracion_segundos, monto_comprometido, hubo_compromiso, promesa_cumplida, alerta_legal, sentiment_score, resumen_IA)
                                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                                ''', (
                                    id_sel, mi_nombre, fn, f'Emisión Omnicanal: {canal}', 
                                    0, 10, 0, 0, 
                                    0, 'Ninguna', 0.5, f"[ACCIÓN IA ENVIADA]: {ai_texto}"
                                ))
                                conn.commit()
                                st.success("🎯 Acción enviada e inscrita silenciosamente en el historial. Listo para el retorno.")
                                import time
                                time.sleep(1.5)
                                st.rerun()
                            except Exception as e:
                                st.error(f"Error de código: {e}")

            with tab2:
                st.markdown("### Escudo Legal (Supervisión Calidad de Llamada)")
                txt_audio = st.text_area("Grabación Cruda simulada:", "Oiga necesito que pague. Me tienen desesperado. Lo voy a bloquear. Deudor: Yo estoy radicado en ley de insolvencia.")
                if st.button("⚖️ Auditar Audio por Fraudes"):
                    with st.spinner("Auditor forense encendido contra la Ley 2300..."):
                        p2 = f"Audita este diálogo de cobranza: '{txt_audio}'. Especifica violaciones legales puntuales. Explica la sanción monetaria para el BPO."
                        try:
                            st.warning(model.generate_content(p2).text)
                        except: pass

            with tab3:
                if not mis_llamadas.empty:
                    st.write("**Historial del Libro Mayor (Haz Clic en una llamada para leer su bitácora explícita):**")
                    ev_hist = st.dataframe(mis_llamadas[['fecha_contacto', 'tipo_contacto', 'hubo_compromiso', 'alerta_legal']], hide_index=True, use_container_width=True, selection_mode="single-row", on_select="rerun")
                    if len(ev_hist.selection.rows) > 0:
                        idx_sel_hist = ev_hist.selection.rows[0]
                        llam_sel = mis_llamadas.iloc[idx_sel_hist]
                        st.info(f"📝 **Notas Anteriores ({llam_sel['fecha_contacto']}):**\n\n{llam_sel['resumen_IA']}")
                
                with st.form("form_cierre", clear_on_submit=True):
                    st.write("**Registrar Respuesta / Retorno del Deudor**")
                    obs = st.text_area("¿Qué le contestó el titular? (Excusas, Negociación, Fecha de Pago confirmada)")
                    rpc = st.checkbox("El contacto fue Titular Exclusivo (RPC Efectivo)")
                    comp_ptp = st.checkbox("Levantó Promesa Real (PTP) a partir de este retorno")
                    sb = st.form_submit_button("Sincronizar Retorno a Servidor Central")
                    
                    if sb:
                        if not obs:
                            st.error("Debes escribir la objeción o respuesta que te brindó.")
                        else:
                            try:
                                from datetime import datetime
                                c = conn.cursor()
                                fn = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                                monto = deudor['saldo_adeudado'] if comp_ptp else 0
                                
                                c.execute('''
                                    INSERT INTO gestiones 
                                    (id_deudor, asesor_humano, fecha_contacto, tipo_contacto, rpc, duracion_segundos, monto_comprometido, hubo_compromiso, promesa_cumplida, alerta_legal, sentiment_score, resumen_IA)
                                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                                ''', (
                                    id_sel, mi_nombre, fn, 'Retorno (Respuesta Deudor)', 
                                    1 if rpc else 0, 180, monto, 1 if comp_ptp else 0, 
                                    0, 'Ninguna', 0.8, f"[RESPUESTA DEL CLIENTE]: {obs}"
                                ))
                                conn.commit()
                                st.success("✅ Retorno guardado! Los KPIs gerenciales acaban de ser actualizados...")
                                import time
                                time.sleep(1.5)
                                st.rerun()
                            except Exception as e:
                                st.error(f"Error de base de datos: {e}")

elif rol_usuario == "🤝 Portal de Transparencia (Cliente B2B)":
    st.title("🌐 Hub Ejecutivo de Transparencia (B2B)")
    st.markdown("Bienvenido al entorno cifrado de **Auditoría de Cartera y Retornos** operado por Acción Legal BPO.")
    banco_cliente = st.selectbox("Acceso Identificado (Partner):", df_deudores['nombre_empresa'].unique())
    
    df_mi_banco = df_deudores[df_deudores['nombre_empresa'] == banco_cliente]
    mi_asignacion = df_mi_banco['asignacion_inicial'].sum()
    mis_recuperos = mi_asignacion - df_mi_banco['saldo_adeudado'].sum()
    perc_rec = (mis_recuperos/mi_asignacion)*100 if mi_asignacion > 0 else 0

    # Cálculo del nuevo KPI gerencial solicitado
    gestiones_banco = df_gestiones[df_gestiones['id_deudor'].isin(df_mi_banco['id_deudor'])]
    alertas_banco = len(gestiones_banco[gestiones_banco['alerta_legal'] != 'Ninguna'])
    pct_alerta = (alertas_banco / len(gestiones_banco) * 100) if len(gestiones_banco) > 0 else 0

    st.divider()
    st.markdown("### 📊 Tablero de Capital y Riesgo Operativo")
    c1, c2, c3, c4 = st.columns(4)
    c1.metric(f"💼 Volumen Confiado al BPO", f"${mi_asignacion/1e6:,.1f} M")
    c2.metric("🟢 Caja Recuperada a la Vena", f"${mis_recuperos/1e6:,.1f} M", f"{perc_rec:.1f}% Ejecución Real")
    c3.metric("🔴 Saldo Restante en la Calle", f"${df_mi_banco['saldo_adeudado'].sum()/1e6:,.1f} M", delta="- Riesgo Abierto", delta_color="inverse")
    c4.metric("⚖️ Ratio de Infracciones NLP", f"{alertas_banco} / {len(gestiones_banco)} Gestiones", f"{pct_alerta:.1f}% Tasa Fuga", delta_color="inverse")
    
    st.divider()
    
    import plotly.express as px
    import plotly.graph_objects as go
    
    cA, cB = st.columns([1.2, 1.2])
    with cA:
        st.markdown("**📉 Estado de la Cartera Pendiente (Según Perfil IA)**")
        st.caption("Categorización algorítmica de la dificultad de recaudo para el saldo restante.")
        
        categorias = []
        for v in df_mi_banco['riesgo_ai_score']:
            if v >= 0.7: categorias.append("1. Alta Voluntad de Pago")
            elif v >= 0.4: categorias.append("2. Recaudo Diciplinado (Nudge)")
            else: categorias.append("3. Riesgo de Default Legal")
            
        df_mi_banco['Riesgo Segmentado'] = categorias
        cartera_cluster = df_mi_banco.groupby('Riesgo Segmentado')['saldo_adeudado'].sum().reset_index()
        
        figA = px.bar(cartera_cluster, x='Riesgo Segmentado', y='saldo_adeudado', text='saldo_adeudado', 
                      color='Riesgo Segmentado', color_discrete_sequence=['#2ecc71', '#f1c40f', '#e74c3c'])
        figA.update_traces(texttemplate='$%{text:,.0f}', textposition='outside')
        figA.update_layout(showlegend=False, yaxis_title="Monto Adeudado ($)", xaxis_title="", margin=dict(t=10, b=10, l=10, r=10), paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)')
        st.plotly_chart(figA, use_container_width=True)

    with cB:
        st.markdown("**📈 Evolución del Recaudo Histórico**")
        st.caption("Proyección de inyección de caja basada en rendimientos.")
        import numpy as np
        fechas_simuladas = pd.date_range(end=pd.Timestamp.today(), periods=10)
        crecimiento = np.linspace(mi_asignacion*0.05, mis_recuperos if mis_recuperos > 0 else mi_asignacion*0.1, 10)
        crecimiento = crecimiento * (1 + np.random.uniform(-0.05, 0.05, 10))
        df_evolucion = pd.DataFrame({'Fecha': fechas_simuladas, 'Capital Recuperado': crecimiento})
        
        figB = px.area(df_evolucion, x='Fecha', y='Capital Recuperado')
        figB.update_traces(line_color='#27ae60', fillcolor='rgba(39, 174, 96, 0.2)')
        # Format axes tick to dollars
        figB.update_layout(yaxis_tickformat='$~s', xaxis_title="", yaxis_title="Recaudo Acumulado ($)", margin=dict(t=10, b=10, l=10, r=10), paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)')
        st.plotly_chart(figB, use_container_width=True)

    st.divider()
    
    colP1, colP2 = st.columns([1, 1])
    with colP1:
        st.markdown("### 🤖 Plan Estratégico General (IA)")
        st.caption("Orquestación algorítmica de la cobranza masiva.")
        st.info("Nuestra Inteligencia Artificial modela predictivamente la volatilidad de sus deudores para minimizar desgaste operativo y maximizar el flujo de caja diario.")
        
        if st.button("🧠 Evaluar Portafolio y Emitir Plan Táctico Semanal", type="primary"):
            with st.spinner("Modelando..."):
                saldos_rojos = len(df_mi_banco[df_mi_banco['riesgo_ai_score'] < 0.4])
                saldos_verdes = len(df_mi_banco[df_mi_banco['riesgo_ai_score'] >= 0.7])
                p_ejecutivo = f"Actúa como Partner Gerente de Acción Legal BPO hablando a tu cliente {banco_cliente}. Su saldo adeudado total es ${df_mi_banco['saldo_adeudado'].sum():,.0f}. IA clasificó {saldos_verdes} MUY fáciles y {saldos_rojos} bastante difíciles. Redacta 1 párrafo de tranquilidad corporativa enfatizando eficacia y antiacoso, y 3 viñetas con el plan táctico semanal hiper optimizado para recuperar ese dinero. Sé muy elitista."
                try: 
                    st.success(model.generate_content(p_ejecutivo).text)
                except: 
                    pass

    with colP2:
        st.markdown("### ⚖️ Auditoría Habeas Data (Ley 1581 y 2300)")
        st.caption("Filtros NLP en vivo protegiendo el respeto a su marca comercial.")
        violaciones = df_gestiones[(df_gestiones['id_deudor'].isin(df_mi_banco['id_deudor'])) & (df_gestiones['alerta_legal'] != 'Ninguna')]
        num_v = len(violaciones)
        
        if num_v == 0:
            st.success("✔️ Fuga Reputacional Activa: 0%")
            st.write("Su portafolio opera bajo pulcritud estadística máxima. No hay quejas de acoso ni extralimitación telefónica el día de hoy.")
        else:
            pct_riesgo = (num_v / len(df_mi_banco)) * 100 if len(df_mi_banco) > 0 else 0
            st.warning(f"⚠️ Alertas Ley 2300 Interceptadas: {num_v} caso(s)")
            st.write(f"Nuestros radares de lenguaje Natural Language Processing (NLP) suspendieron comunicaciones riesgosas o potencialmente acosadoras afectando al {pct_riesgo:.2f}% de la muestra telefónica.")
            st.markdown("**🔍 Auditoría Detallada (Seleccione un caso para emitir sanción)**")
            df_alertas_show = violaciones[['fecha_contacto', 'asesor_humano', 'tipo_contacto', 'alerta_legal', 'resumen_IA']].copy()
            df_alertas_show.rename(columns={
                'fecha_contacto': 'Timestamp',
                'asesor_humano': 'Responsable BPO',
                'tipo_contacto': 'Emisión',
                'alerta_legal': 'Categoría Falta',
                'resumen_IA': 'Evidencia NLP (Transcrito)'
            }, inplace=True)
            
            tabla_infracciones = st.dataframe(df_alertas_show, hide_index=True, use_container_width=True, selection_mode="single-row", on_select="rerun")
            
            if len(tabla_infracciones.selection.rows) > 0:
                idx_sel = tabla_infracciones.selection.rows[0]
                caso_seleccionado = df_alertas_show.iloc[idx_sel]
                asesor_culpable = caso_seleccionado['Responsable BPO']
                falta = caso_seleccionado['Categoría Falta']
                evidencia = caso_seleccionado['Evidencia NLP (Transcrito)']
                
                st.error(f"**Foco Legal Activo:** Expediente bajo lupa para **{asesor_culpable}**")
                
                bf1, bf2 = st.columns(2)
                
                with bf1:
                    if st.button("🔍 Auditar Escena del Delito y Riesgo Legal (GenAI)", use_container_width=True):
                        with st.spinner("Reconstruyendo el hilo conductual y buscando jurisprudencia..."):
                            p_riesgo = f"""
                            Eres un Bufete de Abogados B2B en Colombia especializado en Compliance y Fintech.
                            Cliente: Banco {banco_cliente}. En nuestra plataforma interceptamos una gestión del asesor '{asesor_culpable}'. 
                            Categoría de la Alarma: '{falta}'. 
                            Pedacito de la evidencia: '{evidencia}'.
                            
                            TU MISIÓN FORENSE:
                            1. SIMULACIÓN: Invéntate de manera muy realista cómo sonó el resto de la llamada amenazante/indebida (1 párrafo).
                            2. DAÑO FINANCIERO: Explícale al gerente del banco detalladamente por qué exactamente esa frase, bajo la Ley 2300 de 2023 (Ley de Dejen de Fregar) o la Ley 1581, los va a meter en problemas legales y a qué multas por la Superintendencia Financiera se estarían exponiendo si no contáramos con nuestro BPO interceptándolo.
                            """
                            try:
                                st.warning(model.generate_content(p_riesgo).text)
                            except:
                                st.error("Error conectando con la IA forense.")
                                
                with bf2:
                    if st.button(f"🚨 Emitir Orden de Sanción contra el Asesor", type="primary", use_container_width=True):
                        with st.spinner("Redactando memorando de sanción oficial..."):
                            p_sanc = f"Eres el Vicepresidente de Relaciones Laborales y Compliance de 'Acción Legal BPO'. Estamos reportando en vivo al cliente Corporate {banco_cliente} que el agente '{asesor_culpable}' cometió la falta grave contemplada bajo la categoría '{falta}'. La transcripción del motor de IA comprobó que: '{evidencia}'. Escribe un Memorando Disciplinario corto, directo y de alto rigor corporativo (Estilo Carta Abierta de RRHH). Dicta a '{asesor_culpable}' su penalidad temporal (ej. desconexión del sistema, curso obligatorio de la Ley 2300, etc.) para que el banco lo lea y recupere su absoluta confianza en nuestro control interno."
                            try:
                                st.info(model.generate_content(p_sanc).text)
                            except:
                                st.error("Error conectando con Recursos Humanos AI.")
