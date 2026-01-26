import streamlit as st
import firebase_admin
from firebase_admin import credentials, firestore
import cerebro

# --- 1. CONFIGURACIÓN ---
st.set_page_config(
    page_title="DevMaster AI", 
    layout="wide", 
    page_icon="🔥",
    initial_sidebar_state="expanded"
)

# --- 2. CONEXIÓN DB (HÍBRIDA) ---
if not firebase_admin._apps:
    try:
        if "firebase" in st.secrets:
            key_dict = dict(st.secrets["firebase"])
            key_dict["private_key"] = key_dict["private_key"].replace("\\n", "\n")
            cred = credentials.Certificate(key_dict)
            firebase_admin.initialize_app(cred)
        else:
            cred = credentials.Certificate("firebase_key.json")
            firebase_admin.initialize_app(cred)
    except Exception as e:
        st.error(f"Error Database: {e}")
        st.stop()

db = firestore.client()

# --- 3. FUNCIONES DE BASE DE DATOS ---
def crear_sesion_con_titulo(user, rol_inicial, titulo_inteligente):
    nueva_sesion_ref = db.collection("users").document(user).collection("sessions").document()
    nueva_sesion_ref.set({
        "titulo": titulo_inteligente,
        "rol": rol_inicial,
        "creado": firestore.SERVER_TIMESTAMP
    })
    return nueva_sesion_ref.id

def guardar_mensaje(user, session_id, role, content):
    if session_id:
        db.collection("users").document(user).collection("sessions").document(session_id).collection("msgs").add({
            "role": role, "content": content, "fecha": firestore.SERVER_TIMESTAMP
        })

def cargar_mensajes(user, session_id):
    if not session_id: return []
    ref = db.collection("users").document(user).collection("sessions").document(session_id).collection("msgs")
    return [d.to_dict() for d in ref.order_by("fecha").stream()]

def obtener_sesiones(user):
    ref = db.collection("users").document(user).collection("sessions")
    docs = ref.order_by("creado", direction=firestore.Query.DESCENDING).limit(15).stream()
    return [(d.id, d.to_dict()) for d in docs]

# --- LOGIN ---
def login(u, p):
    doc = db.collection("users").document(u).get()
    if doc.exists and doc.to_dict()["password"] == p: return True
    return False

def crear_user(u, p):
    if db.collection("users").document(u).get().exists: return False
    db.collection("users").document(u).set({"password": p, "plan": "Gratis"})
    return True

# --- 4. INTERFAZ ---
if "usuario" not in st.session_state: st.session_state.usuario = None
if "chat_id" not in st.session_state: st.session_state.chat_id = None

# Callback para limpiar chat al cambiar rol
def al_cambiar_rol():
    st.session_state.chat_id = None

# ==========================================
# 🎨 BARRA LATERAL (CONTROL TOTAL)
# ==========================================
st.sidebar.title("🔥 DevMaster AI")

if not st.session_state.usuario:
    # --- LOGIN EN SIDEBAR ---
    tab1, tab2 = st.sidebar.tabs(["Login", "Registro"])
    with tab1:
        u = st.text_input("User")
        p = st.text_input("Pass", type="password")
        if st.button("Entrar"):
            if login(u, p):
                st.session_state.usuario = u
                st.rerun()
            else: st.error("Error")
    with tab2:
        nu = st.text_input("Nuevo User")
        np = st.text_input("Nueva Pass", type="password")
        if st.button("Crear"): 
            if crear_user(nu, np): st.success("Creado")
            else: st.error("Existe")

