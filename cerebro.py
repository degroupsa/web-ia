import streamlit as st
from openai import OpenAI
from tavily import TavilyClient
import datetime

# --- CONFIGURACIÓN DE SECRETOS ---
try:
    OPENAI_KEY = st.secrets["OPENAI_KEY"]
    TAVILY_KEY = st.secrets["TAVILY_KEY"]
except:
    st.error("⚠️ Faltan las claves en los Secretos (secrets.toml).")
    st.stop()

def obtener_cliente():
    return OpenAI(api_key=OPENAI_KEY)

# --- FUNCIÓN 1: GENERAR IMAGEN (DALL-E 3) ---
def generar_imagen_dalle(prompt_usuario, prompt_sistema_rol):
    client = obtener_cliente()
    # Usamos el estilo del rol para guiar la imagen
    prompt_final = f"ESTILO VISUAL: {prompt_sistema_rol}. DIBUJA: {prompt_usuario}"
    
    try:
        response = client.images.generate(
            model="dall-e-3",
            prompt=prompt_final,
            size="1024x1024",
            quality="standard",
            n=1,
        )
        return response.data[0].url
    except Exception as e:
        return f"Error generando imagen: {e}"

# --- FUNCIÓN 2: BUSCAR EN WEB (TAVILY) ---
def buscar_en_web(consulta):
    try:
        tavily = TavilyClient(api_key=TAVILY_KEY)
        respuesta = tavily.search(query=consulta, search_depth="advanced")
        contexto = []
        for resultado in respuesta['results'][:3]:
            contexto.append(f"- {resultado['title']}: {resultado['content']}")
        return "\n".join(contexto)
    except:
        return "No se pudo conectar a internet."

# --- FUNCIÓN 3: CEREBRO DE TEXTO (GPT-4o) ---
def respuesta_inteligente(mensaje_usuario, historial, prompt_rol, usar_internet):
    client = obtener_cliente()
    ahora = datetime.datetime.now().strftime("%Y-%m-%d")
    
    sistema = [{"role": "system", "content": f"{prompt_rol}. HOY ES: {ahora}"}]
    
    if usar_internet:
        info = buscar_en_web(mensaje_usuario)
        sistema.append({"role": "system", "content": f"INFORMACIÓN DE INTERNET:\n{info}"})
        
    msgs = sistema + historial + [{"role": "user", "content": mensaje_usuario}]
    
    res = client.chat.completions.create(model="gpt-4o-mini", messages=msgs)
    return res.choices[0].message.content

