import streamlit as st
from openai import OpenAI
from tavily import TavilyClient
import datetime
import base64
from pypdf import PdfReader

# --- CONFIGURACIÓN ---
try:
    OPENAI_KEY = str(st.secrets["OPENAI_KEY"])
    TAVILY_KEY = str(st.secrets["TAVILY_KEY"])
except:
    st.error("⚠️ Error: Faltan las API KEYS en secrets.toml")
    st.stop()

def obtener_cliente():
    return OpenAI(api_key=OPENAI_KEY)

# ==========================================
# 🛠️ SUPERPODERES (FUNCIONES TÉCNICAS)
# ==========================================

# 1. VISIÓN ARTIFICIAL (VER IMÁGENES)
def analizar_imagen_vision(mensaje_usuario, imagen_base64, prompt_rol):
    client = obtener_cliente()
    try:
        response = client.chat.completions.create(
            model="gpt-4o", # Modelo con visión
            messages=[
                {"role": "system", "content": f"{prompt_rol}. Estás analizando una imagen subida por el usuario."},
                {
                    "role": "user",
                    "content": [
                        {"type": "text", "text": mensaje_usuario},
                        {"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{imagen_base64}", "detail": "high"}},
                    ],
                }
            ],
            max_tokens=1000
        )
        return response.choices[0].message.content
    except Exception as e: return f"Error Vision: {e}"

# 2. LECTOR DE PDF
def leer_pdf(archivo):
    try:
        pdf_reader = PdfReader(archivo)
        texto = ""
        for page in pdf_reader.pages:
            texto += page.extract_text()
        return texto[:25000] # Límite de caracteres para no saturar
    except Exception as e: return f"Error PDF: {e}"

# 3. GENERADOR DE IMÁGENES (DALL-E 3)
def generar_imagen_dalle(prompt_usuario, estilo_experto):
    client = obtener_cliente()
    prompt_final = f"DIRECTIVAS DE ARTE: {estilo_experto}. DIBUJA: {prompt_usuario}"
    try:
        response = client.images.generate(
            model="dall-e-3", prompt=prompt_final, size="1024x1024", quality="hd", n=1, style="vivid"
        )
        return response.data[0].url
    except Exception as e: return f"Error DALL-E: {e}"

# 4. BUSCADOR WEB
def buscar_en_web(consulta):
    try:
        tavily = TavilyClient(api_key=TAVILY_KEY)
        response = tavily.search(query=consulta, search_depth="advanced")
        return "\n".join([f"- {r['title']}: {r['content']}" for r in response.get('results', [])[:3]])
    except: return "Sin conexión."

# 5. CEREBRO CENTRAL (INTEGRADOR)
def respuesta_inteligente(mensaje, historial, prompt_rol, usar_web, contexto_archivo=None):
    client = obtener_cliente()
    ahora = datetime.datetime.now().strftime("%Y-%m-%d")
    
    sistema = f"{prompt_rol}. HOY ES: {ahora}."
    if contexto_archivo:
        sistema += f"\n\n[CONTEXTO DEL ARCHIVO]:\n{contexto_archivo}\n\nUsa esto para responder."

    msgs_sistema = [{"role": "system", "content": sistema}]
    
    if usar_web:
        info = buscar_en_web(mensaje)
        msgs_sistema.append({"role": "system", "content": f"DATOS WEB: {info}"})
    
    # Limpiamos historial de imágenes previas para no gastar tokens
    hist_limpio = [{"role": str(m["role"]), "content": str(m["content"])} for m in historial if m.get("content") and not str(m["content"]).startswith("http")]
    
    try:
        res = client.chat.completions.create(model="gpt-4o", messages=msgs_sistema + hist_limpio + [{"role":"user", "content":str(mensaje)}])
        return res.choices[0].message.content
    except Exception as e: return f"Error GPT: {e}"

def generar_titulo_corto(msg):
    try:
        return obtener_cliente().chat.completions.create(
            model="gpt-4o-mini", messages=[{"role":"user", "content":f"Resume en 3 palabras: {msg}"}], max_tokens=10
        ).choices[0].message.content.strip()
    except: return "Chat Nuevo"

