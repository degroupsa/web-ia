import streamlit as st
from openai import OpenAI
from tavily import TavilyClient
import datetime # <--- NUEVO: El reloj de Python

# --- CONFIGURACIÓN DE LLAVES SEGURA ---
# Intentamos leer de los Secretos de la Nube, si falla, pedimos que configuren
try:
    OPENAI_KEY = st.secrets["OPENAI_KEY"]
    TAVILY_KEY = st.secrets["TAVILY_KEY"]
except:
    # Esto es solo para que no explote si lo corres local sin secrets.toml
    # Pero lo ideal es configurar secrets localmente también.
    st.error("⚠️ Faltan las claves en los Secretos.")
    st.stop()

def obtener_cliente():
    return OpenAI(api_key=OPENAI_KEY)

def buscar_en_web(consulta):
    try:
        tavily = TavilyClient(api_key=TAVILY_KEY)
        respuesta = tavily.search(query=consulta, search_depth="advanced")
        contexto = []
        for resultado in respuesta['results'][:3]:
            contexto.append(f"- Fuente: {resultado['title']}\n  Info: {resultado['content']}")
        return "\n\n".join(contexto)
    except Exception as e:
        return f"Error web: {e}"

# --- FUNCIÓN PRINCIPAL MEJORADA ---
def respuesta_inteligente(mensaje_usuario, historial_previo, prompt_rol, usar_internet=False):
    client = obtener_cliente()
    
    # 1. OBTENER HORA REAL DEL SISTEMA (Tu PC)
    ahora = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    dia_semana = datetime.datetime.now().strftime("%A") # Da el día en inglés, pero sirve
    
    # 2. INYECTAR EL RELOJ EN EL SISTEMA
    # Le decimos a la IA: "Oye, hoy es ESTE día y hora exacta".
    prompt_sistema_base = f"""
    {prompt_rol}
    
    [DATOS DEL SISTEMA]
    FECHA Y HORA ACTUAL REAL: {ahora} ({dia_semana}).
    Usa esta fecha como verdad absoluta. No la busques en internet.
    """
    
    mensajes_sistema = [{"role": "system", "content": prompt_sistema_base}]
    
    # 3. INTERNET (Si está activado)
    if usar_internet:
        print(f"🌍 Investigando: {mensaje_usuario}")
        datos_web = buscar_en_web(mensaje_usuario)
        inyeccion_web = f"INFORMACIÓN DE INTERNET:\n{datos_web}"
        mensajes_sistema.append({"role": "system", "content": inyeccion_web})

    # 4. ARMAR EL PAQUETE FINAL
    mensajes_completos = mensajes_sistema + historial_previo + [{"role": "user", "content": mensaje_usuario}]

    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=mensajes_completos
    )
    return response.choices[0].message.content

# --- (RESTO DE FUNCIONES IGUAL) ---
def obtener_roles():
    return {
        "Junior Mentor 🐣": {"desc": "Explica simple.", "prompt": "Eres un mentor paciente."},
        "Senior Architect 🏗️": {"desc": "Experto técnico.", "prompt": "Eres un Arquitecto Senior critico."},
        "Investigador Web 🌍": {"desc": "Busca noticias.", "prompt": "Eres un investigador de noticias actuales."}
    }

def generar_prompt_experto(idea, tipo):
    client = obtener_cliente()
    res = client.chat.completions.create(model="gpt-4o-mini", messages=[{"role":"user", "content":f"Prompt para {tipo}: {idea}"}])
    return res.choices[0].message.content