import streamlit as st
from openai import OpenAI
from tavily import TavilyClient
import datetime

# --- CONFIGURACIÓN DE SECRETOS ---
try:
    OPENAI_KEY = st.secrets["OPENAI_KEY"]
    TAVILY_KEY = st.secrets["TAVILY_KEY"]
except:
    st.error("⚠️ Configura tus secretos primero.")
    st.stop()

def obtener_cliente():
    return OpenAI(api_key=OPENAI_KEY)

# --- BASE DE DATOS DE TAREAS Y ROLES (AQUÍ ESTÁ LA MAGIA) ---
def obtener_tareas():
    return {
        "Diseñar una Pagina Web Completa": {
            "icon": "💻",
            "desc": "Genera estructura, código HTML/CSS/JS y copy.",
            "system_prompt": """
            ACTÚA COMO: Un Equipo de Desarrollo Web Full-Stack Senior y Expertos en UX/UI.
            
            TU OBJETIVO: Diseñar y codificar sitios web modernos, responsivos y estéticos.
            
            INSTRUCCIONES CLAVE:
            1. Primero pregunta el objetivo del sitio (Landing, E-commerce, Blog).
            2. Si piden código, entrégalo en bloques separados (HTML, CSS, JS).
            3. Usa librerías modernas (Tailwind, React) si es necesario.
            4. Prioriza la accesibilidad y el SEO.
            """
        },
        "Diseñar un Logotipo (Idea + SVG)": {
            "icon": "🎨",
            "desc": "Crea conceptos de marca y código SVG vectorizado.",
            "system_prompt": """
            ACTÚA COMO: Un Diseñador Gráfico Senior especialista en Branding Minimalista.
            
            TU OBJETIVO: Crear la identidad visual de una marca.
            
            INSTRUCCIONES CLAVE:
            1. Analiza la psicología del color y la tipografía.
            2. Si el usuario pide ver el logo, GENERA CÓDIGO SVG que pueda renderizarse directamente.
            3. Explica el racional creativo detrás de cada decisión.
            """
        },
        "Generar Prompt para Imagen (Midjourney/DALL-E)": {
            "icon": "📸",
            "desc": "Redacta la instrucción perfecta para generar imágenes IA.",
            "system_prompt": """
            ACTÚA COMO: Un Ingeniero de Prompts experto en Generación de Imágenes (Midjourney v6 y DALL-E 3).
            
            TU OBJETIVO: Traducir la idea del usuario en un prompt técnico y artístico.
            
            INSTRUCCIONES CLAVE:
            1. Define: Sujeto, Estilo Artístico, Iluminación, Cámara, Relación de Aspecto (--ar).
            2. Usa palabras clave de fotografía (Bokeh, 8k, Unreal Engine).
            3. Entrega el prompt en bloque de código para copiar fácil.
            """
        },
        "Asistente de Marketing y Redes Sociales": {
            "icon": "🚀",
            "desc": "Crea calendarios, posts virales y estrategias.",
            "system_prompt": """
            ACTÚA COMO: Un Growth Hacker y Copywriter experto.
            
            TU OBJETIVO: Viralizar contenido y aumentar conversiones.
            
            INSTRUCCIONES CLAVE:
            1. Usa ganchos (Hooks) agresivos al inicio.
            2. Estructura el contenido con espacios y emojis estratégicos.
            3. Sugiere Hashtags relevantes.
            4. Adapta el tono a la red social (LinkedIn = Pro, TikTok = Dinámico).
            """
        },
        "Consultor de Negocios y Startups": {
            "icon": "💼",
            "desc": "Evalúa modelos de negocio y pitch decks.",
            "system_prompt": """
            ACTÚA COMO: Un Inversor de Venture Capital y Consultor de Estrategia.
            
            TU OBJETIVO: Encontrar fallos en modelos de negocio y optimizar la rentabilidad.
            
            INSTRUCCIONES CLAVE:
            1. Sé crítico y directo. No adules.
            2. Pide métricas clave (CAC, LTV, MRR) si no las dan.
            3. Usa marcos de trabajo como Lean Canvas o SWOT.
            """
        }
    }

# --- FUNCIONES DE CEREBRO (Mantenemos las mismas de antes) ---
def buscar_en_web(consulta):
    try:
        tavily = TavilyClient(api_key=TAVILY_KEY)
        respuesta = tavily.search(query=consulta, search_depth="advanced")
        contexto = []
        for resultado in respuesta['results'][:3]:
            contexto.append(f"- Fuente: {resultado['title']}\n  Info: {resultado['content']}")
        return "\n\n".join(contexto)
    except Exception as e:
        return f"Error web: {e}"

def respuesta_inteligente(mensaje_usuario, historial_previo, prompt_rol, usar_internet=False):
    client = obtener_cliente()
    ahora = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    prompt_sistema_base = f"""
    {prompt_rol}
    
    [SISTEMA]
    FECHA ACTUAL: {ahora}.
    """
    
    mensajes_sistema = [{"role": "system", "content": prompt_sistema_base}]
    
    if usar_internet:
        datos_web = buscar_en_web(mensaje_usuario)
        mensajes_sistema.append({"role": "system", "content": f"INFO INTERNET:\n{datos_web}"})

    mensajes_completos = mensajes_sistema + historial_previo + [{"role": "user", "content": mensaje_usuario}]

    response = client.chat.completions.create(model="gpt-4o-mini", messages=mensajes_completos)
    return response.choices[0].message.content
