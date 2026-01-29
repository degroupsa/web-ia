import streamlit as st
from modules import database as db
from modules import roles
from modules import google_auth
from modules import styles
import os
import base64  # <--- AGREGADO: Necesario para leer la imagen

# --- FUNCIÓN AUXILIAR (NUEVA) ---
def get_img_as_base64(file_path):
    try:
        with open(file_path, "rb") as f:
            data = f.read()
        return base64.b64encode(data).decode()
    except:
        return None

# --- INTERFAZ PRINCIPAL ---
def render_sidebar():
    # 1. Cargamos el CSS externo
    styles.cargar_css()
    
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

        # --- SIDEBAR LOGIN ---
        with st.sidebar:
            col_icon, col_text = st.columns([0.6, 3])
            with col_icon:
                if os.path.exists("icon.png"): st.image("icon.png", width=50)
                else: st.write("⚡")
            with col_text:
                st.markdown('<div class="sidebar-brand">KORTEXA AI</div>', unsafe_allow_html=True)
                st.caption("Inteligencia Neuronal")
            
            st.divider()

            try: google_url = google_auth.get_login_url()
            except: google_url = "#" 

            t_crear, t_login = st.tabs(["✔️ Crear Cuenta", "🔐 Ingresar"])
            
            # PESTAÑA 1: CREAR
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

            # PESTAÑA 2: LOGIN
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
            st.caption("© 2026 Kortexa AI & DE Group Enterprise.")

        return None, None, None, None, None

    # ==========================================
    # CASO B: PANTALLA APP (LOGUEADO)
    # ==========================================
    else:
        with st.sidebar:
            col_icon, col_text = st.columns([0.6, 2])
            with col_icon:
                if os.path.exists("icon.png"): st.image("icon.png", width=55)
                else: st.write("⚡")
            with col_text:
                st.markdown('<div class="sidebar-brand">KORTEXA AI</div>', unsafe_allow_html=True)
                st.caption("Inteligencia Neuronal")
            
            st.divider()
            
            # --- PERFIL ---
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
            
            # --- SELECCION DE ROL ---
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

def render_welcome_screen(rol_desc):
    styles.render_welcome_html()
    
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

# --- NUEVA FUNCIÓN: CABECERA MINI CON LOGO K ---
def render_mini_header():
    # Intentamos cargar el logo usando la función auxiliar
    img_b64 = get_img_as_base64("icon.png")
    
    if img_b64:
        # Si existe, inyectamos el HTML con la imagen codificada
        icon_html = f'<img src="data:image/png;base64,{img_b64}" style="width: 35px; height: 35px; margin-right: 12px; vertical-align: middle; border-radius: 5px;">'
    else:
        # Fallback al rayo si falla
        icon_html = '<span style="font-size: 25px; margin-right: 10px;">⚡</span>'

    st.markdown(f"""
    <div style="
        display: flex; 
        align-items: center; 
        justify-content: center; 
        margin-bottom: 25px; 
        padding-bottom: 15px; 
        border-bottom: 1px solid rgba(255,255,255,0.05);
        animation: fadeIn 0.5s ease-in-out;
    ">
        {icon_html}
        <h3 style="
            margin:0; 
            font-size: 22px; 
            background: linear-gradient(90deg, #FF5F1F, #FFAA00); 
            -webkit-background-clip: text; 
            -webkit-text-fill-color: transparent; 
            font-weight: 800; 
            font-family: 'Inter', sans-serif;
            display: inline-block;
            vertical-align: middle;
            line-height: 1.5;
        ">
            KORTEXA AI
        </h3>
    </div>
    <style>
        @keyframes fadeIn {{
            from {{ opacity: 0; transform: translateY(-10px); }}
            to {{ opacity: 1; transform: translateY(0); }}
        }}
    </style>
    """, unsafe_allow_html=True)