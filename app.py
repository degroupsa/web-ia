import streamlit as st
import firebase_admin
from firebase_admin import credentials, firestore
import cerebro
import base64

# --- CONFIGURACIÓN PAGE ---
st.set_page_config(page_title="DevMaster AI", layout="wide", page_icon="🔥", initial_sidebar_state="expanded")

# --- CONEXIÓN DB ---
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

# --- FUNCIONES DB ---
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

# --- LOGIN ---
def login(u, p):
    doc = db.collection("users").document(u).get()
    return doc.exists and doc.to_dict()["password"] == p

def crear_user(u, p):
    if db.collection("users").document(u).get().exists: return False
    db.collection("users").document(u).set({"password": p, "plan": "Gratis"})
    return True

# --- ESTADO ---
if "usuario" not in st.session_state: st.session_state.usuario = None
if "chat_id" not in st.session_state: st.session_state.chat_id = None

# AUTO-LOGIN
params = st.query_params
if "user_token" in params and not st.session_state.usuario: st.session_state.usuario = params["user_token"]

def al_cambiar_rol(): st.session_state.chat_id = None

# ==========================================
# 🎨 SIDEBAR (AHORA MÁS LIMPIO)
# ==========================================
st.sidebar.title("🔥 DevMaster AI")

if not st.session_state.usuario:
    st.info("Bienvenido")
    t1, t2 = st.sidebar.tabs(["Entrar", "Registro"])
    with t1:
        u = st.text_input("User"); p = st.text_input("Pass", type="password")
        if st.button("Ingresar"): 
            if login(u,p): st.session_state.usuario = u; st.query_params["user_token"]=u; st.rerun()
            else: st.error("Error")
    with t2:
        nu = st.text_input("New User"); np = st.text_input("New Pass", type="password")
        if st.button("Crear"): 
            if crear_user(nu, np): st.success("Creado");
            else: st.error("Existe")

else:
    st.sidebar.caption(f"👤 {st.session_state.usuario}")
    if st.sidebar.button("➕ Nuevo Chat", type="primary", use_container_width=True):
        st.session_state.chat_id = None; st.rerun()
    
    st.sidebar.divider()
    
    # --- PANEL DE CONTROL ---
    st.sidebar.subheader("🛠️ Panel de Control")
    tareas = cerebro.obtener_tareas()
    
    # Selección de Rol
    idx = list(tareas.keys()).index("Asistente General") if "Asistente General" in tareas else 0
    tarea_sel = st.sidebar.selectbox("Experto:", list(tareas.keys()), index=idx, on_change=al_cambiar_rol)
    
    # Opciones (Limpias)
    c1, c2 = st.sidebar.columns(2)
    web = c1.toggle("🌍 Web", False, help="Buscar en internet")
    img_mode = c2.toggle("🎨 Crear Img", False, help="DALL-E 3")
    
    # ¡YA NO HAY UPLOADER AQUÍ! EL SIDEBAR QUEDA LIMPIO.

    st.sidebar.divider()
    
    # --- HISTORIAL ---
    st.sidebar.subheader("🗂️ Chats")
    for sid, dat in obtener_sesiones(st.session_state.usuario):
        tipo = "primary" if sid == st.session_state.chat_id else "secondary"
        if st.sidebar.button(f"💬 {dat.get('titulo','Chat')}", key=sid, use_container_width=True, type=tipo):
            st.session_state.chat_id = sid; st.rerun()
            
    if st.sidebar.button("Cerrar Sesión"):
        st.query_params.clear(); st.session_state.usuario = None; st.session_state.chat_id = None; st.rerun()

    # ==========================================
    # 🖥️ ZONA DE CHAT
    # ==========================================
    info = tareas[tarea_sel]
    st.subheader(f"{info.get('icon','🤖')} {tarea_sel}")
    
    # Variables de archivo (Se llenarán abajo)
    contexto_archivo = None
    imagen_vision = None
    
    # Etiquetas de estado
    status = []
    if web: status.append("🌐 Online")
    if img_mode: status.append("🎨 Modo Arte")
    
    # Cargar Msgs
    msgs = cargar_msgs(st.session_state.usuario, st.session_state.chat_id) if st.session_state.chat_id else []
    
    if not st.session_state.chat_id and not msgs:
         st.markdown(f"<div style='background:#262730;padding:15px;border-radius:10px'>👋 <b>Hola!</b> {info['desc']}</div>", unsafe_allow_html=True)

    # Renderizar Chat
    for m in msgs:
        with st.chat_message(m["role"]):
            if m["content"].startswith("http") and " " not in m["content"]: st.image(m["content"], width=350)
            else: st.markdown(m["content"])

    # --- 📎 ZONA DE ADJUNTOS (JUSTO ENCIMA DEL CHAT) ---
    # Usamos un expander para simular el botón de "Clip"
    with st.expander("📎 Adjuntar archivo (Imagen o PDF) para este mensaje", expanded=False):
        uploaded_file = st.file_uploader("Selecciona archivo", type=["png", "jpg", "jpeg", "pdf"], key="main_uploader", label_visibility="collapsed")
        
        if uploaded_file:
            if uploaded_file.type == "application/pdf":
                with st.spinner("📄 Procesando PDF..."):
                    contexto_archivo = cerebro.leer_pdf(uploaded_file)
                    st.success(f"PDF Cargado: {uploaded_file.name}")
                    status.append("📄 PDF Listo")
            else:
                st.image(uploaded_file, width=200, caption="Imagen lista para análisis")
                imagen_vision = base64.b64encode(uploaded_file.getvalue()).decode('utf-8')
                status.append("👁️ Imagen Lista")

    # Mostrar estado actualizado con archivos
    if status: st.caption(" | ".join(status))

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
            
            # 1. RUTA IMAGEN (DALL-E)
            if img_mode:
                res = cerebro.generar_imagen_dalle(prompt, info['image_style'])
                if "http" in res: st.image(res, width=350)
                else: st.error(res)
            
            # 2. RUTA VISIÓN (Si hay imagen adjunta)
            elif imagen_vision:
                res = cerebro.analizar_imagen_vision(prompt, imagen_vision, info['prompt'])
                st.markdown(res)
                
            # 3. RUTA TEXTO / PDF / WEB
            else:
                hist = [m for m in msgs if not m["content"].startswith("http")]
                res = cerebro.respuesta_inteligente(prompt, hist, info['prompt'], web, contexto_archivo)
                st.markdown(res)
        
        guardar_msg(st.session_state.usuario, st.session_state.chat_id, "assistant", res)
        if nuevo: st.rerun()
