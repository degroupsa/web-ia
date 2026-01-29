import streamlit as st
import requests
import urllib.parse
import socket

# --- 1. DETECCIÓN AUTOMÁTICA DE ENTORNO (LOCAL vs WEB) ---
def is_local_environment():
    """Detecta si estamos corriendo en la PC o en el Servidor."""
    try:
        hostname = socket.gethostname().lower()
        # Si el nombre de la máquina parece una PC, asumimos local
        if "local" in hostname or "desktop" in hostname or "laptop" in hostname:
            return True
        return False
    except:
        return False

# --- 2. CARGAR CLAVES CON SEGURIDAD ---
try:
    # Verificamos si existe la sección [google] en los secretos
    if "google" in st.secrets:
        CLIENT_ID = st.secrets["google"]["client_id"]
        CLIENT_SECRET = st.secrets["google"]["client_secret"]
        
        # Selección Inteligente de URL
        if is_local_environment():
            # Si estoy en mi PC, uso la dirección local
            REDIRECT_URI = st.secrets["google"].get("redirect_uri_local", "http://localhost:8501")
        else:
            # Si estoy en internet, uso la dirección de producción
            REDIRECT_URI = st.secrets["google"].get("redirect_uri_prod", "https://kortexa.com.ar")
    else:
        # Si el archivo existe pero no tiene [google]
        st.error("⚠️ El archivo secrets.toml existe pero le falta la sección [google].")
        CLIENT_ID = None
        CLIENT_SECRET = None
        REDIRECT_URI = None

except FileNotFoundError:
    st.error("⚠️ No se encuentra el archivo .streamlit/secrets.toml")
    CLIENT_ID = None
    REDIRECT_URI = None
except Exception as e:
    # Captura errores generales de carga
    # st.error(f"⚠️ Error leyendo secretos: {e}") # Descomentar para debug
    CLIENT_ID = None
    REDIRECT_URI = None


# URLs de Google
AUTHORIZATION_URL = "https://accounts.google.com/o/oauth2/v2/auth"
TOKEN_URL = "https://oauth2.googleapis.com/token"
USER_INFO_URL = "https://www.googleapis.com/oauth2/v1/userinfo"

def get_login_url():
    """Genera el enlace para el botón de Google."""
    # SI FALTA EL ID, NO GENERAMOS UN LINK ROTO QUE DA ERROR 400
    if not CLIENT_ID or not REDIRECT_URI:
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
    
    # Validación de seguridad
    if not CLIENT_ID or not REDIRECT_URI: 
        st.error("Falta configuración de credenciales.")
        return None

    try:
        token_data = {
            "code": auth_code,
            "client_id": CLIENT_ID,
            "client_secret": CLIENT_SECRET,
            "redirect_uri": REDIRECT_URI,
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
            return None
            
        return user_r.json()
        
    except Exception as e:
        st.error(f"❌ Error interno en google_auth: {e}")
        return None