import streamlit as st
from modules import database as db
from modules import roles

# --- 1. FUNCIÓN DE ESTILOS CSS (DISEÑO & LOGO) ---
def cargar_estilos_css():
    st.markdown("""
        <style>
            /* OCULTAR ELEMENTOS POR DEFECTO */
            #MainMenu {visibility: hidden;}
            header {visibility: hidden;}
            footer {visibility: hidden;}
            .stDeployButton {display:none;}
            
            /* AJUSTES DE ESPACIADO */
            .block-container {
                padding-top: 1rem;
                padding-bottom: 2rem;
            }
            
            /* ESTILO PARA LAS TARJETAS DE CARACTERÍSTICAS */
            .feature-card {
                background: rgba(255, 255, 255, 0.05);
                border: 1px solid rgba(255, 255, 255, 0.1);
                border-radius: 12px;
                padding: 20px;
                text-align: center;
                transition: transform 0.3s ease;
            }
            .feature-card:hover {
                transform: translateY(-5px);
                border-color: #FF4B4B;
            }
            
            /* BOTONES PERSONALIZADOS */
            button[kind="primary"] {
                border-radius: 8px;
                font-weight: 600;
                box-shadow: 0 4px 14px 0 rgba(255, 75, 75, 0.39);
                transition: all 0.2s ease-in-out;
            }
            button[kind="primary"]:hover {
                transform: scale(1.02);
            }
        </style>
    """, unsafe_allow_html=True)

