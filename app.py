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

# --- 4. GESTIÓN DE SESIÓN PERSISTENTE (AUTO-LOGIN) ---
if "usuario" not in st.session_state: st.session_state.usuario = None
if "chat_id" not in st.session_state: st.session_state.chat_id = None

def auto_login():
    """Recupera el usuario de la URL si se recarga la página"""
    # Verificamos si hay un usuario en los parámetros de la URL
    params = st.query_params
    if "user_token" in params and st.session_state.usuario is None:
        st.session_state.usuario = params["user_token"]

def guardar_sesion_url(usuario):
    """Guarda el usuario en la URL para que no se pierda al F5"""
    st.query_params["user_token"] = usuario

def cerrar_sesion_url():
    """Limpia la URL"""
    st.query_params.clear()
    st.session_state.usuario = None
    st.session_state.chat_id = None
    st.rerun()

# Ejecutamos auto-login al iniciar
auto_login()

# Callback para limpiar chat al cambiar rol
def al_cambiar_rol():
    st.session_state.chat_id = None

# ==========================================
# 🎨 BARRA LATERAL (CONTROL TOTAL)
# ==========================================
st.sidebar.title("🔥 DevMaster AI")

if not st.session_state.usuario:
    # --- LOGIN EN SIDEBAR ---
    st.info("Inicia sesión para continuar")
    tab1, tab2 = st.sidebar.tabs(["Login", "Registro"])
    with tab1:
        u = st.text_input("User")
        p = st.text_input("Pass", type="password")
        if st.button("Entrar"):
            if login(u, p):
                st.session_state.usuario = u
                guardar_sesion_url(u) # <--- GUARDAMOS SESIÓN
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
    
    if st.sidebar.button("➕ Nuevo Chat", use_container_width=True, type="primary"):
        st.session_state.chat_id = None
        st.rerun()
    
    st.sidebar.divider()

    # 2. PANEL DE CONTROL
    st.sidebar.subheader("🛠️ Panel de Control")
    
    tareas = cerebro.obtener_tareas()
    lista_tareas = list(tareas.keys())
    
    # Buscamos el índice del Asistente General para que sea el default
    index_default = 0
    if "Asistente General" in lista_tareas:
        index_default = lista_tareas.index("Asistente General")

    # Selector de Rol (Ya no empieza vacío, empieza en Default)
    tarea_sel = st.sidebar.selectbox(
        "Selecciona Experto:", 
        lista_tareas, 
        index=index_default, 
        on_change=al_cambiar_rol
    )
    
    c1, c2 = st.sidebar.columns(2)
    with c1: web = st.toggle("🌍 Web", False, help="Buscar en Internet")
    with c2: img = st.toggle("🎨 Img", False, help="Generar Imagen DALL-E")

    st.sidebar.divider()

    # 3. HISTORIAL
    st.sidebar.subheader("🗂️ Historial")
    sesiones = obtener_sesiones(st.session_state.usuario)
    for sid, sdata in sesiones:
        tipo_boton = "primary" if sid == st.session_state.chat_id else "secondary"
        if st.sidebar.button(f"💬 {sdata.get('titulo','Chat')}", key=sid, type=tipo_boton, use_container_width=True):
            st.session_state.chat_id = sid
            st.rerun()

    st.sidebar.divider()
    if st.sidebar.button("Cerrar Sesión"):
        cerrar_sesion_url() # <--- LIMPIAMOS SESIÓN

    # ==========================================
    # 🖥️ ÁREA PRINCIPAL
    # ==========================================
    
    # Siempre habrá tarea seleccionada porque quitamos el index=None
    if tarea_sel:
        info = tareas[tarea_sel]
        
        st.subheader(f"{info.get('icon', '🤖')} {tarea_sel}")
        
        # Avisos de modo
        if img: st.caption("✨ Modo Generación de Imágenes Activado")
        if web: st.caption("🌐 Modo Búsqueda Online Activado")

        # Cargar Mensajes
        msgs = []
        if st.session_state.chat_id:
            msgs = cargar_mensajes(st.session_state.usuario, st.session_state.chat_id)
        else:
            # Mensaje de bienvenida inicial
            st.markdown(f"""
            <div style='background-color: #262730; padding: 15px; border-radius: 10px; margin-bottom: 20px;'>
                👋 <b>¡Bienvenido!</b> Soy tu experto en <b>{tarea_sel}</b>.<br>
                {info['desc']}
            </div>
            """, unsafe_allow_html=True)

        # Renderizar Chat
        for m in msgs:
            with st.chat_message(m["role"]):
                if m["content"].startswith("http") and " " not in m["content"]:
                    st.image(m["content"], width=400)
                else:
                    st.markdown(m["content"])

        # INPUT (Ahora garantizado que aparece)
        prompt = st.chat_input(f"Escribe a tu {tarea_sel}...")

        if prompt:
            es_nuevo = False
            # 1. Crear Sesión si no existe
            if not st.session_state.chat_id:
                es_nuevo = True
                with st.spinner("Iniciando conversación..."):
                    # Usamos el generador de títulos de cerebro
                    titulo = cerebro.generar_titulo_corto(prompt)
                    st.session_state.chat_id = crear_sesion_con_titulo(st.session_state.usuario, tarea_sel, titulo)
            
            # 2. Guardar User
            guardar_mensaje(st.session_state.usuario, st.session_state.chat_id, "user", prompt)
            with st.chat_message("user"): st.markdown(prompt)
            
            # 3. Procesar IA
            with st.spinner("Generando respuesta..."):
                res = ""
                if img:
                    estilo = info.get('image_style', info['prompt'])
                    res = cerebro.generar_imagen_dalle(prompt, estilo)
                    if "http" in res: st.image(res)
                    else: st.error(res)
                else:
                    hist_ia = [m for m in msgs if not m["content"].startswith("http")]
                    res = cerebro.respuesta_inteligente(prompt, hist_ia, info['prompt'], web)
                    st.markdown(res)
            
            # 4. Guardar IA
            guardar_mensaje(st.session_state.usuario, st.session_state.chat_id, "assistant", res)
            
            # 5. Recargar para actualizar sidebar (solo si es nuevo)
            if es_nuevo: st.rerun()
