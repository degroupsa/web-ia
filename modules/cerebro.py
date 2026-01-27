import streamlit as st

from openai import OpenAI

from tavily import TavilyClient

import datetime

from pypdf import PdfReader



# --- CLIENTE ---

def obtener_cliente():

    try:

        return OpenAI(api_key=str(st.secrets["OPENAI_KEY"]))

    except: return None



# --- 1. ROUTER INTELIGENTE (EL CEREBRO DEL CEREBRO) ---

def decidir_si_buscar(prompt):

    """

    Usa un modelo rápido (mini) para decidir si la pregunta requiere internet.

    Devuelve True si necesita buscar, False si no.

    """

    client = obtener_cliente()

    try:

        res = client.chat.completions.create(

            model="gpt-4o-mini", # Usamos el barato para pensar rápido

            messages=[

                {"role": "system", "content": "Eres un clasificador. Responde solo 'SI' si el usuario pregunta sobre: noticias, clima, hora actual, precios, eventos recientes, personas famosas actuales o datos factuales que cambian. Responde 'NO' si es creatividad, resumen, saludo, código o conocimiento general histórico."},

                {"role": "user", "content": prompt}

            ],

            max_tokens=5,

            temperature=0

        )

        decision = res.choices[0].message.content.strip().upper()

        return "SI" in decision

    except:

        return False # Ante la duda, no buscamos para no romper nada



# --- 2. HERRAMIENTAS ---

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



def generar_imagen(prompt, estilo):

    client = obtener_cliente()

    try:

        res = client.images.generate(

            model="dall-e-3", prompt=f"ESTILO: {estilo}. DIBUJA: {prompt}", size="1024x1024", quality="hd", style="vivid"

        )

        return res.data[0].url

    except Exception as e: return f"Error DALL-E: {e}"



def leer_pdf(file):

    try:

        reader = PdfReader(file)

        return "".join([p.extract_text() for p in reader.pages])[:25000]

    except: return "Error PDF"



def buscar_web(query):

    try:

        tavily = TavilyClient(api_key=str(st.secrets["TAVILY_KEY"]))

        # Search depth advanced nos da mejores resultados

        res = tavily.search(query=query, search_depth="advanced")

        return "\n".join([f"- {r['title']}: {r['content']}" for r in res.get('results', [])[:3]])

    except: return "Sin conexión."



# --- 3. PROCESADOR PRINCIPAL (CON AUTO-PILOTO) ---

def procesar_texto(msg, hist, rol, web_manual, pdf_ctx):

    client = obtener_cliente()

    

    # A) Detectar Hora Exacta (Para que no se pierda en el tiempo)

    ahora = datetime.datetime.now().strftime("%Y-%m-%d %H:%M UTC")

    

    # B) MODO AUTO-PILOTO DE BÚSQUEDA

    # Si el usuario NO activó el botón, verificamos si hace falta activarlo sola.

    usar_busqueda = web_manual

    debug_msg = ""

    

    if not usar_busqueda:

        if decidir_si_buscar(msg):

            usar_busqueda = True

            debug_msg = " [🔎 Auto-Búsqueda Activada]"



    # C) Construcción del Prompt del Sistema

    sys_msg = f"{rol}. FECHA Y HORA ACTUAL: {ahora}. Tu objetivo es ser la IA más precisa y útil del mundo."

    if pdf_ctx: sys_msg += f"\n\nCONTEXTO PDF:\n{pdf_ctx}"

    

    msgs = [{"role": "system", "content": sys_msg}]

    

    # D) Inyectar Búsqueda si es necesario

    if usar_busqueda:

        info = buscar_web(msg)

        msgs.append({"role": "system", "content": f"DATOS WEB EN TIEMPO REAL (Úsalos si es necesario): {info}"})

    

    # E) Historial y Llamada

    hist_clean = [{"role": m["role"], "content": m["content"]} for m in hist if not m["content"].startswith("http")]

    msgs += hist_clean + [{"role": "user", "content": msg}]

    

    res = client.chat.completions.create(model="gpt-4o", messages=msgs)

    return res.choices[0].message.content + debug_msg



def generar_titulo(msg):

    try:

        return obtener_cliente().chat.completions.create(

            model="gpt-4o-mini", messages=[{"role":"user", "content":f"Título 3 palabras: {msg}"}], max_tokens=10

        ).choices[0].message.content.strip()

    except: return "Nuevo Chat"



# --- DETECTOR DE INTENCIÓN DE IMAGEN ---

def detectar_intencion_imagen(prompt):

    keywords = ["generar imagen", "crear imagen", "dibuja un", "dibújame", "foto de", "imagen de", "ilustración de", "render de"]

    return any(k in prompt.lower() for k in keywords)