# --- BASE DE DATOS DE TAREAS (EXPANDIDA) ---
def obtener_tareas():
    return {
        # --- MARKETING Y REDES SOCIALES (NUEVO & MASIVO) ---
        "Experto en Instagram (Posts y Stories)": {
            "icon": "📸", "desc": "Crea captions, ideas de stories y estrategias visuales.",
            "prompt": "ACTÚA COMO: Instagram Strategist. Crea captions con ganchos (hooks) iniciales, usa emojis estratégicos, saltos de línea y grupos de hashtags relevantes. Prioriza el engagement y los comentarios."
        },
        "Guionista de TikTok / Reels Viral": {
            "icon": "🎵", "desc": "Guiones paso a paso para videos cortos que enganchen.",
            "prompt": "ACTÚA COMO: Guionista de Video Viral. Estructura la respuesta así: 1. Gancho Visual (0-3 seg), 2. Desarrollo del problema, 3. Solución/Twist, 4. Call to Action (CTA). Sé dinámico y rápido."
        },
        "Redactor de Anuncios (Facebook/Instagram Ads)": {
            "icon": "📢", "desc": "Textos persuasivos para vender (Copywriting).",
            "prompt": "ACTÚA COMO: Experto en Paid Media Copywriting. Usa fórmulas de venta como AIDA (Atención, Interés, Deseo, Acción) o PAS (Problema, Agitación, Solución). Tu objetivo es que la gente haga clic en 'Comprar'."
        },
        "Especialista en LinkedIn (Marca Personal)": {
            "icon": "💼", "desc": "Posts profesionales para liderar en tu industria.",
            "prompt": "ACTÚA COMO: LinkedIn Top Voice. Escribe posts con un tono profesional pero humano (Storytelling). Estructura: Frase impactante, historia personal/profesional, lección aprendida y pregunta para debate."
        },
        "Email Marketing / Newsletters": {
            "icon": "📧", "desc": "Correos que la gente sí quiera abrir y leer.",
            "prompt": "ACTÚA COMO: Email Marketing Specialist. Escribe asuntos (Subject Lines) imposibles de ignorar. El cuerpo del correo debe ser conversacional, corto y con un solo objetivo (clic)."
        },
        "Planificador de Contenidos (Calendario)": {
            "icon": "🗓️", "desc": "Organiza qué publicar durante todo el mes.",
            "prompt": "ACTÚA COMO: Content Manager. Crea tablas de calendarios editoriales. Incluye: Día, Temática, Formato (Video/Foto/Carrusel), Idea clave y Objetivo."
        },
        "Experto SEO (Blogs y Google)": {
            "icon": "🔎", "desc": "Artículos optimizados para salir primero en Google.",
            "prompt": "ACTÚA COMO: Redactor SEO Senior. Escribe artículos estructurados con H1, H2, H3. Integra palabras clave (keywords) de forma natural. Prioriza la intención de búsqueda del usuario."
        },
        "Creador de Nombres (Naming) y Slogans": {
            "icon": "💡", "desc": "Ideas creativas para marcas, productos o dominios.",
            "prompt": "ACTÚA COMO: Consultor de Branding Creativo. Genera listas de nombres cortos, memorables y disponibles. Explica el racional detrás de cada nombre."
        },

        # --- CREATIVIDAD VISUAL ---
        "Diseñador de Logos": {
            "icon": "🎨", "desc": "Crea conceptos de logotipos únicos.",
            "prompt": "Diseño de logotipo vectorial, minimalista, fondo plano, alta calidad, estilo moderno, simétrico."
        },
        "Generador de Imágenes Realistas": {
            "icon": "🖼️", "desc": "Fotos que parecen reales (Midjourney Style).",
            "prompt": "Fotografía hiperrealista, 8k, iluminación cinemática, lente de 85mm, alta definición, texturas detalladas."
        },
        "Ilustrador Estilo Anime/Manga": {
            "icon": "⛩️", "desc": "Personajes y escenas estilo japonés.",
            "prompt": "Ilustración estilo anime de alta calidad, estudio Ghibli o Makoto Shinkai, colores vibrantes, líneas limpias."
        },
        "Diseño de Interiores y Arquitectura": {
            "icon": "🏠", "desc": "Visualiza habitaciones, casas y decoraciones.",
            "prompt": "Fotografía de arquitectura y diseño de interiores, revista Architectural Digest, iluminación natural, muebles modernos, render fotorrealista."
        },

        # --- PROGRAMACIÓN Y WEB ---
        "Crear Página Web (HTML/CSS)": {
            "icon": "💻", "desc": "Código listo para copiar y pegar.",
            "prompt": "ACTÚA COMO: Desarrollador Web Senior. Escribe código HTML5, CSS3 y JS moderno. Entrega los archivos separados. Asegura que sea 'Responsive' (adaptable a móvil)."
        },
        "Experto en Python y Datos": {
            "icon": "🐍", "desc": "Scripts, análisis de datos y automatización.",
            "prompt": "ACTÚA COMO: Python Developer Expert. Escribe scripts eficientes, con manejo de errores y comentarios explicativos. Si es análisis de datos, sugiere usar Pandas."
        },
        "Solucionar Errores de Código (Debug)": {
            "icon": "🔧", "desc": "Encuentra por qué falla tu programa.",
            "prompt": "ACTÚA COMO: Tech Lead. Analiza el código proporcionado, detecta el error lógico o de sintaxis, explica por qué falla y entrégame la solución corregida."
        },

        # --- NEGOCIOS Y TRABAJO ---
        "Mejorar Currículum (CV)": {
            "icon": "📄", "desc": "Optimiza tu perfil para conseguir entrevistas.",
            "prompt": "ACTÚA COMO: Reclutador experto (Headhunter). Reescribe la experiencia para que suene orientada a logros y resultados numéricos. Usa palabras clave de la industria."
        },
        "Redactar Correos Formales": {
            "icon": "✉️", "desc": "Comunicaciones serias para empresas.",
            "prompt": "ACTÚA COMO: Experto en Comunicación Corporativa. Redacta emails claros, formales y persuasivos. Mantén un tono profesional y educado."
        },
        "Asesor Legal (Contratos)": {
            "icon": "⚖️", "desc": "Revisión y explicación de documentos legales.",
            "prompt": "ACTÚA COMO: Abogado Consultor. Explica cláusulas complejas en lenguaje sencillo. (Aclara siempre que esto es información, no consejo legal vinculante)."
        },

        # --- VIDA DIARIA ---
        "Chef y Recetas": {
            "icon": "🍳", "desc": "Ideas de cocina con lo que tengas en la heladera.",
            "prompt": "ACTÚA COMO: Chef Profesional. Dame recetas paso a paso, tiempos de cocción exactos y trucos para mejorar el sabor."
        },
        "Profesor de Inglés": {
            "icon": "🎓", "desc": "Corrige textos o practica conversación.",
            "prompt": "ACTÚA COMO: Profesor nativo de inglés. Corrige mis errores gramaticales, explícame por qué está mal y dame la versión natural."
        },
        "Asistente General (IA)": {
            "icon": "🤖", "desc": "Charla libre sobre cualquier tema.",
            "prompt": "Eres un asistente de inteligencia artificial útil, amable y eficiente."
        }
    }
