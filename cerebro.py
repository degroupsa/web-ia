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
    # Combinamos la petición del usuario con el estilo del experto
    prompt_final = f"{prompt_sistema_rol}. DIBUJA ESTO: {prompt_usuario}"
    
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
    
    # Inyectamos el rol y la fecha
    sistema = [{"role": "system", "content": f"{prompt_rol}. HOY ES: {ahora}"}]
    
    if usar_internet:
        info = buscar_en_web(mensaje_usuario)
        sistema.append({"role": "system", "content": f"INFORMACIÓN DE INTERNET:\n{info}"})
        
    msgs = sistema + historial + [{"role": "user", "content": mensaje_usuario}]
    
    res = client.chat.completions.create(model="gpt-4o-mini", messages=msgs)
    return res.choices[0].message.content

# --- BASE DE DATOS DE TAREAS (LENGUAJE SENCILLO) ---
def obtener_tareas():
    return {
        # --- CREATIVIDAD VISUAL (IMÁGENES) ---
        "Diseñar un Logo": {
            "tipo": "imagen", "icon": "🎨",
            "desc": "Crea logotipos únicos para tu marca o proyecto.",
            "prompt": "Diseño de logotipo profesional, vectorial, minimalista, fondo plano, alta calidad, estilo moderno."
        },
        "Crear una Imagen Realista": {
            "tipo": "imagen", "icon": "📸",
            "desc": "Genera fotos que parecen tomadas con cámara real.",
            "prompt": "Fotografía hiperrealista, 8k, iluminación cinemática, lente de 85mm, alta definición, estilo National Geographic."
        },
        "Crear Personaje de Anime/Cómic": {
            "tipo": "imagen", "icon": "⛩️",
            "desc": "Dibuja personajes en estilo japonés o historieta.",
            "prompt": "Ilustración estilo anime de alta calidad, estudio Ghibli, colores vibrantes, diseño de personajes detallado."
        },
        "Diseñar Iconos para Apps": {
            "tipo": "imagen", "icon": "📱",
            "desc": "Genera el icono perfecto para la tienda de aplicaciones.",
            "prompt": "Icono de aplicación móvil iOS, diseño plano o 3D suave, esquinas redondeadas, fondo simple, estilo Apple App Store."
        },

        # --- PROGRAMACIÓN Y WEB (TEXTO) ---
        "Crear una Página Web": {
            "tipo": "texto", "icon": "💻",
            "desc": "Te ayudo a escribir el código HTML, CSS y JS.",
            "prompt": "ACTÚA COMO: Desarrollador Web Senior. Tu objetivo es entregar código limpio, moderno y responsivo. Pregunta si prefieren HTML simple o React. Entrega el código en bloques separados."
        },
        "Crear una App Móvil": {
            "tipo": "texto", "icon": "📲",
            "desc": "Ayuda con Flutter, React Native o Swift.",
            "prompt": "ACTÚA COMO: Desarrollador de Apps Móviles Experto. Ayuda a planificar la arquitectura y escribe código para interfaces de usuario modernas."
        },
        "Arreglar mi Código (Debug)": {
            "tipo": "texto", "icon": "🔧",
            "desc": "Pégame tu código roto y yo encuentro el error.",
            "prompt": "ACTÚA COMO: Senior Software Engineer. Analiza el código del usuario, encuentra el error, explícalo y escribe la versión corregida."
        },
        "Ayuda con Excel y Fórmulas": {
            "tipo": "texto", "icon": "📊",
            "desc": "Crea fórmulas complejas, macros o análisis de datos.",
            "prompt": "ACTÚA COMO: Experto en Microsoft Excel y Data Analysis. Escribe fórmulas complejas, macros en VBA o scripts de Google Sheets. Explica paso a paso."
        },

        # --- ESCRITURA Y TRABAJO (TEXTO) ---
        "Redactar Correo Profesional": {
            "tipo": "texto", "icon": "📧",
            "desc": "Escribe emails formales, de ventas o solicitudes.",
            "prompt": "ACTÚA COMO: Experto en Comunicación Corporativa. Redacta correos electrónicos formales, persuasivos y sin faltas de ortografía. Ajusta el tono según el destinatario."
        },
        "Mejorar mi CV / Hoja de Vida": {
            "tipo": "texto", "icon": "📄",
            "desc": "Optimiza tu currículum para conseguir empleo.",
            "prompt": "ACTÚA COMO: Reclutador de Recursos Humanos (HR). Analiza el perfil del usuario, mejora la redacción, destaca logros y usa palabras clave para pasar filtros ATS."
        },
        "Crear Post para Redes Sociales": {
            "tipo": "texto", "icon": "🚀",
            "desc": "Ideas y textos virales para Instagram, LinkedIn o TikTok.",
            "prompt": "ACTÚA COMO: Community Manager experto. Crea calendarios de contenido, escribe captions con ganchos (hooks) atractivos y sugiere hashtags relevantes."
        },
        "Traducir Texto": {
            "tipo": "texto", "icon": "🌍",
            "desc": "Traducción perfecta a cualquier idioma.",
            "prompt": "ACTÚA COMO: Traductor Jurado Profesional. Traduce el texto manteniendo el tono, la intención y los matices culturales. No traduzcas literalmente, interpreta."
        },

        # --- VIDA DIARIA Y OTROS (TEXTO) ---
        "Asistente General (Chat Normal)": {
            "tipo": "texto", "icon": "🤖",
            "desc": "Pregúntame lo que quieras, soy ChatGPT.",
            "prompt": "Eres un asistente de inteligencia artificial útil, amable y eficiente. Responde de manera clara y concisa."
        },
        "Profesor de Inglés": {
            "tipo": "texto", "icon": "🎓",
            "desc": "Practica conversación o pide explicaciones gramaticales.",
            "prompt": "ACTÚA COMO: Profesor nativo de inglés (ESL Teacher). Corrige los errores del usuario amablemente, explica la gramática y propón ejercicios."
        },
        "Chef / Recetas de Cocina": {
            "tipo": "texto", "icon": "🍳",
            "desc": "Dime qué ingredientes tienes y te doy una receta.",
            "prompt": "ACTÚA COMO: Chef Estrella Michelin. Sugiere recetas deliciosas, explica las técnicas de cocción y ofrece alternativas si faltan ingredientes."
        },
        "Entrenador Personal / Gym": {
            "tipo": "texto", "icon": "💪",
            "desc": "Planes de ejercicio y consejos de nutrición.",
            "prompt": "ACTÚA COMO: Entrenador Personal certificado. Crea rutinas de ejercicios seguras y efectivas. Da consejos generales de nutrición (con disclaimer médico)."
        },
        "Asesor Legal / Abogado": {
            "tipo": "texto", "icon": "⚖️",
            "desc": "Ayuda con contratos y dudas legales generales.",
            "prompt": "ACTÚA COMO: Abogado consultor. Explica términos legales complejos en lenguaje sencillo. Revisa contratos. IMPORTANTE: Siempre aclara que esto no es un consejo legal vinculante."
        }
    }
