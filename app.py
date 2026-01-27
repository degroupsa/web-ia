import streamlit as st
from modules import database as db
from modules import cerebro
from modules import ui
import base64

# --- 1. CONFIGURACIÓN VISUAL Y NOMBRE (Actualizado a Kortexa) ---
st.set_page_config(
    page_title="Kortexa AI",   # <--- NOMBRE ACTUALIZADO
    layout="wide", 
    page_icon="🔗",            # <--- ICONO ACTUALIZADO (Coincide con ui.py)
    initial_sidebar_state="expanded"
)

# Estado inicial
if "usuario" not in st.session_state: st.session_state.usuario = None
if "chat_id" not in st.session_state: st.session_state.chat_id = None
params = st.query_params
if "user_token" in params and not st.session_state.usuario: st.session_state.usuario = params["user_token"]

# 2. RENDERIZAR SIDEBAR
rol_sel, web_mode, img_mode_manual, tareas_dict = ui.render_sidebar()

if not st.session_state.usuario:
    st.stop()

# 3. CABECERA Y ROL
info_rol = tareas_dict[rol_sel]
st.subheader(f"{info_rol.get('icon','🔗')} {rol_sel}") 

# Variables para adjuntos
ctx_pdf = None
img_vision = None

# Cargar historial
msgs = db.cargar_msgs(st.session_state.usuario, st.session_state.chat_id)
if not msgs and not st.session_state.chat_id:
    # <--- SALUDO PERSONALIZADO CON EL NOMBRE NUEVO
    st.info(f"Hola! 👋 Soy Kortexa, tu asistente IA. Mi Rol actual: {info_rol['desc']}")

# Renderizar mensajes anteriores
ui.render_chat_msgs(msgs)

# --- 4. ZONA DE ADJUNTOS (DISEÑO "CLIP" MODERNO) ---
col_clip, col_estado = st.columns([1, 15])

with col_clip:
    # MENÚ FLOTANTE (POPOVER)
    with st.popover("📎", use_container_width=True, help="Adjuntar archivo"):
        st.markdown("### 📂 Subir Archivo")
        up_file = st.file_uploader("Sube un PDF o Imágen", type=["pdf", "png", "jpg", "jpeg"], label_visibility="collapsed")
        
        if up_file:
            if up_file.type == "application/pdf":
                with st.spinner("📄 Kortexa está leyendo el documento.."):
                    ctx_pdf = cerebro.leer_pdf(up_file)
            else:
                img_vision = base64.b64encode(up_file.getvalue()).decode('utf-8')

# Mostrar aviso si hay algo cargado
with col_estado:
    if ctx_pdf:
        st.success(f"📄 Documento cargado: {up_file.name} (Listo para preguntar)", icon="✅")
    elif img_vision:
        st.success(f"🖼️ Imagen cargada: {up_file.name} (Lista para ver)", icon="👁️")

# --- 5. INPUT Y PROCESAMIENTO ---
prompt = st.chat_input("Escribe tu mensaje aquí..")

if prompt:
    # A) Crear sesión si es chat nuevo
    nuevo_chat = False
    if not st.session_state.chat_id:
        nuevo_chat = True
        st.session_state.chat_id = db.crear_sesion(st.session_state.usuario, rol_sel, cerebro.generar_titulo(prompt))
    
    # B) Guardar y mostrar mensaje usuario
    db.guardar_msg(st.session_state.usuario, st.session_state.chat_id, "user", prompt)
    with st.chat_message("user"): st.markdown(prompt)
    
    # C) CEREBRO (KORTEXA THINKING)
    with st.spinner("⚡ Kortexa está procesando.."): # <--- SPINNER ACTUALIZADO
        respuesta = ""
        
        # 1. ¿Es una petición de imagen?
        es_intencion_imagen = cerebro.detectar_intencion_imagen(prompt)
        
        if img_mode_manual or es_intencion_imagen:
            if es_intencion_imagen:
                st.toast("🎨 Generando arte...", icon="🎨")
            respuesta = cerebro.generar_imagen(prompt, info_rol['image_style'])
            
            if "http" in respuesta: st.image(respuesta, width=350)
            else: st.error(respuesta)
            
        # 2. ¿Hay imagen adjunta para ver?
        elif img_vision:
            respuesta = cerebro.analizar_vision(prompt, img_vision, info_rol['prompt'])
            st.markdown(respuesta)
            
        # 3. Texto normal (con búsqueda automática)
        else:
            respuesta = cerebro.procesar_texto(prompt, msgs, info_rol['prompt'], web_mode, ctx_pdf)
            st.markdown(respuesta)
            
    # D) Guardar respuesta IA
    db.guardar_msg(st.session_state.usuario, st.session_state.chat_id, "assistant", respuesta)
    
    if nuevo_chat: st.rerun()