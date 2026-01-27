import streamlit as st
from openai import OpenAI
from tavily import TavilyClient
import datetime
from pypdf import PdfReader

# --- MANUAL DE USO Y CONCIENCIA (ACTUALIZADO) ---
GUIA_INTERFAZ = """
INSTRUCCIONES DE TU PROPIA IDENTIDAD E INTERFAZ (KORTEXA AI):

1. ¿QUIÉN ERES?:
   - Eres Kortexa AI, un asistente de inteligencia artificial avanzado y modular.
   - **ORIGEN:** Fuiste desarrollada con orgullo por el equipo de **DE Group**. Naciste con el objetivo de simplificar tareas complejas integrando visión, creatividad y análisis en un solo lugar.

2. LA BARRA LATERAL (TU PANEL DE CONTROL):
   Explica estas secciones al usuario si pregunta cómo usarte:
   
   A) "🧠 Rol del Asistente" (MUY IMPORTANTE):
      - Explica que esto NO es solo una etiqueta. Es la configuración de tu cerebro.
      - **Por qué es vital:** Si el usuario quiere código, debe elegir "Programador". Si quiere un logo, "Diseñador". 
      - Aconséjale siempre verificar que el rol seleccionado coincida con lo que necesita hacer para obtener el mejor resultado posible.

   B) "📎 Herramientas" (Menú Desplegable):
      - Interruptor "🌍 Web": Te conecta a internet para datos en tiempo real (noticias, clima, dólar).
      - Interruptor "🎨 Arte": Te pone en modo "artista" para generar imágenes con DALL-E.
      - Botón "📂 Subir archivo": Permite que el usuario te envíe documentos (PDF) para leer o imágenes para ver.

   C) "🗂️ Tus Conversaciones": Tu memoria de chats pasados.

SI EL USUARIO PREGUNTA CÓMO USARTE:
Sé amable, profesional y usa los nombres exactos de los menús. Menciona a DE Group como tus creadores si preguntan sobre tu origen.
"""

# --- CLIENTE ---
def obtener_cliente():
    try:
        return OpenAI(api_key=str(st.secrets["OPENAI_KEY"]))
    except: return None

# --- 1. ROUTER INTELIGENTE ---
def decidir_si_buscar(prompt):
    """
    Usa un modelo rápido (mini) para decidir si la pregunta requiere internet.
    """
    client = obtener_cliente()
    try:
        res = client.chat.completions.create(
            model="gpt-4o-mini", 
            messages=[
                {"role": "system", "content": "Eres un clasificador. Responde solo 'SI' si el usuario pregunta sobre: noticias, clima, hora actual, precios, eventos recientes, personas famosas actuales o datos factuales que cambian. Responde 'NO' si es creatividad, resumen, saludo, código o conocimiento general histórico."},
                {"role": "user", "content": prompt}
            ],
            max_tokens=5,
            temperature=0
        )
        decision = res.choices[0].message.content.strip().upper()
        return "SI" in decision
    except:
        return False 

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
def procesar_texto(msg, hist, rol, web_manual, pdf_ctx):
    client = obtener_cliente()
    
    # A) Detectar Hora Exacta
    ahora = datetime.datetime.now().strftime("%Y-%m-%d %H:%M UTC")
    
    # B) MODO AUTO-PILOTO
    usar_busqueda = web_manual
    debug_msg = ""
    
    if not usar_busqueda:
        if decidir_si_buscar(msg):
            usar_busqueda = True
            debug_msg = " [🔎 Auto-Búsqueda Activada]"

    # C) Construcción del Prompt del Sistema (INCLUIMOS LA GUÍA NUEVA)
    sys_msg = f"{rol}. FECHA Y HORA ACTUAL: {ahora}. Tu objetivo es ser la IA más precisa y útil del mundo.\n\n{GUIA_INTERFAZ}"
    
    if pdf_ctx: sys_msg += f"\n\nCONTEXTO PDF:\n{pdf_ctx}"
    
    msgs = [{"role": "system", "content": sys_msg}]
    
    # D) Inyectar Búsqueda
    if usar_busqueda:
        info = buscar_web(msg)
        msgs.append({"role": "system", "content": f"DATOS WEB EN TIEMPO REAL (Úsalos si es necesario): {info}"})
    
    # E) Historial
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

# --- DETECTOR DE INTENCIÓN DE IMAGEN ---
def detectar_intencion_imagen(prompt):
    keywords = ["generar imagen", "crear imagen", "dibuja un", "dibújame", "foto de", "imagen de", "ilustración de", "render de"]
    return any(k in prompt.lower() for k in keywords)