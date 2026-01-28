import streamlit as st
from modules import database as db
from modules import roles
from modules import google_auth
import os

# --- 1. ESTILOS CSS ---
def cargar_estilos_css():
    st.markdown("""
        <style>
            /* Ajustes Generales */
            .block-container {
                padding-top: 4rem; 
                padding-bottom: 5rem;
            }
            
            #MainMenu {visibility: hidden;}
            footer {visibility: hidden;}
            
            /* TÍTULO DE MARCA CENTRAL */
            .brand-title {
                font-family: 'Inter', sans-serif;
                font-weight: 800;
                font-size: 50px;
                text-align: center;
                background: linear-gradient(135deg, #FFFFFF 0%, #B0B0B0 100%);
                -webkit-background-clip: text;
                -webkit-text-fill-color: transparent;
                margin-bottom: 10px;
                letter-spacing: -1.5px;
            }

            /* SUBTÍTULO */
            .hero-subtitle {
                font-family: 'Inter', sans-serif;
                font-weight: 500;
                font-size: 22px;
                text-align: center;
                color: #FF5F1F;
                margin-bottom: 20px;
            }

            /* DESCRIPCIÓN */
            .hero-text {
                font-family: 'Source Sans Pro', sans-serif;
                font-size: 17px;
                text-align: center;
                color: #999999;
                max-width: 800px;
                margin: 0 auto 40px auto;
                line-height: 1.6;
            }

            /* CAJAS DE INFORMACIÓN */
            .info-grid {
                display: flex;
                justify-content: center;
                gap: 20px;
                margin-bottom: 50px;
                flex-wrap: wrap;
            }
            .info-box {
                background: rgba(255, 255, 255, 0.03);
                border: 1px solid rgba(255, 255, 255, 0.08);
                border-radius: 12px;
                padding: 15px 20px;
                text-align: center;
                min-width: 140px;
                display: flex;
                flex-direction: column;
                align-items: center;
                transition: transform 0.3s ease;
                cursor: default;
            }
            .info-box:hover {
                background: rgba(255, 255, 255, 0.06);
                transform: translateY(-5px);
                border-color: #FF5F1F;
            }
            .info-icon { font-size: 26px; margin-bottom: 8px; }
            .info-value { font-size: 15px; font-weight: 700; color: #E0E0E0; display: block; margin-bottom: 2px; }
            .info-label { font-size: 11px; color: #888; text-transform: uppercase; letter-spacing: 0.5px; }
            .ig-link { text-decoration: none; color: #E0E0E0; }
            .ig-link:hover { color: #FF5F1F; }

            /* ESTILOS SIDEBAR MEJORADOS */
            section[data-testid="stSidebar"] {
                background-color: #0E1117; 
                border-right: 1px solid rgba(255, 255, 255, 0.1);
            }
            
            .sidebar-brand {
                font-size: 18px;
                font-weight: 700;
                background: -webkit-linear-gradient(45deg, #FF5F1F, #FF0000);
                -webkit-background-clip: text;
                -webkit-text-fill-color: transparent;
                margin-top: 10px;
            }
            
            .stButton button {
                border-radius: 8px;
                font-weight: 600;
            }
            
            .separator {
                display: flex;
                align-items: center;
                text-align: center;
                color: #555;
                font-size: 12px;
                margin: 15px 0;
            }
            .separator::before, .separator::after {
                content: '';
                flex: 1;
                border-bottom: 1px solid #333;
            }
            .separator::before { margin-right: 10px; }
            .separator::after { margin-left: 10px; }
            
            a[kind="primary"] {
                background-color: #ffffff !important;
                color: #000000 !important;
                border: 1px solid #ddd !important;
            }

            /* PERFIL COMPACTO */
            .user-profile-compact {
                display: flex;
                align-items: center;
                padding: 12px;
                background: rgba(255, 255, 255, 0.03);
                border: 1px solid rgba(255, 255, 255, 0.05);
                border-radius: 10px;
                margin-bottom: 20px;
            }
            .user-avatar {
                width: 38px;
                height: 38px;
                background: linear-gradient(135deg, #FF5F1F, #D60000);
                border-radius: 50%;
                display: flex;
                justify-content: center;
                align-items: center;
                font-weight: 700;
                color: white;
                margin-right: 12px;
                font-size: 16px;
                box-shadow: 0 2px 5px rgba(0,0,0,0.3);
            }
            .user-info {
                display: flex;
                flex-direction: column;
                line-height: 1.2;
            }
            .user-name {
                font-size: 14px;
                font-weight: 600;
                color: #FFF;
            }
            .user-role {
                font-size: 11px;
                color: #888;
                margin-top: 2px;
            }
        </style>
    """, unsafe_allow_html=True)

