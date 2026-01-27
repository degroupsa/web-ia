import streamlit as st
import base64
from modules import database as db
from modules import roles

def render_sidebar():
    # Título de la App
    st.sidebar.title("🔗 Kortexa AI")
    
    # --- LOGICA DE LOGIN ---
    if not st.session_state.usuario:
        t1, t2 = st.sidebar.tabs(["Ingresar", "Crear Cuenta"])
        with t1:
            u = st.text_input("User")
            p = st.text_input("Pass", type="password")
            if st.button("Ingresar"):
                if db.login(u, p): 
                    st.session_state.usuario = u
                    st.query_params["user_token"] = u
                    st.rerun()
                else: st.error("Error de credenciales")
        with t2:
            nu = st.text_input("New User")
            np = st.text_input("New Pass", type="password")
            if st.button("Crear"):
                if db.crear_user(nu, np): st.success("Creado! Loguéate.")
                else: st.error("Usuario ya existe")
        return None, None, None, None

    # --- USUARIO LOGUEADO ---
    else:
        st.sidebar.caption(f"👤 {st.session_state.usuario}")
        
        # Botón Nuevo Chat
        if st.sidebar.button("➕ Nuevo Chat", type="primary", use_container_width=True):
            st.session_state.chat_id = None
            st.rerun()
        
        st.sidebar.divider()
        
        # --- AQUÍ ESTÁ EL CAMBIO DEL TOOLTIP ---
        mensaje_ayuda = "Selecciona el trabajo que quieres realizar y automáticamente se asignarán los roles al chat para un mejor trabajo."
        
        st.sidebar.subheader("🛠️ Selección de Roles", help=mensaje_ayuda)
        # ---------------------------------------
        
        tareas = roles.obtener_tareas()
        
        # Buscamos el índice del Asistente General para que sea el default
        # (Asegúrate de que el nombre coincida exactamente con roles.py)
        default_role = "Asistente General (Multimodal)"
        idx = 0
        if default_role in tareas:
            idx = list(tareas.keys()).index(default_role)
        
        # Callbacks para limpiar estado al cambiar de rol
        def reset(): st.session_state.chat_id = None
        
        rol_sel = st.sidebar.selectbox("Experto:", list(tareas.keys()), index=idx, on_change=reset)
        
        # Toggles de configuración
        c1, c2 = st.sidebar.columns(2)
        web = c1.toggle("🌍 Research", value=False, help="La IA buscará automáticamente si lo necesita. Actívalo para forzar la búsqueda.")
        img_manual = c2.toggle("🎨 Imágen", value=False, help="La IA creará solamente imágenes basándose en lo que le indiques.")
        
        st.sidebar.divider()
        
        # Historial de Conversaciones
        st.sidebar.subheader("🗂️ Tus conversaciones")
        for sid, dat in db.obtener_sesiones(st.session_state.usuario):
            tipo = "primary" if sid == st.session_state.chat_id else "secondary"
            # Cortamos el título si es muy largo para que no rompa el diseño
            titulo = dat.get('titulo', 'Chat')
            if len(titulo) > 25: titulo = titulo[:25] + "..."
            
            if st.sidebar.button(f"💬 {titulo}", key=sid, use_container_width=True, type=tipo):
                st.session_state.chat_id = sid
                st.rerun()
                
        if st.sidebar.button("Cerrar sesión"):
            st.query_params.clear()
            st.session_state.usuario = None
            st.session_state.chat_id = None
            st.rerun()
            
        return rol_sel, web, img_manual, tareas

def render_chat_msgs(msgs):
    for m in msgs:
        with st.chat_message(m["role"]):
            if m["content"].startswith("http") and " " not in m["content"]:
                st.image(m["content"], width=350)
            else:
                st.markdown(m["content"])