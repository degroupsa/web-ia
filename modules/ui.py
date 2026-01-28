import streamlit as st
from modules import database as db
from modules import roles

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
                padding-top: 1rem;
                padding-bottom: 2rem;
            }
            
            /* TARJETAS DE CARACTERÍSTICAS */
            .feature-card {
                background: rgba(255, 255, 255, 0.05);
                border: 1px solid rgba(255, 255, 255, 0.1);
                border-radius: 12px;
                padding: 20px;
                text-align: center;
                transition: transform 0.3s ease;
                height: 100%;
            }
            .feature-card:hover {
                transform: translateY(-5px);
                border-color: #FF4B4B;
            }
            
            /* ESTILOS DE TEXTO PERSONALIZADOS */
            .hero-subtitle {
                font-weight: 300; 
                opacity: 0.9; 
                font-size: 26px; 
                margin-top: -10px; 
                text-align: center;
                font-family: 'Helvetica Neue', sans-serif;
            }
            .hero-text {
                opacity: 0.6; 
                font-size: 16px; 
                max-width: 600px; 
                margin: 20px auto; 
                line-height: 1.6; 
                text-align: center;
            }
            
            /* LOGO BARRA LATERAL */
            .sidebar-logo {
                font-weight: 800;
                font-size: 24px;
                background: -webkit-linear-gradient(45deg, #FF4B4B, #FF914D);
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
        
        # 1. RENDERIZAR LOGO (SVG) - BLOQUE INDEPENDIENTE
        # Este SVG dibuja "KORTEXA AI" con el diseño de red neuronal
        st.markdown("""
            <div style="text-align: center; margin-bottom: 0px;">
                <svg width="100%" height="140" viewBox="0 0 800 140" xmlns="http://www.w3.org/2000/svg">
                    <defs>
                        <linearGradient id="grad_hero" x1="0%" y1="0%" x2="100%" y2="0%">
                            <stop offset="0%" style="stop-color:#FF4B4B;stop-opacity:1" />
                            <stop offset="100%" style="stop-color:#FF914D;stop-opacity:1" />
                        </linearGradient>
                    </defs>
                    <g opacity="0.2" stroke="url(#grad_hero)" stroke-width="1" fill="none">
                        <path d="M250 35 L550 115 M250 115 L550 35 M150 75 L650 75" />
                        <circle cx="400" cy="75" r="50" opacity="0.1" fill="url(#grad_hero)"/>
                    </g>
                    <text x="400" y="95" font-family="sans-serif" font-weight="900" font-size="100" fill="url(#grad_hero)" text-anchor="middle" letter-spacing="-3">KORTEXA AI</text>
                </svg>
            </div>
        """, unsafe_allow_html=True)

        # 2. RENDERIZAR TEXTOS - BLOQUE INDEPENDIENTE (Para evitar errores)
        st.markdown('<div class="hero-subtitle">Tu Segundo Cerebro Digital</div>', unsafe_allow_html=True)
        st.markdown('<div class="hero-text">Plataforma de inteligencia aumentada para potenciar tu productividad creativa y analítica en un entorno minimalista y seguro.</div>', unsafe_allow_html=True)
        
        # 3. CARACTERÍSTICAS
        st.write("") 
        c1, c2, c3 = st.columns(3)
        
        with c1:
            st.markdown("""
                <div class="feature-card">
                    <div style="font-size: 30px;">🧠</div>
                    <div style="font-weight: 700; margin: 10px 0;">IA Multimodal</div>
                    <div style="font-size: 13px; opacity: 0.7;">Texto, imágenes y documentos en un solo flujo.</div>
                </div>
            """, unsafe_allow_html=True)
            
        with c2:
            st.markdown("""
                <div class="feature-card">
                    <div style="font-size: 30px;">⚡</div>
                    <div style="font-weight: 700; margin: 10px 0;">Instantáneo</div>
                    <div style="font-size: 13px; opacity: 0.7;">Infraestructura optimizada sin latencia.</div>
                </div>
            """, unsafe_allow_html=True)
            
        with c3:
            st.markdown("""
                <div class="feature-card">
                    <div style="font-size: 30px;">🛡️</div>
                    <div style="font-weight: 700; margin: 10px 0;">Privacidad</div>
                    <div style="font-size: 13px; opacity: 0.7;">Tus datos encriptados y protegidos.</div>
                </div>
            """, unsafe_allow_html=True)

        # --- BARRA LATERAL ---
        st.sidebar.markdown('<div class="sidebar-logo">🌀 KORTEXA AI</div>', unsafe_allow_html=True)
        st.sidebar.info("👋 Bienvenido. Inicia sesión para acceder.")
        
        t1, t2 = st.sidebar.tabs(["Ingresar", "Registrarse"])
        
        with t1:
            u = st.text_input("Usuario", key="login_user")
            p = st.text_input("Contraseña", type="password", key="login_pass")
            st.write("")
            if st.button("🚀 Ingresar", type="primary", use_container_width=True):
                if db.login(u, p): 
                    st.session_state.usuario = u
                    st.query_params["user_token"] = u
                    st.rerun()
                else: 
                    st.error("Credenciales incorrectas.")
        
        with t2:
            nu = st.text_input("Nuevo Usuario", key="new_user")
            np = st.text_input("Nueva Contraseña", type="password", key="new_pass")
            st.write("")
            if st.button("✨ Crear Cuenta", use_container_width=True):
                if db.crear_user(nu, np): 
                    st.success("¡Cuenta creada!")
                else: 
                    st.error("El usuario ya existe.")
        
        return None, None, None, None, None

    # ==========================================
    # CASO B: USUARIO LOGUEADO
    # ==========================================
    else:
        st.sidebar.markdown('<div class="sidebar-logo" style="text-align:left; font-size:20px;">🌀 KORTEXA AI</div>', unsafe_allow_html=True)
        st.sidebar.caption(f"👤 {st.session_state.usuario}")
        
        if st.sidebar.button("➕ Nuevo Chat", type="primary", use_container_width=True):
            st.session_state.chat_id = None
            st.rerun()
        
        st.sidebar.divider()
        st.sidebar.subheader("🧠 Experto")
        
        tareas = roles.obtener_tareas()
        idx = 0
        default_role = "Asistente General (Multimodal)"
        if default_role in tareas:
            idx = list(tareas.keys()).index(default_role)
            
        def reset(): st.session_state.chat_id = None
        rol_sel = st.sidebar.selectbox("Rol:", list(tareas.keys()), index=idx, on_change=reset, label_visibility="collapsed")
        
        st.sidebar.markdown("---")
        with st.sidebar.expander("🛠️ Herramientas"):
            c1, c2 = st.columns(2)
            with c1: web = st.toggle("Web", False)
            with c2: img = st.toggle("Arte", False)
            up = st.file_uploader("Archivo", type=["pdf","png","jpg"], label_visibility="collapsed")
            if up: st.success("📎 Cargado")

        st.sidebar.divider()
        st.sidebar.subheader("🗂️ Historial")
        sesiones = db.obtener_sesiones(st.session_state.usuario)
        if not sesiones: st.sidebar.caption("Vacío.")
        
        for sid, dat in sesiones:
            tipo = "primary" if sid == st.session_state.chat_id else "secondary"
            tit = dat.get('titulo','Chat')[:18]
            if st.sidebar.button(f"🗨️ {tit}...", key=sid, use_container_width=True, type=tipo):
                st.session_state.chat_id = sid
                st.rerun()
        
        st.sidebar.divider()
        if st.sidebar.button("🔒 Salir", use_container_width=True):
            st.query_params.clear()
            st.session_state.usuario = None
            st.rerun()
            
        return rol_sel, web, img, up, tareas

# --- 3. RENDERIZADO DE CHAT ---
def render_chat_msgs(msgs):
    if not msgs: return
    for m in msgs:
        with st.chat_message(m["role"]):
            if m["content"].startswith("http") and " " not in m["content"]:
                st.image(m["content"], width=400)
            else:
                st.markdown(m["content"])