# --- 2. FUNCIÓN PRINCIPAL DE INTERFAZ ---
def render_sidebar():
    # Inyectamos el CSS
    cargar_estilos_css()
    
    # ==========================================
    # CASO A: USUARIO NO LOGUEADO (LANDING PAGE)
    # ==========================================
    if not st.session_state.usuario:
        
        # --- ZONA CENTRAL (HERO SECTION) ---
        # Este SVG es el logo dibujado con código
        svg_logo = """
        <svg width="120" height="120" viewBox="0 0 100 100" xmlns="http://www.w3.org/2000/svg">
            <defs>
                <linearGradient id="grad1" x1="0%" y1="0%" x2="100%" y2="100%">
                    <stop offset="0%" style="stop-color:#FF4B4B;stop-opacity:1" />
                    <stop offset="100%" style="stop-color:#FF914D;stop-opacity:1" />
                </linearGradient>
            </defs>
            <path fill="url(#grad1)" d="M50 5 L88 27 V73 L50 95 L12 73 V27 Z M50 20 L75 35 V65 L50 80 L25 65 V35 Z M50 35 L60 41 V59 L50 65 L40 59 V41 Z" opacity="0.9"/>
            <circle cx="50" cy="50" r="6" fill="#FFFFFF" opacity="0.8"/>
            <circle cx="50" cy="20" r="3" fill="#FFFFFF" opacity="0.5"/>
            <circle cx="88" cy="27" r="3" fill="#FFFFFF" opacity="0.5"/>
            <circle cx="88" cy="73" r="3" fill="#FFFFFF" opacity="0.5"/>
            <circle cx="50" cy="95" r="3" fill="#FFFFFF" opacity="0.5"/>
            <circle cx="12" cy="73" r="3" fill="#FFFFFF" opacity="0.5"/>
            <circle cx="12" cy="27" r="3" fill="#FFFFFF" opacity="0.5"/>
        </svg>
        """

        # Renderizamos el contenido central
        st.markdown(f"""
            <div style="text-align: center; padding-top: 40px; padding-bottom: 20px;">
                <div style="margin-bottom: 20px;">
                    {svg_logo}
                </div>
                <h1 style="font-size: 55px; font-weight: 800; letter-spacing: -1.5px; margin: 0; 
                           background: -webkit-linear-gradient(45deg, #FF4B4B, #FF914D); 
                           -webkit-background-clip: text; -webkit-text-fill-color: transparent;">
                    KORTEXA AI
                </h1>
                <h3 style="font-weight: 300; opacity: 0.9; font-size: 24px; margin-top: 10px;">
                    Inteligencia Aumentada para Profesionales
                </h3>
                <p style="opacity: 0.6; font-size: 16px; max-width: 600px; margin: 20px auto; line-height: 1.6;">
                    Una suite potente y minimalista diseñada para potenciar tu productividad.
                    <br>Análisis de documentos • Generación Creativa • Asistencia Experta
                </p>
            </div>
        """, unsafe_allow_html=True)
        
        # Columnas de características (Value Props)
        st.write("") # Espacio
        c1, c2, c3 = st.columns(3)
        with c1:
            st.markdown("""
                <div class="feature-card">
                    <div style="font-size: 30px; margin-bottom: 10px;">🧠</div>
                    <div style="font-weight: bold; margin-bottom: 5px;">Multimodal</div>
                    <div style="font-size: 12px; opacity: 0.7;">Procesa texto, imágenes y PDFs en tiempo real.</div>
                </div>
            """, unsafe_allow_html=True)
        with c2:
            st.markdown("""
                <div class="feature-card">
                    <div style="font-size: 30px; margin-bottom: 10px;">⚡</div>
                    <div style="font-weight: bold; margin-bottom: 5px;">Ultra Rápido</div>
                    <div style="font-size: 12px; opacity: 0.7;">Arquitectura optimizada para respuestas inmediatas.</div>
                </div>
            """, unsafe_allow_html=True)
        with c3:
            st.markdown("""
                <div class="feature-card">
                    <div style="font-size: 30px; margin-bottom: 10px;">🔒</div>
                    <div style="font-weight: bold; margin-bottom: 5px;">Seguro</div>
                    <div style="font-size: 12px; opacity: 0.7;">Tus datos y conversaciones están protegidos.</div>
                </div>
            """, unsafe_allow_html=True)

        # --- BARRA LATERAL (LOGIN) ---
        st.sidebar.markdown(f"""
            <div style="text-align: center; margin-bottom: 20px;">
                {svg_logo.replace('width="120"', 'width="60"').replace('height="120"', 'height="60"')}
            </div>
        """, unsafe_allow_html=True)
        
        st.sidebar.info("👋 Bienvenido. Inicia sesión para acceder.")
        
        t1, t2 = st.sidebar.tabs(["Ingresar", "Registrarse"])
        
        with t1:
            u = st.text_input("Usuario", key="login_user")
            p = st.text_input("Contraseña", type="password", key="login_pass")
            st.write("")
            if st.button("🚀 Ingresar al Sistema", type="primary", use_container_width=True):
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
                    st.success("¡Cuenta creada! Ingresa en la otra pestaña.")
                else: 
                    st.error("El usuario ya existe.")
        
        # Retornamos None para que el resto de la app no se ejecute
        return None, None, None, None, None

    # ==========================================
    # CASO B: USUARIO LOGUEADO (APP COMPLETA)
    # ==========================================
    else:
        st.sidebar.markdown("### 🌀 Kortexa AI")
        st.sidebar.caption(f"Sesión activa: {st.session_state.usuario}")
        
        # Botón Nuevo Chat con estilo
        if st.sidebar.button("➕ Nuevo Chat", type="primary", use_container_width=True):
            st.session_state.chat_id = None
            st.rerun()
        
        st.sidebar.divider()
        
        # 1. SELECCIÓN DE ROL
        st.sidebar.subheader("🧠 Rol del Asistente")
        
        tareas = roles.obtener_tareas()
        # Buscar índice por defecto
        default_role = "Asistente General (Multimodal)"
        idx = 0
        if default_role in tareas:
            idx = list(tareas.keys()).index(default_role)
        
        def reset(): st.session_state.chat_id = None
        
        rol_sel = st.sidebar.selectbox(
            "Selecciona tu experto:", 
            list(tareas.keys()), 
            index=idx, 
            on_change=reset,
            label_visibility="collapsed"
        )
        
        # 2. HERRAMIENTAS
        st.sidebar.markdown("---")
        with st.sidebar.expander("🛠️ Panel de Herramientas", expanded=False):
            
            c_tog1, c_tog2 = st.columns(2)
            with c_tog1:
                web_mode = st.toggle("Web", value=False, help="Buscar en Google")
            with c_tog2:
                img_mode = st.toggle("Arte", value=False, help="Generar Imágenes")
            
            st.caption("Subir Documentos")
            up_file = st.file_uploader(
                "Arrastra tu archivo aquí", 
                type=["pdf", "png", "jpg", "jpeg"], 
                label_visibility="collapsed"
            )
            
            if up_file:
                st.success(f"📎 {up_file.name}")
        
        # 3. HISTORIAL
        st.sidebar.divider()
        st.sidebar.subheader("🗂️ Historial")
        
        sesiones = db.obtener_sesiones(st.session_state.usuario)
        
        if not sesiones:
            st.sidebar.caption("No hay chats recientes.")
        
        for sid, dat in sesiones:
            tipo = "primary" if sid == st.session_state.chat_id else "secondary"
            # Cortamos título
            titulo_raw = dat.get('titulo', 'Chat sin título')
            titulo = titulo_raw[:22] + "..." if len(titulo_raw) > 22 else titulo_raw
            
            if st.sidebar.button(f"🗨️ {titulo}", key=sid, use_container_width=True, type=tipo):
                st.session_state.chat_id = sid
                st.rerun()
                
        st.sidebar.divider()
        if st.sidebar.button("🔒 Cerrar Sesión", use_container_width=True):
            st.query_params.clear()
            st.session_state.usuario = None
            st.session_state.chat_id = None
            st.rerun()
            
        return rol_sel, web_mode, img_mode, up_file, tareas

# --- 3. RENDERIZADO DE MENSAJES DEL CHAT ---
def render_chat_msgs(msgs):
    if not msgs:
        return
    for m in msgs:
        with st.chat_message(m["role"]):
            if m["content"].startswith("http") and " " not in m["content"]:
                # Es una imagen
                st.image(m["content"], width=400)
            else:
                # Es texto
                st.markdown(m["content"])