import streamlit as st
from modules import database as db
from modules import roles

# --- 1. FUNCIÓN DE ESTILOS CSS (DISEÑO) ---
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
                height: 100%;
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

            /* LOGO EN LA BARRA LATERAL */
            .sidebar-logo {
                font-family: 'Helvetica Neue', sans-serif;
                font-weight: 800;
                font-size: 24px;
                background: -webkit-linear-gradient(45deg, #FF4B4B, #FF914D);
                -webkit-background-clip: text;
                -webkit-text-fill-color: transparent;
                text-align: center;
                margin-bottom: 20px;
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
        
        # --- ZONA CENTRAL (HERO SECTION CON NUEVO LOGO) ---
        # Este SVG integra el nombre KORTEXA con un diseño de red neuronal en la 'O' y 'X'
        svg_logo_hero = """
        <svg width="100%" height="150" viewBox="0 0 800 150" xmlns="http://www.w3.org/2000/svg">
            <defs>
                <linearGradient id="grad_hero" x1="0%" y1="0%" x2="100%" y2="0%">
                    <stop offset="0%" style="stop-color:#FF4B4B;stop-opacity:1" />
                    <stop offset="100%" style="stop-color:#FF914D;stop-opacity:1" />
                </linearGradient>
            </defs>
            <g opacity="0.2" stroke="url(#grad_hero)" stroke-width="1" fill="none">
                <circle cx="250" cy="75" r="40" />
                <circle cx="550" cy="75" r="40" />
                <path d="M250 35 L550 115 M250 115 L550 35 M150 75 L650 75" />
                <circle cx="150" cy="75" r="5" fill="#FFF" opacity="0.6"/>
                <circle cx="650" cy="75" r="5" fill="#FFF" opacity="0.6"/>
                <circle cx="400" cy="75" r="8" fill="#FFF" opacity="0.8"/>
            </g>
            <text x="400" y="100" font-family="'Helvetica Neue', sans-serif" font-weight="900" font-size="100" fill="url(#grad_hero)" text-anchor="middle" letter-spacing="-2">KORTEXA AI</text>
        </svg>
        """

        # Renderizamos el contenido central como un ÚNICO bloque HTML
        hero_html = f"""
            <div style="text-align: center; padding-top: 20px; padding-bottom: 30px;">
                <div style="margin-bottom: 10px;">
                    {svg_logo_hero}
                </div>
                <h3 style="font-weight: 300; opacity: 0.9; font-size: 26px; margin-top: 0; font-family: 'Helvetica Neue', sans-serif;">
                    Tu Segundo Cerebro Digital
                </h3>
                <p style="opacity: 0.6; font-size: 16px; max-width: 600px; margin: 20px auto; line-height: 1.6;">
                    Plataforma de inteligencia aumentada para potenciar tu productividad creativa y analítica en un entorno minimalista y seguro.
                </p>
            </div>
        """
        st.markdown(hero_html, unsafe_allow_html=True)
        
        # Columnas de características (Value Props)
        st.write("") # Espacio
        c1, c2, c3 = st.columns(3)
        with c1:
            st.markdown("""
                <div class="feature-card">
                    <div style="font-size: 32px; margin-bottom: 15px;">🧠</div>
                    <div style="font-weight: 700; margin-bottom: 8px; font-size: 18px;">IA Multimodal</div>
                    <div style="font-size: 13px; opacity: 0.7; line-height: 1.4;">Procesamiento avanzado de texto, imágenes y documentos PDF en un solo flujo.</div>
                </div>
            """, unsafe_allow_html=True)
        with c2:
            st.markdown("""
                <div class="feature-card">
                    <div style="font-size: 32px; margin-bottom: 15px;">⚡</div>
                    <div style="font-weight: 700; margin-bottom: 8px; font-size: 18px;">Respuesta Instantánea</div>
                    <div style="font-size: 13px; opacity: 0.7; line-height: 1.4;">Infraestructura optimizada para una interacción fluida y sin latencia.</div>
                </div>
            """, unsafe_allow_html=True)
        with c3:
            st.markdown("""
                <div class="feature-card">
                    <div style="font-size: 32px; margin-bottom: 15px;">🛡️</div>
                    <div style="font-weight: 700; margin-bottom: 8px; font-size: 18px;">Privacidad Total</div>
                    <div style="font-size: 13px; opacity: 0.7; line-height: 1.4;">Tus datos y conversaciones están encriptados y son solo tuyos.</div>
                </div>
            """, unsafe_allow_html=True)

        # --- BARRA LATERAL (LOGIN) ---
        st.sidebar.markdown('<div class="sidebar-logo">🌀 KORTEXA AI</div>', unsafe_allow_html=True)
        
        st.sidebar.info("👋 Bienvenido. Inicia sesión para acceder a tu espacio.")
        
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
                    st.success("¡Cuenta creada! Puedes ingresar.")
                else: 
                    st.error("El usuario ya existe.")
        
        # Retornamos None para que el resto de la app no se ejecute
        return None, None, None, None, None

    # ==========================================
    # CASO B: USUARIO LOGUEADO (APP COMPLETA)
    # ==========================================
    else:
        st.sidebar.markdown('<div class="sidebar-logo" style="font-size: 20px; text-align: left;">🌀 KORTEXA AI</div>', unsafe_allow_html=True)
        st.sidebar.caption(f"Sesión activa: {st.session_state.usuario}")
        
        # Botón Nuevo Chat con estilo
        if st.sidebar.button("➕ Nuevo Chat", type="primary", use_container_width=True):
            st.session_state.chat_id = None
            st.rerun()
        
        st.sidebar.divider()
        
        # 1. SELECCIÓN DE ROL
        st.sidebar.subheader("🧠 Asistente Experto")
        
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
        with st.sidebar.expander("🛠️ Herramientas", expanded=False):
            
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