else:
    # --- USUARIO LOGUEADO ---
    st.sidebar.caption(f"Hola, {st.session_state.usuario}")
    
    # 1. BOTÓN NUEVO CHAT (Siempre arriba)
    if st.sidebar.button("➕ Nuevo Chat", use_container_width=True, type="primary"):
        st.session_state.chat_id = None
        st.rerun()
    
    st.sidebar.divider()

    # 2. PANEL DE CONTROL (ROLES Y HERRAMIENTAS)
    st.sidebar.subheader("🛠️ Panel de Control")
    
    tareas = cerebro.obtener_tareas()
    
    # Selector de Rol (Ahora fijo en la izquierda)
    tarea_sel = st.sidebar.selectbox(
        "Selecciona Experto:", 
        list(tareas.keys()), 
        index=None, 
        placeholder="Buscar rol...",
        on_change=al_cambiar_rol
    )
    
    # Interruptores (Ahora fijos debajo del rol)
    c1, c2 = st.sidebar.columns(2)
    with c1: web = st.toggle("🌍 Web", False, help="Buscar en Internet")
    with c2: img = st.toggle("🎨 Img", False, help="Generar Imagen DALL-E")

    st.sidebar.divider()

    # 3. HISTORIAL DE CHATS
    st.sidebar.subheader("🗂️ Historial")
    sesiones = obtener_sesiones(st.session_state.usuario)
    for sid, sdata in sesiones:
        # Estilo del botón: Resaltado si es el chat actual
        tipo_boton = "primary" if sid == st.session_state.chat_id else "secondary"
        if st.sidebar.button(f"💬 {sdata.get('titulo','Chat')}", key=sid, type=tipo_boton, use_container_width=True):
            st.session_state.chat_id = sid
            st.rerun()

    # 4. SALIR
    st.sidebar.divider()
    if st.sidebar.button("Cerrar Sesión"):
        st.session_state.usuario = None
        st.session_state.chat_id = None
        st.rerun()

    # ==========================================
    # 🖥️ ÁREA PRINCIPAL (CHAT LIMPIO)
    # ==========================================
    
    if tarea_sel:
        info = tareas[tarea_sel]
        
        # Título dinámico en el chat
        st.subheader(f"{info['icon']} {tarea_sel}")
        if img: st.caption("✨ Modo Generación de Imágenes Activado")
        if web: st.caption("🌐 Modo Búsqueda Online Activado")

        # Cargar Mensajes
        msgs = []
        if st.session_state.chat_id:
            msgs = cargar_mensajes(st.session_state.usuario, st.session_state.chat_id)
        else:
            # Mensaje de bienvenida del rol
            st.info(f"👋 **¡Listo!** Soy tu {tarea_sel}. {info['desc']}")

        # Renderizar Chat
        for m in msgs:
            with st.chat_message(m["role"]):
                if m["content"].startswith("http") and " " not in m["content"]:
                    st.image(m["content"], width=400)
                else:
                    st.markdown(m["content"])

        # INPUT (Siempre abajo)
        prompt = st.chat_input(f"Escribe a tu {tarea_sel}...")

        if prompt:
            # 1. Crear Sesión si no existe
            es_nuevo = False
            if not st.session_state.chat_id:
                es_nuevo = True
                with st.spinner("Creando sala..."):
                    titulo = cerebro.generar_titulo_corto(prompt)
                    st.session_state.chat_id = crear_sesion_con_titulo(st.session_state.usuario, tarea_sel, titulo)
            
            # 2. Guardar User
            guardar_mensaje(st.session_state.usuario, st.session_state.chat_id, "user", prompt)
            with st.chat_message("user"): st.markdown(prompt)
            
            # 3. Procesar IA
            with st.spinner("Trabajando..."):
                res = ""
                if img:
                    # USAMOS EL FIX DE ESTILO AQUÍ:
                    estilo = info.get('image_style', info['prompt'])
                    res = cerebro.generar_imagen_dalle(prompt, estilo)
                    
                    if "http" in res: st.image(res)
                    else: st.error(res)
                else:
                    # Texto normal
                    hist_ia = [m for m in msgs if not m["content"].startswith("http")]
                    res = cerebro.respuesta_inteligente(prompt, hist_ia, info['prompt'], web)
                    st.markdown(res)
            
            # 4. Guardar IA
            guardar_mensaje(st.session_state.usuario, st.session_state.chat_id, "assistant", res)
            
            # 5. Actualizar sidebar si es nuevo
            if es_nuevo: st.rerun()

    else:
        # Pantalla de inicio vacía (cuando no hay rol seleccionado)
        st.markdown("""
        <div style='text-align: center; padding-top: 50px;'>
            <h1>🔥 DevMaster AI</h1>
            <h3>Selecciona un Experto en el menú de la izquierda para comenzar 👈</h3>
        </div>
        """, unsafe_allow_html=True)
