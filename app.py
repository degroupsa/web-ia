import streamlit as st
from modules import database as db
from modules import cerebro
from modules import ui
import base64

# --- CONFIGURACIÓN INICIAL DE LA PÁGINA ---
st.set_page_config(
    page_title="Kortexa AI", 
    layout="wide", 
    page_icon="🔗", 
    initial_sidebar_state="expanded"
)

# --- GESTIÓN DE ESTADO (SESSION STATE) ---
if "usuario" not in st.session_state: 
    st.session_state.usuario = None
if "chat_id" not in st.session_state: 
    st.session_state.chat_id = None

# Recuperar token de la URL si existe
params = st.query_params
if "user_token" in params and not st.session_state.usuario: 
    st.session_state.usuario = params["user_token"]

# --- 1. RENDERIZAR SIDEBAR ---
resultado_sidebar = ui.render_sidebar()

# Si no hay login, detener
if resultado_sidebar[0] is None:
    st.stop() 

# Desempaquetamos variables
rol_sel, web_mode, img_mode_manual, up_file, tareas_dict = resultado_sidebar

# --- 2. CABECERA PRINCIPAL ---
info_rol = tareas_dict[rol_sel]
st.subheader(f"{info_rol.get('icon','🔗')} {rol_sel}")

# --- 3. PROCESAMIENTO DE ARCHIVOS ---
ctx_pdf = None
img_vision = None

if up_file:
    if up_file.type == "application/pdf":
        with st.spinner("📄 Kortexa está analizando el documento.."):
            ctx_pdf = cerebro.leer_pdf(up_file)
    else:
        img_vision = base64.b64encode(up_file.getvalue()).decode('utf-8')

# --- 4. CARGAR Y MOSTRAR HISTORIAL ---
msgs = db.cargar_msgs(st.session_state.usuario, st.session_state.chat_id)

# --- PANTALLA DE BIENVENIDA (MEJORADA PERO MANTENIENDO TU ESENCIA) ---
if not msgs and not st.session_state.chat_id:
    # Usamos un contenedor con borde para que no se vea desprolijo
    with st.container(border=True):
        st.markdown(f"### 👋 Hola! Soy Kortexa")
        st.markdown("**Tu asistente de IA, desarrollado por DE Group.**")
        st.divider()
        # Mostramos la descripción del rol que pediste
        st.info(f"**Mi Rol actual es:** {info_rol['desc']}")
        
        # El incentivo que pediste para que el usuario pregunte
        st.markdown("""
        💡 **¿Primera vez aquí?** Pruéba preguntarme: *'¿Cómo funcionas?'* o *'¿Qué rol debo elegir para mi tarea?'*
        """)

ui.render_chat_msgs(msgs)

# --- 5. BARRA DE ESTADO ---
status_indicators = []
if web_mode: status_indicators.append("🌍 Búsqueda Web: ACTIVA")
if img_mode_manual: status_indicators.append("🎨 Modo Arte: ACTIVO")
if ctx_pdf: status_indicators.append(f"📄 Analizando PDF: {up_file.name}")
if img_vision: status_indicators.append(f"⏳ Analizando Imágen: {up_file.name}")

if status_indicators:
    st.caption(" | ".join(status_indicators))

# --- 6. INPUT Y LÓGICA ---
prompt = st.chat_input("Escribe tu mensaje aquí..")

if prompt:
    # A) VELOCIDAD: Mostrar mensaje inmediatamente
    with st.chat_message("user"): st.markdown(prompt)

    # B) Procesar
    with st.spinner("⏳ Kortexa está trabajando.."):
        
        # Gestión de sesión nueva
        nuevo_chat = False
        if not st.session_state.chat_id:
            nuevo_chat = True
            st.session_state.chat_id = db.crear_sesion(st.session_state.usuario, rol_sel, cerebro.generar_titulo(prompt))
        
        db.guardar_msg(st.session_state.usuario, st.session_state.chat_id, "user", prompt)
        
        respuesta = ""
        es_img = cerebro.detectar_intencion_imagen(prompt)
        
        if img_mode_manual or (es_img and not img_mode_manual):
            if es_img: st.toast("🎨 Kortexa está diseñando..", icon="🎨")
            respuesta = cerebro.generar_imagen(prompt, info_rol['image_style'])
            if "http" in respuesta: st.image(respuesta, width=350)
            else: st.error(respuesta)
        
        elif img_vision:
            respuesta = cerebro.analizar_vision(prompt, img_vision, info_rol['prompt'])
            st.markdown(respuesta)
            
        else:
            # Pasamos 'rol_sel' para que el detective de roles funcione
            respuesta = cerebro.procesar_texto(
                prompt, msgs, info_rol['prompt'], web_mode, ctx_pdf, rol_sel
            )
            st.markdown(respuesta)
            
        db.guardar_msg(st.session_state.usuario, st.session_state.chat_id, "assistant", respuesta)
    
    if nuevo_chat: st.rerun()