# --- 2. INTERFAZ PRINCIPAL ---
def render_sidebar():
    cargar_estilos_css()
    
    # ==========================================
    # CASO A: PANTALLA DE INICIO (NO LOGUEADO)
    # ==========================================
    if not st.session_state.usuario:
        
        # --- ZONA CENTRAL ---
        c1, c2, c3 = st.columns([1, 1.5, 1]) 
        with c2:
            if os.path.exists("logo.png"):
                st.image("logo.png", use_container_width=True)
            else:
                st.markdown('<div class="brand-title">KORTEXA AI</div>', unsafe_allow_html=True)

        st.markdown('<div class="hero-subtitle">Ecosistema de Inteligencia Neuronal Corporativa</div>', unsafe_allow_html=True)
        
        st.markdown("""
            <div class="hero-text">
                Bienvenido al núcleo Kortexa. Nuestra plataforma multimodal unifica análisis de datos, 
                visión artificial y generación de contenido. Diseñado por el equipo DE Group para ofrecer 
                <b>precisión profesional</b> garantizando tu <b>seguridad total</b> mediante 
                <b>Cifrado de Extremo a Extremo</b>.
            </div>
        """, unsafe_allow_html=True)

        st.markdown("""
            <div class="info-grid">
                <div class="info-box"><span class="info-icon">🤖</span><span class="info-value">Roles IA</span><span class="info-label">Pre-cargados</span></div>
                <div class="info-box"><span class="info-icon">✨</span><span class="info-value">Prompts</span><span class="info-label">Avanzados</span></div>
                <div class="info-box"><span class="info-icon">💎</span><span class="info-value">Planes</span><span class="info-label">Mes / Año</span></div>
                <div class="info-box"><span class="info-icon">💬</span><a href="https://instagram.com/kortexa.ai" target="_blank" class="ig-link"><span class="info-value">@kortexa.ai</span></a><span class="info-label">Soporte</span></div>
            </div>
        """, unsafe_allow_html=True)

        # --- SIDEBAR ---
        with st.sidebar:
            col_icon, col_text = st.columns([1, 3])
            with col_icon:
                if os.path.exists("icon.png"): 
                    st.image("icon.png", width=50)
                else:
                    st.write("⚡")
            with col_text:
                st.markdown('<div class="sidebar-brand">KORTEXA AI</div>', unsafe_allow_html=True)
                st.caption("Inteligencia Neuronal")
            
            st.divider()

            try: google_url = google_auth.get_login_url()
            except: google_url = "#" 

            t_crear, t_login = st.tabs(["✔️ Crear Cuenta", "🔐 Ingresar"])
            
            # PESTAÑA 1: CREAR CUENTA
            with t_crear:
                st.write("")
                st.markdown("##### Nuevo Usuario")
                nu = st.text_input("Nombre de Usuario", key="u_new", placeholder="Ej: Kortexaia")
                np = st.text_input("Contraseña", type="password", key="p_new", placeholder="@TuContraseña")
                st.write("")
                if st.button("Registrarse", use_container_width=True, type="primary"):
                    if db.crear_user(nu, np): 
                        st.session_state.usuario = nu
                        st.query_params["user_token"] = nu 
                        st.toast(f"¡Bienvenido, {nu}!", icon="🚀")
                        st.rerun()
                    else: 
                        st.error("Ese nombre de Usuario ya existe.")
                
                st.markdown('<div class="separator">o regístrate con</div>', unsafe_allow_html=True)
                st.link_button("🔵 Continuar con Google", google_url, use_container_width=True)

            # PESTAÑA 2: INGRESAR
            with t_login:
                st.write("")
                st.markdown("##### Iniciar Sesión")
                u = st.text_input("Nombre de Usuario", key="u_log", placeholder="Ej: Kortexaia")
                p = st.text_input("Contraseña", type="password", key="p_log", placeholder="@TuContraseña")
                st.write("")
                if st.button("Ingresar", use_container_width=True):
                    if db.login(u, p):
                        st.session_state.usuario = u
                        st.query_params["user_token"] = u 
                        st.rerun()
                    else:
                        st.error("Datos incorrectos.")
                
                st.markdown('<div class="separator">o inicia con</div>', unsafe_allow_html=True)
                st.link_button("🔵 Continuar con Google", google_url, use_container_width=True)
            
            st.markdown("---")
            st.caption("© 2026 Kortexa AI & DE Group Enterprise. All rights reserved.")

        return None, None, None, None, None

    # ==========================================
    # CASO B: PANTALLA DE LA APP (LOGUEADO)
    # ==========================================
    else:
        with st.sidebar:
            col_icon, col_text = st.columns([1, 3])
            with col_icon:
                if os.path.exists("icon.png"):
                    st.image("icon.png", width=45)
                else:
                    st.write("⚡")
            with col_text:
                st.markdown('<div class="sidebar-brand">KORTEXA</div>', unsafe_allow_html=True)
            
            st.divider()
            
            # --- TU PERFIL COMPACTO ---
            inicial = st.session_state.usuario[0].upper()
            st.markdown(f"""
                <div class="user-profile-compact">
                    <div class="user-avatar">{inicial}</div>
                    <div class="user-info">
                        <span class="user-name">{st.session_state.usuario}</span>
                        <span class="user-role">Plan Enterprise</span>
                    </div>
                </div>
            """, unsafe_allow_html=True)
            
            if st.button("📁 Nuevo Chat", type="primary", use_container_width=True):
                st.session_state.chat_id = None
                st.rerun()
            
            st.markdown("### 🧠 Panel de Control")
            
            tareas = roles.obtener_tareas()
            idx = list(tareas.keys()).index("Asistente General (Multimodal)") if "Asistente General (Multimodal)" in tareas else 0
            def reset(): st.session_state.chat_id = None
            rol = st.selectbox("Rol Seleccionado:", list(tareas.keys()), index=idx, on_change=reset)
            
            with st.expander("⚙️ Configuración"):
                web = st.toggle("Búsqueda Web", value=True)
                img = st.toggle("Generar Imágenes")
                up = st.file_uploader("Adjuntar Archivos", label_visibility="collapsed")
                if up: st.toast("Archivo Adjunto", icon="📂")
            
            st.markdown("### 🗂️ Tus Conversaciones")
            sesiones = db.obtener_sesiones(st.session_state.usuario)
            
            with st.container(height=300, border=False):
                if not sesiones: st.caption("No hay chats recientes.")
                for sid, dat in sesiones:
                    tipo = "primary" if sid == st.session_state.chat_id else "secondary"
                    if st.button(f"💬 {dat.get('titulo','Chat')[:15]}...", key=sid, type=tipo, use_container_width=True):
                        st.session_state.chat_id = sid
                        st.rerun()
            
            st.divider()
            if st.button("🔒 Cerrar Sesión", use_container_width=True):
                st.session_state.usuario = None
                st.query_params.clear() 
                st.rerun()
            
        return rol, web, img, up, tareas

