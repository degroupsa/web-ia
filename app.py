import streamlit as st
import firebase_admin
from firebase_admin import credentials, firestore
import cerebro

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
        st.error(f"Error DB: {e}")
        st.stop()

db = firestore.client()

# --- 3. FUNCIONES DE SESIÓN (LÓGICA NUEVA) ---
def crear_sesion_con_titulo(user, rol_inicial, titulo_inteligente):
    """Crea la sesión con el título generado por IA"""
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

# --- 4. LOGIN ---
def login(u, p):
    doc = db.collection("users").document(u).get()
    if doc.exists and doc.to_dict()["password"] == p: return True
    return False

def crear_user(u, p):
    if db.collection("users").document(u).get().exists: return False
    db.collection("users").document(u).set({"password": p, "plan": "Gratis"})
    return True

# --- 5. INTERFAZ ---
if "usuario" not in st.session_state: st.session_state.usuario = None
if "chat_id" not in st.session_state: st.session_state.chat_id = None

# Función para limpiar chat al cambiar rol
def al_cambiar_rol():
    st.session_state.chat_id = None

# SIDEBAR
st.sidebar.title("🔥 DevMaster AI")

if not st.session_state.usuario:
    tab1, tab2 = st.tabs(["Login", "Registro"])
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
    # --- HISTORIAL SIDEBAR ---
    if st.sidebar.button("➕ Nuevo Chat", use_container_width=True):
        st.session_state.chat_id = None
        st.rerun()
    
    st.sidebar.caption("Historial")
    sesiones = obtener_sesiones(st.session_state.usuario)
    for sid, sdata in sesiones:
        if st.sidebar.button(f"💬 {sdata.get('titulo','Chat')}", key=sid):
            st.session_state.chat_id = sid
            st.rerun()
            
    st.sidebar.divider()
    if st.sidebar.button("Salir"):
        st.session_state.usuario = None
        st.session_state.chat_id = None
        st.rerun()

    # --- MAIN AREA ---
    st.subheader(f"Hola, {st.session_state.usuario}")
    
    tareas = cerebro.obtener_tareas()
    tarea = st.selectbox("Experto:", list(tareas.keys()), index=None, placeholder="Selecciona Rol...", on_change=al_cambiar_rol)

    if tarea:
        info = tareas[tarea]
        
        # Opciones
        c1, c2 = st.columns(2)
        with c1: web = st.toggle("🌍 Internet", False)
        with c2: img = st.toggle("🎨 Imagen", False)
        
        st.divider()

        # Cargar Mensajes (si existe chat_id)
        msgs = []
        if st.session_state.chat_id:
            msgs = cargar_mensajes(st.session_state.usuario, st.session_state.chat_id)
        else:
            st.info("👋 Escribe abajo para iniciar una nueva conversación.")

        # Mostrar Chat
        for m in msgs:
            with st.chat_message(m["role"]):
                if m["content"].startswith("http") and " " not in m["content"]:
                    st.image(m["content"], width=300)
                else:
                    st.markdown(m["content"])

        # INPUT
        prompt = st.chat_input(f"Escribe a {tarea}...")

        if prompt:
            # --- 1. GESTIÓN DE SESIÓN (CRÍTICO) ---
            es_nuevo_chat = False
            
            if not st.session_state.chat_id:
                es_nuevo_chat = True
                # Generamos Título Inteligente
                with st.spinner("Creando sala de chat..."):
                    titulo_ia = cerebro.generar_titulo_corto(prompt)
                    # Creamos ID pero NO hacemos rerun todavía
                    st.session_state.chat_id = crear_sesion_con_titulo(st.session_state.usuario, tarea, titulo_ia)
            
            # --- 2. GUARDAR Y MOSTRAR USER ---
            guardar_mensaje(st.session_state.usuario, st.session_state.chat_id, "user", prompt)
            with st.chat_message("user"): st.markdown(prompt)
            
            # --- 3. GENERAR RESPUESTA IA ---
            with st.spinner("Pensando..."):
                res = ""
                if img:
                    res = cerebro.generar_imagen_dalle(prompt, info['prompt'])
                    if "http" in res: st.image(res)
                    else: st.error(res)
                else:
                    # Filtramos historial para contexto IA
                    hist_ia = [m for m in msgs if not m["content"].startswith("http")]
                    res = cerebro.respuesta_inteligente(prompt, hist_ia, info['prompt'], web)
                    st.markdown(res)
            
            # --- 4. GUARDAR IA ---
            guardar_mensaje(st.session_state.usuario, st.session_state.chat_id, "assistant", res)
            
            # --- 5. RECARGAR SOLO SI FUE CHAT NUEVO ---
            # Esto es para que aparezca el botón nuevo en el sidebar
            if es_nuevo_chat:
                st.rerun()
