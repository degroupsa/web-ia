import streamlit as st
import firebase_admin
from firebase_admin import credentials, firestore
import cerebro
import uuid # Para generar IDs únicos de chat

# --- 1. CONFIGURACIÓN ---
st.set_page_config(page_title="DevMaster AI", layout="wide", page_icon="🔥")

# --- 2. CONEXIÓN DB ---
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

# --- 3. GESTIÓN DE SESIONES (NUEVO) ---
def crear_sesion(user, rol_inicial, primer_mensaje):
    """Crea un nuevo documento de sesión y retorna su ID"""
    titulo = primer_mensaje[:30] + "..." # Título automático
    nueva_sesion_ref = db.collection("users").document(user).collection("sessions").document()
    nueva_sesion_ref.set({
        "titulo": titulo,
        "rol": rol_inicial,
        "creado": firestore.SERVER_TIMESTAMP
    })
    return nueva_sesion_ref.id

def obtener_sesiones(user):
    """Trae la lista de chats anteriores para el sidebar"""
    ref = db.collection("users").document(user).collection("sessions")
    # Ordenamos por creado descendente (el más nuevo arriba)
    docs = ref.order_by("creado", direction=firestore.Query.DESCENDING).limit(10).stream()
    return [(d.id, d.to_dict()) for d in docs]

def guardar_mensaje(user, session_id, role, content):
    if session_id:
        db.collection("users").document(user).collection("sessions").document(session_id).collection("msgs").add({
            "role": role, "content": content, "fecha": firestore.SERVER_TIMESTAMP
        })

def cargar_mensajes_sesion(user, session_id):
    if not session_id: return []
    ref = db.collection("users").document(user).collection("sessions").document(session_id).collection("msgs")
    return [d.to_dict() for d in ref.order_by("fecha").stream()]

# --- 4. LÓGICA DE LOGIN ---
def login(user, pwd):
    doc = db.collection("users").document(user).get()
    if doc.exists and doc.to_dict()["password"] == pwd: return doc.to_dict()
    return None

def crear_usuario(user, pwd):
    doc = db.collection("users").document(user).get()
    if doc.exists: return False
    db.collection("users").document(user).set({"password": pwd, "plan": "Gratis"})
    return True

# --- 5. INTERFAZ ---
if "usuario" not in st.session_state: st.session_state.usuario = None
if "chat_actual_id" not in st.session_state: st.session_state.chat_actual_id = None

# Función para resetear chat al cambiar rol
def cambio_de_rol():
    st.session_state.chat_actual_id = None # Esto fuerza un chat nuevo

# NAVEGACIÓN
st.sidebar.title("🔥 DevMaster AI")

if not st.session_state.usuario:
    st.header("Bienvenido")
    tab1, tab2 = st.tabs(["Entrar", "Registrarse"])
    with tab1:
        u = st.text_input("Usuario")
        p = st.text_input("Contraseña", type="password")
        if st.button("Entrar"):
            if login(u, p):
                st.session_state.usuario = u
                st.rerun()
            else: st.error("Error")
    with tab2:
        nu = st.text_input("User")
        np = st.text_input("Pass", type="password")
        if st.button("Crear"):
            if crear_usuario(nu, np): st.success("Creado")
            else: st.error("Existe")

else:
    # --- SIDEBAR: HISTORIAL DE CHATS ---
    st.sidebar.divider()
    if st.sidebar.button("➕ Nuevo Chat", use_container_width=True):
        st.session_state.chat_actual_id = None
        st.rerun()
    
    st.sidebar.subheader("Historial Reciente")
    sesiones_previas = obtener_sesiones(st.session_state.usuario)
    
    for s_id, s_data in sesiones_previas:
        titulo = s_data.get("titulo", "Chat sin título")
        # Si hacemos click, cargamos ese chat
        if st.sidebar.button(f"💬 {titulo}", key=s_id):
            st.session_state.chat_actual_id = s_id
            st.rerun()

    st.sidebar.divider()
    if st.sidebar.button("Cerrar Sesión"):
        st.session_state.usuario = None
        st.session_state.chat_actual_id = None
        st.rerun()

    # --- ÁREA PRINCIPAL ---
    st.subheader(f"Hola, {st.session_state.usuario}")

    # Selector de Tareas
    tareas = cerebro.obtener_tareas()
    
    # IMPORTANTE: on_change ejecuta 'cambio_de_rol' si seleccionas algo nuevo
    tarea_sel = st.selectbox(
        "Elige un Experto:", 
        list(tareas.keys()), 
        index=None, 
        placeholder="Busca aquí...",
        on_change=cambio_de_rol 
    )

    if tarea_sel:
        info = tareas[tarea_sel]
        
        # Opciones
        c1, c2 = st.columns(2)
        with c1: web_on = st.toggle("🌍 Internet", value=False)
        with c2: img_on = st.toggle("🎨 Imagen", value=False)
        
        st.divider()

        # CARGAR MENSAJES (Si hay chat activo)
        mensajes_pantalla = []
        if st.session_state.chat_actual_id:
            mensajes_pantalla = cargar_mensajes_sesion(st.session_state.usuario, st.session_state.chat_actual_id)
        else:
            st.info("💡 Escribe abajo para iniciar un NUEVO chat con este rol.")

        # Renderizar Chat
        for m in mensajes_pantalla:
            with st.chat_message(m["role"]):
                if m["content"].startswith("http") and " " not in m["content"]:
                    st.image(m["content"], width=300)
                else:
                    st.markdown(m["content"])

        # INPUT USUARIO
        prompt = st.chat_input(f"Escribe a tu {tarea_sel}...")

        if prompt:
            # 1. Si es el primer mensaje, CREAMOS LA SESIÓN
            if not st.session_state.chat_actual_id:
                st.session_state.chat_actual_id = crear_sesion(st.session_state.usuario, tarea_sel, prompt)
                st.rerun() # Recargamos para que aparezca el historial creado

            # 2. Guardar User
            guardar_mensaje(st.session_state.usuario, st.session_state.chat_actual_id, "user", prompt)
            with st.chat_message("user"): st.markdown(prompt)

            # 3. Generar Respuesta
            with st.spinner("Pensando..."):
                res_final = ""
                if img_on:
                    res_final = cerebro.generar_imagen_dalle(prompt, info['prompt'])
                    st.image(res_final) if "http" in res_final else st.error(res_final)
                else:
                    # Filtramos historial para la IA
                    hist_ia = [m for m in mensajes_pantalla if not m["content"].startswith("http")]
                    res_final = cerebro.respuesta_inteligente(prompt, hist_ia, info['prompt'], web_on)
                    st.markdown(res_final)
            
            # 4. Guardar IA
            guardar_mensaje(st.session_state.usuario, st.session_state.chat_actual_id, "assistant", res_final)
