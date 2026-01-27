import streamlit as st
from modules import database as db
from modules import roles

# --- FUNCIÓN NUEVA: ESTILOS CSS PERSONALIZADOS ---
def cargar_estilos_css():
    st.markdown("""
        <style>
            /* 1. OCULTAR MENÚS DE STREAMLIT (Los círculos blancos y pie de página) */
            #MainMenu {visibility: hidden;}
            header {visibility: hidden;}
            footer {visibility: hidden;}
            .stDeployButton {display:none;}
            
            /* 2. REDUCIR ESPACIO VACÍO BARRA LATERAL (El hueco rojo) */
            section[data-testid="stSidebar"] > div:first-child {
                padding-top: 1rem;
            }
            
            /* 3. BORRAR ESPACIO VACÍO ARRIBA DEL CHAT */
            .block-container {
                padding-top: 2rem;
                padding-bottom: 2rem;
            }

            /* 4. ESTILO DE TARJETAS (Para la bienvenida y alertas) */
            [data-testid="stVerticalBlock"] > [style*="flex-direction: column;"] > [data-testid="stVerticalBlock"] {
                border-radius: 10px;
                border: 1px solid rgba(250, 250, 250, 0.1);
            }
            
            /* 5. BOTONES MÁS BONITOS (Efecto Hover) */
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

# --- FUNCIÓN 1: BARRA LATERAL ---
def render_sidebar():
    # INYECTAMOS LOS ESTILOS AL INICIO
    cargar_estilos_css()
    
    # Título de la App
    st.sidebar.title("🔗 Kortexa AI")
    
    # --- LOGICA DE LOGIN ---
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
                    st.error("Error de credenciales o usuario no registrado.")
        
        with t2:
            nu = st.text_input("Crear Usuario", key="new_user")
            np = st.text_input("Crear Contraseña", type="password", key="new_pass")
            if st.button("Crear Cuenta"):
                if db.crear_user(nu, np): 
                    st.success("¡Cuenta creada! Por favor ingresa desde la pestaña 'Ingresar'.")
                else: 
                    st.error("El usuario ya existe.")
        
        return None, None, None, None, None

    # --- INTERFAZ DE USUARIO LOGUEADO ---
    else:
        st.sidebar.caption(f"👤 Conectado como: {st.session_state.usuario}")
        
        # Botón para limpiar el chat actual
        if st.sidebar.button("➕ Nuevo Chat", type="primary", use_container_width=True):
            st.session_state.chat_id = None
            st.rerun()
        
        st.sidebar.divider()
        
        # 1. SELECCIÓN DE ROL
        mensaje_ayuda = "Selecciona el trabajo que quieres realizar y automáticamente se asignarán los roles necesarios."
        st.sidebar.subheader("🧠 Rol del Asistente", help=mensaje_ayuda)
        
        tareas = roles.obtener_tareas()
        
        # Buscamos el índice del rol por defecto
        default_role = "Asistente General (Multimodal)"
        idx = 0
        if default_role in tareas:
            idx = list(tareas.keys()).index(default_role)
        
        # Callback para reiniciar chat al cambiar de rol
        def reset(): st.session_state.chat_id = None
        
        rol_sel = st.sidebar.selectbox(
            "Selecciona un experto:", 
            list(tareas.keys()), 
            index=idx, 
            on_change=reset,
            label_visibility="collapsed"
        )
        
        # 2. MENÚ DESPLEGABLE DE HERRAMIENTAS
        st.sidebar.markdown("---")
        with st.sidebar.expander("📎 Herramientas", expanded=False):
            st.caption("Configuración del chat actual:")
            
            # Botones verticales
            web_mode = st.toggle("🌍 Web", value=False, help="Fuerza a la IA a buscar información actualizada en internet.")
            img_mode = st.toggle("🎨 Arte", value=False, help="Activa el modo de generación de imágenes.")
            
            st.markdown("### 📂 Subir archivo")
            up_file = st.file_uploader(
                "Sube un PDF o una Imágen", 
                type=["pdf", "png", "jpg", "jpeg"], 
                label_visibility="collapsed"
            )
            
            if up_file:
                st.success(f"✅ Archivo listo: {up_file.name}")
        
        # 3. HISTORIAL DE CHATS
        st.sidebar.divider()
        st.sidebar.subheader("🗂️ Tus Conversaciones")
        
        sesiones = db.obtener_sesiones(st.session_state.usuario)
        
        if not sesiones:
            st.sidebar.info("No hay chats guardados.")
        
        for sid, dat in sesiones:
            tipo = "primary" if sid == st.session_state.chat_id else "secondary"
            titulo_raw = dat.get('titulo', 'Chat sin título')
            titulo = titulo_raw[:22] + "..." if len(titulo_raw) > 22 else titulo_raw
            
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

# --- FUNCIÓN 2: RENDERIZAR MENSAJES ---
def render_chat_msgs(msgs):
    if not msgs:
        return
    for m in msgs:
        with st.chat_message(m["role"]):
            if m["content"].startswith("http") and " " not in m["content"]:
                st.image(m["content"], width=350)
            else:
                st.markdown(m["content"])