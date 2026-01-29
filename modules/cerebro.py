import streamlit as st
import os  # <--- 1. IMPORTANTE: Necesario para leer variables de Render
from openai import OpenAI
from tavily import TavilyClient
import datetime
from pypdf import PdfReader
from modules import roles 

# --- MANUAL DE USO DINÁMICO (CEREBRO DE LA IDENTIDAD) ---
def obtener_guia_dinamica(rol_actual):
    """
    Define la personalidad y las instrucciones de la interfaz.
    """
    dict_roles = roles.obtener_tareas()
    nombres_roles = ", ".join(dict_roles.keys())
    
    return f"""
    INSTRUCCIONES DE SISTEMA (KORTEXA AI - DE GROUP):

    1. IDENTIDAD Y TONO:
       - Eres **Kortexa AI**, una inteligencia desarrollada por **DE Group**.
       - NO eres un modelo de lenguaje genérico; eres una herramienta integrada en esta aplicación específica.
       - Tu ROL ACTUAL es: "{rol_actual}".

    2. TUS ROLES DISPONIBLES:
       [{nombres_roles}]

    3. >>> CASO ESPECIAL: PREGUNTA "¿CÓMO FUNCIONAS?" (PRIORIDAD MÁXIMA):
       Si el usuario pregunta "¿Cómo funcionas?", "¿Qué haces?" o "¿Cómo se usa?", 
       NO des una lista aburrida. Habla de ti misma integrando la interfaz así:
       
       "¡Hola! Soy Kortexa. No soy solo un chat, soy todo este entorno que ves. Déjame guiarte por mi interfaz:
       
       🧠 **Mi Cerebro (Menú Roles):**
       A tu izquierda verás 'Rol del Asistente'. Ahí es donde configuras mi mentalidad. Si me pones en modo 'Abogado', pensaré como tal. ¡Es vital que elijas el experto adecuado para cada tarea!
       
       📎 **Mis Herramientas (Menú Desplegable):**
       En la barra lateral tienes mis 'superpoderes':
       - **Web:** Enciéndelo para conectarme a Google en tiempo real.
       - **Arte:** Enciéndelo si quieres que dibuje para ti.
       - **Subir Archivo:** Dame documentos PDF para leer o imágenes para analizar.
       
       Todo esto está diseñado por DE Group para potenciar tu trabajo. ¿Probamos cambiar mi rol o subir un archivo?"

    4. DETECTIVE DE ROLES (ALTA VISIBILIDAD):
       Si el usuario pide algo complejo (ej: "crear web", "contrato") y tu rol NO es el adecuado:
       
       DEBES INICIAR TU RESPUESTA CON ESTE BLOQUE EXACTO (Usa el signo '>' para citar):
       
       > ⚠️ **ATENCIÓN: RECOMENDACIÓN DE EXPERTO**
       > He notado que quieres realizar una tarea específica.
       > Para obtener un resultado profesional, por favor **cambia mi rol a '[Nombre del Rol Ideal]'** en la barra lateral izquierda.
       
       (Luego de este bloque, responde a la pregunta lo mejor que puedas).
    """

# --- CLIENTE (HÍBRIDO: RENDER + LOCAL) ---
def obtener_cliente():
    # 1. Intentamos leer la variable de entorno de Render
    api_key = os.environ.get("OPENAI_API_KEY")
    
    # 2. Si no existe (estamos en local), usamos st.secrets
    if not api_key:
        try:
            api_key = st.secrets["OPENAI_KEY"]
        except:
            return None

    return OpenAI(api_key=str(api_key))

# --- 1. ROUTER ---
def decidir_si_buscar(prompt):
    client = obtener_cliente()
    if not client: return False # Protección si no hay clave
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
        # Lógica híbrida también para Tavily
        t_key = os.environ.get("TAVILY_KEY")
        if not t_key:
            try: t_key = st.secrets["TAVILY_KEY"]
            except: return "Error: Falta API Key de Tavily."

        tavily = TavilyClient(api_key=str(t_key))
        res = tavily.search(query=query, search_depth="advanced")
        return "\n".join([f"- {r['title']}: {r['content']}" for r in res.get('results', [])[:3]])
    except: return "Sin conexión."

# --- 3. PROCESADOR PRINCIPAL ---
def procesar_texto(msg, hist, rol_prompt, web_manual, pdf_ctx, nombre_rol_actual):
    client = obtener_cliente()
    if not client: return "⚠️ Error de Configuración: No se detectó la API Key de OpenAI."

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
    
    # Usamos gpt-4o (asegúrate que tu cuenta tenga saldo, sino cambia a gpt-3.5-turbo)
    res = client.chat.completions.create(model="gpt-4o", messages=msgs)
    return res.choices[0].message.content + debug_msg

def generar_titulo(msg):
    client = obtener_cliente()
    if not client: return "Nuevo Chat"
    try:
        return client.chat.completions.create(
            model="gpt-4o-mini", messages=[{"role":"user", "content":f"Título 3 palabras: {msg}"}], max_tokens=10
        ).choices[0].message.content.strip()
    except: return "Nuevo Chat"

def detectar_intencion_imagen(prompt):
    keywords = ["generar imagen", "crear imagen", "dibuja", "dibújame", "foto de", "imagen de"]
    return any(k in prompt.lower() for k in keywords)