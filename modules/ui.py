import streamlit as st
from modules import database as db
from modules import roles
import os

# --- 1. ESTILOS CSS (AJUSTADOS PARA MENOR DISTANCIA) ---
def cargar_estilos_css():
    st.markdown("""
        <style>
            #MainMenu {visibility: hidden;}
            header {visibility: hidden;}
            footer {visibility: hidden;}
            .block-container {padding-top: 1rem; padding-bottom: 2rem;} /* Reducido padding superior */
            
            /* Tarjetas */
            .feature-card {
                background: rgba(255, 255, 255, 0.05);
                border: 1px solid rgba(255, 255, 255, 0.1);
                border-radius: 16px;
                padding: 20px;
                text-align: center;
                height: 100%;
                transition: all 0.3s ease;
            }
            .feature-card:hover {
                transform: translateY(-5px);
                border-color: #FF5F1F;
                box-shadow: 0 5px 15px rgba(255, 95, 31, 0.2);
            }
            
            /* Títulos */
            .hero-title {
                font-family: sans-serif;
                font-weight: 900;
                font-size: 45px;
                background: -webkit-linear-gradient(45deg, #FF5F1F, #FF0000);
                -webkit-background-clip: text;
                -webkit-text-fill-color: transparent;
                text-align: center;
                margin-bottom: 5px; /* Reducido margen inferior */
                margin-top: 0px; /* Reducido margen superior */
            }
            .hero-subtitle {
                font-size: 20px;
                text-align: center;
                color: #E0E0E0;
                margin-bottom: 30px;
                margin-top: 0px; /* Reducido margen superior */
            }

            /* LOGO BARRA LATERAL */
            .sidebar-logo {
                font-weight: 800;
                font-size: 24px;
                background: -webkit-linear-gradient(45deg, #FF5F1F, #FF0000);
                -webkit-background-clip: text;
                -webkit-text-fill-color: transparent;
                margin-bottom: 20px;
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

# --- 2. INTERFAZ (CÓDIGO COMPLETO) ---
def render_sidebar():
    cargar_estilos_css()
    
    # --- PANTALLA DE INICIO (LOGIN) ---
    if not st.session_state.usuario:
        
        # A) ZONA DEL LOGO (IMAGEN REAL)
        # Usamos 3 columnas para centrar la imagen en el medio
        c1, c2, c3 = st.columns([1, 2, 1])
        with c2:
            # Intenta cargar logo.png o logo.jpg
            if os.path.exists("logo.png"):
                st.image("logo.png", use_container_width=True)
            elif os.path.exists("logo.jpg"):
                st.image("logo.jpg", use_container_width=True)
            else:
                # Si no encuentra nada, muestra un aviso
                st.warning("⚠️ No encuentro el archivo 'logo.png' o 'logo.jpg'")

        # B) TEXTOS
        st.markdown('<div class="hero-title">KORTEXA AI</div>', unsafe_allow_html=True)
        st.markdown('<div class="hero-subtitle">Inteligencia Neuronal Avanzada</div>', unsafe_allow_html=True)
        
        # C) CARACTERÍSTICAS
        c_a, c_b, c_c = st.columns(3)
        with c_a:
            st.markdown('<div class="feature-card">🧠<br><b>Multimodal</b></div>', unsafe_allow_html=True)
        with c_b:
            st.markdown('<div class="feature-card">⚡<br><b>Velocidad</b></div>', unsafe_allow_html=True)
        with c_c:
            st.markdown('<div class="feature-card">🛡️<br><b>Seguridad</b></div>', unsafe_allow_html=True)

        # D) BARRA LATERAL LOGIN
        st.sidebar.markdown('<div class="sidebar-logo">🔐 Acceso</div>', unsafe_allow_html=True)
        t1, t2 = st.sidebar.tabs(["Entrar", "Crear"])
        
        with t1:
            u = st.text_input("Usuario", key="u_log")
            p = st.text_input("Clave", type="password", key="p_log")
            st.write("")
            if st.button("🚀 Conectar", type="primary", use_container_width=True):
                if db.login(u, p):
                    st.session_state.usuario = u
                    st.rerun()
                else:
                    st.error("Error credenciales")
        
        with t2:
            nu = st.text_input("Nuevo Usuario", key="u_new")
            np = st.text_input("Nueva Clave", type="password", key="p_new")
            st.write("")
            if st.button("✨ Crear", use_container_width=True):
                if db.crear_user(nu, np): st.success("Creado")
                else: st.error("Ya existe")
                
        return None, None, None, None, None

    # --- PANTALLA APP (LOGUEADO) ---
    else:
        st.sidebar.markdown('<div class="sidebar-logo">⚡ KORTEXA AI</div>', unsafe_allow_html=True)
        st.sidebar.caption(f"👤 {st.session_state.usuario}")
        if st.sidebar.button("➕ Nuevo Chat", use_container_width=True):
            st.session_state.chat_id = None
            st.rerun()
            
        st.sidebar.divider()
        tareas = roles.obtener_tareas()
        idx = list(tareas.keys()).index("Asistente General (Multimodal)") if "Asistente General (Multimodal)" in tareas else 0
        def reset(): st.session_state.chat_id = None
        rol = st.sidebar.selectbox("Rol", list(tareas.keys()), index=idx, on_change=reset)
        
        st.sidebar.markdown("---")
        with st.sidebar.expander("🛠️ Herramientas"):
            web = st.sidebar.toggle("Web")
            img = st.sidebar.toggle("Arte")
            up = st.sidebar.file_uploader("Archivo", label_visibility="collapsed")
        
        st.sidebar.divider()
        sesiones = db.obtener_sesiones(st.session_state.usuario)
        for sid, dat in sesiones:
            if st.sidebar.button(f"🗨️ {dat.get('titulo','Chat')[:15]}...", key=sid):
                st.session_state.chat_id = sid
                st.rerun()
                
        if st.sidebar.button("Salir"):
            st.session_state.usuario = None
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