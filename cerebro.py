import streamlit as st
from openai import OpenAI
from tavily import TavilyClient
import datetime

# --- CONFIGURACIÓN DE SECRETOS ---
try:
    # Forzamos conversión a string para evitar errores de tipo
    OPENAI_KEY = str(st.secrets["OPENAI_KEY"])
    TAVILY_KEY = str(st.secrets["TAVILY_KEY"])
except:
    st.error("⚠️ Faltan las claves en los Secretos.")
    st.stop()

def obtener_cliente():
    return OpenAI(api_key=OPENAI_KEY)

# --- GENERAR IMAGEN ---
def generar_imagen_dalle(prompt_usuario, prompt_sistema_rol):
    client = obtener_cliente()
    prompt_final = f"ESTILO: {prompt_sistema_rol}. DIBUJA: {prompt_usuario}"
    try:
        response = client.images.generate(
            model="dall-e-3", prompt=prompt_final, size="1024x1024", quality="standard", n=1
        )
        return response.data[0].url
    except Exception as e:
        return f"Error generando imagen: {e}"

# --- BUSCAR EN WEB ---
def buscar_en_web(consulta):
    try:
        tavily = TavilyClient(api_key=TAVILY_KEY)
        respuesta = tavily.search(query=consulta, search_depth="advanced")
        contexto = []
        # Validamos que 'results' exista y sea lista
        if 'results' in respuesta and isinstance(respuesta['results'], list):
            for resultado in respuesta['results'][:3]:
                contexto.append(f"- {resultado.get('title', 'Sin titulo')}: {resultado.get('content', '')}")
            return "\n".join(contexto)
        return "Sin resultados relevantes."
    except:
        return "No se pudo conectar a internet."

# --- CEREBRO DE TEXTO (BLINDADO) ---
def respuesta_inteligente(mensaje_usuario, historial, prompt_rol, usar_internet):
    client = obtener_cliente()
    ahora = datetime.datetime.now().strftime("%Y-%m-%d")
    
    # 1. Limpieza de historial (Anti-Error TypeError)
    historial_limpio = []
    for msg in historial:
        if msg.get("content"): # Solo si tiene contenido
            historial_limpio.append({
                "role": str(msg["role"]), 
                "content": str(msg["content"]) # Forzamos string
            })

    # 2. Construcción del Sistema
    sistema = [{"role": "system", "content": f"{prompt_rol}. FECHA: {ahora}"}]
    
    if usar_internet:
        info = buscar_en_web(mensaje_usuario)
        sistema.append({"role": "system", "content": f"DATOS WEB: {info}"})
        
    # 3. Ensamblaje final
    msgs = sistema + historial_limpio + [{"role": "user", "content": str(mensaje_usuario)}]
    
    try:
        res = client.chat.completions.create(model="gpt-4o-mini", messages=msgs)
        return res.choices[0].message.content
    except Exception as e:
        return f"Error en el cerebro IA: {e}"

# --- BASE DE DATOS DE TAREAS (TUS CATEGORÍAS) ---
def obtener_tareas():
    return {
        # --- MARKETING ---
        "Experto en Instagram": {"icon": "📸", "desc": "Estrategias, captions y hashtags.", "prompt": "ACTÚA COMO: Instagram Strategist. Crea captions con hooks virales."},
        "Guionista de TikTok": {"icon": "🎵", "desc": "Guiones para videos cortos.", "prompt": "ACTÚA COMO: Guionista Viral. Estructura: Gancho, Desarrollo, Twist, CTA."},
        "Copywriter de Anuncios": {"icon": "📢", "desc": "Textos para Ads que vendan.", "prompt": "ACTÚA COMO: Experto en Paid Media. Usa fórmulas AIDA o PAS."},
        "Planificador de Contenidos": {"icon": "🗓️", "desc": "Calendarios editoriales.", "prompt": "ACTÚA COMO: Content Manager. Organiza por tablas: Día, Formato, Idea."},
        
        # --- NEGOCIOS ---
        "Asesor de Negocios": {"icon": "💼", "desc": "Estrategia y modelos de negocio.", "prompt": "ACTÚA COMO: Consultor de Negocios Senior. Evalúa riesgos y oportunidades."},
        "Naming (Crear Nombres)": {"icon": "💡", "desc": "Ideas de nombres para marcas.", "prompt": "ACTÚA COMO: Consultor de Branding. Genera nombres cortos y memorables."},
        
        # --- CREATIVIDAD ---
        "Diseñador de Logos": {"icon": "🎨", "desc": "Conceptos visuales de marcas.", "prompt": "Diseño de logotipo vectorial, minimalista, fondo plano."},
        "Generador de Imágenes": {"icon": "🖼️", "desc": "Crea cualquier imagen realista.", "prompt": "Fotografía cinemática, alta definición, 8k."},
        
        # --- DEV ---
        "Desarrollador Web": {"icon": "💻", "desc": "HTML, CSS, JS y React.", "prompt": "ACTÚA COMO: Senior Full Stack Developer. Escribe código limpio y modular."},
        "Experto en Python": {"icon": "🐍", "desc": "Scripts y automatización.", "prompt": "ACTÚA COMO: Python Expert. Escribe scripts eficientes con manejo de errores."},
        
        # --- GENERAL ---
        "Asistente General": {"icon": "🤖", "desc": "Chat libre.", "prompt": "Eres un asistente útil y amable."}
    }
