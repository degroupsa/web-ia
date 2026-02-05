import streamlit as st
import time
import re
from modules import cerebro
from modules import database as db
from modules import ui 
from modules import roles 
from modules import auth_firebase as auth
from modules import files 

# --- CONFIGURACIÓN ---
st.set_page_config(page_title="Kortexa AI", page_icon="icon.png", layout="wide")

# --- ESTILOS CSS GLOBALES ---
st.markdown("""
<style>
    /* 1. OCULTAR HEADER DE STREAMLIT (Hamburguesa) */
    header {visibility: hidden;}
    
    /* 2. LÍNEA SUPERIOR DEGRADADA (NUEVO) */
    .stApp::before {
        content: "";
        position: fixed;
        top: 0;
        left: 0;
        width: 100%;
        height: 4px; /* Grosor de la línea */
        background: linear-gradient(90deg, #FF5F1F, #FFAA00); /* Degradado Kortexa */
        z-index: 999999; /* Para que quede por encima de todo */
        box-shadow: 0 0 10px rgba(255, 95, 31, 0.5); /* Resplandor */
    }

    /* 3. ESTILO DE BADGE DE ROL */
    .role-badge {
        background: linear-gradient(90deg, #1E1E1E 0%, #2b2b2b 100%);
        color: #FF5F1F; padding: 6px 12px; border-radius: 20px;
        font-size: 0.8rem; border: 1px solid #FF5F1F; display: inline-flex;
        align-items: center; gap: 5px; font-weight: bold; margin-bottom: 10px;
    }

    /* 4. ANIMACIÓN DE CARGA (SPINNER) */
    .kortexa-loader {
        border: 4px solid #333; 
        border-top: 4px solid #FF5F1F; 
        border-radius: 50%;
        width: 25px;
        height: 25px;
        animation: spin 1s linear infinite;
        display: inline-block;
        vertical-align: middle;
        margin-right: 10px;
    }
    .loading-text {
        color: #ccc;
        font-style: italic;
        vertical-align: middle;
        font-size: 0.95rem;
    }
    @keyframes spin {
        0% { transform: rotate(0deg); }
        100% { transform: rotate(360deg); }
    }
</style>
""", unsafe_allow_html=True)

# --- GESTIÓN DE ESTADO ---
if "user_token" not in st.session_state: st.session_state.user_token = None
if "usuario" not in st.session_state: st.session_state.usuario = None
if "chat_id" not in st.session_state: st.session_state.chat_id = None
if "rol_actual" not in st.session_state: st.session_state.rol_actual = "Asistente General (Multimodal)"

# --- PERSISTENCIA ---
if not st.session_state.usuario:
    params = st.query_params
    token_url = params.get("user_token", None)
    if token_url:
        st.session_state.usuario = token_url
        st.session_state.user_token = token_url 

# ==========================================
# 🖥️ UI RENDER
# ==========================================
res_sidebar = ui.render_sidebar()
rol_seleccionado, usar_web, usar_img, archivo_adjunto, diccionario_tareas = res_sidebar

if rol_seleccionado is None: st.stop() 

# ==========================================
# 🚀 LÓGICA
# ==========================================
if rol_seleccionado != st.session_state.rol_actual:
    st.session_state.rol_actual = rol_seleccionado

tareas_dict = roles.obtener_tareas()
info_rol = tareas_dict.get(st.session_state.rol_actual, tareas_dict.get("Asistente General (Multimodal)"))

st.subheader(f"{info_rol.get('icon','')} {info_rol.get('title', st.session_state.rol_actual)}")
st.markdown(f'<div class="role-badge">MODO: {st.session_state.rol_actual.upper()}</div>', unsafe_allow_html=True)

def mostrar_mensaje(contenido):
    # Renderizado inteligente de imágenes
    imagen_match = re.search(r"!\[.*?\]\((.*?)\)", contenido)
    if imagen_match:
        url = imagen_match.group(1)
        url = url.split(" ")[0] 
        st.image(url, width=500) 
    else:
        st.markdown(contenido)

