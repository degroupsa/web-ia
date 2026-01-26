import streamlit as st
import firebase_admin
from firebase_admin import credentials, firestore
import cerebro
import base64

# --- 1. CONFIGURACIÓN ---
st.set_page_config(page_title="DevMaster AI", layout="wide", page_icon="🔥", initial_sidebar_state="expanded")

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
    except: st.stop()

db = firestore.client()

# --- 3. FUNCIONES DB ---
def crear_sesion(user, rol, titulo):
    ref = db.collection("users").document(user).collection("sessions").document()
    ref.set({"titulo": titulo, "rol": rol, "creado": firestore.SERVER_TIMESTAMP})
    return ref.id

def guardar_msg(user, sid, role, content):
    if sid: db.collection("users").document(user).collection("sessions").document(sid).collection("msgs").add({"role": role, "content": content, "fecha": firestore.SERVER_TIMESTAMP})

def cargar_msgs(user, sid):
    if not sid: return []
    ref = db.collection("users").document(user).collection("sessions").document(sid).collection("msgs")
    return [d.to_dict() for d in ref.order_by("fecha").stream()]

def obtener_sesiones(user):
    ref = db.collection("users").document(user).collection("sessions")
    docs = ref.order_by("creado", direction=firestore.Query.DESCENDING).limit(15).stream()
    return [(d.id, d.to_dict()) for d in docs]

# --- 4. LOGIN ---
def login(u, p):
    doc = db.collection("users").document(u).get()
    return doc.exists and doc.to_dict()["password"] == p

def crear_user(u, p):
    if db.collection("users").document(u).get().exists: return False
    db.collection("users").document(u).set({"password": p, "plan": "Gratis"})
    return True

# --- INIT STATE ---
if "usuario" not in st.session_state: st.session_state.usuario = None
if "chat_id" not in st.session_state: st.session_state.chat_id = None
if "archivo_cache" not in st.session_state: st.session_state.archivo_cache = None

# AUTO-LOGIN
params = st.query_params
if "user_token" in params and not st.session_state.usuario: st.session_state.usuario = params["user_token"]

def al_cambiar_rol(): st.session_state.chat_id = None; st.session_state.archivo_cache = None

# ==========================================
# 🎨 UI SIDEBAR
# ==========================================
st.sidebar.title("🔥 DevMaster Ultimate")

if not st.session_state.usuario:
    st.info("Acceso Seguro")
    t1, t2 = st.sidebar.tabs(["Entrar", "Crear"])
    with t1:
        u = st.text_input("User"); p = st.text_input("Pass", type="password")
        if st.button("Ingresar"): 
            if login(u,p): st.session_state.usuario = u; st.query_params["user_token"]=u; st.rerun()
            else: st.error("Error")
    with t2:
        nu = st.text_input("New User"); np = st.text_input("New Pass", type="password")
        if st.button("Registrar"): 
            if crear_user(nu, np): st.success("Ok")
            else: st.error("Existe")

