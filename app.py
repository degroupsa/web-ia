import streamlit as st
import streamlit.components.v1 as components
import base64
import os
import shutil

# --- 0. BLOQUE DE AUTO-REPARACIÓN (CRÍTICO: DEBE IR PRIMERO) ---
# Esto asegura que el archivo secrets.toml exista ANTES de importar google_auth
try:
    # Definimos rutas
    render_secrets = "/etc/secrets/secrets.toml"
    target_folder = ".streamlit"
    target_file = os.path.join(target_folder, "secrets.toml")

    # Si no existe la carpeta local, la creamos
    if not os.path.exists(target_folder):
        os.makedirs(target_folder, exist_ok=True)

    # Si estamos en Render y el archivo no está en su sitio, lo movemos
    if os.path.exists(render_secrets) and not os.path.exists(target_file):
        shutil.copy(render_secrets, target_file)
        print("✅ Archivo secrets.toml movido exitosamente al inicio.")
        
except Exception as e:
    print(f"⚠️ Error en auto-reparación: {e}")


# --- 1. CONFIGURACIÓN DE PÁGINA ---
st.set_page_config(
    page_title="Kortexa AI", 
    layout="wide", 
    page_icon="icon.png", 
    initial_sidebar_state="expanded"
)

# --- 2. IMPORTS DE MÓDULOS ---
# Importamos aquí para que lean los secretos que acabamos de mover (si aplicaba)
from modules import database as db
from modules import cerebro
from modules import ui
from modules import google_auth 

# --- 3. GESTIÓN DE PERSISTENCIA ---
if "user_token" in st.query_params and "usuario" not in st.session_state:
    st.session_state.usuario = st.query_params["user_token"]
elif "usuario" not in st.session_state:
    st.session_state.usuario = None

if "chat_id" not in st.session_state: 
    st.session_state.chat_id = None

# --- 4. LÓGICA DE GOOGLE (CORREGIDA Y BLINDADA) ---
# Solo procesamos el código si el usuario NO está logueado aún.
if "code" in st.query_params:
    # Caso A: Usuario no logueado, intentamos entrar
    if not st.session_state.usuario:
        code = st.query_params["code"]
        user_info = google_auth.get_user_info(code)
        
        if user_info:
            email = user_info.get("email")
            nombre = user_info.get("name")
            
            if db.login_google(email, nombre):
                st.session_state.usuario = email
                
                # --- LIMPIEZA DE URL (FIX CRÍTICO) ---
                # Borramos el 'code' viejo para evitar error 'invalid_grant' al recargar
                st.query_params.clear()
                st.query_params["user_token"] = email 
                
                st.toast(f"¡Hola {nombre}!", icon="👋")
                st.rerun()
    
    # Caso B: Usuario YA logueado pero el código sigue en la URL
    else:
        # Limpiamos la URL silenciosamente para que quede limpia
        st.query_params.clear()
        if st.session_state.usuario:
             st.query_params["user_token"] = st.session_state.usuario

# --- 5. RENDERIZAR SIDEBAR ---
resultado_sidebar = ui.render_sidebar()

if resultado_sidebar[0] is None:
    st.stop() 

# Desempaquetamos variables
rol_sel, web_mode, img_mode_manual, up_file, tareas_dict = resultado_sidebar

# --- 6. CABECERA Y APP ---
info_rol = tareas_dict[rol_sel]
st.subheader(f"{info_rol.get('icon','🔗')} {info_rol.get('title', rol_sel)}")

# Procesamiento de archivos
ctx_pdf = None
img_vision = None

if up_file:
    if up_file.type == "application/pdf":
        with st.spinner("📄 Kortexa está analizando el documento.."):
            ctx_pdf = cerebro.leer_pdf(up_file)
    else:
        img_vision = base64.b64encode(up_file.getvalue()).decode('utf-8')

# --- CARGAR HISTORIAL ---
if st.session_state.usuario:
    if not st.session_state.chat_id:
        msgs = []
    else:
        msgs = db.cargar_msgs(st.session_state.usuario, st.session_state.chat_id) or []
else:
    msgs = []

# --- PANTALLA DE BIENVENIDA VS CABECERA MINI ---
# Si NO hay historial y NO hay sesión de chat activa -> Mostramos Bienvenida Gigante
if not msgs and not st.session_state.chat_id:
    ui.render_welcome_screen(info_rol['desc'])

# Si YA estamos chateando -> Mostramos la Cabecera Mini (Anchor Visual)
else:
    ui.render_mini_header()

# Renderizar chat (Esto sigue igual)
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
            msgs_safe = msgs if msgs is not None else []
            respuesta = cerebro.procesar_texto(
                prompt, msgs_safe, info_rol['prompt'], web_mode, ctx_pdf, rol_sel
            )
            st.markdown(respuesta)

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