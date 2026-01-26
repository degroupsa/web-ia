import streamlit as st
import firebase_admin
from firebase_admin import credentials, firestore
import cerebro

# --- 1. CONFIGURACIÓN ---
st.set_page_config(page_title="DevMaster AI", layout="wide", page_icon="🔥")

# --- 2. CONEXIÓN A FIREBASE ---
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

# --- 3. FUNCIONES DB ---
def crear_usuario(user, pwd):
    doc = db.collection("users").document(user).get()
    if doc.exists: return False
    db.collection("users").document(user).set({
        "password": pwd, "plan": "Gratis", "fecha": firestore.SERVER_TIMESTAMP
    })
    return True

def login(user, pwd):
    doc = db.collection("users").document(user).get()
    if doc.exists and doc.to_dict()["password"] == pwd:
        return doc.to_dict()
    return None

def guardar_historial(user, role, content):
    db.collection("users").document(user).collection("chats").add({
        "role": role, "content": content, "fecha": firestore.SERVER_TIMESTAMP
    })

def cargar_historial(user):
    ref = db.collection("users").document(user).collection("chats")
    return [d.to_dict() for d in ref.order_by("fecha").stream()]

# --- 4. INTERFAZ ---
st.sidebar.title("🔥 DevMaster AI")
if "usuario" not in st.session_state: st.session_state.usuario = None

menu = st.sidebar.radio("Navegación", ["Login", "Plataforma AI"] if not st.session_state.usuario else ["Plataforma AI", "Mi Cuenta"])

# LOGIN
if menu == "Login":
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
        nu = st.text_input("Nuevo User")
        np = st.text_input("Nueva Pass", type="password")
        if st.button("Crear"):
            if crear_usuario(nu, np): st.success("Creado!")
            else: st.error("Ya existe")

# PLATAFORMA
elif menu == "Plataforma AI":
    st.subheader(f"Hola, {st.session_state.usuario}")
    
    tareas = cerebro.obtener_tareas()
    tarea_sel = st.selectbox("¿Qué necesitas hoy?", list(tareas.keys()), index=None, placeholder="Busca: Marketing, Logo, Web...")
    
    if tarea_sel:
        info = tareas[tarea_sel]
        st.success(f"✅ Rol Activo: **{tarea_sel}**")
        
        # --- ZONA DE CONTROL (INTERRUPTORES) ---
        # Aquí permitimos que CUALQUIER rol tenga superpoderes
        col1, col2 = st.columns(2)
        with col1:
            modo_web = st.toggle("🌍 Buscar en Web (Noticias)", value=False)
        with col2:
            modo_imagen = st.toggle("🎨 Generar Imagen (DALL-E)", value=False)
            
        if modo_imagen:
            st.info("🖼️ Modo Imagen Activado: Describe lo que quieres dibujar.")
        elif modo_web:
            st.info("📰 Modo Online Activado: La IA buscará datos actuales.")
            
        st.divider()

        # Historial
        msgs = cargar_historial(st.session_state.usuario)
        for m in msgs:
            with st.chat_message(m["role"]):
                if m["content"].startswith("http") and " " not in m["content"]:
                    st.image(m["content"], width=300)
                else:
                    st.markdown(m["content"])

        # Chat Input
        prompt = st.chat_input(f"Escribe a tu {tarea_sel}...")
        
        if prompt:
            # Guardar User
            with st.chat_message("user"): st.markdown(prompt)
            guardar_historial(st.session_state.usuario, "user", prompt)
            
            with st.spinner("Generando..."):
                res_final = ""
                
                # --- LÓGICA UNIVERSAL: ¿IMAGEN O TEXTO? ---
                if modo_imagen:
                    # Generamos imagen SIN IMPORTAR EL ROL
                    res_final = cerebro.generar_imagen_dalle(prompt, info['prompt'])
                    if "Error" in res_final:
                        st.error(res_final)
                    else:
                        st.image(res_final, caption="Imagen generada")
                else:
                    # Generamos texto (con o sin internet)
                    hist_ia = [m for m in msgs[-5:] if not m["content"].startswith("http")]
                    res_final = cerebro.respuesta_inteligente(
                        prompt, hist_ia, info['prompt'], modo_web
                    )
                    st.markdown(res_final)
            
            # Guardar IA
            guardar_historial(st.session_state.usuario, "assistant", res_final)

elif menu == "Mi Cuenta":
    st.header(f"Usuario: {st.session_state.usuario}")
    if st.button("Salir"):
        st.session_state.usuario = None
        st.rerun()
