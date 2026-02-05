import time
import google.generativeai as genai
from modules import tools
import streamlit as st

# ==========================================
# 🔑 CONFIGURACIÓN DE GEMINI
# ==========================================
GEMINI_API_KEY = "AIzaSyCi0nXWreFloqaqB_QSt3iQeVgDmHwofmM" 

try:
    genai.configure(api_key=GEMINI_API_KEY)
except Exception as e:
    print(f"Error configurando: {e}")

generation_config = {
    "temperature": 0.85,
    "top_p": 0.95,
    "top_k": 64,
    "max_output_tokens": 8192,
}

safety_settings = [
    {"category": "HARM_CATEGORY_HARASSMENT", "threshold": "BLOCK_NONE"},
    {"category": "HARM_CATEGORY_HATE_SPEECH", "threshold": "BLOCK_NONE"},
    {"category": "HARM_CATEGORY_SEXUALLY_EXPLICIT", "threshold": "BLOCK_NONE"},
    {"category": "HARM_CATEGORY_DANGEROUS_CONTENT", "threshold": "BLOCK_NONE"},
]

def obtener_modelo_exacto(plan):
    # LISTA EXACTA BASADA EN TU CAPTURA DE PANTALLA (VERDE)
    if plan in ["pro", "enterprise"]:
        return [
            "gemini-3-pro-preview",    # Tu modelo más potente (detectado en lista)
            "gemini-2.5-pro",          # Respaldo sólido (detectado en lista)
            "nano-banana-pro-preview", # Tu versión visual (detectado en lista)
            "gemini-2.0-flash-exp"     # Último recurso
        ]
    else:
        return ["gemini-2.5-flash", "gemini-flash-latest"]

def chat_con_gemini(mensaje_usuario, mensaje_con_contexto, historial_previo, nombre_rol_actual, plan="free", token=None, usar_img_toggle=False):
    
    # ---------------------------------------------------------
    # 1. MODO IMAGEN ACTIVADO
    # ---------------------------------------------------------
    tiene_permiso_img = plan in ["pro", "enterprise"]

    if usar_img_toggle and tiene_permiso_img:
        try:
            url = tools.generar_imagen(mensaje_usuario)
            yield f"![Imagen Generada]({url})\n\n> **Kortexa Art Studio:** {mensaje_usuario}"
            return 
        except Exception as e:
            yield f"⚠️ Error visual: {e}"
            return
            
    elif usar_img_toggle and not tiene_permiso_img:
         yield "🔒 **Acceso Denegado:** Kortexa Art Studio requiere Plan PRO."
         return

    # ---------------------------------------------------------
    # 2. MODO TEXTO (Gemini 3.0 / 2.5)
    # ---------------------------------------------------------
    modelos_candidatos = obtener_modelo_exacto(plan)
    
    chat_history = []
    for m in historial_previo:
        if isinstance(m, dict):
            role = "user" if m["role"] == "user" else "model"
            content = str(m.get("content", ""))
            if "![" not in content: 
                chat_history.append({"role": role, "parts": [content]})

    for nombre_modelo in modelos_candidatos:
        try:
            # LÓGICA DE ALERTA VISUAL
            instruccion_extra = ""
            if not usar_img_toggle:
                # Si está apagado, le obligamos a mostrar una ALERTA VISIBLE
                instruccion_extra = """
                ATENCIÓN: El módulo de imágenes está APAGADO.
                Si el usuario pide una imagen, responde EXACTAMENTE con este formato:
                
                > ⚠️ **SISTEMA VISUAL EN ESPERA**
                >
                > Para generar imágenes, por favor **activa el interruptor 'Imágenes'** en el menú lateral.
                """

            identidad = f"""
            Eres Kortexa AI, un desarrollo tecnológico de **DE Group Enterprise**.
            Sistema: **Inteligencia Neuronal v3.0**.
            Rol Actual: {nombre_rol_actual}.
            
            DIRECTRICES:
            1. Si te presentas, di: "Soy Kortexa AI, desarrollo de DE Group Enterprise, Sistema de Inteligencia Neuronal v3.0".
            2. Nunca menciones a Google.
            3. {instruccion_extra}
            """
            
            model = genai.GenerativeModel(
                model_name=nombre_modelo,
                generation_config=generation_config,
                safety_settings=safety_settings,
                system_instruction=identidad
            )
            chat_session = model.start_chat(history=chat_history)
            response = chat_session.send_message(mensaje_con_contexto, stream=True)
            
            texto_completo = "" 
            for chunk in response:
                if chunk.text:
                    texto_completo += chunk.text 
                    yield texto_completo 
                    time.sleep(0.01)
            return 

        except Exception as e:
            continue 

    yield f"⚠️ **Error de Sistema:** No se pudo conectar con los modelos 3.0 ni 2.5."