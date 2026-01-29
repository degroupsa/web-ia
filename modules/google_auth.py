import streamlit as st
import requests
import urllib.parse
import socket

# --- 1. DETECCIÓN AUTOMÁTICA DE ENTORNO (LOCAL vs WEB) ---
def is_local_environment():
    """Devuelve True si estamos en la PC, False si estamos en la Web."""
    try:
        hostname = socket.gethostname().lower()
        # Si el nombre de la máquina tiene 'local', 'desktop' o 'laptop', es tu PC
        if "local" in hostname or "desktop" in hostname or "laptop" in hostname:
            return True
        return False
    except:
        return False

# --- 2. CARGAR CLAVES DESDE SECRETS ---
try:
    if "google" in st.secrets:
        CLIENT_ID = st.secrets["google"]["client_id"]
        CLIENT_SECRET = st.secrets["google"]["client_secret"]
        
        # Lógica de selección de URI
        if is_local_environment():
            # Si estoy en mi PC, uso la dirección local
            REDIRECT_URI = st.secrets["google"].get("redirect_uri_local", "http://localhost:8501")
            # print("🔹 MODO LOCAL DETECTADO") # Debug en consola
        else:
            # Si estoy en internet, uso la dirección de producción
            REDIRECT_URI = st.secrets["google"].get("redirect_uri_prod", "https://kortexa.com.ar")
            # print("🔸 MODO PRODUCCIÓN DETECTADO") # Debug en consola
    else:
        # Si falta la sección [google] en secrets.toml
        CLIENT_ID = None
        CLIENT_SECRET = None
        REDIRECT_URI = None

except Exception as e:
    # Captura errores si el archivo secrets.toml está mal escrito
    st.error(f"Error crítico leyendo secrets.toml: {e}")
    CLIENT_ID = None
    REDIRECT_URI = None


# URLs de Google
AUTHORIZATION_URL = "https://accounts.google.com/o/oauth2/v2/auth"
TOKEN_URL = "https://oauth2.googleapis.com/token"
USER_INFO_URL = "https://www.googleapis.com/oauth2/v1/userinfo"

def get_login_url():
    """Genera el enlace para el botón de Google."""
    # Validación de seguridad: Si no hay ID o URI, no generamos link roto
    if not CLIENT_ID or not REDIRECT_URI:
        st.error("⚠️ Falta configuración de Google (Client ID o Redirect URI). Revisa secrets.toml")
        return "#"
        
    params = {
        "client_id": CLIENT_ID,
        "redirect_uri": REDIRECT_URI,
        "response_type": "code",
        "scope": "openid email profile",
        "access_type": "offline",
        "prompt": "select_account"
    }
    return f"{AUTHORIZATION_URL}?{urllib.parse.urlencode(params)}"

def get_user_info(auth_code):
    """Intercambia el código de autorización por los datos del usuario."""
    
    # Validación doble
    if not CLIENT_ID or not REDIRECT_URI: 
        return None

    try:
        token_data = {
            "code": auth_code,
            "client_id": CLIENT_ID,
            "client_secret": CLIENT_SECRET,
            "redirect_uri": REDIRECT_URI, # ¡Debe ser IDÉNTICA a la usada en get_login_url!
            "grant_type": "authorization_code",
        }
        
        token_r = requests.post(TOKEN_URL, data=token_data)
        
        # --- DIAGNÓSTICO DE ERRORES ---
        if not token_r.ok:
            st.error("❌ Error de conexión con Google.")
            st.code(f"Estado: {token_r.status_code}\nRespuesta: {token_r.text}\nURI usada: {REDIRECT_URI}")
            st.stop()
            return None
            
        token_json = token_r.json()
        access_token = token_json.get("access_token")

        headers = {"Authorization": f"Bearer {access_token}"}
        user_r = requests.get(USER_INFO_URL, headers=headers)
        
        if not user_r.ok:
            st.error("❌ Error obteniendo perfil de usuario.")
            return None
            
        return user_r.json()
        
    except Exception as e:
        st.error(f"❌ Error interno en google_auth: {e}")
        return None