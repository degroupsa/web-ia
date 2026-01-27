import streamlit as st
import streamlit.components.v1 as components  # <--- NUEVO IMPORT PARA EL SCROLL
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

# Recuperar token de la URL si existe (para mantener sesión al recargar)
params = st.query_params
if "user_token" in params and not st.session_state.usuario: 
    st.session_state.usuario = params["user_token"]

# --- 1. RENDERIZAR SIDEBAR ---
# Llamamos a la función UI y desempaquetamos los 5 valores que retorna
resultado_sidebar = ui.render_sidebar()

# Si el usuario no está logueado, ui.render_sidebar devuelve None en el primer valor
if resultado_sidebar[0] is None:
    st.stop() # Detenemos la ejecución aquí hasta que se loguee

# Desempaquetamos las variables si hay login exitoso
rol_sel, web_mode, img_mode_manual, up_file, tareas_dict = resultado_sidebar

# --- 2. CABECERA PRINCIPAL ---
info_rol = tareas_dict[rol_sel]
# Mostramos el icono y el nombre del rol seleccionado
st.subheader(f"{info_rol.get('icon','🔗')} {rol_sel}")

# --- 3. PROCESAMIENTO DE ARCHIVOS (PREVIO AL CHAT) ---
ctx_pdf = None
img_vision = None

# Si el usuario subió algo en el sidebar, lo procesamos ahora
if up_file:
    if up_file.type == "application/pdf":
        with st.spinner("📄 Kortexa está analizando el documento.."):
            ctx_pdf = cerebro.leer_pdf(up_file)
    else:
        # Si es imagen, la convertimos a base64 para que GPT-4o la pueda "ver"
        img_vision = base64.b64encode(up_file.getvalue()).decode('utf-8')

# --- 4. CARGAR Y MOSTRAR HISTORIAL ---
msgs = db.cargar_msgs(st.session_state.usuario, st.session_state.chat_id)

# --- PANTALLA DE BIENVENIDA (Limpia y profesional) ---
# Si no hay mensajes y no hay ID de chat, es un chat nuevo
if not msgs and not st.session_state.chat_id:
    # Contenedor con borde para destacar la bienvenida
    with st.container(border=True):
        st.markdown(f"### 👋 Hola! Soy Kortexa")
        st.markdown("**Tu asistente de IA, desarrollado por DE Group.**")
        st.divider()
        st.info(f"**Mi Rol actual es:** {info_rol['desc']}")
        
        # Incentivo para preguntar sobre la interfaz
        st.markdown("""
        💡 **¿Primera vez aquí?** Pruéba preguntarme: *'¿Cómo funcionas?'* o *'¿Qué rol debo elegir para mi tarea?'*
        """)

# Renderizamos los mensajes existentes
ui.render_chat_msgs(msgs)

# --- 5. BARRA DE ESTADO (FEEDBACK VISUAL) ---
# Creamos una lista de "etiquetas" para mostrar encima del chat si hay herramientas activas
status_indicators = []

if web_mode: 
    status_indicators.append("🌍 Búsqueda Web: ACTIVA")
if img_mode_manual: 
    status_indicators.append("🎨 Modo Arte: ACTIVO")
if ctx_pdf: 
    status_indicators.append(f"📄 Analizando PDF: {up_file.name}")
if img_vision: 
    status_indicators.append(f"⏳ Analizando Imágen: {up_file.name}")

# Si hay algo en la lista, lo mostramos como un texto pequeño (caption)
if status_indicators:
    st.caption(" | ".join(status_indicators))

# --- 6. INPUT DE CHAT Y LÓGICA DE RESPUESTA ---
prompt = st.chat_input("Escribe tu mensaje aquí..")

if prompt:
    # A) Mostrar mensaje INMEDIATAMENTE (Velocidad mejorada)
    with st.chat_message("user"): 
        st.markdown(prompt)

    # B) Procesamiento
    with st.spinner("⏳ Kortexa está trabajando.."):
        
        # Gestión de Sesión Nueva
        nuevo_chat = False
        if not st.session_state.chat_id:
            nuevo_chat = True
            # Creamos la sesión en la base de datos y obtenemos el ID
            st.session_state.chat_id = db.crear_sesion(
                st.session_state.usuario, 
                rol_sel, 
                cerebro.generar_titulo(prompt)
            )
        
        # Guardar Mensaje del Usuario en BD
        db.guardar_msg(st.session_state.usuario, st.session_state.chat_id, "user", prompt)
        
        # Lógica del Cerebro
        respuesta = ""
        es_intencion_imagen = cerebro.detectar_intencion_imagen(prompt)
        
        # CASO 1: Generación de Imagen
        if img_mode_manual or (es_intencion_imagen and not img_mode_manual):
            if es_intencion_imagen:
                st.toast("🎨 Kortexa está diseñando..", icon="🎨")
            
            # Llamada a DALL-E 3
            respuesta = cerebro.generar_imagen(prompt, info_rol['image_style'])
            
            # Si es una URL, la mostramos como imagen, si no, mostramos el error
            if "http" in respuesta: 
                st.image(respuesta, width=350)
            else: 
                st.error(respuesta)
        
        # CASO 2: Visión (Analizar imagen subida)
        elif img_vision:
            respuesta = cerebro.analizar_vision(prompt, img_vision, info_rol['prompt'])
            st.markdown(respuesta)
            
        # CASO 3: Texto Normal (Chat, Web Search, PDF)
        else:
            # IMPORTANTE: Pasamos 'rol_sel' al cerebro para el "Detective de Roles"
            respuesta = cerebro.procesar_texto(
                prompt, msgs, info_rol['prompt'], web_mode, ctx_pdf, rol_sel
            )
            st.markdown(respuesta)

            # --- CORRECCIÓN DE SCROLL (AUTO-ALIGN) ---
            # Este script busca el último mensaje del chat y lo alinea al inicio (arriba)
            # para que el usuario no tenga que subir manualmente.
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
            
        # Guardar Respuesta de la IA
        db.guardar_msg(st.session_state.usuario, st.session_state.chat_id, "assistant", respuesta)
    
    # Recargamos la página solo si era un chat nuevo para que actualice la URL y el historial
    if nuevo_chat: 
        st.rerun()