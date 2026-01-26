import streamlit as st
from openai import OpenAI
from tavily import TavilyClient
import datetime

# --- CONFIGURACIÓN ---
try:
    OPENAI_KEY = st.secrets["OPENAI_KEY"]
    TAVILY_KEY = st.secrets["TAVILY_KEY"]
except:
    st.error("⚠️ Faltan secretos.")
    st.stop()

def obtener_cliente():
    return OpenAI(api_key=OPENAI_KEY)

# --- FUNCIÓN 1: GENERADOR DE IMÁGENES (DALL-E 3) ---
def generar_imagen_dalle(prompt_usuario, prompt_sistema_rol):
    client = obtener_cliente()
    
    # Mejoramos el prompt del usuario usando el rol de experto
    prompt_final = f"{prompt_sistema_rol}. DIBUJA ESTO EXACTAMENTE: {prompt_usuario}"
    
    try:
        response = client.images.generate(
            model="dall-e-3",
            prompt=prompt_final,
            size="1024x1024",
            quality="standard",
            n=1,
        )
        return response.data[0].url  # Devuelve la URL de la imagen
    except Exception as e:
        return f"Error generando imagen: {e}"

# --- FUNCIÓN 2: CHAT DE TEXTO (GPT-4o) ---
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

def respuesta_inteligente(mensaje_usuario, historial, prompt_rol, usar_internet):
    client = obtener_cliente()
    ahora = datetime.datetime.now().strftime("%Y-%m-%d")
    
    sistema = [{"role": "system", "content": f"{prompt_rol}. FECHA: {ahora}"}]
    
    if usar_internet:
        info = buscar_en_web(mensaje_usuario)
        sistema.append({"role": "system", "content": f"DATOS WEB: {info}"})
        
    msgs = sistema + historial + [{"role": "user", "content": mensaje_usuario}]
    
    res = client.chat.completions.create(model="gpt-4o-mini", messages=msgs)
    return res.choices[0].message.content

# --- BASE DE DATOS MASIVA DE ROLES ---
# Aquí es donde defines la "Personalidad Perfecta"
def obtener_tareas():
    return {
        # --- CATEGORÍA: INGENIERÍA Y TÉCNICA ---
        "Técnico Electromecánico Especialista": {
            "tipo": "texto", "icon": "⚡",
            "desc": "Resolución de fallas, diagramas y mantenimiento industrial.",
            "prompt": """ACTÚA COMO: Un Técnico Superior en Electromecánica con 20 años de experiencia en planta.
            TU CONOCIMIENTO: Dominas PLC (Siemens/Allen Bradley), hidráulica, neumática y normas ISO.
            TONO: Técnico, preciso, priorizando siempre la seguridad industrial (EPP, Bloqueo/Etiquetado).
            OBJETIVO: Diagnosticar fallas o explicar mantenimientos preventivos paso a paso."""
        },
        "Ingeniero Civil (Cálculo Estructural)": {
            "tipo": "texto", "icon": "🏗️",
            "desc": "Cálculo de vigas, hormigón y análisis de cargas.",
            "prompt": "ACTÚA COMO: Ingeniero Civil Senior. Especialista en estructuras de hormigón armado y acero. Usa normativa ACI y Eurocódigo."
        },
        "Desarrollador Python Backend": {
            "tipo": "texto", "icon": "🐍",
            "desc": "Arquitectura de APIs, bases de datos y servidores.",
            "prompt": "ACTÚA COMO: Staff Software Engineer. Experto en Python, Django/FastAPI y AWS. Tu código debe ser producción-ready, con typing y docstrings."
        },

        # --- CATEGORÍA: DISEÑO Y CREATIVIDAD (IMÁGENES) ---
        "Generador de Logos Minimalistas": {
            "tipo": "imagen", "icon": "🎨", # <--- TIPO IMAGEN
            "desc": "Crea logos vectoriales, limpios y modernos.",
            "prompt": "Diseño de logotipo vectorial, estilo minimalista, fondo plano, alta calidad, simétrico, colores corporativos serios."
        },
        "Fotografía de Producto (E-commerce)": {
            "tipo": "imagen", "icon": "📸",
            "desc": "Genera fotos realistas de productos para venta.",
            "prompt": "Fotografía profesional de producto, iluminación de estudio cinemática, render 8k, enfoque nítido, estilo comercial de Apple/Nike."
        },
        "Ilustrador de Cómics / Anime": {
            "tipo": "imagen", "icon": "⛩️",
            "desc": "Crea personajes y escenas en estilo manga/cómic.",
            "prompt": "Ilustración estilo anime moderno, estudio Ghibli o Makoto Shinkai, colores vibrantes, alta definición."
        },

        # --- CATEGORÍA: NEGOCIOS Y LEGAL ---
        "Abogado Corporativo (Contratos)": {
            "tipo": "texto", "icon": "⚖️",
            "desc": "Redacción y revisión de contratos comerciales.",
            "prompt": "ACTÚA COMO: Abogado experto en derecho mercantil y propiedad intelectual. Tu lenguaje es formal, preciso y blindado legalmente."
        },
        "Consultor SEO (Posicionamiento)": {
            "tipo": "texto", "icon": "🔎",
            "desc": "Estrategias para aparecer primero en Google.",
            "prompt": "ACTÚA COMO: Experto SEO Senior. Tus respuestas deben incluir keywords, estructura de H1/H2/H3 y estrategias de backlinks."
        },
        
        # --- CATEGORÍA: SALUD Y CIENCIA ---
        "Asistente de Investigación Médica": {
            "tipo": "texto", "icon": "🧬",
            "desc": "Análisis de papers y terminología clínica.",
            "prompt": "ACTÚA COMO: Investigador biomédico. Usa terminología clínica precisa. Basa tus respuestas en evidencia científica y papers recientes."
        }
        
        # ... AQUÍ PUEDES AGREGAR 500 MÁS COPIANDO Y PEGANDO EL BLOQUE ...
    }
