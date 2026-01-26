import streamlit as st
import base64
from modules import database as db
from modules import roles

def render_sidebar():
    st.sidebar.title("🔥 DevMaster AI")
    
    # Login
    if not st.session_state.usuario:
        t1, t2 = st.sidebar.tabs(["Entrar", "Crear"])
        with t1:
            u = st.text_input("User"); p = st.text_input("Pass", type="password")
            if st.button("Entrar"):
                if db.login(u, p): 
                    st.session_state.usuario = u
                    st.query_params["user_token"] = u
                    st.rerun()
                else: st.error("Error")
        with t2:
            nu = st.text_input("New User"); np = st.text_input("New Pass", type="password")
            if st.button("Crear"):
                if db.crear_user(nu, np): st.success("OK")
                else: st.error("Existe")
        return None, None, None, None

    # Usuario Logueado
    else:
        st.sidebar.caption(f"👤 {st.session_state.usuario}")
        if st.sidebar.button("➕ Nuevo Chat", type="primary", use_container_width=True):
            st.session_state.chat_id = None
            st.rerun()
        
        st.sidebar.divider()
        st.sidebar.subheader("🛠️ Panel")
        
        tareas = roles.obtener_tareas()
        idx = list(tareas.keys()).index("Asistente General") if "Asistente General" in tareas else 0
        
        # Callbacks para limpiar estado
        def reset(): st.session_state.chat_id = None
        
        rol_sel = st.sidebar.selectbox("Experto:", list(tareas.keys()), index=idx, on_change=reset)
        
        c1, c2 = st.sidebar.columns(2)
        web = c1.toggle("🌍 Web", False)
        # NOTA: El toggle de imagen sigue existiendo para forzarlo, 
        # pero ahora tendremos detección automática también.
        img_manual = c2.toggle("🎨 Img", False)
        
        st.sidebar.divider()
        st.sidebar.subheader("🗂️ Chats")
        for sid, dat in db.obtener_sesiones(st.session_state.usuario):
            tipo = "primary" if sid == st.session_state.chat_id else "secondary"
            if st.sidebar.button(f"💬 {dat.get('titulo','Chat')}", key=sid, use_container_width=True, type=tipo):
                st.session_state.chat_id = sid
                st.rerun()
                
        if st.sidebar.button("Salir"):
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