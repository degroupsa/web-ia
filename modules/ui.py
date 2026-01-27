import streamlit as st
from modules import database as db
from modules import roles

def render_sidebar():
    # Título de la App
    st.sidebar.title("🔗 Kortexa AI")
    
    # --- LOGICA DE LOGIN ---
    # Si no hay usuario en sesión, mostramos el login y retornamos None para detener la app principal
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
                    st.error("Error de credenciales o usuario no encontrado.")
        
        with t2:
            nu = st.text_input("Nuevo Usuario", key="new_user")
            np = st.text_input("Nueva Contraseña", type="password", key="new_pass")
            if st.button("Crear Cuenta"):
                if db.crear_user(nu, np): 
                    st.success("¡Cuenta creada! Por favor ingresa desde la pestaña 'Ingresar'.")
                else: 
                    st.error("El usuario ya existe.")
        
        # Retornamos una tupla de Nones para indicar que no hay sesión activa
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
        mensaje_ayuda = "Selecciona el trabajo que quieres realizar y automáticamente se asignarán los roles al chat para un mejor trabajo."
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
        
        # 2. MENÚ DESPLEGABLE DE HERRAMIENTAS (Clean UI)
        st.sidebar.markdown("---")
        # Usamos un expander para ocultar la complejidad hasta que el usuario la necesite
        with st.sidebar.expander("📎 Adjuntos y Herramientas", expanded=False):
            st.caption("Configuración del mensaje actual:")
            
            # Columnas para los interruptores
            c1, c2 = st.columns(2)
            web_mode = c1.toggle("🌍 Web", value=False, help="Fuerza a la IA a buscar información actualizada en internet.")
            img_mode = c2.toggle("🎨 Arte", value=False, help="Activa el modo de generación de imágenes DALL-E 3.")
            
            st.markdown("### 📂 Subir archivo")
            up_file = st.file_uploader(
                "Sube un PDF o una Imagen", 
                type=["pdf", "png", "jpg", "jpeg"], 
                label_visibility="collapsed"
            )
            
            # Feedback visual dentro del expander
            if up_file:
                st.success(f"✅ Archivo listo: {up_file.name}")
        
        # 3. HISTORIAL DE CHATS
        st.sidebar.divider()
        st.sidebar.subheader("🗂️ Historial")
        
        sesiones = db.obtener_sesiones(st.session_state.usuario)
        
        if not sesiones:
            st.sidebar.info("No hay chats guardados.")
        
        for sid, dat in sesiones:
            # Estilo del botón según si es el chat activo
            tipo = "primary" if sid == st.session_state.chat_id else "secondary"
            
            # Acortar título si es muy largo
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
            
        # Retornamos todas las variables necesarias a app.py
        return rol_sel, web_mode, img_mode, up_file, tareas