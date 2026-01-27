import streamlit as st
from modules import database as db
from modules import roles

# --- FUNCIÓN DE ESTILOS CSS (DISEÑO) ---
def cargar_estilos_css():
    st.markdown("""
        <style>
            /* 1. OCULTAR MENÚS DE STREAMLIT */
            #MainMenu {visibility: hidden;}
            header {visibility: hidden;}
            footer {visibility: hidden;}
            .stDeployButton {display:none;}
            
            /* 2. AJUSTAR ESPACIOS BARRA LATERAL */
            section[data-testid="stSidebar"] > div:first-child {
                padding-top: 1rem;
            }
            
            /* 3. AJUSTAR ESPACIOS CHAT */
            .block-container {
                padding-top: 2rem;
                padding-bottom: 2rem;
            }

            /* 4. TARJETAS */
            [data-testid="stVerticalBlock"] > [style*="flex-direction: column;"] > [data-testid="stVerticalBlock"] {
                border-radius: 10px;
                border: 1px solid rgba(250, 250, 250, 0.1);
            }
            
            /* 5. BOTONES PERSONALIZADOS */
            button[kind="primary"] {
                border-radius: 8px;
                font-weight: bold;
                transition: all 0.3s ease;
            }
            button[kind="primary"]:hover {
                transform: scale(1.02);
                box-shadow: 0px 4px 15px rgba(255, 75, 75, 0.4);
            }
        </style>
    """, unsafe_allow_html=True)

# --- FUNCIÓN PRINCIPAL BARRA LATERAL ---
def render_sidebar():
    # Inyectamos el diseño
    cargar_estilos_css()
    
    st.sidebar.title("🔗 Kortexa AI")
    
    # --- PANTALLA DE LOGIN ---
    if not st.session_state.usuario:
        t1, t2 = st.sidebar.tabs(["Ingresar", "Crear Cuenta"])
        
        with t1:
            u = st.text_input("Usuario", key="login_user")
            p = st.text_input("Contraseña", type="password", key="login_pass")
            if st.button("Ingresar"):
                if db.login(u, p): 
                    st.session_state.usuario = u
                    st.query_params["user_token"] = u
                    st.rerun()
                else: 
                    st.error("Credenciales incorrectas.")
        
        with t2:
            nu = st.text_input("Nuevo Usuario", key="new_user")
            np = st.text_input("Nueva Contraseña", type="password", key="new_pass")
            if st.button("Crear Cuenta"):
                if db.crear_user(nu, np): 
                    st.success("¡Cuenta creada! Ingresa en la otra pestaña.")
                else: 
                    st.error("El usuario ya existe.")
        
        return None, None, None, None, None

    # --- PANTALLA PRINCIPAL (LOGUEADO) ---
    else:
        st.sidebar.caption(f"👤 {st.session_state.usuario}")
        
        # Botón Nuevo Chat
        if st.sidebar.button("➕ Nuevo Chat", type="primary", use_container_width=True):
            st.session_state.chat_id = None
            st.rerun()
        
        st.sidebar.divider()
        
        # 1. SELECCIÓN DE ROL (Con tus textos)
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
            label_visibility="collapsed",
            help="Elige la personalidad de la IA para tu tarea actual."
        )
        
        # 2. HERRAMIENTAS
        st.sidebar.markdown("---")
        with st.sidebar.expander("📎 Herramientas", expanded=False):
            
            # Toggles
            web_mode = st.toggle("🌍 Web", value=False, help="Activar búsqueda en Google.")
            img_mode = st.toggle("🎨 Arte", value=False, help="Activar generador de imágenes.")
            
            # Subida de archivo
            st.markdown("### 📂 Subir archivo")
            up_file = st.file_uploader(
                "PDF o Imagen", 
                type=["pdf", "png", "jpg", "jpeg"], 
                label_visibility="collapsed"
            )
            
            if up_file:
                st.success(f"✅ Cargado: {up_file.name}")
        
        # 3. HISTORIAL
        st.sidebar.divider()
        st.sidebar.subheader("🗂️ Tus Conversaciones")
        
        sesiones = db.obtener_sesiones(st.session_state.usuario)
        
        if not sesiones:
            st.sidebar.info("Sin historial reciente.")
        
        for sid, dat in sesiones:
            tipo = "primary" if sid == st.session_state.chat_id else "secondary"
            # Cortamos el título si es muy largo
            titulo_raw = dat.get('titulo', 'Chat sin título')
            titulo = titulo_raw[:20] + "..." if len(titulo_raw) > 20 else titulo_raw
            
            if st.sidebar.button(f"💬 {titulo}", key=sid, use_container_width=True, type=tipo):
                st.session_state.chat_id = sid
                st.rerun()
                
        st.sidebar.divider()
        if st.sidebar.button("Cerrar Sesión", use_container_width=True):
            st.query_params.clear()
            st.session_state.usuario = None
            st.session_state.chat_id = None
            st.rerun()
            
        return rol_sel, web_mode, img_mode, up_file, tareas

# --- RENDERIZADO DE MENSAJES ---
def render_chat_msgs(msgs):
    if not msgs:
        return
    for m in msgs:
        with st.chat_message(m["role"]):
            if m["content"].startswith("http") and " " not in m["content"]:
                st.image(m["content"], width=350)
            else:
                st.markdown(m["content"])