def render_chat_msgs(msgs):
    if not msgs: return
    for m in msgs:
        with st.chat_message(m["role"]):
            if m["content"].startswith("http") and " " not in m["content"]:
                st.image(m["content"], width=400)
            else:
                st.markdown(m["content"])

# --- NUEVA FUNCIÓN: PANTALLA DE BIENVENIDA (TEXTO KORTEXA) ---
def render_welcome_screen(rol_desc):
    # Saludo principal
    st.markdown(f"""
    <div style="text-align: center; margin-bottom: 40px; margin-top: 20px;">
        <h1 style="background: linear-gradient(to right, #FF5F1F, #FF8C00); -webkit-background-clip: text; -webkit-text-fill-color: transparent; font-weight: 800; font-size: 60px;">Hola! Soy Kortexa</h1>
        <h3 style="color: #E0E0E0; font-weight: 400; font-size: 20px;">Estoy aquí para potenciar tus proyectos. ¿En qué puedo ayudarte hoy?</h3>
        <p style="color: #999; font-size: 16px; margin-top: 10px;">Si eres nuevo en la app, <b>Puedo enseñarte a utilizarme!</b> Solo tiene que preguntarme, "Como funcionas?" o "Como te utilizo?"</p>
    </div>
    """, unsafe_allow_html=True)
    
    # Tarjetas de sugerencias (Prompt Starters)
    c1, c2, c3 = st.columns(3)
    
    with c1:
        with st.container(border=True):
            st.markdown("📄 **Análisis de Datos**")
            st.caption("Carga un documento y pídeme que extraiga la información clave.")
    with c2:
        with st.container(border=True):
            st.markdown("❓ **Ayuda y Soporte**")
            st.caption("Si eres nuevo, prueba preguntarme: *'¿Cómo funcionas?'* o *'Dame un tour'*.")
    with c3:
        with st.container(border=True):
            st.markdown("🎨 **Creatividad**")
            st.caption("Genera imágenes únicas o redacta contenido original en segundos.")