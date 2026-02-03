import streamlit as st
import streamlit.components.v1 as components
import base64
import os
import shutil
import re
from modules import database as db
from modules import cerebro
from modules import ui
from modules import google_auth
from modules import roles

# --- CONFIGURACIÓN ---
st.set_page_config(page_title="Kortexa AI", page_icon="icon.png", layout="wide", initial_sidebar_state="expanded")

# --- CSS PERSONALIZADO ---
st.markdown("""
    <style>
        header {visibility: hidden;}
        /* Estilo para el Badge del Rol */
        .role-badge {
            background-color: #1E1E1E;
            color: #FF5F1F;
            padding: 5px 10px;
            border-radius: 15px;
            font-size: 12px;
            border: 1px solid #FF5F1F;
            margin-bottom: 10px;
            display: inline-block;
            font-weight: bold;
        }
        /* Estilo para la CAJA DE ALERTA DE ROL (Advertencias) */
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

# --- AUTO-REPARACIÓN SECRETS ---
try:
    if not os.path.exists(".streamlit"):
        os.makedirs(".streamlit", exist_ok=True)
    if os.path.exists("/etc/secrets/secrets.toml") and not os.path.exists(".streamlit/secrets.toml"):
        shutil.copy("/etc/secrets/secrets.toml", ".streamlit/secrets.toml")
except:
    pass

# --- SESSION STATE ---
if "user_token" in st.query_params and "usuario" not in st.session_state:
    st.session_state.usuario = st.query_params["user_token"]
elif "usuario" not in st.session_state:
    st.session_state.usuario = None

if "chat_id" not in st.session_state:
    st.session_state.chat_id = None

# Inicializamos el rol si no existe
if "rol_actual" not in st.session_state:
    st.session_state.rol_actual = "Asistente General (Multimodal)"

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

# --- RENDER SIDEBAR ---
# Nota: La UI del sidebar es prioritaria si el usuario interactúa con ella,
# pero si la IA cambia el rol, debemos respetarlo.
res_sidebar = ui.render_sidebar()
if res_sidebar[0] is None:
    st.stop()

rol_sidebar, web_mode, img_mode_manual, up_file, tareas_dict = res_sidebar

# --- SINCRONIZACIÓN DE ROL ---
# Detectamos si el usuario cambió manualmente el sidebar
if "last_sidebar_rol" not in st.session_state:
    st.session_state.last_sidebar_rol = rol_sidebar

if rol_sidebar != st.session_state.last_sidebar_rol:
    # Cambio manual por usuario: actualizamos el estado global
    st.session_state.rol_actual = rol_sidebar
    st.session_state.last_sidebar_rol = rol_sidebar

# El rol activo final es el que está en session_state (ya sea por sidebar o por IA)
rol_activo = st.session_state.rol_actual

# Validación de seguridad por si el rol no existe
if rol_activo not in tareas_dict:
    rol_activo = "Asistente General (Multimodal)"
    st.session_state.rol_actual = rol_activo

info_rol = tareas_dict[rol_activo]

# --- HEADER ---
st.subheader(f"{info_rol.get('icon','🔗')} {info_rol.get('title', rol_activo)}")
st.markdown(f'<div class="role-badge">MODO ACTUAL: {rol_activo.upper()}</div>', unsafe_allow_html=True)

# --- ARCHIVOS ---
ctx_pdf, img_vision = None, None
if up_file:
    if up_file.type == "application/pdf":
        with st.spinner("📄 Analizando documento..."):
            ctx_pdf = cerebro.leer_pdf(up_file)
    else:
        img_vision = base64.b64encode(up_file.getvalue()).decode("utf-8")

# --- HISTORIAL ---
if st.session_state.usuario:
    msgs = db.cargar_msgs(st.session_state.usuario, st.session_state.chat_id) or [] if st.session_state.chat_id else []
else:
    msgs = []

if not msgs and not st.session_state.chat_id:
    ui.render_welcome_screen(info_rol["desc"])
else:
    ui.render_mini_header()

for m in msgs:
    with st.chat_message(m["role"], avatar="👤" if m["role"] == "user" else "icon.png"):
        st.markdown(m["content"])

# --- CHAT INPUT ---
prompt = st.chat_input("Escribe tu mensaje aquí..")

if prompt:
    # Mensaje usuario
    with st.chat_message("user", avatar="👤"):
        st.markdown(prompt)

    nuevo_chat = False
    if not st.session_state.chat_id:
        nuevo_chat = True
        st.session_state.chat_id = db.crear_sesion(
            st.session_state.usuario,
            rol_activo,
            cerebro.generar_titulo(prompt)
        )

    db.guardar_msg(st.session_state.usuario, st.session_state.chat_id, "user", prompt)

    # ============================
    # 🕵️ DETECCIÓN DE CAMBIO DE ROL AUTOMÁTICO
    # ============================
    # Verificamos si el usuario pide explícitamente cambiar de rol (ej: "Actúa como abogado")
    nuevo_rol_ia = cerebro.detectar_cambio_rol(prompt)

    if nuevo_rol_ia and nuevo_rol_ia != rol_activo:
        # ¡CAMBIO DETECTADO!
        st.session_state.rol_actual = nuevo_rol_ia
        
        # Mostramos mensaje de transición
        with st.chat_message("assistant", avatar="icon.png"):
            aviso = f"🔄 **Entendido. Cambiando mi configuración a: {nuevo_rol_ia}...**"
            st.markdown(aviso)
            db.guardar_msg(st.session_state.usuario, st.session_state.chat_id, "assistant", aviso)
        
        # Recargamos la app para que el nuevo rol tome control total (prompts, estilos, etc.)
        st.rerun()

    # ============================
    # RESPUESTA ASISTENTE (Si no hubo cambio de rol)
    # ============================
    with st.chat_message("assistant", avatar="icon.png"):

        es_intencion_imagen = cerebro.detectar_intencion_imagen(prompt)

        if img_vision:
            with st.spinner("👁️ Analizando imagen..."):
                resp_text = cerebro.analizar_vision(prompt, img_vision, info_rol["prompt"])
                st.markdown(resp_text)
                db.guardar_msg(st.session_state.usuario, st.session_state.chat_id, "assistant", resp_text)
        else:
            with st.spinner(f"Kortexa ({rol_activo}) está trabajando..."):
                stream = cerebro.procesar_texto(
                    prompt, msgs or [], info_rol["prompt"], web_mode, ctx_pdf, rol_activo
                )
                resp_text = st.write_stream(stream)

            contenido_final = resp_text

            # Renderizado de Apps HTML
            patron_html = r"```html(.*?)```"
            bloques_html = re.findall(patron_html, resp_text, re.DOTALL)

            if bloques_html:
                for codigo_html in bloques_html:
                    st.caption("⚡ Kortexa App Engine")
                    components.html(codigo_html, height=400, scrolling=True)

            # Generación de Imagen
            if es_intencion_imagen or img_mode_manual:
                st.markdown("---")
                with st.spinner("🎨 Diseñando..."):
                    url_img = cerebro.generar_imagen(prompt, info_rol["image_style"])
                    if "http" in url_img:
                        st.image(url_img, width=400)
                        contenido_final += f"\n\n![Imagen Generada]({url_img})"
                    else:
                        st.warning(url_img)
                        contenido_final += f"\n\n(Error: {url_img})"

            db.guardar_msg(st.session_state.usuario, st.session_state.chat_id, "assistant", contenido_final)
            
            # Auto-Scroll
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

    if nuevo_chat:
        st.rerun()