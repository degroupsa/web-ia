import streamlit as st
import os  
from openai import OpenAI
from tavily import TavilyClient
import datetime
from pypdf import PdfReader
from modules import roles 

# --- MANUAL DE USO DINÁMICO ---
def obtener_guia_dinamica(rol_actual):
    dict_roles = roles.obtener_tareas()
    nombres_roles = ", ".join(dict_roles.keys())
    
    # DETECTIVE DE ROLES: SI ESTAMOS EN MODO GENERAL, ACTIVAR AVISO
    aviso_detective = ""
    if "General" in rol_actual:
        aviso_detective = """
        ⚠️ PROTOCOLO DE EXCELENCIA (MODO GENERAL):
        Si el usuario pide algo específico (Logo, Contrato, Código), NO te niegues.
        PERO, DEBES iniciar tu respuesta con este bloque EXACTO para avisarle:
        
        > ⚠️ **RECOMENDACIÓN KORTEXA:** He notado que pides una tarea especializada. Para resultados de nivel experto, te sugiero cambiar mi rol en el menú lateral.
        
        (Y luego continúa con la tarea normalmente).
        """

    return f"""
    INSTRUCCIONES DEL SISTEMA (KORTEXA AI):

    {aviso_detective}
    
    ⚠️ REGLA SUPREMA: CAPACIDAD VISUAL
    - TÚ SÍ PUEDES GENERAR IMÁGENES (DALL-E 3).
    - Si detectas intención visual ("logo", "foto", "diseño"), CONFIRMA LA ACCIÓN.
    - Ejemplo: "¡Entendido! Estoy creando el diseño ahora mismo..."

    IDENTIDAD:
    - Eres Kortexa AI. Rol Actual: "{rol_actual}".
    - Sé profesional, directo y extremadamente eficiente.

    ROLES DISPONIBLES: [{nombres_roles}]
    """

# --- CLIENTE ---
def obtener_cliente():
    api_key = os.environ.get("OPENAI_API_KEY")
    if not api_key:
        try: api_key = st.secrets["OPENAI_KEY"]
        except: return None
    return OpenAI(api_key=str(api_key))

# --- ROUTER ---
def decidir_si_buscar(prompt):
    client = obtener_cliente()
    if not client: return False
    try:
        res = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": "Responde SI si pregunta datos actuales/noticias. SI NO, responde NO."},
                {"role": "user", "content": prompt}
            ],
            max_tokens=5, temperature=0
        )
        return "SI" in res.choices[0].message.content.strip().upper()
    except: return False

# --- HERRAMIENTAS ---
def analizar_vision(msg, b64_img, rol):
    client = obtener_cliente()
    try:
        res = client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {"role": "system", "content": f"{rol}. Analiza la imagen con detalle extremo."},
                {"role": "user", "content": [{"type": "text", "text": msg}, {"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{b64_img}"}}]}
            ]
        )
        return res.choices[0].message.content
    except Exception as e: return f"Error Vision: {e}"

def generar_imagen(prompt_usuario, estilo):
    client = obtener_cliente()
    
    # 1. REFINADOR DE PROMPT "AWARD WINNING"
    try:
        system_instruction = """
        ERES UN DIRECTOR DE ARTE EXPERTO EN DALL-E 3.
        
        TU MISIÓN: Escribir el prompt visual PERFECTO en INGLÉS.
        
        SI EL ESTILO ES 'ADAPTATIVE' (Modo General):
        - Detecta qué pide el usuario.
        - Si es LOGO: "Vector logo, minimalist, flat design, white background, clean lines".
        - Si es FOTO: "Photorealistic, 8k, cinematic lighting".
        
        SI EL ESTILO ES ESPECÍFICO (Modo Experto):
        - Úsalo como base y poténcialo.
        
        REGLA DE ORO:
        - Si el usuario pide un texto, indícalo: "The text 'EJEMPLO' is integrated elegantly".
        - NO inventes objetos aleatorios. Cíñete al pedido.
        
        SALIDA: Solo el prompt técnico en Inglés.
        """
        
        refinado = client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {"role": "system", "content": system_instruction},
                {"role": "user", "content": f"Usuario: {prompt_usuario}. Estilo Configurado: {estilo}"}
            ]
        )
        prompt_final = refinado.choices[0].message.content

    except:
        prompt_final = f"High quality image of {prompt_usuario}, {estilo}"

    # 2. GENERACIÓN
    try:
        res = client.images.generate(
            model="dall-e-3", 
            prompt=prompt_final, 
            size="1024x1024", 
            quality="hd", 
            style="vivid"
        )
        return res.data[0].url
    except Exception as e:
        err = str(e).lower()
        if "safety" in err:
            return "🛡️ Kortexa Security: La imagen no se pudo generar por políticas de contenido. Intenta suavizar la descripción."
        return f"⚠️ Error Imagen: {e}"

def leer_pdf(file):
    try:
        reader = PdfReader(file)
        return "".join([p.extract_text() for p in reader.pages])[:25000]
    except: return "Error PDF"

def buscar_web(query):
    try:
        t_key = os.environ.get("TAVILY_KEY")
        if not t_key:
            try: t_key = st.secrets["TAVILY_KEY"]
            except: return "Falta API Tavily."
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
    usar_busqueda = web_manual
    debug_msg = ""
    if not usar_busqueda and decidir_si_buscar(msg):
        usar_busqueda = True
        debug_msg = " [🔎 Web]"

    guia = obtener_guia_dinamica(nombre_rol_actual)
    sys_msg = f"{rol_prompt}. FECHA: {ahora}.\n\n{guia}"
    if pdf_ctx: sys_msg += f"\n\nPDF: {pdf_ctx}"
    
    msgs = [{"role": "system", "content": sys_msg}]
    if usar_busqueda:
        info = buscar_web(msg)
        msgs.append({"role": "system", "content": f"DATOS WEB: {info}"})
    
    hist_clean = []
    for m in hist:
        c = str(m["content"])
        if not c.startswith("http") and "⚠️" not in c and "🛡️" not in c:
            hist_clean.append({"role": m["role"], "content": c})
            
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
        client = obtener_cliente()
        return client.chat.completions.create(
            model="gpt-4o-mini", messages=[{"role":"user", "content":f"Título 3 palabras: {msg}"}], max_tokens=10
        ).choices[0].message.content.strip()
    except: return "Nuevo Chat"

# --- DETECTOR DE INTENCIÓN VISUAL ---
def detectar_intencion_imagen(prompt):
    p = prompt.lower().strip()
    frases = [
        "un logo", "el logo", "diseño de logo", "crear logo", 
        "una imagen", "la imagen", "crear imagen", "generar imagen",
        "una foto", "la foto", "foto de",
        "un flyer", "un banner", "un boceto", 
        "opciones visuales", "ejemplos visuales", "muestrame opciones",
        "dame opciones", "pasame opciones"
    ]
    if any(f in p for f in frases): return True
    
    verbos = ["gener", "crea", "hac", "diseñ", "muestr", "da", "quier", "pasa", "ver"]
    objetos = ["imagen", "logo", "foto", "flyer", "icono", "boceto", "diseño", "opcion"]

    tiene_verbo = any(v in p for v in verbos)
    tiene_objeto = any(o in p for o in objetos)
    
    return tiene_verbo and tiene_objeto