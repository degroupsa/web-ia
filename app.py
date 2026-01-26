import streamlit as st
import firebase_admin
from firebase_admin import credentials, firestore
import cerebro

# --- CONFIGURACIÓN DE PÁGINA ---
st.set_page_config(page_title="DevMaster AI", layout="wide", page_icon="🔥")

# --- CONEXIÓN A FIREBASE (HÍBRIDA) ---
if not firebase_admin._apps:
    try:
        # INTENTO 1: Conexión CLOUD (Usando st.secrets)
        if "firebase" in st.secrets:
            # Convertimos el secreto de Streamlit (que es un objeto especial) a un diccionario normal de Python
            key_dict = dict(st.secrets["firebase"])
            
            # Hay un bug conocido en Streamlit donde las claves privadas con "\n" se rompen.
            # Esta línea lo arregla mágicamente:
            key_dict["private_key"] = key_dict["private_key"].replace("\\n", "\n")

            cred = credentials.Certificate(key_dict)
            firebase_admin.initialize_app(cred)
        
        # INTENTO 2: Conexión LOCAL (Usando archivo json si estás en tu PC)
        else:
            cred = credentials.Certificate("firebase_key.json")
            firebase_admin.initialize_app(cred)
            
    except Exception as e:
        st.error(f"Error de base de datos: {e}")
        st.stop()

db = firestore.client()

# --- FUNCIONES DE BASE DE DATOS (CLOUD) ---
def crear_usuario(user, pwd):
    # En Firebase usamos "Colecciones" y "Documentos"
    doc_ref = db.collection("users").document(user)
    doc = doc_ref.get()
    
    if doc.exists:
        return False # El usuario ya existe
    else:
        # Guardamos el usuario nuevo
        doc_ref.set({
            "password": pwd,
            "plan": "Gratis",
            "fecha_registro": firestore.SERVER_TIMESTAMP
        })
        return True

def login(user, pwd):
    doc_ref = db.collection("users").document(user)
    doc = doc_ref.get()
    
    if doc.exists:
        datos = doc.to_dict()
        if datos["password"] == pwd:
            return datos # Retorna el diccionario con plan, password, etc.
    return None

def guardar_mensaje_historial(user, role, content):
    # Guardamos cada mensaje en una sub-colección del usuario
    db.collection("users").document(user).collection("chats").add({
        "role": role,
        "content": content,
        "fecha": firestore.SERVER_TIMESTAMP
    })

def cargar_historial(user):
    # Traemos los mensajes ordenados por fecha
    chats_ref = db.collection("users").document(user).collection("chats")
    docs = chats_ref.order_by("fecha").stream()
    
    mensajes = []
    for doc in docs:
        mensajes.append(doc.to_dict())
    return mensajes

# --- NAVEGACIÓN ---
st.sidebar.title("🔥 DevMaster Cloud")

if "usuario" not in st.session_state:
    st.session_state.usuario = None

menu = st.sidebar.radio("Navegación", ["Login / Registro", "Plataforma AI", "Generador Prompts"])

# ==========================================
# 🔐 LOGIN
# ==========================================
if menu == "Login / Registro":
    st.header("Acceso Cloud")
    tab1, tab2 = st.tabs(["Ingresar", "Crear Cuenta"])
    
    with tab1:
        user = st.text_input("Usuario")
        pwd = st.text_input("Contraseña", type="password")
        if st.button("Entrar"):
            datos = login(user, pwd)
            if datos:
                st.session_state.usuario = user
                st.session_state.plan = datos["plan"]
                st.success(f"¡Hola {user}! Plan: {datos['plan']}")
            else:
                st.error("Datos incorrectos")

    with tab2:
        new_user = st.text_input("Nuevo Usuario")
        new_pwd = st.text_input("Nueva Contraseña", type="password")
        if st.button("Registrarse en la Nube"):
            if crear_usuario(new_user, new_pwd):
                st.success("Cuenta creada en Firebase. Ahora entra.")
            else:
                st.error("Ese usuario ya existe.")

# ==========================================
# 🤖 PLATAFORMA IA (ACTUALIZADA)
# ==========================================
elif menu == "Plataforma AI":
    if not st.session_state.usuario:
        st.warning("🔒 Inicia sesión primero.")
    else:
        st.subheader(f"Área de Trabajo de {st.session_state.usuario}")
        
        # 1. Roles
        roles = cerebro.obtener_roles()
        rol_sel = st.selectbox("Experto:", list(roles.keys()))
        info_rol = roles[rol_sel]
        
        # --- NUEVO: INTERRUPTOR DE INTERNET ---
        col_toggle, col_info = st.columns([1, 3])
        with col_toggle:
            usar_web = st.toggle("🌍 Modo Online (Internet)", value=False)
        
        if usar_web:
            st.caption("⚡ La IA buscará datos en Google antes de responder.")

        # 2. Historial desde Firebase
        mensajes_db = cargar_historial(st.session_state.usuario)
        for msg in mensajes_db:
            with st.chat_message(msg["role"]):
                st.markdown(msg["content"])

        # 3. Input
        prompt = st.chat_input("Consulta a la IA...")
        
        if prompt:
            # A) Guardar User
            with st.chat_message("user"):
                st.markdown(prompt)
            guardar_mensaje_historial(st.session_state.usuario, "user", prompt)
            
            # B) LLAMADA INTELIGENTE AL CEREBRO
            with st.spinner("Procesando..."):
                # Preparamos el historial para enviarlo (sin el prompt actual aun)
                historial_para_ia = [{"role": m["role"], "content": m["content"]} for m in mensajes_db[-5:]]
                
                # Llamamos a la función nueva de cerebro.py
                txt_ia = cerebro.respuesta_inteligente(
                    mensaje_usuario=prompt,
                    historial_previo=historial_para_ia,
                    prompt_rol=info_rol['prompt'],
                    usar_internet=usar_web  # <--- Le pasamos el estado del botón
                )
            
            # C) Guardar IA
            with st.chat_message("assistant"):
                st.markdown(txt_ia)
            guardar_mensaje_historial(st.session_state.usuario, "assistant", txt_ia)

# ==========================================
# ✨ GENERADOR PROMPTS
# ==========================================
elif menu == "Generador Prompts":
    # (Este se mantiene igual, usando cerebro.py)
    if not st.session_state.usuario:
        st.warning("🔒 Login requerido.")
    else:
        st.header("Generador Profesional")
        idea = st.text_area("Idea:")
        tipo = st.selectbox("Tipo:", ["Texto", "Imagen", "Código"])
        if st.button("Generar"):
            res = cerebro.generar_prompt_experto(idea, tipo)
            st.code(res)