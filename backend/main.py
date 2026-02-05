import os
import requests
import json
import firebase_admin
from firebase_admin import credentials, auth
from fastapi import FastAPI, HTTPException, Header, Depends
from pydantic import BaseModel
from typing import List, Optional

# --- CONFIGURACIÓN ---
# ⚠️ TU API KEY DE GOOGLE (IA)
GOOGLE_API_KEY = "AIzaSyCi0nXWreFloqaqB_QSt3iQeVgDmHwofmM" 

URL_BASE = "https://generativelanguage.googleapis.com/v1beta/models"

# Modelos
MOTOR_FREE = "gemini-2.5-flash"
MOTOR_PRO = "gemini-2.5-pro"
MOTOR_IMAGEN = "gemini-2.5-flash-image"

# --- INICIALIZACIÓN DE FIREBASE (SEGURIDAD) ---
# Esto permite al Backend verificar quién es el usuario
if not firebase_admin._apps:
    try:
        # Buscamos la llave en la carpeta raíz (un nivel arriba de 'backend/')
        ruta_key = os.path.join(os.path.dirname(os.path.dirname(__file__)), "firebase_key.json")
        
        if os.path.exists(ruta_key):
            cred = credentials.Certificate(ruta_key)
            firebase_admin.initialize_app(cred)
            print("🔐 Firebase Admin conectado exitosamente.")
        else:
            print(f"⚠️ ADVERTENCIA: No se encontró firebase_key.json en {ruta_key}")
    except Exception as e:
        print(f"Error iniciando Firebase: {e}")

# --- ESTRUCTURAS DE DATOS ---
class Mensaje(BaseModel):
    role: str
    content: str

class PeticionChat(BaseModel):
    mensaje_usuario: str
    historial: List[Mensaje] = []
    plan: str = "free"
    rol_actual: str = "Asistente General"
    # Nuevo: Token de usuario (opcional por ahora para no romper tu frontend actual)
    token_usuario: Optional[str] = None 

# --- INICIALIZAR APP ---
app = FastAPI(
    title="Kortexa API (Segura)",
    version="3.0",
    description="Backend con Capa de Seguridad Firebase"
)

# --- FUNCIÓN DE SEGURIDAD (EL PORTERO) ---
async def verificar_usuario(authorization: str = Header(None)):
    """
    Este es el 'Portero' de la discoteca.
    Verifica que el usuario traiga un Token válido de Firebase.
    """
    # MODO PERMISIVO (TEMPORAL): Si no hay token, dejamos pasar como "invitado"
    # Esto es para que tu Streamlit actual no deje de funcionar hoy.
    if not authorization:
        return {"uid": "invitado", "email": "anonimo"}

    try:
        token = authorization.replace("Bearer ", "")
        decoded_token = auth.verify_id_token(token)
        return decoded_token # Devuelve los datos del usuario (uid, email)
    except Exception as e:
        # Si el token es falso o expiró, denegamos acceso
        print(f"Intento de acceso inválido: {e}")
        # En el futuro, aquí lanzaremos HTTPException(401)
        return {"uid": "invitado", "email": "error_token"}

# --- LÓGICA DE NEGOCIO (IGUAL QUE ANTES) ---

def api_gemini_texto(historial_formateado, modelo):
    url = f"{URL_BASE}/{modelo}:generateContent?key={GOOGLE_API_KEY}"
    headers = {"Content-Type": "application/json"}
    
    tools_payload = {
        "function_declarations": [
            {
                "name": "herramienta_generar_imagen",
                "description": "Genera una imagen visual.",
                "parameters": {
                    "type": "OBJECT",
                    "properties": {
                        "descripcion_detallada": {"type": "STRING"},
                    },
                    "required": ["descripcion_detallada"]
                }
            }
        ]
    }

    data = {
        "contents": historial_formateado,
        "tools": [tools_payload]
    }
    
    try:
        response = requests.post(url, headers=headers, json=data)
        if response.status_code != 200: return None, f"Error Google Texto: {response.text}"
        return response.json(), None
    except Exception as e: return None, str(e)

def api_gemini_imagen(prompt):
    url = f"{URL_BASE}/{MOTOR_IMAGEN}:generateContent?key={GOOGLE_API_KEY}"
    headers = {"Content-Type": "application/json"}
    data = {"contents": [{"parts": [{"text": prompt}]}]}
    try:
        response = requests.post(url, headers=headers, json=data)
        if response.status_code != 200: return None, f"Error HTTP Google: {response.text}"
        try:
            datos = response.json()
            partes = datos["candidates"][0]["content"]["parts"]
            for parte in partes:
                if "inlineData" in parte:
                    b64 = parte["inlineData"]["data"]
                    mime = parte["inlineData"]["mimeType"]
                    return f"data:{mime};base64,{b64}", None
            return None, f"⚠️ Google respondió solo texto: {json.dumps(datos)}"
        except Exception as e: return None, f"Error leyendo JSON: {str(e)}"
    except Exception as e: return None, str(e)

# --- ENDPOINTS ---

@app.get("/")
def home():
    return {"status": "Kortexa Brain Secure 🔒"}

@app.post("/v1/chat")
async def chatear(peticion: PeticionChat, authorization: Optional[str] = Header(None)):
    
    # 1. VERIFICACIÓN DE SEGURIDAD 👮‍♂️
    usuario = await verificar_usuario(authorization)
    print(f"👤 Solicitud de: {usuario.get('email', 'Anónimo')} (UID: {usuario.get('uid')})")
    
    # Aquí podríamos bloquear si el usuario no pagó, etc.
    
    # --- RESTO DEL CÓDIGO (Igual que antes) ---
    if "TU_API_KEY" in GOOGLE_API_KEY:
        raise HTTPException(status_code=500, detail="Falta API KEY")

    modelo = MOTOR_PRO if peticion.plan == "pro" else MOTOR_FREE
    
    contents = []
    sys_msg = f"SYSTEM: Eres Kortexa (Plan {peticion.plan}). Rol: {peticion.rol_actual}."
    contents.append({"role": "user", "parts": [{"text": sys_msg}]})
    contents.append({"role": "model", "parts": [{"text": "OK"}]})
    
    for m in peticion.historial:
        role = "user" if m.role == "user" else "model"
        if "data:image" not in m.content:
            contents.append({"role": role, "parts": [{"text": m.content}]})

    contents.append({"role": "user", "parts": [{"text": peticion.mensaje_usuario}]})

    resp_json, error = api_gemini_texto(contents, modelo)
    
    if error: raise HTTPException(status_code=502, detail=f"Error Motor IA: {error}")

    try:
        candidato = resp_json["candidates"][0]["content"]["parts"][0]
        
        if "functionCall" in candidato:
            fn = candidato["functionCall"]
            if fn["name"] == "herramienta_generar_imagen":
                if peticion.plan == "free":
                    return {"respuesta": "🔒 Función Premium: Actualiza a PRO."}
                
                prompt_img = fn["args"].get("descripcion_detallada")
                url_img, err_img = api_gemini_imagen(prompt_img)
                if err_img: return {"respuesta": f"❌ ERROR: {err_img}"}
                return {"respuesta": f"![Imagen Generada]({url_img})"}

        if "text" in candidato: return {"respuesta": candidato["text"]}
            
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Excepción: {str(e)}")

    return {"respuesta": "Sin contenido."}