else:
    st.sidebar.caption(f"👤 {st.session_state.usuario}")
    if st.sidebar.button("➕ Nuevo Chat", type="primary", use_container_width=True):
        st.session_state.chat_id = None; st.session_state.archivo_cache = None; st.rerun()
    
    st.sidebar.divider()
    
    # --- PANEL DE CONTROL ---
    st.sidebar.subheader("🛠️ Herramientas")
    tareas = cerebro.obtener_tareas()
    
    # Selector Rol
    idx = list(tareas.keys()).index("Asistente General (Multimodal)") if "Asistente General (Multimodal)" in tareas else 0
    tarea_sel = st.sidebar.selectbox("Experto:", list(tareas.keys()), index=idx, on_change=al_cambiar_rol)
    
    # Opciones
    c1, c2 = st.sidebar.columns(2)
    web = c1.toggle("🌍 Web", False, help="Buscar en internet")
    img_mode = c2.toggle("🎨 Crear Img", False, help="DALL-E 3")
    
    # --- ZONA DE CARGA DE ARCHIVOS (NUEVO) ---
    st.sidebar.divider()
    st.sidebar.subheader("📂 Subir Archivos")
    uploaded_file = st.sidebar.file_uploader("Imagen o PDF", type=["png", "jpg", "jpeg", "pdf"], key="file_uploader")
    
    # Procesamiento de archivo en tiempo real
    contexto_archivo = None
    imagen_para_vision = None
    
    if uploaded_file:
        # Si es PDF
        if uploaded_file.type == "application/pdf":
            with st.spinner("📄 Leyendo documento..."):
                texto_pdf = cerebro.leer_pdf(uploaded_file)
                contexto_archivo = texto_pdf
                st.sidebar.success("PDF Cargado en memoria")
        
        # Si es Imagen (Para Visión)
        else:
            st.sidebar.image(uploaded_file, caption="Imagen lista para análisis", use_container_width=True)
            # Convertir a Base64 para enviar a GPT-4o
            bytes_data = uploaded_file.getvalue()
            imagen_para_vision = base64.b64encode(bytes_data).decode('utf-8')

    st.sidebar.divider()
    
    # Historial
    st.sidebar.subheader("🗂️ Chats")
    for sid, dat in obtener_sesiones(st.session_state.usuario):
        if st.sidebar.button(f"💬 {dat.get('titulo','Chat')}", key=sid, use_container_width=True, type="secondary" if sid != st.session_state.chat_id else "primary"):
            st.session_state.chat_id = sid; st.rerun()
            
    if st.sidebar.button("Cerrar Sesión"):
        st.query_params.clear(); st.session_state.usuario = None; st.session_state.chat_id = None; st.rerun()

    # ==========================================
    # 🖥️ MAIN CHAT
    # ==========================================
    info = tareas[tarea_sel]
    st.subheader(f"{info.get('icon','🤖')} {tarea_sel}")
    
    # Etiquetas de estado
    status = []
    if web: status.append("🌐 Online")
    if img_mode: status.append("🎨 Modo Arte")
    if contexto_archivo: status.append("📄 Leyendo PDF")
    if imagen_para_vision: status.append("👁️ Viendo Imagen")
    if status: st.caption(" | ".join(status))

    # Cargar Msgs
    msgs = cargar_msgs(st.session_state.usuario, st.session_state.chat_id) if st.session_state.chat_id else []
    
    if not st.session_state.chat_id and not msgs:
        st.markdown(f"<div style='background:#262730;padding:15px;border-radius:10px'>👋 <b>Hola!</b> {info['desc']}</div>", unsafe_allow_html=True)

    for m in msgs:
        with st.chat_message(m["role"]):
            if m["content"].startswith("http") and " " not in m["content"]: st.image(m["content"], width=350)
            else: st.markdown(m["content"])

    # INPUT
    prompt = st.chat_input("Escribe tu mensaje...")
    
    if prompt:
        nuevo = False
        if not st.session_state.chat_id:
            nuevo = True
            st.session_state.chat_id = crear_sesion(st.session_state.usuario, tarea_sel, cerebro.generar_titulo_corto(prompt))
        
        guardar_msg(st.session_state.usuario, st.session_state.chat_id, "user", prompt)
        with st.chat_message("user"): st.markdown(prompt)
        
        with st.spinner("Procesando..."):
            res = ""
            
            # --- RUTA 1: CREAR IMAGEN (DALL-E) ---
            if img_mode:
                res = cerebro.generar_imagen_dalle(prompt, info['image_style'])
                if "http" in res: st.image(res, width=350)
                else: st.error(res)
            
            # --- RUTA 2: VISIÓN (ANALIZAR IMAGEN SUBIDA) ---
            elif imagen_para_vision:
                res = cerebro.analizar_imagen_vision(prompt, imagen_para_vision, info['prompt'])
                st.markdown(res)
                
            # --- RUTA 3: TEXTO / PDF / WEB ---
            else:
                hist = [m for m in msgs if not m["content"].startswith("http")]
                res = cerebro.respuesta_inteligente(prompt, hist, info['prompt'], web, contexto_archivo)
                st.markdown(res)
        
        guardar_msg(st.session_state.usuario, st.session_state.chat_id, "assistant", res)
        if nuevo: st.rerun()
