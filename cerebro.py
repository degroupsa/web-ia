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

# --- GENERADOR DE TÍTULOS ---
def generar_titulo_corto(primer_mensaje):
    client = obtener_cliente()
    try:
        res = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": "Genera un título de 3-5 palabras resumen. Sin comillas."},
                {"role": "user", "content": primer_mensaje}
            ], max_tokens=15
        )
        return res.choices[0].message.content.strip()
    except: return "Nuevo Chat"

# --- GENERAR IMAGEN ---
def generar_imagen_dalle(prompt_usuario, estilo_experto):
    client = obtener_cliente()
    prompt_final = f"""
    DIRECTIVAS DE ARTE OBLIGATORIAS: {estilo_experto}
    OBJETO A DIBUJAR: {prompt_usuario}
    IMPORTANTE: Asegura alta fidelidad, coherencia visual y acabado profesional.
    """
    try:
        response = client.images.generate(
            model="dall-e-3", prompt=prompt_final, size="1024x1024", quality="hd", n=1, style="vivid"
        )
        return response.data[0].url
    except Exception as e:
        return f"Error generando imagen: {e}"

# --- BUSCADOR WEB ---
def buscar_en_web(consulta):
    try:
        tavily = TavilyClient(api_key=TAVILY_KEY)
        respuesta = tavily.search(query=consulta, search_depth="advanced")
        contexto = []
        if 'results' in respuesta:
            for r in respuesta['results'][:3]:
                contexto.append(f"- {r.get('title')}: {r.get('content')}")
            return "\n".join(contexto)
        return "Sin info."
    except: return "Error conexión."

# --- CEREBRO TEXTO ---
def respuesta_inteligente(mensaje, historial, prompt_rol, usar_web):
    client = obtener_cliente()
    ahora = datetime.datetime.now().strftime("%Y-%m-%d")
    
    hist_limpio = [{"role": str(m["role"]), "content": str(m["content"])} for m in historial if m.get("content")]
    
    sistema = [{"role": "system", "content": f"{prompt_rol}. HOY ES: {ahora}"}]
    if usar_web:
        info = buscar_en_web(mensaje)
        sistema.append({"role": "system", "content": f"DATOS WEB ACTUALES: {info}"})
        
    try:
        res = client.chat.completions.create(model="gpt-4o-mini", messages=sistema + hist_limpio + [{"role":"user", "content":str(mensaje)}])
        return res.choices[0].message.content
    except Exception as e: return f"Error: {e}"

# --- BASE DE DATOS DE ROLES (CORREGIDA Y COMPLETA) ---
def obtener_tareas():
    return {
        # --- DISEÑO GRÁFICO ---
        "Diseñador de Logos Pro": {
            "icon": "🎨",
            "desc": "Crea conceptos de marca atemporales estilo Paul Rand.",
            "prompt": """ACTÚA COMO: Diseñador de Identidad Visual Senior.
            METODOLOGÍA:
            1. Pregunta sobre los valores de la marca.
            2. Explica la psicología del color.
            3. Describe 3 conceptos minimalistas.""",
            "image_style": """ESTILO DE LOGOTIPO VECTORIAL PROFESIONAL.
            Estilo: Minimalismo Plano (Flat Design), Geometría Sagrada.
            Fondo: Blanco sólido puro.
            Características: Líneas limpias, espacio negativo, simetría perfecta."""
        },
        
        "Generador de Imágenes Hiperrealistas": {
            "icon": "📸",
            "desc": "Fotografía estilo National Geographic y Cine.",
            "prompt": "Eres un Fotógrafo Profesional. Describes escenas con vocabulario técnico (apertura, ISO, lentes).",
            "image_style": """FOTOGRAFÍA HIPERREALISTA PREMIADA.
            Cámara: Sony A7R IV, Lente 85mm f/1.2.
            Iluminación: Cinematográfica, Volumétrica.
            Motor: Unreal Engine 5 render, 8k resolution."""
        },
        
        "Ilustrador de Cómics / Anime": {
            "icon": "⛩️",
            "desc": "Estilo Manga Shonen Jump y Studio Ghibli.",
            "prompt": "Eres un Mangaka experto. Ayudas a crear personajes y arcos narrativos.",
            "image_style": """ILUSTRACIÓN ESTILO ANIME DE ALTA GAMA.
            Línea: Ink lines definidas y limpias.
            Colores: Vibrantes, cel-shading moderno.
            Composición: Dinámica, ángulo de cámara dramático."""
        },

        # --- MARKETING ---
        "Estratega de Instagram & Reels": {
            "icon": "📱",
            "desc": "Growth Hacking y contenido viral.",
            "prompt": """ACTÚA COMO: Growth Hacker de Redes Sociales.
            ESTRUCTURA OBLIGATORIA: 1. HOOK, 2. RETENCIÓN, 3. VALOR, 4. CTA.""",
            "image_style": """FOTOGRAFÍA LIFESTYLE PARA INSTAGRAM.
            Estilo: Estético, 'Aesthetic', luminoso.
            Formato: Composición centrada, alta calidad."""
        },

        # --- PROGRAMACIÓN ---
        "Desarrollador Web Full Stack": {
            "icon": "💻",
            "desc": "Código limpio en React, Python y Arquitectura.",
            "prompt": """ACTÚA COMO: Senior Software Engineer.
            REGLAS: Código limpio, modular y seguro.""",
            "image_style": """UI/UX DESIGN MOCKUP.
            Estilo: Interfaz moderna, Glassmorphism, Dark Mode."""
        },

        # --- NEGOCIOS ---
        "Consultor de Negocios": {
            "icon": "💼",
            "desc": "Análisis de Startups y Pitch Decks.",
            "prompt": """ACTÚA COMO: Inversor de Venture Capital.
            METODOLOGÍA: Sé crítico, céntrate en métricas (CAC, LTV).""",
            "image_style": """FOTOGRAFÍA CORPORATIVA MODERNA.
            Ambiente: Oficina de vidrio, reuniones profesionales, iluminación de estudio."""
        },

        # --- GENERAL ---
        "Asistente General": {
            "icon": "🤖",
            "desc": "Tu asistente de IA para cualquier consulta.",
            "prompt": "Eres un asistente de inteligencia artificial útil, amable y eficiente.",
            "image_style": "Arte digital abstracto y futurista, colores neón, alta tecnología."
        }
    }
