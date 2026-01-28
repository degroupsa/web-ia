import streamlit as st
from modules import database as db
from modules import roles
from PIL import Image
import os

# --- 1. FUNCIÓN DE ESTILOS CSS ---
def cargar_estilos_css():
    st.markdown("""
        <style>
            /* OCULTAR ELEMENTOS POR DEFECTO */
            #MainMenu {visibility: hidden;}
            header {visibility: hidden;}
            footer {visibility: hidden;}
            .stDeployButton {display:none;}
            
            /* AJUSTES GENERALES */
            .block-container {
                padding-top: 2rem;
                padding-bottom: 2rem;
            }
            
            /* TARJETAS */
            .feature-card {
                background: rgba(255, 255, 255, 0.05);
                border: 1px solid rgba(255, 255, 255, 0.1);
                border-radius: 16px;
                padding: 20px;
                text-align: center;
                transition: all 0.3s ease;
                height: 100%;
            }
            .feature-card:hover {
                transform: translateY(-5px);
                border-color: #FF5F1F;
                box-shadow: 0 5px 15px rgba(255, 95, 31, 0.2);
            }
            
            /* TEXTOS */
            .hero-title {
                font-family: sans-serif;
                font-weight: 900;
                font-size: 48px;
                letter-spacing: -1px;
                margin: 0;
                background: -webkit-linear-gradient(45deg, #FF5F1F, #FF0000);
                -webkit-background-clip: text;
                -webkit-text-fill-color: transparent;
                text-transform: uppercase;
                text-align: center;
            }
            .hero-subtitle {
                font-weight: 400;
                opacity: 0.9;
                font-size: 20px;
                margin-top: 5px;
                text-align: center;
                color: #E0E0E0;
            }
            .hero-text {
                opacity: 0.7;
                font-size: 15px;
                max-width: 600px;
                margin: 15px auto;
                line-height: 1.5;
                text-align: center;
                color: #C0C0C0;
            }
            
            /* LOGO BARRA LATERAL */
            .sidebar-logo {
                font-weight: 800;
                font-size: 24px;
                background: -webkit-linear-gradient(45deg, #FF5F1F, #FF0000);
                -webkit-background-clip: text;
                -webkit-text-fill-color: transparent;
                margin-bottom: 20px;
            }
        </style>
    """, unsafe_allow_html=True)

