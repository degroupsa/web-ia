import streamlit as st
import firebase_admin
from firebase_admin import credentials, firestore
import cerebro  # Importamos tu archivo de lógica

# --- 1. CONFIGURACIÓN DE PÁGINA ---
st.set_page_config(
    page_title="DevMaster AI", 
    layout="wide", 
    page_icon="🔥",
    initial_sidebar_state="expanded"
)

# --- 2. CONEXIÓN A FIREBASE (HÍBRIDA Y ROBUSTA) ---
# Intentamos conectar. Si ya está conectado, no hace nada.
if not firebase_admin._apps:
    try:
        # INTENTO A: Conexión NUBE (Streamlit Cloud usando Secrets)
        if "firebase" in st.secrets:
            # Convertimos el objeto de secretos a un diccionario normal
            key_dict = dict(st.secrets["firebase"])
            # Arreglamos el bug de los saltos de línea en la clave privada
            key_dict["private_key"] = key_dict["private_key"].replace("\\n", "\n")
            
            cred = credentials.Certificate(key_dict)
            firebase_admin.initialize_app(cred)
        
        # INTENTO B: Conexión LOCAL (Tu PC usando el archivo json)
        else:
            cred = credentials.Certificate("firebase_key.json")
            firebase_admin.initialize_app(cred)
            
    except Exception as e:
        st.error(f"❌ Error crítico de base de datos: {e}")
        st.stop()

# Cliente de Base de Datos
db = firestore.client()

# --- 3. FUNCIONES DE BASE DE DATOS ---
def crear_usuario(user, pwd):
    doc_ref = db.collection("users").document(user)
    if doc_ref.get().exists:
        return False
    
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
            return datos
    return None

def guardar_mensaje_historial(user, role, content):
    # Guardamos en la subcolección 'chats' del usuario
    db.collection("users").document(user).collection("chats").add({
        "role": role,
        "content": content,
        "fecha": firestore.SERVER_TIMESTAMP
    })

def cargar_historial(user):
    # Traemos los mensajes ordenados por fecha
    chats_ref = db.collection("users").document(user).collection("chats")
    docs = chats_ref.order_by("fecha").stream()
    return [doc.to_dict() for doc in docs]

# --- 4. INTERFAZ: BARRA LATERAL (SIDEBAR) ---
st.sidebar.title("🔥 DevMaster AI")

if "usuario" not in st.session_state:
    st.session_state.usuario = None

# Menú de navegación dinámico
opciones_menu = ["Login / Registro"]
if st.session_state.usuario:
    opciones_menu = ["Plataforma AI", "Generador Prompts", "Mi Cuenta"]

menu = st.sidebar.radio("Navegación", opciones_menu)

# Mostrar estado del usuario abajo a la izquierda
if st.session_state.usuario:
    st.sidebar.divider()
    st.sidebar.caption(f"👤 Conectado como: {st.session_state.usuario}")
    if st.sidebar.button("Cerrar Sesión"):
        st.session_state.usuario = None
        st.rerun()

# ==========================================
# 🔐 MÓDULO: LOGIN / REGISTRO
# ==========================================
if menu == "Login / Registro":
    st.header("Acceso a la Plataforma")
    tab1, tab2 = st.tabs(["Ingresar", "Crear Cuenta"])
    
    with tab1:
        u = st.text_input("Usuario")
        p = st.text_input("Contraseña", type="password")
        if st.button("Entrar"):
            data = login(u, p)
            if data:
                st.session_state.usuario = u
                st.session_state.plan = data["plan"]
                st.success("¡Bienvenido!")
                st.rerun() # Recarga la página para mostrar el menú nuevo
            else:
                st.error("Datos incorrectos")
                
    with tab2:
        nu = st.text_input("Nuevo Usuario")
        np = st.text_input("Nueva Contraseña", type="password")
        if st.button("Registrarse"):
            if crear_usuario(nu, np):
                st.success("Cuenta creada. Ahora inicia sesión.")
            else:
                st.error("El usuario ya existe.")

