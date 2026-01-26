import streamlit as st
from openai import OpenAI
from tavily import TavilyClient
import datetime
from pypdf import PdfReader

# Configurar Cliente
def obtener_cliente():
    try:
        return OpenAI(api_key=str(st.secrets["OPENAI_KEY"]))
    except: return None

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
        res = tavily.search(query=query, search_depth="advanced")
        return "\n".join([f"- {r['title']}: {r['content']}" for r in res.get('results', [])[:3]])
    except: return "Sin conexión."

def procesar_texto(msg, hist, rol, web, pdf_ctx):
    client = obtener_cliente()
    ahora = datetime.datetime.now().strftime("%Y-%m-%d")
    sys_msg = f"{rol}. FECHA: {ahora}."
    if pdf_ctx: sys_msg += f"\n\nCONTEXTO PDF:\n{pdf_ctx}"
    
    msgs = [{"role": "system", "content": sys_msg}]
    if web:
        info = buscar_web(msg)
        msgs.append({"role": "system", "content": f"DATOS WEB: {info}"})
    
    # Limpiar historial (solo texto)
    hist_clean = [{"role": m["role"], "content": m["content"]} for m in hist if not m["content"].startswith("http")]
    msgs += hist_clean + [{"role": "user", "content": msg}]
    
    res = client.chat.completions.create(model="gpt-4o", messages=msgs)
    return res.choices[0].message.content

def generar_titulo(msg):
    try:
        return obtener_cliente().chat.completions.create(
            model="gpt-4o-mini", messages=[{"role":"user", "content":f"Título 3 palabras: {msg}"}], max_tokens=10
        ).choices[0].message.content.strip()
    except: return "Nuevo Chat"

# --- DETECTOR DE INTENCIÓN AUTOMÁTICA ---
def detectar_intencion_imagen(prompt):
    """Devuelve True si el usuario parece querer una imagen"""
    palabras_clave = ["generar imagen", "crear imagen", "dibuja un", "dibújame", "foto de", "imagen de", "ilustración de", "render de", "generame una foto"]
    prompt_lower = prompt.lower()
    return any(k in prompt_lower for k in palabras_clave)