# --- 2. FUNCIÓN PRINCIPAL ---
def render_sidebar():
    cargar_estilos_css()
    
    # ==========================================
    # CASO A: USUARIO NO LOGUEADO (LANDING PAGE)
    # ==========================================
    if not st.session_state.usuario:
        
        # 1. RENDERIZAR TU IMAGEN (LOGO)
        # Usamos columnas para centrar la imagen perfectamente
        col1, col2, col3 = st.columns([1, 2, 1])
        with col2:
            # Busca logo.png o logo.jpg
            if os.path.exists("logo.png"):
                st.image("logo.png", use_container_width=True)
            elif os.path.exists("logo.jpg"):
                st.image("logo.jpg", use_container_width=True)
            else:
                st.warning("⚠️ Falta el archivo logo.png en la carpeta")

        # 2. TEXTOS
        st.markdown('<div class="hero-title">KORTEXA AI</div>', unsafe_allow_html=True)
        st.markdown('<div class="hero-subtitle">Inteligencia Neuronal Avanzada</div>', unsafe_allow_html=True)
        st.markdown('<div class="hero-text">Potencia tu flujo de trabajo con nuestra arquitectura multimodal de baja latencia.</div>', unsafe_allow_html=True)
        
        # 3. CARACTERÍSTICAS
        st.write("") 
        c1, c2, c3 = st.columns(3)
        
        with c1:
            st.markdown("""
                <div class="feature-card">
                    <div style="font-size:30px; margin-bottom:10px;">🧠</div>
                    <div style="font-weight:700;">Multimodal</div>
                    <div style="font-size:13px; opacity:0.7;">Texto, visión y documentos.</div>
                </div>
            """, unsafe_allow_html=True)
            
        with c2:
            st.markdown("""
                <div class="feature-card">
                    <div style="font-size:30px; margin-bottom:10px;">⚡</div>
                    <div style="font-weight:700;">Velocidad</div>
                    <div style="font-size:13px; opacity:0.7;">Respuestas instantáneas.</div>
                </div>
            """, unsafe_allow_html=True)
            
        with c3:
            st.markdown("""
                <div class="feature-card">
                    <div style="font-size:30px; margin-bottom:10px;">🛡️</div>
                    <div style="font-weight:700;">Seguridad</div>
                    <div style="font-size:13px; opacity:0.7;">Encriptación total.</div>
                </div>
            """, unsafe_allow_html=True)

        # --- BARRA LATERAL ---
        st.sidebar.markdown('<div class="sidebar-logo">⚡ KORTEXA AI</div>', unsafe_allow_html=True)
        st.sidebar.info("Inicia sesión para acceder al sistema.")
        
        t1, t2 = st.sidebar.tabs(["Ingresar", "Registrar"])
        
        with t1:
            u = st.text_input("Usuario", key="l_u")
            p = st.text_input("Contraseña", type="password", key="l_p")
            st.write("")
            if st.button("🚀 Conectar", type="primary", use_container_width=True):
                if db.login(u, p): 
                    st.session_state.usuario = u
                    st.rerun()
                else: 
                    st.error("Error de credenciales.")
        
        with t2:
            nu = st.text_input("Nuevo Usuario", key="n_u")
            np = st.text_input("Nueva Contraseña", type="password", key="n_p")
            st.write("")
            if st.button("✨ Crear Nodo", use_container_width=True):
                if db.crear_user(nu, np): 
                    st.success("Creado con éxito.")
                else: 
                    st.error("Usuario existente.")
        
        return None, None, None, None, None

    # ==========================================
    # CASO B: USUARIO LOGUEADO
    # ==========================================
    else:
        st.sidebar.markdown('<div class="sidebar-logo">⚡ KORTEXA AI</div>', unsafe_allow_html=True)
        st.sidebar.caption(f"🟢 En línea: {st.session_state.usuario}")
        
        if st.sidebar.button("➕ Nuevo Chat", type="primary", use_container_width=True):
            st.session_state.chat_id = None
            st.rerun()
        
        st.sidebar.divider()
        st.sidebar.subheader("🧠 Módulos")
        
        tareas = roles.obtener_tareas()
        idx = 0
        if "Asistente General (Multimodal)" in tareas:
            idx = list(tareas.keys()).index("Asistente General (Multimodal)")
            
        def reset(): st.session_state.chat_id = None
        rol_sel = st.sidebar.selectbox("Rol:", list(tareas.keys()), index=idx, on_change=reset, label_visibility="collapsed")
        
        st.sidebar.markdown("---")
        with st.sidebar.expander("🛠️ Herramientas"):
            c1, c2 = st.columns(2)
            with c1: web = st.toggle("Web", False)
            with c2: img = st.toggle("Arte", False)
            up = st.file_uploader("Archivo", type=["pdf","png","jpg"], label_visibility="collapsed")
            if up: st.success("Cargado")

        st.sidebar.divider()
        st.sidebar.subheader("🗂️ Historial")
        sesiones = db.obtener_sesiones(st.session_state.usuario)
        if not sesiones: st.sidebar.caption("Sin datos.")
        
        for sid, dat in sesiones:
            tipo = "primary" if sid == st.session_state.chat_id else "secondary"
            tit = dat.get('titulo','Chat')[:18]
            if st.sidebar.button(f"🗨️ {tit}...", key=sid, use_container_width=True, type=tipo):
                st.session_state.chat_id = sid
                st.rerun()
        
        st.sidebar.divider()
        if st.sidebar.button("🔒 Desconectar", use_container_width=True):
            st.query_params.clear()
            st.session_state.usuario = None
            st.rerun()
            
        return rol_sel, web, img, up, tareas

def render_chat_msgs(msgs):
    if not msgs: return
    for m in msgs:
        with st.chat_message(m["role"]):
            if m["content"].startswith("http") and " " not in m["content"]:
                st.image(m["content"], width=400)
            else:
                st.markdown(m["content"])