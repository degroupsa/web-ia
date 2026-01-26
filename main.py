import streamlit as st
from modules import database as db
from modules import cerebro
from modules import ui
import base64

# Configuración inicial
st.set_page_config(page_title="DevMaster AI", layout="wide", page_icon="🔥", initial_sidebar_state="expanded")

# Estado inicial
if "usuario" not in st.session_state: st.session_state.usuario = None
if "chat_id" not in st.session_state: st.session_state.chat_id = None
params = st.query_params
if "user_token" in params and not st.session_state.usuario: st.session_state.usuario = params["user_token"]

# 1. RENDERIZAR SIDEBAR
rol_sel, web_mode, img_mode_manual, tareas_dict = ui.render_sidebar()

# Si no hay usuario, detenemos aquí
if not st.session_state.usuario:
    st.stop()

# 2. LOGICA DEL CHAT
info_rol = tareas_dict[rol_sel]
st.subheader(f"{info_rol.get('icon','🤖')} {rol_sel}")

# Variables para adjuntos
ctx_pdf = None
img_vision = None

# Cargar mensajes previos
msgs = db.cargar_msgs(st.session_state.usuario, st.session_state.chat_id)
if not msgs and not st.session_state.chat_id:
    st.info(f"👋 {info_rol['desc']}")

# Renderizar historial
ui.render_chat_msgs(msgs)

# 3. ZONA DE ADJUNTOS (CLIP)
with st.expander("📎 Adjuntar (PDF o Imagen)", expanded=False):
    up_file = st.file_uploader("Archivo", type=["pdf", "png", "jpg"], label_visibility="collapsed")
    if up_file:
        if up_file.type == "application/pdf":
            with st.spinner("Leyendo PDF..."):
                ctx_pdf = cerebro.leer_pdf(up_file)
                st.success("PDF Listo")
        else:
            st.image(up_file, width=200)
            img_vision = base64.b64encode(up_file.getvalue()).decode('utf-8')

# 4. INPUT Y LÓGICA DE DETECCIÓN AUTOMÁTICA
prompt = st.chat_input("Escribe tu mensaje...")

if prompt:
    # A) Gestión de Sesión
    nuevo_chat = False
    if not st.session_state.chat_id:
        nuevo_chat = True
        st.session_state.chat_id = db.crear_sesion(st.session_state.usuario, rol_sel, cerebro.generar_titulo(prompt))
    
    # B) Guardar y Mostrar User
    db.guardar_msg(st.session_state.usuario, st.session_state.chat_id, "user", prompt)
    with st.chat_message("user"): st.markdown(prompt)
    
    # C) CEREBRO: DECISIÓN INTELIGENTE
    with st.spinner("Procesando..."):
        respuesta = ""
        
        # --- DETECCIÓN AUTOMÁTICA DE IMAGEN ---
        # Si el switch manual está ON o si el texto dice "dibuja..."
        es_intencion_imagen = cerebro.detectar_intencion_imagen(prompt)
        
        if img_mode_manual or es_intencion_imagen:
            # Activamos DALL-E
            if es_intencion_imagen:
                st.toast("🎨 Detecté que quieres dibujar. Generando imagen...", icon="🎨")
            
            respuesta = cerebro.generar_imagen(prompt, info_rol['image_style'])
            if "http" in respuesta: st.image(respuesta, width=350)
            else: st.error(respuesta)
            
        elif img_vision:
            respuesta = cerebro.analizar_vision(prompt, img_vision, info_rol['prompt'])
            st.markdown(respuesta)
            
        else:
            respuesta = cerebro.procesar_texto(prompt, msgs, info_rol['prompt'], web_mode, ctx_pdf)
            st.markdown(respuesta)
            
    # D) Guardar IA
    db.guardar_msg(st.session_state.usuario, st.session_state.chat_id, "assistant", respuesta)
    
    if nuevo_chat: st.rerun()