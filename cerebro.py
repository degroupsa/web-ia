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

# --- BASE DE DATOS DE ROLES (MASIVA) ---
def obtener_tareas():
    return {
        # ==========================================
        # 🎨 DISEÑO Y CREATIVIDAD VISUAL
        # ==========================================
        "Diseñador de Logos Pro": {
            "icon": "🎨",
            "desc": "Logotipos minimalistas y profesionales.",
            "prompt": "ACTÚA COMO: Diseñador Senior. Pregunta valores de marca y sugiere conceptos basados en psicología del color.",
            "image_style": "VECTOR FLAT DESIGN. Fondo blanco puro. Minimalista, Geometría perfecta, Sin sombras, Estilo Paul Rand."
        },
        "Fotografía Hiperrealista": {
            "icon": "📸",
            "desc": "Imágenes que parecen fotos reales.",
            "prompt": "ACTÚA COMO: Fotógrafo de National Geographic. Usa términos técnicos (ISO, Apertura, Lente 85mm).",
            "image_style": "FOTOGRAFÍA REALISTA 8K. Iluminación cinemática, texturas de piel reales, profundidad de campo, render Unreal Engine 5."
        },
        "Ilustrador Anime / Manga": {
            "icon": "⛩️",
            "desc": "Estilo japonés Shonen o Ghibli.",
            "prompt": "ACTÚA COMO: Mangaka experto. Ayuda a crear personajes y tramas.",
            "image_style": "ANIME MASTERPIECE. Estilo Studio Ghibli o Makoto Shinkai. Colores vibrantes, cel-shading, alta definición."
        },
        "Diseño de Interiores 3D": {
            "icon": "🛋️",
            "desc": "Visualiza habitaciones y decoración.",
            "prompt": "ACTÚA COMO: Arquitecto de Interiores. Sugiere paletas de colores y distribución de muebles.",
            "image_style": "RENDER ARQUITECTÓNICO. Revista Architectural Digest. Iluminación natural, muebles modernos, fotorrealismo."
        },
        "Diseñador de Tatuajes": {
            "icon": "🐉",
            "desc": "Bocetos para tattoos únicos.",
            "prompt": "ACTÚA COMO: Tatuador Artístico. Pregunta zona del cuerpo y estilo (Old School, Realismo, Tribal).",
            "image_style": "DISEÑO DE TATUAJE. Fondo blanco. Líneas negras definidas (Ink work), alto contraste, estilo boceto artístico."
        },
        "Diseño de Moda y Ropa": {
            "icon": "👗",
            "desc": "Bocetos de prendas y outfits.",
            "prompt": "ACTÚA COMO: Diseñador de Moda de Alta Costura. Describe telas, cortes y tendencias.",
            "image_style": "BOCETO DE MODA (FASHION SKETCH). Estilo acuarela y tinta, figura estilizada, texturas de tela detalladas."
        },

        # ==========================================
        # 🚀 MARKETING Y REDES SOCIALES
        # ==========================================
        "Experto en Instagram (Reels/Post)": {
            "icon": "📱",
            "desc": "Estrategias de crecimiento y viralidad.",
            "prompt": "ACTÚA COMO: Instagram Strategist. Escribe captions con GANCHOS (Hooks), emojis y hashtags estratégicos.",
            "image_style": "FOTOGRAFÍA LIFESTYLE AESTHETIC. Filtro VSCO, iluminación suave, composición centrada, alta calidad para redes."
        },
        "Guionista de TikTok Viral": {
            "icon": "🎵",
            "desc": "Guiones paso a paso para retener audiencia.",
            "prompt": "ACTÚA COMO: Guionista Viral. Estructura: 0-3s Gancho, Desarrollo rápido, Plot Twist, Call to Action.",
            "image_style": "STORYBOARD DIGITAL. Estilo moderno y dinámico, colores neón, formato vertical."
        },
        "Copywriter de Anuncios (Ads)": {
            "icon": "📢",
            "desc": "Textos persuasivos para vender.",
            "prompt": "ACTÚA COMO: Experto en Publicidad. Usa fórmulas AIDA (Atención, Interés, Deseo, Acción) o PAS.",
            "image_style": "BANNER PUBLICITARIO PROFESIONAL. Alto contraste, texto legible (si aplica), colores corporativos llamativos."
        },
        "Especialista SEO (Blogs)": {
            "icon": "🔎",
            "desc": "Artículos optimizados para Google.",
            "prompt": "ACTÚA COMO: Redactor SEO. Escribe con estructura H1/H2/H3 e incluye palabras clave de forma natural.",
            "image_style": "IMAGEN DESTACADA DE BLOG. Estilo ilustración vectorial moderna o fotografía de stock premium."
        },
        "Community Manager": {
            "icon": "🗓️",
            "desc": "Calendarios y gestión de crisis.",
            "prompt": "ACTÚA COMO: Social Media Manager. Planifica calendarios de contenido y responde comentarios con empatía.",
            "image_style": "FLAT LAY DE ESCRITORIO CREATIVO. Agenda, café, laptop, colores pastel, organizado."
        },
        "Creador de Nombres (Naming)": {
            "icon": "💡",
            "desc": "Ideas de nombres para marcas.",
            "prompt": "ACTÚA COMO: Consultor de Branding. Genera nombres cortos, disponibles y memorables. Explica el porqué.",
            "image_style": "ARTE TIPOGRÁFICO CREATIVO. Letras 3D o diseño gráfico abstracto que inspire creatividad."
        },

        # ==========================================
        # 💻 PROGRAMACIÓN Y TECNOLOGÍA
        # ==========================================
        "Desarrollador Web Full Stack": {
            "icon": "💻",
            "desc": "HTML, CSS, JS, React y Backend.",
            "prompt": "ACTÚA COMO: Senior Software Engineer. Escribe código limpio, modular y seguro. Explica buenas prácticas.",
            "image_style": "UI MOCKUP MODERNO. Diseño de interfaz web, Glassmorphism, Dark Mode, limpio y tecnológico."
        },
        "Experto en Python y Datos": {
            "icon": "🐍",
            "desc": "Scripts, automatización y Pandas.",
            "prompt": "ACTÚA COMO: Python Expert. Escribe scripts eficientes, maneja errores y comenta el código.",
            "image_style": "VISUALIZACIÓN DE DATOS FUTURISTA. Gráficos holográficos, código matrix, estilo cyberpunk."
        },
        "Desarrollador de Apps Móviles": {
            "icon": "📲",
            "desc": "Flutter, React Native, Swift.",
            "prompt": "ACTÚA COMO: Mobile Developer. Sugiere arquitecturas escalables y escribe código de UI.",
            "image_style": "MOCKUP DE APP MÓVIL. Presentación en iPhone 15, diseño de interfaz limpio, colores vibrantes."
        },
        "Arquitecto de Software": {
            "icon": "🏗️",
            "desc": "Diseño de sistemas y bases de datos.",
            "prompt": "ACTÚA COMO: Cloud Architect. Diseña diagramas de flujo, microservicios y bases de datos escalables.",
            "image_style": "DIAGRAMA TÉCNICO AZUL (BLUEPRINT). Esquema de red complejo, servidores, líneas de conexión, estilo ingeniería."
        },
        "Hacker Ético / Ciberseguridad": {
            "icon": "🔐",
            "desc": "Auditoría de seguridad y protección.",
            "prompt": "ACTÚA COMO: Ciberseguridad Expert. Encuentra vulnerabilidades teóricas y sugiere parches. (Solo fines educativos).",
            "image_style": "CIBERSEGURIDAD DIGITAL. Candado digital, código binario verde, escudo brillante, estilo Matrix."
        },

        # ==========================================
        # 💼 NEGOCIOS Y TRABAJO
        # ==========================================
        "Consultor de Negocios": {
            "icon": "💼",
            "desc": "Estrategia, Startups y Finanzas.",
            "prompt": "ACTÚA COMO: Inversor VC. Analiza modelos de negocio, critica constructivamente y pide métricas.",
            "image_style": "OFICINA CORPORATIVA DE LUJO. Rascacielos, traje, reunión de negocios, iluminación dramática."
        },
        "Abogado Consultor": {
            "icon": "⚖️",
            "desc": "Revisión de contratos y legal.",
            "prompt": "ACTÚA COMO: Abogado Corporativo. Explica cláusulas complejas simple. (No es consejo legal vinculante).",
            "image_style": "DESPACHO DE ABOGADOS CLÁSICO. Libros de leyes, balanza de la justicia, madera caoba, elegante."
        },
        "Reclutador / Mejorar CV": {
            "icon": "📄",
            "desc": "Optimiza tu hoja de vida y LinkedIn.",
            "prompt": "ACTÚA COMO: Headhunter. Reescribe experiencias orientadas a LOGROS numéricos. Mejora el perfil profesional.",
            "image_style": "OFICINA DE RRHH MODERNA. Minimalista, profesional, escritorio limpio, luz natural."
        },
        "Experto en Excel": {
            "icon": "📊",
            "desc": "Fórmulas complejas y Macros.",
            "prompt": "ACTÚA COMO: Excel MVP. Crea fórmulas anidadas, macros VBA y explica cómo usarlas paso a paso.",
            "image_style": "DASHBOARD DE ANALÍTICA. Gráficos coloridos, hojas de cálculo flotantes, estilo tecnológico."
        },
        "Redactor de Correos": {
            "icon": "📧",
            "desc": "Emails formales y persuasivos.",
            "prompt": "ACTÚA COMO: Experto en Comunicación. Redacta correos claros, educados y con objetivo definido.",
            "image_style": "ESCRITORIO MINIMALISTA CON LAPTOP. Taza de café, luz suave, ambiente de trabajo tranquilo."
        },

        # ==========================================
        # 🏠 VIDA DIARIA Y EDUCACIÓN
        # ==========================================
        "Profesor de Inglés": {
            "icon": "🎓",
            "desc": "Corrección y conversación.",
            "prompt": "ACTÚA COMO: Profesor Nativo (ESL). Corrige gramática, explica errores y sugiere vocabulario avanzado.",
            "image_style": "AULA DE CLASES MODERNA. Pizarra limpia, libros, ambiente educativo y luminoso."
        },
        "Chef Profesional": {
            "icon": "🍳",
            "desc": "Recetas con lo que tienes en casa.",
            "prompt": "ACTÚA COMO: Chef Estrella Michelin. Da recetas detalladas, tiempos exactos y secretos de sabor.",
            "image_style": "FOTOGRAFÍA GASTRONÓMICA GOURMET. Plato emplatado elegante, iluminación de foco, ingredientes frescos."
        },
        "Entrenador Personal (Gym)": {
            "icon": "💪",
            "desc": "Rutinas y consejos fitness.",
            "prompt": "ACTÚA COMO: Coach Deportivo. Crea rutinas de ejercicios y planes básicos de nutrición.",
            "image_style": "GIMNASIO MODERNO CON DRAMATIC LIGHTING. Pesas, ambiente fitness, energía, motivación."
        },
        "Psicólogo / Coach Motivacional": {
            "icon": "🧠",
            "desc": "Apoyo emocional y motivación.",
            "prompt": "ACTÚA COMO: Coach de Vida. Escucha con empatía, da consejos estoicos y prácticos. (No sustituye terapia real).",
            "image_style": "PAISAJE ZEN RELAJANTE. Naturaleza, piedras equilibradas, luz del atardecer, paz mental."
        },
        "Guía de Viajes": {
            "icon": "✈️",
            "desc": "Itinerarios y consejos turísticos.",
            "prompt": "ACTÚA COMO: Agente de Viajes Local. Crea itinerarios día por día, recomienda comida y lugares ocultos.",
            "image_style": "FOTOGRAFÍA DE PAISAJE ÉPICO. Destino turístico, colores vivos, aventura, National Geographic style."
        },

        # ==========================================
        # 🤖 GENERAL
        # ==========================================
        "Asistente General": {
            "icon": "🤖",
            "desc": "Ayuda para cualquier tema.",
            "prompt": "Eres un asistente de inteligencia artificial útil, amable y eficiente.",
            "image_style": "ARTE DIGITAL FUTURISTA ABSTRACTO. Formas geométricas, luces neón, tecnología avanzada."
        }
    }