# ==========================================
# 📂 BASE DE DATOS DE ROLES (COMPLETA)
# ==========================================
def obtener_tareas():
    return {
        # --- 🎨 DISEÑO Y CREATIVIDAD ---
        "Diseñador de Logos Pro": {
            "icon": "🎨", "desc": "Logotipos minimalistas y branding.",
            "prompt": "ACTÚA COMO: Diseñador Senior. Pregunta valores y sugiere conceptos.",
            "image_style": "VECTOR FLAT DESIGN. Fondo blanco puro. Minimalista, Geometría perfecta, Sin sombras."
        },
        "Fotografía Hiperrealista": {
            "icon": "📸", "desc": "Imágenes estilo National Geographic.",
            "prompt": "ACTÚA COMO: Fotógrafo Profesional. Usa vocabulario técnico (ISO, Lentes).",
            "image_style": "FOTOGRAFÍA REALISTA 8K. Iluminación cinemática, texturas reales, render Unreal Engine 5."
        },
        "Ilustrador Anime / Manga": {
            "icon": "⛩️", "desc": "Estilo japonés Shonen o Ghibli.",
            "prompt": "ACTÚA COMO: Mangaka experto. Crea personajes y escenas.",
            "image_style": "ANIME MASTERPIECE. Estilo Studio Ghibli. Colores vibrantes, cel-shading."
        },
        "Diseño de Interiores 3D": {
            "icon": "🛋️", "desc": "Visualiza espacios y decoración.",
            "prompt": "ACTÚA COMO: Arquitecto de Interiores.",
            "image_style": "RENDER ARQUITECTÓNICO. Revista Architectural Digest. Iluminación natural, fotorrealismo."
        },
        "Diseñador de Tatuajes": {
            "icon": "🐉", "desc": "Bocetos e ideas para tatuajes.",
            "prompt": "ACTÚA COMO: Tatuador Artístico.",
            "image_style": "DISEÑO DE TATUAJE. Fondo blanco. Líneas negras definidas (Ink work), estilo boceto."
        },
        "Diseño de Moda": {
            "icon": "👗", "desc": "Bocetos de ropa y alta costura.",
            "prompt": "ACTÚA COMO: Diseñador de Moda.",
            "image_style": "FASHION SKETCH. Estilo acuarela y tinta, figura estilizada, texturas detalladas."
        },

        # --- 🚀 MARKETING DIGITAL ---
        "Experto en Instagram": {
            "icon": "📱", "desc": "Estrategias, Reels y crecimiento.",
            "prompt": "ACTÚA COMO: Instagram Strategist. Usa Hooks, emojis y hashtags.",
            "image_style": "FOTOGRAFÍA LIFESTYLE AESTHETIC. Filtro VSCO, iluminación suave."
        },
        "Guionista de TikTok": {
            "icon": "🎵", "desc": "Guiones virales paso a paso.",
            "prompt": "ACTÚA COMO: Guionista Viral. Estructura: Gancho, Desarrollo, Twist, CTA.",
            "image_style": "STORYBOARD DIGITAL. Estilo moderno, neón, formato vertical."
        },
        "Copywriter de Anuncios": {
            "icon": "📢", "desc": "Textos persuasivos para Ads.",
            "prompt": "ACTÚA COMO: Experto en Ads. Usa fórmulas AIDA o PAS.",
            "image_style": "BANNER PUBLICITARIO. Alto contraste, colores corporativos llamativos."
        },
        "Especialista SEO": {
            "icon": "🔎", "desc": "Blogs optimizados para Google.",
            "prompt": "ACTÚA COMO: Redactor SEO. Usa estructura H1/H2/H3 y palabras clave.",
            "image_style": "ILUSTRACIÓN VECTORIAL PARA BLOG. Moderna y limpia."
        },
        "Community Manager": {
            "icon": "🗓️", "desc": "Calendarios y gestión de redes.",
            "prompt": "ACTÚA COMO: Social Media Manager. Planifica contenidos.",
            "image_style": "FLAT LAY DE ESCRITORIO. Agenda, café, organizado."
        },
        "Creador de Nombres (Naming)": {
            "icon": "💡", "desc": "Ideas de nombres para marcas.",
            "prompt": "ACTÚA COMO: Consultor de Branding. Genera nombres cortos y memorables.",
            "image_style": "TIPOGRAFÍA 3D CREATIVA."
        },

        # --- 💻 PROGRAMACIÓN & TECH (CON VISIÓN) ---
        "Programador Senior (Vision)": {
            "icon": "💻", "desc": "Sube captura de error o pide código.",
            "prompt": "ACTÚA COMO: Tech Lead. Si recibes una imagen de código, analízala. Escribe código limpio.",
            "image_style": "UI MOCKUP TECNOLÓGICO. Dark mode, código en pantalla."
        },
        "Experto en Python": {
            "icon": "🐍", "desc": "Scripts, datos y automatización.",
            "prompt": "ACTÚA COMO: Python Expert. Escribe scripts eficientes.",
            "image_style": "VISUALIZACIÓN DE DATOS CYBERPUNK."
        },
        "Desarrollador Móvil": {
            "icon": "📲", "desc": "Apps en Flutter/React Native.",
            "prompt": "ACTÚA COMO: Mobile Developer.",
            "image_style": "MOCKUP IPHONE 15. Interfaz de app limpia."
        },
        "Hacker Ético / Seguridad": {
            "icon": "🔐", "desc": "Ciberseguridad y auditoría.",
            "prompt": "ACTÚA COMO: Ciberseguridad Expert. (Fines educativos).",
            "image_style": "SEGURIDAD DIGITAL MATRIX. Código binario, candado verde."
        },

        # --- 💼 NEGOCIOS & DOCUMENTOS ---
        "Analista de Documentos (PDF)": {
            "icon": "📊", "desc": "Sube un PDF y lo analizo.",
            "prompt": "ACTÚA COMO: Data Analyst. Lee el documento adjunto y extrae conclusiones.",
            "image_style": "INFOGRAFÍA DE DATOS."
        },
        "Consultor de Negocios": {
            "icon": "💼", "desc": "Startups, estrategia y pitch.",
            "prompt": "ACTÚA COMO: Inversor VC. Analiza modelos de negocio críticamente.",
            "image_style": "OFICINA CORPORATIVA LUJOSA."
        },
        "Abogado Consultor": {
            "icon": "⚖️", "desc": "Contratos y dudas legales.",
            "prompt": "ACTÚA COMO: Abogado Corporativo. Explica simple.",
            "image_style": "DESPACHO LEGAL CLÁSICO."
        },
        "Mejorar Currículum (CV)": {
            "icon": "📄", "desc": "Optimiza tu perfil laboral.",
            "prompt": "ACTÚA COMO: Recruiter. Enfoca la experiencia a logros.",
            "image_style": "OFICINA RRHH MINIMALISTA."
        },
        "Experto en Excel": {
            "icon": "📈", "desc": "Fórmulas y Macros.",
            "prompt": "ACTÚA COMO: Excel MVP.",
            "image_style": "DASHBOARD ANALÍTICO."
        },

        # --- 🏠 VIDA, EDUCACIÓN & VARIOS ---
        "Profesor de Inglés": {
            "icon": "🎓", "desc": "Corrección y conversación.",
            "prompt": "ACTÚA COMO: Profesor Nativo. Corrige errores.",
            "image_style": "AULA DE CLASES MODERNA."
        },
        "Chef (Análisis de Heladera)": {
            "icon": "🍳", "desc": "Sube foto de ingredientes -> Receta.",
            "prompt": "ACTÚA COMO: Chef Michelin. Si hay foto, identifica ingredientes y crea receta.",
            "image_style": "PLATO GOURMET EMPLATADO."
        },
        "Entrenador Personal": {
            "icon": "💪", "desc": "Rutinas de gym y dieta.",
            "prompt": "ACTÚA COMO: Coach Fitness.",
            "image_style": "GIMNASIO CON ILUMINACIÓN DRAMÁTICA."
        },
        "Psicólogo / Coach": {
            "icon": "🧠", "desc": "Apoyo y motivación.",
            "prompt": "ACTÚA COMO: Coach de Vida. (No es terapia médica).",
            "image_style": "PAISAJE ZEN RELAJANTE."
        },
        "Guía de Viajes": {
            "icon": "✈️", "desc": "Itinerarios turísticos.",
            "prompt": "ACTÚA COMO: Agente de Viajes.",
            "image_style": "PAISAJE ÉPICO NATIONAL GEOGRAPHIC."
        },
        "Traductor Universal": {
            "icon": "🌍", "desc": "Traducción de textos/docs.",
            "prompt": "ACTÚA COMO: Traductor Profesional.",
            "image_style": "MAPA MUNDI ARTÍSTICO."
        },

        # --- 🤖 GENERAL ---
        "Asistente General": {
            "icon": "🤖", "desc": "Ayuda multimodal (Chat/Visión).",
            "prompt": "Eres una IA avanzada y útil.",
            "image_style": "ARTE ABSTRACTO FUTURISTA."
        }
    }
