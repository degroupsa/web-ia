import streamlit as st
from openai import OpenAI
from tavily import TavilyClient
import datetime
from pypdf import PdfReader
from modules import roles  # <--- Importamos roles para la guía dinámica

# --- MANUAL DE USO DINÁMICO (DETECTIVE DE ROLES) ---
def obtener_guia_dinamica(rol_actual):
    """
    Genera instrucciones dinámicas. Kortexa lee sus propios roles
    y aprende a recomendar el mejor para la tarea del usuario.
    """
    # Obtenemos la lista real de roles disponibles para que la IA los conozca
    dict_roles = roles.obtener_tareas()
    nombres_roles = ", ".join(dict_roles.keys())
    
    return f"""
    INSTRUCCIONES DE SISTEMA (KORTEXA AI - DE GROUP):

    1. TU IDENTIDAD:
       - Eres Kortexa AI, un desarrollo de **DE Group**.
       - Tu ROL ACTUAL seleccionado por el usuario es: "{rol_actual}".

    2. TUS MÓDULOS DISPONIBLES:
       Tienes instalados estos roles en la barra lateral: 
       [{nombres_roles}]

    3. >>> INSTRUCCIÓN DE "DETECTIVE DE ROLES" (PRIORIDAD ALTA):
       Tu trabajo es asegurarte de que el usuario use el mejor experto para su problema.
       
       SI el usuario pide algo complejo (ej: "crear una web", "contrato legal", "logo") 
       Y tu rol actual NO es el especialista adecuado (ej: estás en "Asistente General"):
       
       DEBES iniciar tu respuesta con una sugerencia amigable:
       "💡 **Sugerencia Kortexa:** Para esta tarea, te recomiendo cambiar al rol **'[Nombre del Rol Ideal]'** en la barra lateral."
       
       LUEGO, responde a la pregunta lo mejor que puedas con tu rol actual.

    4. SOBRE LA INTERFAZ (Si preguntan "Cómo funcionas"):
       - Explica que en "🧠 Rol del Asistente" cambian tu personalidad.
       - En "📎 Herramientas" tienen Web, Arte y Carga de Archivos.
       - Menciona que eres un desarrollo de DE Group.
    """

# --- CLIENTE ---
def obtener_cliente():
    try:
        return OpenAI(api_key=str(st.secrets["OPENAI_KEY"]))
    except: return None

# --- 1. ROUTER INTELIGENTE ---
def decidir_si_buscar(prompt):
    """
    Decide si la pregunta requiere búsqueda en internet.
    """
    client = obtener_cliente()
    try:
        res = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": "Responde SI si el usuario pregunta sobre: noticias, clima, hora, precios, eventos recientes. Responde NO si es charla general."},
                {"role": "user", "content": prompt}
            ],
            max_tokens=5, temperature=0
        )
        return "SI" in res.choices[0].message.content.strip().upper()
    except: return False

# --- 2. HERRAMIENTAS ---
def analizar_vision(msg, b64_img, rol):
    client = obtener_cliente()
    try:
        res = client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {"role": "system", "content": f"{rol}. Analiza la imagen."},
                {"role": "user", "content": [{"type": "text", "text": msg}, {"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{b64_img}"}}]}
            ]
        )
        return res.choices[0].message.content
    except Exception as e: return f"Error Vision: {e}"

def generar_imagen(prompt, estilo):
    client = obtener_cliente()
    try:
        res = client.images.generate(
            model="dall-e-3", prompt=f"ESTILO: {estilo}. DIBUJA: {prompt}", size="1024x1024", quality="hd", style="vivid"
        )
        return res.data[0].url
    except Exception as e: return f"Error DALL-E: {e}"

def leer_pdf(file):
    try:
        reader = PdfReader(file)
        return "".join([p.extract_text() for p in reader.pages])[:25000]
    except: return "Error PDF"

def buscar_web(query):
    try:
        tavily = TavilyClient(api_key=str(st.secrets["TAVILY_KEY"]))
        res = tavily.search(query=query, search_depth="advanced")
        return "\n".join([f"- {r['title']}: {r['content']}" for r in res.get('results', [])[:3]])
    except: return "Sin conexión."

# --- 3. PROCESADOR PRINCIPAL ---
def procesar_texto(msg, hist, rol_prompt, web_manual, pdf_ctx, nombre_rol_actual):
    client = obtener_cliente()
    ahora = datetime.datetime.now().strftime("%Y-%m-%d %H:%M UTC")
    
    # Auto-piloto
    usar_busqueda = web_manual
    debug_msg = ""
    if not usar_busqueda and decidir_si_buscar(msg):
        usar_busqueda = True
        debug_msg = " [🔎 Auto-Web]"

    # Generamos la guía pasando el rol actual
    guia_actualizada = obtener_guia_dinamica(nombre_rol_actual)

    # Construcción del Prompt
    sys_msg = f"{rol_prompt}. FECHA: {ahora}. Objetivo: Ser la mejor IA de DE Group.\n\n{guia_actualizada}"
    
    if pdf_ctx: sys_msg += f"\n\nCONTEXTO PDF:\n{pdf_ctx}"
    
    msgs = [{"role": "system", "content": sys_msg}]
    
    if usar_busqueda:
        info = buscar_web(msg)
        msgs.append({"role": "system", "content": f"DATOS WEB: {info}"})
    
    hist_clean = [{"role": m["role"], "content": m["content"]} for m in hist if not m["content"].startswith("http")]
    msgs += hist_clean + [{"role": "user", "content": msg}]
    
    res = client.chat.completions.create(model="gpt-4o", messages=msgs)
    return res.choices[0].message.content + debug_msg

def generar_titulo(msg):
    try:
        return obtener_cliente().chat.completions.create(
            model="gpt-4o-mini", messages=[{"role":"user", "content":f"Título 3 palabras: {msg}"}], max_tokens=10
        ).choices[0].message.content.strip()
    except: return "Nuevo Chat"

def detectar_intencion_imagen(prompt):
    keywords = ["generar imagen", "crear imagen", "dibuja", "dibújame", "foto de", "imagen de"]
    return any(k in prompt.lower() for k in keywords)