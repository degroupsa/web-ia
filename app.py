import streamlit as st
import streamlit.components.v1 as components
import base64
import os
import shutil

# --- CONFIGURACIÓN ---
st.set_page_config(
    page_title="Kortexa AI",
    page_icon="icon.png",
    layout="wide",
    initial_sidebar_state="expanded"
)

# --- AUTO-REPARACIÓN ---
try:
    render_secrets = "/etc/secrets/secrets.toml"
    target_folder = ".streamlit"
    target_file = os.path.join(target_folder, "secrets.toml")
    if not os.path.exists(target_folder): os.makedirs(target_folder, exist_ok=True)
    if os.path.exists(render_secrets) and not os.path.exists(target_file):
        shutil.copy(render_secrets, target_file)
except: pass

# --- CSS PERSONALIZADO (AQUÍ ESTÁ LA ALERTA AMARILLA) ---
def cargar_css():
    st.markdown("""
        <style>
            /* ESTILOS PREVIOS (Header, Sidebar, etc...) */
            header::before {
                content: ""; position: absolute; top: 0; left: 0; width: 100%; height: 4px;
                background: linear-gradient(90deg, #FF5F1F, #FF0000, #FFAA00); z-index: 9999;
            }
            header { border-top: none !important; }
            section[data-testid="stSidebar"] { background-color: #050505 !important; border-right: 1px solid #333 !important; }
            [data-testid="stSidebar"] * { color: #FFFFFF !important; }
            button[kind="primary"] { background-color: #FF5F1F !important; border: none !important; color: white !important; }
            
            /* =========================================
               13. CAJA DE ALERTA DE ROL (NUEVO)
               ========================================= */
            [data-testid="stChatMessageContent"] blockquote {
                background-color: rgba(255, 193, 7, 0.15) !important;
                border-left: 4px solid #FFC107 !important;
                padding: 15px !important;
                border-radius: 4px !important;
                margin-bottom: 20px !important;
            }
            [data-testid="stChatMessageContent"] blockquote p {
                color: #FFC107 !important;
                font-weight: bold !important;
                font-size: 15px !important;
            }
        </style>
    """, unsafe_allow_html=True)

cargar_css()

# --- IMPORTS ---
from modules import database as db
from modules import cerebro
from modules import ui
from modules import google_auth 

# --- SESSION STATE ---
if "user_token" in st.query_params and "usuario" not in st.session_state:
    st.session_state.usuario = st.query_params["user_token"]
elif "usuario" not in st.session_state:
    st.session_state.usuario = None

if "chat_id" not in st.session_state: st.session_state.chat_id = None

# --- GOOGLE LOGIN ---
if "code" in st.query_params:
    if not st.session_state.usuario:
        code = st.query_params["code"]
        user_info = google_auth.get_user_info(code)
        if user_info:
            email, nombre = user_info.get("email"), user_info.get("name")
            if db.login_google(email, nombre):
                st.session_state.usuario = email
                st.query_params.clear()
                st.query_params["user_token"] = email 
                st.rerun()
    else:
        st.query_params.clear()
        if st.session_state.usuario: st.query_params["user_token"] = st.session_state.usuario

# --- RENDER SIDEBAR ---
res_sidebar = ui.render_sidebar()
if res_sidebar[0] is None: st.stop() 
rol_sel, web_mode, img_mode_manual, up_file, tareas_dict = res_sidebar

# --- HEADER ---
info_rol = tareas_dict[rol_sel]
st.subheader(f"{info_rol.get('icon','🔗')} {info_rol.get('title', rol_sel)}")

# --- ARCHIVOS ---
ctx_pdf, img_vision = None, None
if up_file:
    if up_file.type == "application/pdf":
        with st.spinner("📄 Analizando documento..."): ctx_pdf = cerebro.leer_pdf(up_file)
    else: img_vision = base64.b64encode(up_file.getvalue()).decode('utf-8')

# --- HISTORIAL ---
if st.session_state.usuario:
    msgs = db.cargar_msgs(st.session_state.usuario, st.session_state.chat_id) or [] if st.session_state.chat_id else []
else: msgs = []

if not msgs and not st.session_state.chat_id: ui.render_welcome_screen(info_rol['desc'])
else: ui.render_mini_header()

ui.render_chat_msgs(msgs)

# --- CHAT INPUT ---
prompt = st.chat_input("Escribe tu mensaje aquí..")

if prompt:
    # 1. Usuario
    with st.chat_message("user", avatar="👤"): st.markdown(prompt)
    
    # 2. Crear Chat si no existe
    nuevo_chat = False
    if not st.session_state.chat_id:
        nuevo_chat = True
        st.session_state.chat_id = db.crear_sesion(st.session_state.usuario, rol_sel, cerebro.generar_titulo(prompt))
    
    db.guardar_msg(st.session_state.usuario, st.session_state.chat_id, "user", prompt)
    
    # 3. Respuesta Asistente
    with st.chat_message("assistant", avatar="icon.png" if os.path.exists("icon.png") else None):
        
        es_intencion_imagen = cerebro.detectar_intencion_imagen(prompt)
        
        # A) MODO VISIÓN
        if img_vision:
            with st.spinner("👁️ Analizando imagen..."):
                resp_text = cerebro.analizar_vision(prompt, img_vision, info_rol['prompt'])
                st.markdown(resp_text)
                db.guardar_msg(st.session_state.usuario, st.session_state.chat_id, "assistant", resp_text)

        # B) MODO TEXTO / GENERACIÓN
        else:
            msgs_safe = msgs if msgs is not None else []
            with st.spinner("Kortexa está pensando..."):
                stream = cerebro.procesar_texto(
                    prompt, msgs_safe, info_rol['prompt'], web_mode, ctx_pdf, rol_sel
                )
                resp_text = st.write_stream(stream)
            
            contenido_final = resp_text

            # 2. Generación Imagen (FORZADA SI SE DETECTÓ AL INICIO)
            if es_intencion_imagen or img_mode_manual:
                st.markdown("---")
                with st.spinner("🎨 Diseñando imagen de alta calidad..."):
                    url_img = cerebro.generar_imagen(prompt, info_rol['image_style'])
                    if "http" in url_img:
                        st.image(url_img, width=400)
                        contenido_final += f"\n\n![Imagen Generada]({url_img})"
                    else:
                        st.warning(url_img)
                        contenido_final += f"\n\n(Error: {url_img})"

            db.guardar_msg(st.session_state.usuario, st.session_state.chat_id, "assistant", contenido_final)
            
            # --- AUTO SCROLL ---
            js_scroll = """
            <script>
                function scrollDown() {
                    var chatElements = window.parent.document.querySelectorAll(".stChatMessage");
                    if (chatElements.length > 0) {
                        chatElements[chatElements.length - 1].scrollIntoView({behavior: "smooth", block: "end"});
                    }
                }
                setTimeout(scrollDown, 500);
            </script>
            """
            components.html(js_scroll, height=0)

    if nuevo_chat: st.rerun()