import streamlit as st
from openai import OpenAI
from tavily import TavilyClient
import datetime

# --- CONFIGURACIÓN ---
try:
    OPENAI_KEY = str(st.secrets["OPENAI_KEY"])
    TAVILY_KEY = str(st.secrets["TAVILY_KEY"])
except:
    st.error("⚠️ Faltan secretos.")
    st.stop()

def obtener_cliente():
    return OpenAI(api_key=OPENAI_KEY)

# --- NUEVO: GENERADOR DE TÍTULOS INTELIGENTES ---
def generar_titulo_corto(primer_mensaje):
    """Crea un título resumen de 3 a 5 palabras basado en el mensaje"""
    client = obtener_cliente()
    try:
        res = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": "Eres un experto en resumir. Genera un TÍTULO de máximo 5 palabras que resuma el siguiente mensaje del usuario. Solo devuelve el título, sin comillas ni puntos."},
                {"role": "user", "content": primer_mensaje}
            ],
            max_tokens=15
        )
        return res.choices[0].message.content.strip()
    except:
        return "Nuevo Chat"

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

# --- BUSCAR WEB ---
def buscar_en_web(consulta):
    try:
        tavily = TavilyClient(api_key=TAVILY_KEY)
        respuesta = tavily.search(query=consulta, search_depth="advanced")
        contexto = []
        if 'results' in respuesta and isinstance(respuesta['results'], list):
            for resultado in respuesta['results'][:3]:
                contexto.append(f"- {resultado.get('title', 'Web')}: {resultado.get('content', '')}")
            return "\n".join(contexto)
        return "Sin resultados."
    except:
        return "Error de conexión."

# --- CEREBRO TEXTO ---
def respuesta_inteligente(mensaje_usuario, historial, prompt_rol, usar_internet):
    client = obtener_cliente()
    ahora = datetime.datetime.now().strftime("%Y-%m-%d")
    
    # Limpieza de datos (Anti-Crash)
    historial_limpio = []
    for msg in historial:
        if msg.get("content"):
            historial_limpio.append({"role": str(msg["role"]), "content": str(msg["content"])})

    sistema = [{"role": "system", "content": f"{prompt_rol}. FECHA: {ahora}"}]
    
    if usar_internet:
        info = buscar_en_web(mensaje_usuario)
        sistema.append({"role": "system", "content": f"DATOS WEB: {info}"})
        
    msgs = sistema + historial_limpio + [{"role": "user", "content": str(mensaje_usuario)}]
    
    try:
        res = client.chat.completions.create(model="gpt-4o-mini", messages=msgs)
        return res.choices[0].message.content
    except Exception as e:
        return f"Error IA: {e}"

# --- TAREAS ---
def obtener_tareas():
    return {
        "Experto en Instagram": {"icon": "📸", "desc": "Estrategias y captions.", "prompt": "ACTÚA COMO: Instagram Strategist."},
        "Guionista de TikTok": {"icon": "🎵", "desc": "Guiones virales.", "prompt": "ACTÚA COMO: Guionista Viral."},
        "Diseñador de Logos": {"icon": "🎨", "desc": "Conceptos visuales.", "prompt": "Diseño de logotipo vectorial, minimalista."},
        "Desarrollador Web": {"icon": "💻", "desc": "HTML/React Expert.", "prompt": "ACTÚA COMO: Senior Full Stack Developer."},
        "Asesor de Negocios": {"icon": "💼", "desc": "Estrategia.", "prompt": "ACTÚA COMO: Consultor Senior."},
        "Asistente General": {"icon": "🤖", "desc": "Chat libre.", "prompt": "Eres un asistente útil."}
        # ... (Puedes agregar más aquí) ...
    }
