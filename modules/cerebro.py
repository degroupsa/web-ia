import streamlit as st
import os  
from openai import OpenAI
from tavily import TavilyClient
import datetime
from pypdf import PdfReader
from modules import roles 

# --- CLIENTE ---
def obtener_cliente():
    api_key = os.environ.get("OPENAI_API_KEY")
    if not api_key:
        try: api_key = st.secrets["OPENAI_KEY"]
        except: return None
    return OpenAI(api_key=str(api_key))

# --- MANUAL DE USO DINÁMICO ---
def obtener_guia_dinamica(rol_actual):
    # Lógica de advertencia si estamos en modo general
    advertencia_contexto = ""
    if "General" in rol_actual:
        advertencia_contexto = """
        IMPORTANTE - DETECCIÓN DE ROL:
        Estás en modo 'Asistente General'.
        - Si el usuario te pide una tarea altamente especializada (ej: diseñar un logo profesional, redactar un contrato legal, auditar código complejo):
          NO te niegues a hacerlo. HAZLO, pero OBLIGATORIAMENTE inicia tu respuesta con este bloque de advertencia:
          
          > ⚠️ **RECOMENDACIÓN:** Para un resultado de nivel experto en esta tarea, te sugiero cambiar al rol especializado correspondiente desde el menú o pidiéndomelo (ej: "Actúa como Diseñador").
          
          ---
        """

    return f"""
    SISTEMA KORTEXA AI.
    ROL ACTUAL: {rol_actual}.
    
    {advertencia_contexto}

    CAPACIDADES ACTIVAS:
    1. GENERACIÓN DE IMÁGENES (DALL-E 3): Si el usuario pide imagen, HAZLA.
    2. GENERACIÓN DE APPS (HTML): Si pide una app/juego, genera el código HTML completo.
    3. CAMBIO DE ROL: Si el usuario pide explícitamente "actúa como abogado" o "cambia a modo X", CONFIRMA el cambio verbalmente.
    """

# --- DETECTOR DE CAMBIO DE ROL ---
def detectar_cambio_rol(prompt):
    """
    Analiza si el usuario quiere cambiar de personalidad explícitamente.
    Devuelve la CLAVE del rol en el diccionario roles.py o None.
    """
    p = prompt.lower()
    
    # Mapeo exhaustivo de palabras clave a las claves EXACTAS de roles.py
    mapa_roles = {
        "abogado": "Abogado Consultor",
        "legal": "Abogado Consultor",
        "leyes": "Abogado Consultor",
        "programador": "Programador Senior (Vision)",
        "codigo": "Programador Senior (Vision)",
        "dev": "Programador Senior (Vision)",
        "diseñador": "Diseñador de Logos Pro",
        "diseño": "Diseñador de Logos Pro",
        "logo": "Diseñador de Logos Pro",
        "foto": "Fotografía Hiperrealista",
        "fotografo": "Fotografía Hiperrealista",
        "marketing": "Copywriter PRO (Ventas)",
        "copywriter": "Copywriter PRO (Ventas)",
        "general": "Asistente General (Multimodal)",
        "normal": "Asistente General (Multimodal)",
        "asistente": "Asistente General (Multimodal)",
        "ingles": "Profesor de Inglés",
        "idiomas": "Profesor de Inglés",
        "chef": "Chef (Análisis de Heladera)",
        "cocina": "Chef (Análisis de Heladera)",
        "entrenador": "Entrenador Personal (Gym)",
        "fitness": "Entrenador Personal (Gym)",
        "psicologo": "Psicólogo / Coach Motivacional",
        "coach": "Psicólogo / Coach Motivacional",
        "viajes": "Guía de Viajes",
        "turismo": "Guía de Viajes",
        "traductor": "Traductor Universal",
        "excel": "Experto en Excel",
        "mobile": "Desarrollador de Apps Móviles",
        "app": "Desarrollador de Apps Móviles",
        "hacker": "Hacker Ético / Ciberseguridad",
        "seguridad": "Hacker Ético / Ciberseguridad",
        "arquitecto": "Arquitecto de Software",
        "interiores": "Diseño de Interiores 3D",
        "decoracion": "Diseño de Interiores 3D",
        "anime": "Ilustrador Anime / Manga",
        "manga": "Ilustrador Anime / Manga",
        "tatuaje": "Diseñador de Tatuajes",
        "moda": "Diseño de Moda y Ropa",
        "ropa": "Diseño de Moda y Ropa",
        "instagram": "Experto en Instagram (Reels/Post)",
        "redes": "Experto en Instagram (Reels/Post)",
        "tiktok": "Guionista de TikTok Viral",
        "ads": "Copywriter de Anuncios (Ads)",
        "anuncio": "Copywriter de Anuncios (Ads)",
        "seo": "Especialista SEO (Blogs)",
        "community": "Community Manager",
        "naming": "Creador de Nombres (Naming)",
        "nombre": "Creador de Nombres (Naming)",
        "python": "Experto en Python y Datos",
        "datos": "Experto en Python y Datos",
        "negocios": "Consultor de Negocios",
        "empresa": "Consultor de Negocios",
        "pdf": "Analista de Documentos (PDF)",
        "documento": "Analista de Documentos (PDF)",
        "reclutador": "Reclutador / Mejorar CV",
        "cv": "Reclutador / Mejorar CV",
        "email": "Redactor de Correos",
        "correo": "Redactor de Correos",
        "product manager": "Product Manager (PM)",
        "pm": "Product Manager (PM)",
        "ux": "UX Writer / UX Designer",
        "metrics": "Analista de Métricas y KPIs",
        "kpi": "Analista de Métricas y KPIs",
        "prompt engineer": "Prompt Engineer"
    }

    # Frases gatillo para cambio de rol
    triggers = ["actua como", "cambia a", "cambia tu rol a", "ponte en modo", "se un", "sé un", "modo", "quiero hablar con el"]
    
    if any(t in p for t in triggers):
        for key, rol_name in mapa_roles.items():
            if key in p:
                return rol_name
    return None

