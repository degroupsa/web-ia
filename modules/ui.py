import streamlit as st
from modules import database as db
from modules import roles

def render_sidebar():
    st.sidebar.title("🔗 Kortexa AI")
    
    # --- LOGIN ---
    if not st.session_state.usuario:
        t1, t2 = st.sidebar.tabs(["Ingresar", "Crear"])
        with t1:
            u = st.text_input("User"); p = st.text_input("Pass", type="password")
            if st.button("Entrar"):
                if db.login(u, p): 
                    st.session_state.usuario = u; st.query_params["user_token"] = u; st.rerun()
                else: st.error("Error")
        with t2:
            nu = st.text_input("N_User"); np = st.text_input("N_Pass", type="password")
            if st.button("Crear"):
                if db.crear_user(nu, np): st.success("Creado")
                else: st.error("Existe")
        return None, None, None, None, None # Retornamos vacíos

    # --- APP PRINCIPAL ---
    else:
        st.sidebar.caption(f"👤 {st.session_state.usuario}")
        if st.sidebar.button("➕ Nuevo Chat", type="primary", use_container_width=True):
            st.session_state.chat_id = None; st.rerun()
        
        st.sidebar.divider()
        
        # 1. SELECCIÓN DE ROL
        st.sidebar.subheader("🧠 Rol del Asistente")
        tareas = roles.obtener_tareas()
        idx = list(tareas.keys()).index("Asistente General (Multimodal)") if "Asistente General (Multimodal)" in tareas else 0
        def reset(): st.session_state.chat_id = None
        rol_sel = st.sidebar.selectbox("Rol:", list(tareas.keys()), index=idx, on_change=reset, label_visibility="collapsed")
        
        # 2. MENÚ DESPLEGABLE DE HERRAMIENTAS (LIMPIO Y ORDENADO)
        st.sidebar.markdown("---")
        with st.sidebar.expander("📎 Adjuntos y Herramientas", expanded=False):
            st.caption("Configuración del mensaje actual:")
            
            # A) Toggles
            c1, c2 = st.columns(2)
            web = c1.toggle("🌍 Web", help="Forzar búsqueda en internet")
            img = c2.toggle("🎨 Arte", help="Modo generador de imágenes")
            
            # B) Archivo
            st.markdown("### 📂 Subir archivo")
            up_file = st.file_uploader("PDF o Imagen", type=["pdf", "png", "jpg"], label_visibility="collapsed")
            
            if up_file:
                st.success(f"✅ Cargado: {up_file.name}")
        
        # 3. HISTORIAL
        st.sidebar.divider()
        st.sidebar.subheader("🗂️ Historial")
        for sid, dat in db.obtener_sesiones(st.session_state.usuario):
            tipo = "secondary" if sid != st.session_state.chat_id else "primary"
            tit = dat.get('titulo', 'Chat')[:20] + "..." if len(dat.get('titulo','')) > 20 else dat.get('titulo', 'Chat')
            if st.sidebar.button(f"💬 {tit}", key=sid, use_container_width=True, type=tipo):
                st.session_state.chat_id = sid; st.rerun()
        
        if st.sidebar.button("Cerrar Sesión"):
            st.session_state.clear(); st.rerun()
            
        # Retornamos TODO lo necesario a app.py
        return rol_sel, web, img, up_file, tareas