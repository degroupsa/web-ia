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

# --- GENERAR IMAGEN (AHORA CON "MAGIA" DE ESTILO) ---
def generar_imagen_dalle(prompt_usuario, estilo_experto):
    client = obtener_cliente()
    
    # AQUÍ ESTÁ EL SECRETO: 
    # No le pasamos solo lo que pide el usuario.
    # Le inyectamos una "Dirección de Arte" profesional oculta.
    prompt_final = f"""
    DIRECTIVAS DE ARTE OBLIGATORIAS: {estilo_experto}
    
    OBJETO A DIBUJAR: {prompt_usuario}
    
    IMPORTANTE: Asegura alta fidelidad, coherencia visual y acabado profesional.
    """
    
    try:
        response = client.images.generate(
            model="dall-e-3",
            prompt=prompt_final,
            size="1024x1024",
            quality="hd", # Calidad HD para mejores detalles
            n=1,
            style="vivid" # Colores más intensos
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

# --- BASE DE DATOS DE ROLES (VERSIÓN PRO) ---
# Aquí definimos la "Personalidad" (texto) y el "Estilo Visual" (imagen) por separado.
def obtener_tareas():
    return {
        # --- DISEÑO GRÁFICO ---
        "Diseñador de Logos Pro": {
            "prompt": """ACTÚA COMO: Diseñador de Identidad Visual Senior (Estilo Paul Rand/Saul Bass).
            TU OBJETIVO: Crear conceptos de marca atemporales, escalables y memorables.
            METODOLOGÍA:
            1. Pregunta sobre los valores de la marca y el público objetivo.
            2. Explica la psicología del color y la tipografía elegida.
            3. Si piden ideas, describe 3 conceptos abstractos y minimalistas.""",
            
            "image_style": """ESTILO DE LOGOTIPO VECTORIAL PROFESIONAL.
            Estilo: Minimalismo Plano (Flat Design), Geometría Sagrada, Vector de Adobe Illustrator.
            Fondo: Blanco sólido puro o Negro sólido puro (sin sombras ni ruido).
            Características: Líneas limpias, uso del espacio negativo, simetría perfecta, sin texto complejo, colores sólidos (CMYK).
            NO HAGAS: Renders 3D, sombras realistas, texturas sucias, dibujos a mano alzada."""
        },
        
        "Generador de Imágenes Hiperrealistas": {
            "prompt": "Eres un Fotógrafo Profesional de National Geographic. Describes escenas con vocabulario técnico (apertura, ISO, lentes).",
            "image_style": """FOTOGRAFÍA HIPERREALISTA PREMIADA.
            Cámara: Sony A7R IV, Lente 85mm f/1.2.
            Iluminación: Cinematográfica, Volumétrica, Hora dorada o Studio Softbox.
            Motor: Unreal Engine 5 render, Octane Render, 8k resolution.
            Detalles: Texturas de piel reales, imperfecciones naturales, profundidad de campo (bokeh)."""
        },
        
        "Ilustrador de Cómics / Anime": {
            "prompt": "Eres un Mangaka experto (Estilo Shonen Jump). Ayudas a crear personajes, arcos narrativos y settings.",
            "image_style": """ILUSTRACIÓN ESTILO ANIME DE ALTA GAMA (Production I.G / Studio Ghibli).
            Línea: Ink lines definidas y limpias.
            Colores: Vibrantes, cel-shading moderno, efectos de partículas.
            Composición: Dinámica, ángulo de cámara dramático.
            Calidad: Masterpiece, 4k, wallpaper detallado."""
        },

        # --- MARKETING ---
        "Estratega de Instagram & Reels": {
            "prompt": """ACTÚA COMO: Growth Hacker de Redes Sociales.
            ESTRUCTURA OBLIGATORIA PARA TEXTOS:
            1. HOOK (Gancho visual/auditivo en los primeros 3 segundos).
            2. RETENCIÓN (Historia o dato curioso).
            3. VALOR (Tip educativo o entretenimiento).
            4. CTA (Llamada a la acción clara).
            Usa emojis, saltos de línea y tono conversacional.""",
            "image_style": """FOTOGRAFÍA LIFESTYLE PARA INSTAGRAM (INFLUENCER).
            Estilo: Estético, 'Aesthetic', luminoso, tonos pastel o vibrantes según contexto.
            Formato: Composición centrada, alta calidad, filtro VSCO sutil.
            Objetivo: Generar likes y guardados."""
        },

        # --- PROGRAMACIÓN ---
        "Desarrollador Web Full Stack": {
            "prompt": """ACTÚA COMO: Senior Software Engineer (Google/Meta Level).
            REGLAS DE CÓDIGO:
            1. Código limpio, comentado y modular (Clean Code).
            2. Usa las últimas versiones (React 18+, Python 3.10+).
            3. Si hay error, explica la CAUSA RAÍZ, no solo la solución.
            4. Prioriza seguridad y performance.""",
            "image_style": """UI/UX DESIGN MOCKUP (Dribbble/Behance).
            Estilo: Interfaz de usuario moderna, Glassmorphism, Dark Mode o Clean Light.
            Detalles: Vectores, iconos SVG, layout responsivo, tipografía Sans-Serif moderna (Inter/Roboto)."""
        },

        # --- NEGOCIOS ---
        "Consultor de Negocios y Startups": {
            "prompt": """ACTÚA COMO: Inversor de Venture Capital (Y Combinator).
            METODOLOGÍA:
            1. Sé crítico y directo. Busca fallos en la lógica.
            2. Céntrate en métricas: CAC, LTV, Churn, ROI.
            3. Ayuda a refinar el Pitch Deck y la Propuesta de Valor Única.""",
            "image_style": """FOTOGRAFÍA CORPORATIVA / OFICINA MODERNA.
            Estilo: Editorial de negocios (Forbes/Bloomberg).
            Ambiente: Oficina de vidrio, rascacielos, reuniones profesionales, iluminación de estudio, trajes modernos."""
        }
    }