# Cargar Historial
msgs = db.cargar_msgs(st.session_state.usuario, st.session_state.chat_id)
if not msgs: ui.render_welcome_screen(info_rol["desc"])

for m in msgs:
    with st.chat_message(m["role"], avatar="icon.png" if m["role"] == "assistant" else "👤"):
        mostrar_mensaje(m["content"])

# INPUT
prompt = st.chat_input("Escribe tu mensaje...")

if prompt:
    # 1. Mostrar usuario
    with st.chat_message("user", avatar="👤"): 
        if archivo_adjunto: st.markdown(f"📎 *Archivo: {archivo_adjunto.name}*")
        st.markdown(prompt)
    
    # 2. Crear sesión
    first_msg = False
    if not st.session_state.chat_id:
        st.session_state.chat_id = db.crear_sesion(st.session_state.usuario, st.session_state.rol_actual, prompt[:30])
        first_msg = True 
        
    db.guardar_msg(st.session_state.usuario, st.session_state.chat_id, "user", prompt)

    # 3. Respuesta IA
    with st.chat_message("assistant", avatar="icon.png"):
        container = st.empty()
        full_resp = ""
        imagen_generada = False 

        # --- ANIMACIÓN DE CARGA CON BRANDING ---
        texto_estado = "Procesando solicitud..."
        if usar_img: 
            # ¡AQUÍ ESTÁ EL NOMBRE QUE PEDISTE!
            texto_estado = "🎨 Kortexa Art Studio está diseñando..."
        elif archivo_adjunto: 
            texto_estado = "Analizando documento adjunto..."
        else: 
            texto_estado = "Kortexa Neural v3.0 pensando..."

        html_loader = f"""
        <div style="display: flex; align-items: center; margin-bottom: 15px;">
            <div class="kortexa-loader"></div>
            <div class="loading-text">{texto_estado}</div>
        </div>
        """
        container.markdown(html_loader, unsafe_allow_html=True)
        time.sleep(0.25) 
        # --------------------------

        # Contexto
        contexto_sistema = ""
        if archivo_adjunto and not usar_img:
            texto_archivo = files.procesar_archivo(archivo_adjunto)
            contexto_sistema += texto_archivo
        
        if usar_web and not usar_img: 
            contexto_sistema += "\n[SISTEMA: Búsqueda Web DISPONIBLE.]"

        mensaje_con_contexto = prompt + contexto_sistema

        # Llamada al Cerebro
        stream = cerebro.chat_con_gemini(
            mensaje_usuario=prompt,
            mensaje_con_contexto=mensaje_con_contexto,
            historial_previo=msgs, 
            nombre_rol_actual=st.session_state.rol_actual, 
            plan=st.session_state.get("plan_actual", "free"), 
            token=st.session_state.user_token,
            usar_img_toggle=usar_img
        )
        
        try:
            for chunk in stream:
                # Al usar el nuevo cerebro.py, 'chunk' ya trae el texto acumulado
                full_resp = chunk
                
                es_imagen = "![" in full_resp and "(" in full_resp
                
                if es_imagen:
                    imagen_generada = True
                    container.empty() 
                    mostrar_mensaje(full_resp)
                else:
                    container.markdown(full_resp + "▌")
            
            # Limpieza final del cursor
            if not imagen_generada and full_resp:
                container.markdown(full_resp)

        except Exception as e:
            full_resp = f"Error: {e}"
            container.error(full_resp)
            # DIAGNÓSTICO TÉCNICO (Solo visible si hay error)
            with st.expander("🛠️ Diagnóstico del Sistema"):
                st.write(f"Detalle del error: {str(e)}")

        # Guardar en DB solo si no es un error y no es una acción interna
        if "ACTION_" not in full_resp and full_resp and "Error:" not in full_resp:
            db.guardar_msg(st.session_state.usuario, st.session_state.chat_id, "assistant", full_resp)
    
    if first_msg:
        time.sleep(0.5)
        st.rerun()