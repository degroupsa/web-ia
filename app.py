import streamlit as st
from modules import database as db
from modules import cerebro
from modules import ui
import base64

# CONFIGURACIÓN
st.set_page_config(page_title="Kortexa AI", layout="wide", page_icon="🔗")

# ESTADO
if "usuario" not in st.session_state: st.session_state.usuario = None
if "chat_id" not in st.session_state: st.session_state.chat_id = None
if "user_token" in st.query_params and not st.session_state.usuario: st.session_state.usuario = st.query_params["user_token"]

# 1. RENDER SIDEBAR (Recuperamos los controles del sidebar)
res = ui.render_sidebar()
if res[0] is None: st.stop()

rol_sel, web_mode, img_mode_manual, up_file, tareas_dict = res

# 2. HEADER
info_rol = tareas_dict[rol_sel]
st.subheader(f"{info_rol.get('icon','🔗')} {rol_sel}")

# 3. PROCESAR ARCHIVOS (Vienen del sidebar)
ctx_pdf = None
img_vision = None

if up_file:
    if up_file.type == "application/pdf":
        with st.spinner("📄 Procesando PDF..."):
            ctx_pdf = cerebro.leer_pdf(up_file)
    else:
        img_vision = base64.b64encode(up_file.getvalue()).decode('utf-8')

# 4. CHAT HISTORY
msgs = db.cargar_msgs(st.session_state.usuario, st.session_state.chat_id)
if not msgs and not st.session_state.chat_id:
    st.info(f"👋 Soy Kortexa. {info_rol['desc']}")

ui.render_chat_msgs(msgs)

# 5. BARRA DE ESTADO (Feedback visual encima del chat)
# Esto sirve para que el usuario sepa qué está activado sin mirar el sidebar
status = []
if web_mode: status.append("🌍 Internet: ON")
if img_mode_manual: status.append("🎨 Modo Arte: ON")
if ctx_pdf: status.append(f"📄 PDF: {up_file.name}")
if img_vision: status.append(f"👁️ Viendo: {up_file.name}")

if status:
    st.caption(" | ".join(status))

# 6. INPUT
prompt = st.chat_input("Escribe tu mensaje...")

if prompt:
    # Nuevo Chat
    if not st.session_state.chat_id:
        st.session_state.chat_id = db.crear_sesion(st.session_state.usuario, rol_sel, cerebro.generar_titulo(prompt))
    
    # Guardar User
    db.guardar_msg(st.session_state.usuario, st.session_state.chat_id, "user", prompt)
    with st.chat_message("user"): st.markdown(prompt)
    
    # Cerebro
    with st.spinner("⚡ Kortexa pensando..."):
        respuesta = ""
        es_img = cerebro.detectar_intencion_imagen(prompt)
        
        if img_mode_manual or (es_img and not img_mode_manual):
            if es_img: st.toast("🎨 Generando imagen...")
            respuesta = cerebro.generar_imagen(prompt, info_rol['image_style'])
            if "http" in respuesta: st.image(respuesta, width=350)
            else: st.error(respuesta)
        
        elif img_vision:
            respuesta = cerebro.analizar_vision(prompt, img_vision, info_rol['prompt'])
            st.markdown(respuesta)
            
        else:
            respuesta = cerebro.procesar_texto(prompt, msgs, info_rol['prompt'], web_mode, ctx_pdf)
            st.markdown(respuesta)
            
    db.guardar_msg(st.session_state.usuario, st.session_state.chat_id, "assistant", respuesta)