# ==========================================
# 🤖 MÓDULO: PLATAFORMA AI (EL NÚCLEO)
# ==========================================
elif menu == "Plataforma AI":
    # --- HEADER: BUSCADOR DE TAREAS ---
    st.subheader(f"Hola, {st.session_state.usuario}. ¿Qué vamos a crear hoy?")
    
    # Traemos las tareas desde cerebro.py
    tareas_disponibles = cerebro.obtener_tareas()
    lista_tareas = list(tareas_disponibles.keys())
    
    tarea_seleccionada = st.selectbox(
        "Selecciona un experto o tarea:",
        options=lista_tareas,
        index=None,
        placeholder="Escribe para buscar (ej: logo, python, marketing)..."
    )
    
    # --- LÓGICA PRINCIPAL ---
    if tarea_seleccionada:
        info = tareas_disponibles[tarea_seleccionada]
        tipo_tarea = info.get("tipo", "texto") # Detectamos si es imagen o texto

        # FEEDBACK VISUAL (Banner Verde)
        st.success(f"✅ Experto asignado correctamente: **{tarea_seleccionada}**")
        
        # Detalles del rol
        with st.expander(f"Ver detalles del Rol {info['icon']}"):
            st.write(f"**Descripción:** {info['desc']}")
            st.caption("Prompt de sistema optimizado cargado.")

        # Interruptor de Internet (Solo visible si es tarea de texto)
        usar_web = False
        if tipo_tarea == "texto":
            usar_web = st.toggle("🌍 Modo Online (Buscar en Google)", value=False)
            if usar_web:
                st.caption("⚡ La IA buscará datos en tiempo real antes de responder.")
        
        st.divider()

        # --- MOSTRAR HISTORIAL ---
        mensajes_db = cargar_historial(st.session_state.usuario)
        
        for msg in mensajes_db:
            with st.chat_message(msg["role"]):
                contenido = msg["content"]
                # LÓGICA VISUAL: Si parece una URL de imagen, mostramos la foto
                if contenido.startswith("http") and " " not in contenido:
                    st.image(contenido, width=400)
                else:
                    st.markdown(contenido)

        # --- INPUT DEL USUARIO ---
        prompt = st.chat_input(f"Escribe tu instrucción para {tarea_seleccionada}...")
        
        if prompt:
            # 1. Mostrar y Guardar lo que escribió el usuario
            with st.chat_message("user"):
                st.markdown(prompt)
            guardar_mensaje_historial(st.session_state.usuario, "user", prompt)
            
            # 2. PROCESAMIENTO (CEREBRO)
            with st.spinner(f"El experto {info['icon']} está trabajando en ello..."):
                
                texto_para_guardar = ""
                
                # --- CAMINO A: GENERAR IMAGEN (DALL-E) ---
                if tipo_tarea == "imagen":
                    resultado = cerebro.generar_imagen_dalle(prompt, info['prompt'])
                    
                    if "Error" in resultado:
                        st.error(resultado)
                        texto_para_guardar = f"Error: {resultado}"
                    else:
                        st.image(resultado, caption="Imagen Generada por DevMaster AI")
                        texto_para_guardar = resultado # Guardamos la URL
                
                # --- CAMINO B: CHAT DE TEXTO (GPT-4o) ---
                else:
                    # Filtramos historial para no pasarle URLs de imágenes al chat de texto
                    historial_ia = [
                        {"role": m["role"], "content": m["content"]} 
                        for m in mensajes_db[-5:] 
                        if not m["content"].startswith("http")
                    ]
                    
                    resultado = cerebro.respuesta_inteligente(
                        mensaje_usuario=prompt,
                        historial=historial_ia,
                        prompt_rol=info['prompt'],
                        usar_internet=usar_web
                    )
                    st.markdown(resultado)
                    texto_para_guardar = resultado

            # 3. Guardar la respuesta de la IA en Firebase
            guardar_mensaje_historial(st.session_state.usuario, "assistant", texto_para_guardar)
            
    else:
        st.info("👆 Por favor, selecciona una tarea en el menú de arriba para activar la IA.")

# ==========================================
# ✨ MÓDULO: GENERADOR DE PROMPTS
# ==========================================
elif menu == "Generador Prompts":
    st.header("✨ Refinador de Prompts")
    st.markdown("Si no sabes cómo pedirle algo a la IA, escribe tu idea vaga aquí y te daré el prompt perfecto.")
    
    c1, c2 = st.columns([2,1])
    with c1:
        idea = st.text_area("Idea básica:", "Ej: Quiero un plan de dieta.")
    with c2:
        tipo = st.selectbox("Formato:", ["Texto", "Imagen", "Código"])
        
    if st.button("Mejorar Prompt"):
        with st.spinner("Optimizando..."):
            # Usamos una función simple de cerebro (puedes reutilizar respuesta_inteligente o crear una específica)
            prompt_sistema = "Eres un experto en Prompt Engineering. Mejora la idea del usuario."
            res = cerebro.respuesta_inteligente(f"Mejora esta idea para {tipo}: {idea}", [], prompt_sistema, False)
            st.code(res)

# ==========================================
# 👤 MÓDULO: MI CUENTA
# ==========================================
elif menu == "Mi Cuenta":
    st.header("Panel de Usuario")
    st.info(f"Usuario: {st.session_state.usuario}")
    st.warning(f"Plan Actual: {st.session_state.plan}")
    st.caption("Próximamente: Historial de facturación y Upgrade a PRO.")