# --- HERRAMIENTAS ---
def analizar_vision(msg, b64_img, rol):
    client = obtener_cliente()
    try:
        res = client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {"role": "system", "content": f"{rol}. Analiza la imagen."},
                {"role": "user", "content": [{"type": "text", "text": msg}, {"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{b64_img}"}}]}
            ]
        )
        return res.choices[0].message.content
    except Exception as e: return f"Error Vision: {e}"

def generar_imagen(prompt_usuario, estilo):
    client = obtener_cliente()
    
    # 1. REFINADOR "ESPEJO" (LITERAL)
    try:
        system_instruction = """
        ERES UN TRADUCTOR LITERAL DE PROMPTS PARA DALL-E.
        
        INSTRUCCIONES:
        1. NO agregues estilos "futuristas" ni "neón" a menos que el usuario lo pida explícitamente.
        2. APEGO TOTAL al pedido del usuario. Si pide algo simple, el prompt debe ser simple.
        
        Devuelve SOLO el prompt en Inglés.
        """
        
        refinado = client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {"role": "system", "content": system_instruction},
                {"role": "user", "content": f"Usuario: {prompt_usuario}. Contexto de estilo sugerido (ignorar si el usuario pide otro): {estilo}"}
            ]
        )
        prompt_final = refinado.choices[0].message.content
    except:
        prompt_final = prompt_usuario # Fallback directo

    # 2. GENERACIÓN
    try:
        res = client.images.generate(
            model="dall-e-3", 
            prompt=prompt_final, 
            size="1024x1024", 
            quality="standard", 
            style="vivid"
        )
        return res.data[0].url
    except Exception as e:
        if "safety" in str(e).lower(): return "🛡️ Error de seguridad en la imagen."
        return f"⚠️ Error: {e}"

def leer_pdf(file):
    try:
        reader = PdfReader(file)
        return "".join([p.extract_text() for p in reader.pages])[:25000]
    except: return "Error PDF"

def buscar_web(query):
    try:
        t_key = os.environ.get("TAVILY_KEY") or st.secrets["TAVILY_KEY"]
        tavily = TavilyClient(api_key=str(t_key))
        res = tavily.search(query=query, search_depth="advanced")
        return "\n".join([f"- {r['title']}: {r['content']}" for r in res.get('results', [])[:3]])
    except: return "Sin conexión."

# --- PROCESADOR DE TEXTO (STREAMING) ---
def procesar_texto(msg, hist, rol_prompt, web_manual, pdf_ctx, nombre_rol_actual):
    client = obtener_cliente()
    if not client: 
        yield "⚠️ Error API Key."
        return

    ahora = datetime.datetime.now().strftime("%Y-%m-%d %H:%M")
    
    # Auto-Search logic simplificada
    usar_busqueda = web_manual
    debug_msg = ""
    if not usar_busqueda and ("precio" in msg.lower() or "noticia" in msg.lower() or "clima" in msg.lower()):
        usar_busqueda = True
        debug_msg = " [🔎 Web]"

    guia = obtener_guia_dinamica(nombre_rol_actual)
    sys_msg = f"{rol_prompt}. FECHA: {ahora}.\n\n{guia}"
    if pdf_ctx: sys_msg += f"\n\nPDF: {pdf_ctx}"
    
    msgs = [{"role": "system", "content": sys_msg}]
    if usar_busqueda:
        info = buscar_web(msg)
        msgs.append({"role": "system", "content": f"DATOS WEB: {info}"})
    
    # Limpiamos historial
    hist_clean = [m for m in hist if not str(m["content"]).startswith("http")]
    msgs += hist_clean + [{"role": "user", "content": msg}]
    
    try:
        stream = client.chat.completions.create(model="gpt-4o", messages=msgs, stream=True)
        for chunk in stream:
            if chunk.choices[0].delta.content:
                yield chunk.choices[0].delta.content
        if debug_msg: yield debug_msg
    except Exception as e:
        yield f"Error: {e}"

def generar_titulo(msg):
    try:
        return obtener_cliente().chat.completions.create(
            model="gpt-4o-mini", messages=[{"role":"user", "content":f"Título 3 palabras: {msg}"}], max_tokens=10
        ).choices[0].message.content.strip()
    except: return "Nuevo Chat"

# --- DETECTOR DE INTENCIÓN VISUAL ---
def detectar_intencion_imagen(prompt):
    p = prompt.lower().strip()
    directos = ["un logo", "el logo", "crear logo", "una imagen", "la imagen", "generar imagen", "una foto", "un flyer", "opciones visuales"]
    if any(f in p for f in directos): return True
    verbos = ["gener", "crea", "hac", "diseñ", "muestr", "dame", "quier", "pasa", "ver"]
    objetos = ["imagen", "logo", "foto", "flyer", "icono", "boceto", "diseño", "opcion"]
    return any(v in p for v in verbos) and any(o in p for o in objetos)