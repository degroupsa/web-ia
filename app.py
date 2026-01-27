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

if not st.session_state.usuario:
    st.stop()

# 2. LÓGICA DEL CHAT
info_rol = tareas_dict[rol_sel]
st.subheader(f"{info_rol.get('icon','🤖')} {rol_sel}")

# Variables para adjuntos
ctx_pdf = None
img_vision = None

# Cargar historial
msgs = db.cargar_msgs(st.session_state.usuario, st.session_state.chat_id)
if not msgs and not st.session_state.chat_id:
    st.info(f"👋 {info_rol['desc']}")

# Renderizar mensajes
ui.render_chat_msgs(msgs)

# --- 3. ZONA DE ADJUNTOS (DISEÑO MODERNO TIPO WHATSAPP) ---
# Creamos dos columnas justo encima de la barra de chat
# Columna 1 (Pequeña): El botón del Clip
# Columna 2 (Grande): Avisos de qué se cargó
col_clip, col_estado = st.columns([1, 15])

with col_clip:
    # Popover: Un botón pequeño que abre un menú flotante
    with st.popover("📎", use_container_width=True):
        st.markdown("### 📂 Adjuntar archivo")
        up_file = st.file_uploader("Selecciona PDF o Imagen", type=["pdf", "png", "jpg"], label_visibility="collapsed")
        
        if up_file:
            if up_file.type == "application/pdf":
                with st.spinner("📄 Procesando..."):
                    ctx_pdf = cerebro.leer_pdf(up_file)
            else:
                img_vision = base64.b64encode(up_file.getvalue()).decode('utf-8')

# Mostramos el estado en la columna de al lado para que el usuario sepa que cargó algo
with col_estado:
    if ctx_pdf:
        st.success(f"📄 Documento PDF listo para analizar: {up_file.name}")
    elif img_vision:
        st.success(f"🖼️ Imagen cargada para visión: {up_file.name}")

# 4. INPUT Y CEREBRO
prompt = st.chat_input("Escribe tu mensaje...")

if prompt:
    # A) Gestión de Sesión
    nuevo_chat = False
    if not st.session_state.chat_id:
        nuevo_chat = True
        st.session_state.chat_id = db.crear_sesion(st.session_state.usuario, rol_sel, cerebro.generar_titulo(prompt))
    
    # B) Guardar User
    db.guardar_msg(st.session_state.usuario, st.session_state.chat_id, "user", prompt)
    with st.chat_message("user"): st.markdown(prompt)
    
    # C) CEREBRO
    with st.spinner("Procesando..."):
        respuesta = ""
        
        # Detectar intención
        es_intencion_imagen = cerebro.detectar_intencion_imagen(prompt)
        
        if img_mode_manual or es_intencion_imagen:
            if es_intencion_imagen:
                st.toast("🎨 Detecté que quieres dibujar. Generando imagen...", icon="🎨")
            
            respuesta = cerebro.generar_imagen(prompt, info_rol['image_style'])
            if "http" in respuesta: st.image(respuesta, width=350)
            else: st.error(respuesta)
            
        elif img_vision:
            respuesta = cerebro.analizar_vision(prompt, img_vision, info_rol['prompt'])
            st.markdown(respuesta)
            
        else:
            # Aquí la IA decidirá sola si buscar en web o no (Router en cerebro.py)
            respuesta = cerebro.procesar_texto(prompt, msgs, info_rol['prompt'], web_mode, ctx_pdf)
            st.markdown(respuesta)
            
    # D) Guardar IA
    db.guardar_msg(st.session_state.usuario, st.session_state.chat_id, "assistant", respuesta)
    
    if nuevo_chat: st.rerun()