import streamlit as st
import streamlit.components.v1 as components
from modules import database as db
from modules import cerebro
from modules import ui
from modules import google_auth
import base64

# --- 1. CONFIGURACIÓN (SIEMPRE VA PRIMERO) ---
st.set_page_config(
    page_title="Kortexa AI", 
    layout="wide", 
    page_icon="icon.png", 
    initial_sidebar_state="expanded"
)

# --- 2. GESTIÓN DE PERSISTENCIA (FIX REFRESH) ---
if "user_token" in st.query_params and "usuario" not in st.session_state:
    st.session_state.usuario = st.query_params["user_token"]
elif "usuario" not in st.session_state:
    st.session_state.usuario = None

if "chat_id" not in st.session_state: 
    st.session_state.chat_id = None

# --- 3. LÓGICA DE GOOGLE ---
if "code" in st.query_params:
    code = st.query_params["code"]
    user_info = google_auth.get_user_info(code)
    
    if user_info:
        email = user_info.get("email")
        nombre = user_info.get("name")
        
        if db.login_google(email, nombre):
            st.session_state.usuario = email
            st.query_params["user_token"] = email # Persistencia
            st.toast(f"¡Hola {nombre}!", icon="👋")
            st.rerun()

# --- 4. RENDERIZAR SIDEBAR ---
resultado_sidebar = ui.render_sidebar()

if resultado_sidebar[0] is None:
    st.stop() 

# Desempaquetamos variables
rol_sel, web_mode, img_mode_manual, up_file, tareas_dict = resultado_sidebar

# --- 5. CABECERA Y APP ---
info_rol = tareas_dict[rol_sel]
st.subheader(f"{info_rol.get('icon','🔗')} {rol_sel}")

# Procesamiento de archivos
ctx_pdf = None
img_vision = None

if up_file:
    if up_file.type == "application/pdf":
        with st.spinner("📄 Kortexa está analizando el documento.."):
            ctx_pdf = cerebro.leer_pdf(up_file)
    else:
        img_vision = base64.b64encode(up_file.getvalue()).decode('utf-8')

# Cargar historial
msgs = db.cargar_msgs(st.session_state.usuario, st.session_state.chat_id)

# --- PANTALLA DE BIENVENIDA (Aquí llamamos a la nueva función) ---
if not msgs and not st.session_state.chat_id:
    # Esta función ahora está definida en tu ui.py actualizado
    ui.render_welcome_screen(info_rol['desc'])

# Renderizar chat
ui.render_chat_msgs(msgs)

# Barra de estado
status_indicators = []
if web_mode: status_indicators.append("🌍 Búsqueda Web: ACTIVA")
if img_mode_manual: status_indicators.append("🎨 Modo Arte: ACTIVO")
if ctx_pdf: status_indicators.append(f"📄 PDF: {up_file.name}")
if img_vision: status_indicators.append(f"⏳ Img: {up_file.name}")

if status_indicators:
    st.caption(" | ".join(status_indicators))

# Input de Chat
prompt = st.chat_input("Escribe tu mensaje aquí..")

if prompt:
    with st.chat_message("user"): 
        st.markdown(prompt)

    with st.spinner("⏳ Kortexa está trabajando.."):
        nuevo_chat = False
        if not st.session_state.chat_id:
            nuevo_chat = True
            st.session_state.chat_id = db.crear_sesion(
                st.session_state.usuario, rol_sel, cerebro.generar_titulo(prompt)
            )
        
        db.guardar_msg(st.session_state.usuario, st.session_state.chat_id, "user", prompt)
        
        respuesta = ""
        es_intencion_imagen = cerebro.detectar_intencion_imagen(prompt)
        
        if img_mode_manual or (es_intencion_imagen and not img_mode_manual):
            if es_intencion_imagen: st.toast("🎨 Diseñando..", icon="🎨")
            respuesta = cerebro.generar_imagen(prompt, info_rol['image_style'])
            if "http" in respuesta: st.image(respuesta, width=350)
            else: st.error(respuesta)
        
        elif img_vision:
            respuesta = cerebro.analizar_vision(prompt, img_vision, info_rol['prompt'])
            st.markdown(respuesta)
            
        else:
            respuesta = cerebro.procesar_texto(
                prompt, msgs, info_rol['prompt'], web_mode, ctx_pdf, rol_sel
            )
            st.markdown(respuesta)

            # Auto-scroll
            js_scroll = """
            <script>
                var chat_elements = window.parent.document.querySelectorAll('.stChatMessage');
                if (chat_elements.length > 0) {
                    var last_element = chat_elements[chat_elements.length - 1];
                    last_element.scrollIntoView({behavior: 'smooth', block: 'start'});
                }
            </script>
            """
            components.html(js_scroll, height=0)
            
        db.guardar_msg(st.session_state.usuario, st.session_state.chat_id, "assistant", respuesta)
    
    if nuevo_chat: st.rerun()